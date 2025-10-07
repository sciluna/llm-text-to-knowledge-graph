# Comparison Results Analysis Tools

## Overview

This directory contains tools for comparing BEL statements extracted by TextToKG (LLM) and INDRA (rule-based), plus analysis scripts for generating statistics and exports.

## Scripts

### 1. compare_bel_statements.py
Main comparison tool that performs entity-focused matching of BEL statements.

**Usage:**
```bash
# Compare specific index
python compare_bel_statements.py --index 3 \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json

# Compare all indices
python compare_bel_statements.py \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --output-dir ./comparison_results/
```

See [README_comparison.md](README_comparison.md) for detailed documentation.

### 2. analyze_comparison_results.py
Analysis tool that processes comparison results to generate statistics and CSV exports.

**Usage:**
```bash
# Basic analysis with core matches CSV
python analyze_comparison_results.py --results-dir ./comparison_results/

# Full analysis with all exports
python analyze_comparison_results.py \
  --results-dir ./comparison_results/ \
  --export-all \
  --save-stats
```

**Options:**
- `--results-dir`: Directory containing comparison results (default: ./comparison_results/)
- `--output-dir`: Directory to save exports (default: ./comparison_results/)
- `--export-all`: Export all matches including LLM-only and INDRA-only to CSV
- `--save-stats`: Save statistics to JSON file

## Output Files

### From compare_bel_statements.py

1. **comparison_index_N.json** - Detailed structured results per index
   - Evidence-level breakdown
   - Match details with scores
   - BEL statement pairs

2. **comparison_index_N.txt** - Human-readable report per index
   - Summary statistics
   - Matched statements with scores
   - LLM-only and INDRA-only statements

3. **comparison_all_indices.json** - Combined results for all indices

### From analyze_comparison_results.py

1. **core_matches.csv** - All core matches for easy review
   ```csv
   index,evidence,llm_statement,indra_statement,score,modification_match,activity_match,...
   3,"AKT2 phosphorylated...",act(p(HGNC:AKT2)...),p(HGNC:392 ! AKT2)...,0.8,True,False,...
   ```

2. **all_matches.csv** - All matches including LLM-only and INDRA-only (with --export-all)
   ```csv
   match_type,index,evidence,llm_statement,indra_statement,score,...
   core,3,"AKT2...",act(p(HGNC:AKT2)...),p(HGNC:392...)...
   llm_only,11,"DYRK1A...",act(p(HGNC:DYRK1A)...),,0,...
   ```

3. **statistics.json** - Comprehensive statistics (with --save-stats)
   ```json
   {
     "total_indices": 17,
     "total_llm_statements": 62,
     "total_core_matches": 8,
     "core_match_score_distribution": {"0.80": 7, "0.55": 1},
     ...
   }
   ```

## Statistics Explained

### Match Types
- **Exact matches** (score ≥ 0.9): Perfect alignment of entities, relationships, and modifications
- **Core matches** (0.5 ≤ score < 0.9): Entities and relationship match, but details differ
  - Score 0.80: Modifications match exactly, activity wrapper differs
  - Score 0.55: Modifications differ in details
- **LLM-only**: Statements extracted by TextToKG but not INDRA
- **INDRA-only**: Statements extracted by INDRA but not TextToKG

### Key Metrics

**Precision:**
- LLM precision = (exact + core matches) / total LLM statements
- INDRA precision = (exact + core matches) / total INDRA statements

**Coverage:**
- Number of indices with at least one match
- Distribution of match types across corpus

**Core Match Details:**
- % with modification match (modifications identical)
- % with activity match (both use or don't use activity wrapper)
- % with relationship compatible (same or compatible relationship types)

**Score Distribution:**
- Histogram of match scores for core matches
- Helps identify common representation differences

## Example Workflow

```bash
# 1. Run comparison on all indices
python compare_bel_statements.py \
  --llm-file texttoKG_cleaned.json \
  --indra-file indra_bel_cleaned.json \
  --output-dir ./comparison_results/

# 2. Generate statistics and exports
python analyze_comparison_results.py \
  --results-dir ./comparison_results/ \
  --export-all \
  --save-stats

# 3. Review results
# - Check statistics in terminal output
# - Open core_matches.csv in spreadsheet software
# - Review specific indices in comparison_index_N.txt files
```

## Interpreting Results

### Current Corpus Statistics
```
Total indices:                17
Total LLM statements:         62
Total INDRA statements:       27
Core matches:                 8
LLM-only:                     54
INDRA-only:                   19

LLM precision:                12.90%
INDRA precision:              29.63%
```

### Key Findings

1. **No exact matches**: Systems use different syntax conventions (activity wrappers, identifier formats)

2. **8 core matches (score 0.80)**: Same biological facts with representation differences
   - 6/8 have modification_match = true (75%)
   - All represent valid matches where modifications align

3. **Different coverage**: TextToKG extracts ~2.3× more statements than INDRA
   - Could indicate LLM over-extraction or INDRA conservatism
   - Many LLM-only and INDRA-only represent different facts from same text

4. **Low precision scores**: Primarily due to different extraction patterns
   - Not a quality issue - systems extract different aspects of complex sentences
   - See index 11 example: DYRK1A→SIRT1 vs SIRT1→TP53 from same sentence

### Score 0.80 Interpretation
A score of 0.80 typically means:
- ✓ Core entities match (subject and object)
- ✓ Relationship matches exactly
- ✓ Modifications match exactly (type, residue, position)
- ✗ Activity wrapper differs (`act()` present in one, absent in other)

This represents the **same biological fact** with different syntactic specificity.

## Files in This Directory

- `bel_parser.py` - BEL parsing and normalization utilities
- `compare_bel_statements.py` - Main comparison script
- `analyze_comparison_results.py` - Statistics and CSV export script
- `README_comparison.md` - Detailed comparison tool documentation
- `README_analysis.md` - This file
- `COMPARISON_SUMMARY.md` - Overall methodology and findings
- `comparison_results/` - Output directory
  - `comparison_index_*.json` - Per-index results
  - `comparison_index_*.txt` - Per-index reports
  - `comparison_all_indices.json` - Combined results
  - `core_matches.csv` - Core matches export
  - `all_matches.csv` - All matches export (optional)
  - `statistics.json` - Statistics export (optional)

## Tips for Manual Review

When reviewing core_matches.csv:

1. **Filter by score**: Scores of 0.80 are high-quality matches with only syntax differences
2. **Check modification_match**: True means modifications are identical
3. **Compare statements side-by-side**: Look for patterns in representation differences
4. **Review evidence text**: Understand what both systems extracted from the source

When reviewing all_matches.csv:

1. **Group by match_type**: Review exact, core, llm_only, indra_only separately
2. **Look for patterns in LLM-only**: Are these over-extractions or INDRA misses?
3. **Look for patterns in INDRA-only**: Are these genuine misses by the LLM?
4. **Consider evidence context**: Different facts from same text are not errors
