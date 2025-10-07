# BEL Statement Comparison Tool

## Overview

This tool performs structured comparison of BEL (Biological Expression Language) statements extracted by TextToKG (LLM-based) and INDRA (rule-based) systems from the same biomedical text.

**Key Features:**
- Entity-focused matching using bipartite graph matching
- Distinguishes between "different facts from same text" vs "low quality matches"
- Properly handles BEL modifications, activities, and complexes
- Per-index analysis for targeted review
- No LLM API calls required for comparison

## Files

- `bel_parser.py` - BEL parsing, normalization, and comparison utilities
- `compare_bel_statements.py` - Main comparison script
- `comparison_results/` - Output directory (created automatically)

## Installation

The tool requires Python 3.7+. For optimal performance, install scipy:

```bash
pip install scipy numpy
```

If scipy is not available, the tool will fall back to a greedy matching algorithm.

## Usage

### Compare a specific index

```bash
python compare_bel_statements.py \
  --index 3 \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --output-dir ./comparison_results/
```

### Compare all indices

```bash
python compare_bel_statements.py \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --output-dir ./comparison_results/
```

### Adjust matching threshold

```bash
python compare_bel_statements.py \
  --index 11 \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --threshold 0.6 \
  --format both
```

## Command-Line Options

- `--llm-file`: Path to TextToKG JSON file (required)
- `--indra-file`: Path to INDRA BEL JSON file (required)
- `--index`: Specific index to compare (optional, compares all if omitted)
- `--threshold`: Minimum match score for comparability (default: 0.5)
- `--output-dir`: Directory for results (default: current directory)
- `--format`: Output format - `json`, `text`, or `both` (default: both)

## Output

For each index, the tool generates:

1. **JSON file** (`comparison_index_N.json`): Structured results with detailed match information
2. **Text report** (`comparison_index_N.txt`): Human-readable summary

### Match Types

- **Exact match** (score ≥ 0.9): Entities, relationship, and modifications all match perfectly
- **Core match** (0.5 ≤ score < 0.9): Core entities and relationship match, but details differ
  - Score 0.80: Modifications match exactly, but one has activity wrapper (`act()`) and the other doesn't
  - Score 0.55-0.65: Modifications differ in residue/position, or only modification type matches
  - Score 0.50: Just core entities + relationship, modifications completely differ
- **LLM-only**: Statement extracted by TextToKG but not by INDRA
- **INDRA-only**: Statement extracted by INDRA but not by TextToKG

### Metrics

- **LLM precision**: Proportion of LLM statements matched to INDRA statements
- **INDRA precision**: Proportion of INDRA statements matched to LLM statements

## Scoring System

The matching algorithm uses entity-focused scoring:

1. **Level 0: Core entities** (required for comparability)
   - Subject and object entities must overlap
   - If not, statements are incomparable (LLM-only or INDRA-only)

2. **Level 1: Relationship** (max 0.30 points)
   - Exact match: +0.30
   - Compatible (e.g., increases/directlyIncreases): +0.20
   - Incompatible: +0.00

3. **Level 2: Modifications & Activities** (max 0.50 points)
   - Subject modification exact match: +0.25
   - Subject modification type match: +0.10
   - Object modification exact match: +0.25
   - Object modification type match: +0.10

**Maximum score: 1.0**

## Example Output

```
================================================================================
BEL STATEMENT COMPARISON REPORT - INDEX 11
================================================================================

AGGREGATE SUMMARY:
  Total LLM statements:     4
  Total INDRA statements:   1
  Exact matches:            0
  Core matches:             0
  LLM-only statements:      4
  INDRA-only statements:    1

EVIDENCE-LEVEL BREAKDOWN:
--------------------------------------------------------------------------------

Evidence: Kinases DYRK1A and DYRK3 have been shown to phosphorylate human...
  LLM statements: 2, INDRA statements: 1

  LLM-only statements (INDRA missed these):
    act(p(HGNC:DYRK1A), ma(GO:"kinase activity")) directlyIncreases p(HGNC:SIRT1, pmod(Ph, Thr, 522))
    act(p(HGNC:DYRK3), ma(GO:"kinase activity")) directlyIncreases p(HGNC:SIRT1, pmod(Ph, Thr, 522))

  INDRA-only statements (LLM missed these):
    p(HGNC:SIRT1) directlyDecreases p(HGNC:TP53, pmod(Ac))
```

This correctly identifies that DYRK1A→SIRT1 and SIRT1→TP53 are **different facts** from the same sentence, not low-quality matches.

## Understanding the Results

### Common Patterns

1. **Different facts from complex sentences**: LLM and INDRA may extract different (valid) relationships from the same evidence text. These appear as LLM-only and INDRA-only.

2. **Representation differences**: Same fact, different syntax (e.g., `act(p(X))` vs `p(X)`). These show as core matches with activity_match details.

3. **Modification specificity**: One system includes position/residue, the other doesn't. Shows as core match with partial modification score.

4. **Coverage differences**: One system extracts more statements from the same text.

## Troubleshooting

**Issue**: All matches show as LLM-only or INDRA-only
- Check threshold setting (try lower values like 0.3)
- Verify entity identifier formats match (HGNC, GO, CHEBI)

**Issue**: Unexpected core matches
- Review match details in JSON output
- Check if modifications are being normalized correctly

**Issue**: Performance is slow
- Install scipy for optimal matching algorithm
- Process indices one at a time using `--index`
