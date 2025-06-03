import json
import re
import sys


def build_minimal_results(llm_results):
    minimal_results = []
    for res in llm_results:
        minimal_entry = {
            "Index": res.get("Index"),
            "Results": [
                {
                    "bel_statement": r.get("bel_statement"),
                    "evidence": r.get("evidence")
                }
                for r in res.get("Results", [])
            ],
            "annotations": res.get("annotations", [])
        }
        minimal_results.append(minimal_entry)

    return minimal_results


def extract_ns_id(term):
    """
    Given a BEL term like "g(HGNC:BRCA1)" or 'bp(GO:"BRCA1 trafficking pathway")',
    extract and return a tuple (namespace, identifier).
    """
    pattern = r'\w+\(\s*([A-Z]+):\s*("?)(.+?)\2\s*\)'
    m = re.search(pattern, term)
    if m:
        ns = m.group(1).strip()
        identifier = m.group(3).strip()
        return ns, identifier
    return None, None


def parse_bel_statement(bel_statement):
    """
    Parses a BEL statement assumed to have a structure like:
      term1 <relationship> term2
    and returns a list of (namespace, identifier) pairs extracted from term1 and term2.
    """
    relationships = (
        "association|causesNoChange|decreases|directlyDecreases|directlyIncreases|"
        "hasActivity|hasComponent|hasComponents|hasMember|hasMembers|increases|isA|"
        "negativeCorrelation|orthologous|positiveCorrelation|rateLimitingStepOf|"
        "regulates|subProcessOf|transcribedTo|translatedTo|binds"
    )
    pattern = rf"(.+?)\s+(?:{relationships})\s+(.+)"
    m = re.match(pattern, bel_statement)
    pairs = []
    if m:
        term1 = m.group(1).strip()
        term2 = m.group(2).strip()
        ns1, id1 = extract_ns_id(term1)
        ns2, id2 = extract_ns_id(term2)
        if ns1 and id1:
            pairs.append((ns1, id1))
        if ns2 and id2:
            pairs.append((ns2, id2))
    return pairs


def compute_scores(llm_results, annotations):
    """
    Computes a per-statement score based on the number of correct (namespace, identifier)
    pairs in each BEL statement compared with the annotation list.

    For each extracted pair:
      - If (namespace, identifier) exactly matches an annotation (by id or entry_name),
        it is counted as correct.
      - Otherwise, if the identifier exists in any annotation (via id or entry_name) but with a
        different namespace, it flags a "wrong namespace" error.
      - If the identifier is not found at all, it flags a "manufactured entity" error.

    Returns:
      - A list of entries (each with Index, bel_statement, correct_terms, mismatched_terms, score,
        error_flag, and error_types)
      - overall_score: fraction of total correctly matched terms.
    """
    valid_pairs_by_entry_name = set((ann['db'], ann['entry_name']) for ann in annotations)
    valid_pairs_by_id = set((ann['db'], ann['id']) for ann in annotations)

    total_correct = 0
    total_terms = 0
    entries = []

    for result_obj in llm_results:
        index_val = result_obj.get("Index")
        for statement_obj in result_obj.get("Results", []):
            bel_stmt = statement_obj.get("bel_statement", "")
            pairs = parse_bel_statement(bel_stmt)
            correct_count = 0
            correct_terms = []
            mismatched_terms = []
            for ns, identifier in pairs:
                total_terms += 1
                if (ns, identifier) in valid_pairs_by_id or (ns, identifier) in valid_pairs_by_entry_name:
                    correct_count += 1
                    total_correct += 1
                    correct_terms.append({
                        "term": f"{ns}:{identifier}",
                        "namespace": ns,
                        "identifier": identifier
                    })
                else:
                    # Check if the identifier exists in any annotation with a different namespace.
                    expected_namespaces = [ann["db"] for ann in annotations if (ann["entry_name"] == identifier or ann["id"] == identifier)]
                    if expected_namespaces:
                        mismatched_terms.append({
                            "term": f"{ns}:{identifier}",
                            "namespace": ns,
                            "identifier": identifier,
                            "error": "wrong namespace",
                            "expected_namespaces": list(set(expected_namespaces))
                        })
                    else:
                        mismatched_terms.append({
                            "term": f"{ns}:{identifier}",
                            "namespace": ns,
                            "identifier": identifier,
                            "error": "manufactured entity"
                        })
            score = correct_count / len(pairs) if pairs else 0

            entry = {
                "Index": index_val,
                "bel_statement": bel_stmt,
                "correct_terms": correct_terms,
                "mismatched_terms": mismatched_terms,
                "score": score
            }
            entries.append(entry)
    overall_score = total_correct / total_terms if total_terms > 0 else 0
    return entries, overall_score


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_entities.py <annotation_file.json> <llm_results_file.json>")
        sys.exit(1)

    annotation_file = sys.argv[1]
    llm_file = sys.argv[2]

    # Load the annotation list from the annotation file.
    with open(annotation_file, "r", encoding="utf-8") as f:
        annotation_data = json.load(f)
    # Assuming the annotation file is structured as a dict with keys (e.g., "1", "2", etc.)
    annotations = []
    for key, value in annotation_data.items():
        annotations.extend(value.get("annotations", []))
    # Deduplicate annotations
    unique_annotations = {(ann['db'], ann['id'], ann['entry_name']): ann for ann in annotations}
    annotations_list = list(unique_annotations.values())

    # Load LLM results (with BEL statements) from the LLM results file.
    with open(llm_file, "r", encoding="utf-8") as f:
        llm_data = json.load(f)
    llm_results = llm_data.get("LLM_extractions", [])

    # Compute scores and check entities.
    scoring_entries, overall_score = compute_scores(llm_results, annotations_list)

    # Save the comparison & scoring output to "comparison_scoring.json"
    output = {"entries": scoring_entries, "overall_score": overall_score}
    with open("comparison_scoring.json", "w", encoding="utf-8") as comp_file:
        json.dump(output, comp_file, indent=2)
    print("Comparison and scoring results saved to 'comparison_scoring.json'.")
    print("Overall Score:", overall_score)


if __name__ == "__main__":
    main()
