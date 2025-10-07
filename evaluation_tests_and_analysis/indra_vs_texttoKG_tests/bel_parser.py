"""BEL Statement Parser and Normalizer.

This module provides utilities for parsing, normalizing, and comparing
BEL (Biological Expression Language) statements from different sources.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class BELEntity:
    """Represents a biological entity extracted from BEL syntax."""

    namespace: Optional[str]  # e.g., "HGNC", "GO", "CHEBI"
    identifier: Optional[str]  # e.g., "AKT1", "0006468"
    raw_text: str             # Full original text

    @property
    def core_id(self) -> str:
        """Return the core identifier for matching."""
        if self.namespace and self.identifier:
            return f"{self.namespace}:{self.identifier}"
        return self.raw_text

    def __hash__(self):
        return hash(self.core_id)

    def __eq__(self, other):
        if not isinstance(other, BELEntity):
            return False
        return self.core_id == other.core_id


@dataclass
class BELModification:
    """Represents a protein modification in BEL."""

    mod_type: str           # e.g., "Ph", "Ac", "Me"
    residue: Optional[str]  # e.g., "Ser", "Thr", "Tyr"
    position: Optional[int] # e.g., 326

    def matches(self, other: 'BELModification', strict: bool = True) -> bool:
        """Check if two modifications match.

        Args:
            other: Another modification to compare
            strict: If True, require exact residue/position match
        """
        if self.mod_type != other.mod_type:
            return False

        if strict:
            return (self.residue == other.residue and
                    self.position == other.position)

        # Relaxed: just mod_type matches
        return True


@dataclass
class BELComponent:
    """Represents a BEL subject or object component."""

    core_entity: BELEntity
    has_activity: bool = False
    activity_type: Optional[str] = None  # e.g., "kinase activity"
    modification: Optional[BELModification] = None
    is_complex: bool = False
    complex_members: List[BELEntity] = None
    raw_text: str = ""

    def __post_init__(self):
        if self.complex_members is None:
            self.complex_members = []

    def get_all_entities(self) -> Set[BELEntity]:
        """Get all entities involved in this component."""
        entities = {self.core_entity}
        if self.complex_members:
            entities.update(self.complex_members)
        return entities


@dataclass
class BELStatement:
    """Parsed BEL statement with structured components."""

    subject: BELComponent
    relationship: Optional[str]
    object: Optional[BELComponent]
    raw_statement: str

    def is_comparable(self) -> bool:
        """Check if this is a relational statement (has subject, rel, object)."""
        return self.relationship is not None and self.object is not None


class BELParser:
    """Parser for BEL statements into structured components."""

    # BEL relationship types
    RELATIONSHIPS = [
        'directlyIncreases', 'directlyDecreases',
        'increases', 'decreases',
        'causesNoChange', 'cnc',
        'association',
        'isA', 'partOf', 'hasComponent',
        'positiveCorrelation', 'pos',
        'negativeCorrelation', 'neg',
        'regulates', 'reg'
    ]

    # Relationship compatibility groups
    RELATIONSHIP_GROUPS = {
        'positive': {'increases', 'directlyIncreases', 'pos', 'positiveCorrelation'},
        'negative': {'decreases', 'directlyDecreases', 'neg', 'negativeCorrelation'},
        'structural': {'partOf', 'hasComponent', 'isA'},
        'regulatory': {'regulates', 'reg'},
        'neutral': {'association', 'causesNoChange', 'cnc'}
    }

    # Modification type mappings (order matters - more specific patterns first)
    MODIFICATION_MAPPINGS = {
        # INDRA format with GO IDs and annotations
        r'go:0006468 ! "[^"]+"': 'Ph',  # go:0006468 ! "protein phosphorylation"
        r'go:0006473 ! "[^"]+"': 'Ac',  # go:0006473 ! "protein acetylation"
        r'go:0006479 ! "[^"]+"': 'Me',  # go:0006479 ! "protein methylation"
        r'go:0016567 ! "[^"]+"': 'Ub',  # go:0016567 ! "protein ubiquitination"
        r'go:0016925 ! "[^"]+"': 'Sumo',  # go:0016925 ! "protein sumoylation"
        # GO IDs without annotations
        r'go:0006468': 'Ph',  # phosphorylation
        r'go:0006473': 'Ac',  # acetylation
        r'go:0006479': 'Me',  # methylation
        r'go:0016567': 'Ub',  # ubiquitination
        r'go:0016925': 'Sumo', # sumoylation
        # Text descriptions
        r'phosphorylation': 'Ph',
        r'acetylation': 'Ac',
        r'methylation': 'Me',
        r'ubiquitination': 'Ub',
        r'ubiquitylation': 'Ub',
        r'sumoylation': 'Sumo',
        # Standard abbreviations (keep as-is)
        r'\bPh\b': 'Ph',
        r'\bAc\b': 'Ac',
        r'\bMe\b': 'Me',
        r'\bUb\b': 'Ub',
        r'\bSumo\b': 'Sumo',
    }

    def __init__(self):
        # Sort relationships by length (longest first) to avoid partial matches
        self.relationships = sorted(self.RELATIONSHIPS, key=len, reverse=True)

    def normalize_indra_format(self, text: str) -> str:
        """Convert INDRA format 'HGNC:391 ! AKT1' to 'HGNC:AKT1'."""
        # Pattern: namespace:number ! name
        pattern = r'\b([A-Z][A-Z0-9]*):[\w\d]+ ! ([\w\d]+)'
        return re.sub(pattern, r'\1:\2', text)

    def normalize_modifications(self, text: str) -> str:
        """Normalize modification terms to standard abbreviations."""
        normalized = text
        for pattern, replacement in self.MODIFICATION_MAPPINGS.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        # Clean up quotes around modification types
        normalized = re.sub(r'["\']([A-Z][a-z]+)["\']', r'\1', normalized)

        return normalized

    def extract_entity(self, text: str) -> BELEntity:
        """Extract entity from BEL text."""
        # Look for namespace:identifier pattern
        namespace_pattern = r'\b([A-Z][A-Z0-9]+):([A-Za-z0-9_\-]+|"[^"]+")'
        match = re.search(namespace_pattern, text)

        if match:
            namespace = match.group(1)
            identifier = match.group(2).strip('"')
            return BELEntity(namespace=namespace, identifier=identifier, raw_text=text)

        # Fallback: use raw text
        return BELEntity(namespace=None, identifier=None, raw_text=text.strip())

    def extract_modification(self, text: str) -> Optional[BELModification]:
        """Extract modification from pmod() syntax."""
        # Pattern: pmod(Type, Residue, Position) or pmod(Type)
        pmod_pattern = r'pmod\(([^,\)]+)(?:,\s*([A-Za-z]{3})(?:,\s*(\d+))?)?\)'
        match = re.search(pmod_pattern, text)

        if not match:
            return None

        mod_type = self.normalize_modifications(match.group(1).strip())
        residue = match.group(2) if match.group(2) else None
        position = int(match.group(3)) if match.group(3) else None

        return BELModification(mod_type=mod_type, residue=residue, position=position)

    def parse_component(self, text: str) -> BELComponent:
        """Parse a BEL component (subject or object)."""
        text = text.strip()
        normalized_text = self.normalize_indra_format(text)
        normalized_text = self.normalize_modifications(normalized_text)

        # Check for complex
        if normalized_text.startswith('complex('):
            return self._parse_complex(normalized_text)

        # Check for activity
        has_activity = normalized_text.startswith('act(')
        activity_type = None

        if has_activity:
            # Extract activity type from ma() if present
            ma_pattern = r'ma\(([^)]+)\)'
            ma_match = re.search(ma_pattern, normalized_text)
            if ma_match:
                activity_type = ma_match.group(1).strip('"\'')

            # Extract the protein part
            # Pattern: act(p(...), ma(...)) or act(p(...))
            protein_pattern = r'act\((p\([^)]+\))'
            protein_match = re.search(protein_pattern, normalized_text)
            if protein_match:
                protein_text = protein_match.group(1)
            else:
                protein_text = normalized_text
        else:
            protein_text = normalized_text

        # Extract entity
        entity = self.extract_entity(protein_text)

        # Extract modification
        modification = self.extract_modification(protein_text)

        return BELComponent(
            core_entity=entity,
            has_activity=has_activity,
            activity_type=activity_type,
            modification=modification,
            raw_text=text
        )

    def _parse_complex(self, text: str) -> BELComponent:
        """Parse a complex statement."""
        # Extract members from complex(p(...), p(...), ...)
        member_pattern = r'p\([^)]+\)'
        members = re.findall(member_pattern, text)

        member_entities = [self.extract_entity(m) for m in members]

        # Use first member as core entity
        core_entity = member_entities[0] if member_entities else BELEntity(None, None, text)

        return BELComponent(
            core_entity=core_entity,
            is_complex=True,
            complex_members=member_entities,
            raw_text=text
        )

    def parse(self, statement: str) -> BELStatement:
        """Parse a complete BEL statement."""
        statement = statement.strip()

        # Normalize formats
        normalized = self.normalize_indra_format(statement)
        normalized = self.normalize_modifications(normalized)

        # Find relationship
        relationship = None
        rel_start = -1
        rel_end = -1

        for rel in self.relationships:
            pattern = r'\b' + re.escape(rel) + r'\b'
            match = re.search(pattern, normalized)
            if match:
                relationship = rel
                rel_start = match.start()
                rel_end = match.end()
                break

        # Extract components
        if relationship:
            subject_text = normalized[:rel_start].strip()
            object_text = normalized[rel_end:].strip()

            subject = self.parse_component(subject_text)
            obj = self.parse_component(object_text)

            return BELStatement(
                subject=subject,
                relationship=relationship,
                object=obj,
                raw_statement=statement
            )
        else:
            # No relationship found - just a subject
            subject = self.parse_component(normalized)
            return BELStatement(
                subject=subject,
                relationship=None,
                object=None,
                raw_statement=statement
            )

    def get_relationship_group(self, relationship: str) -> Optional[str]:
        """Get the semantic group for a relationship."""
        for group, rels in self.RELATIONSHIP_GROUPS.items():
            if relationship in rels:
                return group
        return None

    def relationships_compatible(self, rel1: str, rel2: str) -> bool:
        """Check if two relationships are semantically compatible."""
        if rel1 == rel2:
            return True

        group1 = self.get_relationship_group(rel1)
        group2 = self.get_relationship_group(rel2)

        return group1 == group2 and group1 is not None


class BELComparator:
    """Compare BEL statements using entity-focused matching."""

    def __init__(self, parser: BELParser = None):
        self.parser = parser or BELParser()

    def calculate_match_score(self, stmt1: BELStatement, stmt2: BELStatement) -> Tuple[float, Dict]:
        """Calculate match score between two BEL statements.

        Returns:
            Tuple of (score, details_dict)
        """
        details = {
            'comparable': False,
            'core_entities_match': False,
            'relationship_match': False,
            'relationship_compatible': False,
            'modification_match': False,
            'activity_match': False,
            'components': {}
        }

        score = 0.0

        # Both must be relational statements to be comparable
        if not (stmt1.is_comparable() and stmt2.is_comparable()):
            return 0.0, details

        # Level 0: Core entity matching (required for comparability)
        subj_entities1 = stmt1.subject.get_all_entities()
        subj_entities2 = stmt2.subject.get_all_entities()
        obj_entities1 = stmt1.object.get_all_entities()
        obj_entities2 = stmt2.object.get_all_entities()

        subject_match = bool(subj_entities1 & subj_entities2)
        object_match = bool(obj_entities1 & obj_entities2)

        details['components']['subject_entities_match'] = subject_match
        details['components']['object_entities_match'] = object_match

        # Not comparable if core entities don't match
        if not (subject_match and object_match):
            return 0.0, details

        details['comparable'] = True
        details['core_entities_match'] = True

        # Level 1: Relationship scoring
        if stmt1.relationship == stmt2.relationship:
            score += 0.30
            details['relationship_match'] = True
            details['relationship_compatible'] = True
        elif self.parser.relationships_compatible(stmt1.relationship, stmt2.relationship):
            score += 0.20
            details['relationship_compatible'] = True

        # Level 2: Modification details (subject)
        subj_mod_score = 0.0
        subj_mod_exact = False
        if stmt1.subject.modification and stmt2.subject.modification:
            if stmt1.subject.modification.matches(stmt2.subject.modification, strict=True):
                subj_mod_score = 0.25
                subj_mod_exact = True
            elif stmt1.subject.modification.matches(stmt2.subject.modification, strict=False):
                subj_mod_score = 0.10  # Partial credit for same mod type
        elif stmt1.subject.modification is None and stmt2.subject.modification is None:
            subj_mod_score = 0.25  # Both have no modification
        # If only one has modification, score stays 0

        # Level 2: Modification details (object)
        obj_mod_score = 0.0
        obj_mod_exact = False
        if stmt1.object.modification and stmt2.object.modification:
            if stmt1.object.modification.matches(stmt2.object.modification, strict=True):
                obj_mod_score = 0.25
                obj_mod_exact = True
            elif stmt1.object.modification.matches(stmt2.object.modification, strict=False):
                obj_mod_score = 0.10
        elif stmt1.object.modification is None and stmt2.object.modification is None:
            obj_mod_score = 0.25

        score += subj_mod_score + obj_mod_score

        # Set modification_match flag if either subject or object mods match exactly
        details['modification_match'] = subj_mod_exact or obj_mod_exact

        # Activity matching (bonus, not part of core score)
        if stmt1.subject.has_activity == stmt2.subject.has_activity:
            details['activity_match'] = True

        return score, details

    def find_best_matches(
        self,
        llm_statements: List[str],
        indra_statements: List[str],
        threshold: float = 0.5
    ) -> List[Dict]:
        """Find best matches using bipartite matching approach.

        Uses scipy's Hungarian algorithm if available, otherwise falls back
        to a greedy matching approach.

        Returns list of match dictionaries with scores and details.
        """
        if not llm_statements or not indra_statements:
            # Handle empty cases
            results = []
            for llm_stmt in llm_statements:
                results.append({
                    'llm_statement': llm_stmt,
                    'indra_statement': None,
                    'match_type': 'llm_only',
                    'score': 0.0,
                    'details': {}
                })
            for indra_stmt in indra_statements:
                results.append({
                    'llm_statement': None,
                    'indra_statement': indra_stmt,
                    'match_type': 'indra_only',
                    'score': 0.0,
                    'details': {}
                })
            return results

        # Parse all statements
        llm_parsed = [self.parser.parse(s) for s in llm_statements]
        indra_parsed = [self.parser.parse(s) for s in indra_statements]

        # Build score matrix
        n_llm = len(llm_statements)
        n_indra = len(indra_statements)

        score_matrix = []
        details_matrix = []

        for i in range(n_llm):
            row_scores = []
            row_details = []
            for j in range(n_indra):
                score, details = self.calculate_match_score(llm_parsed[i], indra_parsed[j])
                row_scores.append(score)
                row_details.append(details)
            score_matrix.append(row_scores)
            details_matrix.append(row_details)

        # Try to use scipy for optimal matching
        try:
            import numpy as np
            from scipy.optimize import linear_sum_assignment

            # Make square matrix by padding with zeros
            size = max(n_llm, n_indra)
            cost_matrix = [[0.0 for _ in range(size)] for _ in range(size)]

            for i in range(n_llm):
                for j in range(n_indra):
                    cost_matrix[i][j] = -score_matrix[i][j]  # Negative for minimization

            # Find optimal assignment
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            # Build results
            results = []
            matched_llm = set()
            matched_indra = set()

            for i, j in zip(row_ind, col_ind):
                if i < n_llm and j < n_indra:
                    score = score_matrix[i][j]
                    details = details_matrix[i][j]

                    if score >= threshold and details.get('comparable', False):
                        match_type = 'exact_match' if score >= 0.9 else 'core_match'
                        results.append({
                            'llm_statement': llm_statements[i],
                            'indra_statement': indra_statements[j],
                            'match_type': match_type,
                            'score': score,
                            'details': details
                        })
                        matched_llm.add(i)
                        matched_indra.add(j)

        except ImportError:
            # Fallback to greedy matching
            results = []
            matched_llm = set()
            matched_indra = set()

            # Create list of all possible matches with scores
            all_matches = []
            for i in range(n_llm):
                for j in range(n_indra):
                    score = score_matrix[i][j]
                    details = details_matrix[i][j]
                    if score >= threshold and details.get('comparable', False):
                        all_matches.append((score, i, j, details))

            # Sort by score (highest first) and greedily assign
            all_matches.sort(reverse=True)

            for score, i, j, details in all_matches:
                if i not in matched_llm and j not in matched_indra:
                    match_type = 'exact_match' if score >= 0.9 else 'core_match'
                    results.append({
                        'llm_statement': llm_statements[i],
                        'indra_statement': indra_statements[j],
                        'match_type': match_type,
                        'score': score,
                        'details': details
                    })
                    matched_llm.add(i)
                    matched_indra.add(j)

        # Add unmatched LLM statements
        for i in range(n_llm):
            if i not in matched_llm:
                results.append({
                    'llm_statement': llm_statements[i],
                    'indra_statement': None,
                    'match_type': 'llm_only',
                    'score': 0.0,
                    'details': {}
                })

        # Add unmatched INDRA statements
        for j in range(n_indra):
            if j not in matched_indra:
                results.append({
                    'llm_statement': None,
                    'indra_statement': indra_statements[j],
                    'match_type': 'indra_only',
                    'score': 0.0,
                    'details': {}
                })

        return results
