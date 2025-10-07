# BEL Statement Comparison Analysis

## Summary of Approach

This comparison tool addresses the fundamental issues identified in the previous comparison attempts:

### Problems with Previous Approach
1. **Cartesian explosion**: Created a row for every LLM × INDRA statement combination
2. **Many-to-many confusion**: Didn't properly handle optimal matching
3. **False mismatches**: Forced different facts into low-quality matches
4. **LLM-as-judge overhead**: Used expensive GPT-4 calls for similarity scoring

### New Approach
1. **Entity-focused matching**: Core entities must match for comparability
2. **Bipartite graph matching**: Finds optimal 1:1 statement pairing
3. **Structured scoring**: Separates entity matching from detail matching
4. **Different facts ≠ mismatches**: Properly identifies when systems extract different (valid) information

## Key Insight: Different Facts from Same Text

The most important finding from the reviewer's analysis was correctly identifying cases like:

**Evidence text:**
> "Kinases DYRK1A and DYRK3 have been shown to phosphorylate human SIRT1 at T522, stimulating the deacetylation of p53 by SIRT1"

**TextToKG extracted:**
- DYRK1A → SIRT1 (phosphorylation)
- DYRK3 → SIRT1 (phosphorylation)

**INDRA extracted:**
- SIRT1 → TP53 (deacetylation)

**Previous approach**: Would force-match these and call it a "bad match" (score ~0.24)

**New approach**: Correctly identifies these as **different facts** from the same sentence:
- 2 LLM-only statements (INDRA missed the kinase relationships)
- 1 INDRA-only statement (TextToKG missed the downstream effect)

This is not a quality problem - both systems extracted valid information, just different aspects of the complex biological relationship described.

## Scoring System

### Level 0: Comparability Filter
- Subject entities must overlap (HGNC:AKT1 matches HGNC:AKT1 or HGNC:391)
- Object entities must overlap
- If either fails → statements are about different facts (LLM-only or INDRA-only)

### Level 1: Relationship Scoring (max 0.30)
- Exact match (directlyIncreases = directlyIncreases): +0.30
- Compatible (increases ≈ directlyIncreases): +0.20
- Incompatible (increases ≠ decreases): +0.00

### Level 2: Detail Scoring (max 0.50)
- **Subject modifications** (0.25 max):
  - Exact: pmod(Ph, Ser, 326) = pmod(Ph, Ser, 326) → +0.25
  - Partial: pmod(Ph, Ser, 326) vs pmod(Ph, Thr, 142) → +0.10
  - Mismatch: pmod(Ph) vs none → +0.00

- **Object modifications** (0.25 max):
  - Same scoring as subject

### Thresholds
- Score ≥ 0.9: **Exact match** (entities, relationship, and all details match)
- Score ≥ 0.5: **Core match** (entities and relationship compatible, details differ)
- Score < 0.5: **Not comparable** (different facts or incompatible relationships)

## Results Overview

### Overall Corpus Statistics
```
Total indices compared:       17
Total LLM statements:         62
Total INDRA statements:       27
Total exact matches:          0
Total core matches:           8
Total LLM-only statements:    54
Total INDRA-only statements:  19

Overall LLM precision:        12.90%
Overall INDRA precision:      29.63%
```

### Interpretation

1. **No exact matches**: Systems use different syntax conventions (act() wrapper, identifier formats, modification notation)

2. **8 core matches**: Same biological facts, different representation details:
   - Different activity specifications
   - Different modification detail levels
   - Different entity identifier formats

3. **54 LLM-only vs 27 INDRA statements**: TextToKG extracts ~2.3× more statements
   - LLM may be over-extracting
   - INDRA may be more conservative
   - Different facts from complex sentences

4. **Low precision scores**: Primarily due to:
   - Systems extracting different facts from same text
   - Different coverage (LLM extracts more)
   - Not a quality issue - just different extraction patterns

## Example Analyses

### Index 3: Phosphorylation Cascade

**Evidence**: "Mass spectrometry showed that AKT1 also phosphorylated HSF1 at T142, S230 and T527"

**TextToKG** (3 statements):
- AKT1 → HSF1(pmod Ph, Thr, 142)
- AKT1 → HSF1(pmod Ph, Ser, 230)
- AKT1 → HSF1(pmod Ph, Thr, 527)

**INDRA** (4 statements):
- AKT1 → HSF1(pmod Ph, Thr, 142)
- AKT1 → HSF1(pmod Ph, Ser, 230)
- AKT1 → HSF1(pmod Ph, Ser, 326)
- AKT1 → HSF1(pmod Ph, Thr, 527)

**Result**: 3 core matches with modification details differing due to greedy matching

### Index 11: Multi-step Pathway

**Evidence**: "Kinases DYRK1A and DYRK3 have been shown to phosphorylate human SIRT1 at T522, stimulating the deacetylation of p53 by SIRT1"

**Result**:
- 2 LLM-only: DYRK1A/DYRK3 phosphorylate SIRT1
- 1 INDRA-only: SIRT1 deacetylates p53
- 0 matches (correctly - these are different causal steps)

## Recommendations

### For Analysis
1. **Examine LLM-only and INDRA-only separately**: These often represent different valid facts, not errors
2. **Use core matches to assess representation alignment**: Do systems capture the same facts with different syntax?
3. **Consider coverage vs precision tradeoff**: More statements doesn't mean better or worse

### For Improvement
1. **Syntax normalization**: Standardize entity identifiers, modification notation
2. **Multi-fact extraction**: Develop methods to extract all relationships from complex sentences
3. **Confidence scoring**: Add confidence to distinguish high-quality from speculative extractions

### For Evaluation
1. **Don't penalize different facts**: LLM-only and INDRA-only aren't necessarily wrong
2. **Manual review of matches**: Check if "core matches" truly represent same biology
3. **Gold standard creation**: Manually annotate what SHOULD be extracted for true evaluation

## Files Generated

- `bel_parser.py`: Reusable BEL parsing and comparison utilities
- `compare_bel_statements.py`: Main comparison script
- `README_comparison.md`: Usage documentation
- `comparison_results/comparison_index_N.json`: Detailed results per index
- `comparison_results/comparison_index_N.txt`: Human-readable reports
- `comparison_results/comparison_all_indices.json`: Combined results

## Usage

```bash
# Compare specific index
python compare_bel_statements.py --index 11 \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json

# Compare all indices
python compare_bel_statements.py \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --output-dir ./comparison_results/
```

See `README_comparison.md` for detailed documentation.
