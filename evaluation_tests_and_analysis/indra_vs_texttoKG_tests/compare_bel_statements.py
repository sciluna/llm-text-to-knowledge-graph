#!/usr/bin/env python3
"""Compare BEL statements from TextToKG and INDRA using structured matching.

This script performs entity-focused comparison of BEL statements using
bipartite graph matching to properly identify which facts were extracted
by each system from complex biomedical text.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from bel_parser import BELParser, BELComparator


def load_json_file(file_path: str) -> List[Dict]:
    """Load JSON file and return data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_statements_by_evidence(data: List[Dict], source: str) -> Dict[str, Dict[str, List[str]]]:
    """Extract BEL statements organized by index and evidence.

    Args:
        data: JSON data from either texttoKG or INDRA
        source: Either 'llm' or 'indra' to determine structure

    Returns:
        Dict mapping index -> evidence -> list of BEL statements
    """
    result = defaultdict(lambda: defaultdict(list))

    for entry in data:
        index = str(entry.get('Index', ''))

        if source == 'llm':
            # TextToKG format: entry['Result'] contains list of {evidence, bel_statement}
            for item in entry.get('Result', []):
                evidence = item.get('evidence', '').strip()
                statement = item.get('bel_statement', '').strip()
                if statement:
                    result[index][evidence].append(statement)

        elif source == 'indra':
            # INDRA format: entry['evidences'] contains list of {Evidence, Results}
            for ev_entry in entry.get('evidences', []):
                evidence = ev_entry.get('Evidence', '').strip()
                for res in ev_entry.get('Results', []):
                    statement = res.get('bel_statement', '').strip()
                    if statement:
                        result[index][evidence].append(statement)

    return dict(result)


def compare_evidence_statements(
    llm_statements: List[str],
    indra_statements: List[str],
    comparator: BELComparator,
    threshold: float
) -> Dict:
    """Compare LLM and INDRA statements for a single evidence text."""
    matches = comparator.find_best_matches(llm_statements, indra_statements, threshold)

    # Categorize matches
    exact_matches = [m for m in matches if m['match_type'] == 'exact_match']
    core_matches = [m for m in matches if m['match_type'] == 'core_match']
    llm_only = [m for m in matches if m['match_type'] == 'llm_only']
    indra_only = [m for m in matches if m['match_type'] == 'indra_only']

    return {
        'llm_statements': llm_statements,
        'indra_statements': indra_statements,
        'matches': {
            'exact': exact_matches,
            'core': core_matches,
            'llm_only': llm_only,
            'indra_only': indra_only
        },
        'summary': {
            'n_llm_statements': len(llm_statements),
            'n_indra_statements': len(indra_statements),
            'n_exact_matches': len(exact_matches),
            'n_core_matches': len(core_matches),
            'n_llm_only': len(llm_only),
            'n_indra_only': len(indra_only),
            'llm_recall': len(exact_matches + core_matches) / len(llm_statements) if llm_statements else 0,
            'indra_recall': len(exact_matches + core_matches) / len(indra_statements) if indra_statements else 0
        }
    }


def compare_index(
    index: str,
    llm_data: Dict[str, Dict[str, List[str]]],
    indra_data: Dict[str, Dict[str, List[str]]],
    comparator: BELComparator,
    threshold: float
) -> Dict:
    """Compare all evidence texts within a single index."""
    llm_evidences = llm_data.get(index, {})
    indra_evidences = indra_data.get(index, {})

    # Get all unique evidence texts
    all_evidences = set(llm_evidences.keys()) | set(indra_evidences.keys())

    evidence_results = {}

    for evidence in sorted(all_evidences):
        llm_stmts = llm_evidences.get(evidence, [])
        indra_stmts = indra_evidences.get(evidence, [])

        result = compare_evidence_statements(llm_stmts, indra_stmts, comparator, threshold)
        evidence_results[evidence] = result

    # Aggregate statistics
    total_llm = sum(r['summary']['n_llm_statements'] for r in evidence_results.values())
    total_indra = sum(r['summary']['n_indra_statements'] for r in evidence_results.values())
    total_exact = sum(r['summary']['n_exact_matches'] for r in evidence_results.values())
    total_core = sum(r['summary']['n_core_matches'] for r in evidence_results.values())
    total_llm_only = sum(r['summary']['n_llm_only'] for r in evidence_results.values())
    total_indra_only = sum(r['summary']['n_indra_only'] for r in evidence_results.values())

    return {
        'index': index,
        'n_evidence_texts': len(all_evidences),
        'evidence_results': evidence_results,
        'aggregate_summary': {
            'total_llm_statements': total_llm,
            'total_indra_statements': total_indra,
            'total_exact_matches': total_exact,
            'total_core_matches': total_core,
            'total_llm_only': total_llm_only,
            'total_indra_only': total_indra_only,
            'llm_precision': (total_exact + total_core) / total_llm if total_llm else 0,
            'indra_precision': (total_exact + total_core) / total_indra if total_indra else 0,
        }
    }


def format_summary_report(results: Dict) -> str:
    """Format comparison results into a readable summary report."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"BEL STATEMENT COMPARISON REPORT - INDEX {results['index']}")
    lines.append("=" * 80)
    lines.append("")

    agg = results['aggregate_summary']
    lines.append("AGGREGATE SUMMARY:")
    lines.append(f"  Total LLM statements:     {agg['total_llm_statements']}")
    lines.append(f"  Total INDRA statements:   {agg['total_indra_statements']}")
    lines.append(f"  Exact matches:            {agg['total_exact_matches']}")
    lines.append(f"  Core matches:             {agg['total_core_matches']}")
    lines.append(f"  LLM-only statements:      {agg['total_llm_only']}")
    lines.append(f"  INDRA-only statements:    {agg['total_indra_only']}")
    lines.append(f"  LLM precision:            {agg['llm_precision']:.2%}")
    lines.append(f"  INDRA precision:          {agg['indra_precision']:.2%}")
    lines.append("")

    lines.append(f"EVIDENCE-LEVEL BREAKDOWN ({results['n_evidence_texts']} evidence texts):")
    lines.append("-" * 80)

    for evidence, ev_result in results['evidence_results'].items():
        summary = ev_result['summary']
        lines.append(f"\nEvidence: {evidence[:100]}{'...' if len(evidence) > 100 else ''}")
        lines.append(f"  LLM statements: {summary['n_llm_statements']}, "
                    f"INDRA statements: {summary['n_indra_statements']}")
        lines.append(f"  Exact matches: {summary['n_exact_matches']}, "
                    f"Core matches: {summary['n_core_matches']}")
        lines.append(f"  LLM-only: {summary['n_llm_only']}, "
                    f"INDRA-only: {summary['n_indra_only']}")

        # Show match details
        matches = ev_result['matches']
        if matches['exact']:
            lines.append("  Exact matches:")
            for m in matches['exact']:
                lines.append(f"    LLM:   {m['llm_statement']}")
                lines.append(f"    INDRA: {m['indra_statement']}")
                lines.append(f"    Score: {m['score']:.2f}")

        if matches['core']:
            lines.append("  Core matches (entities match, details differ):")
            for m in matches['core']:
                lines.append(f"    LLM:   {m['llm_statement']}")
                lines.append(f"    INDRA: {m['indra_statement']}")
                lines.append(f"    Score: {m['score']:.2f}")
                details = m['details']
                if not details.get('relationship_match'):
                    lines.append(f"      → Relationship differs: compatible={details.get('relationship_compatible')}")
                if not details.get('modification_match'):
                    lines.append(f"      → Modifications differ")

        if matches['llm_only']:
            lines.append("  LLM-only statements (INDRA missed these):")
            for m in matches['llm_only']:
                lines.append(f"    {m['llm_statement']}")

        if matches['indra_only']:
            lines.append("  INDRA-only statements (LLM missed these):")
            for m in matches['indra_only']:
                lines.append(f"    {m['indra_statement']}")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Compare BEL statements from TextToKG and INDRA using entity-focused matching.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare statements in index 3
  %(prog)s --index 3 --llm-file texttoKG_cleaned.json --indra-file indra_bel_cleaned.json

  # Compare all indices with custom threshold
  %(prog)s --llm-file texttoKG_cleaned.json --indra-file indra_bel_cleaned.json --threshold 0.6

  # Save results to custom directory
  %(prog)s --index 11 --llm-file texttoKG_cleaned.json --indra-file indra_bel_cleaned.json \\
           --output-dir ./comparison_results/
        """
    )

    parser.add_argument(
        '--llm-file',
        required=True,
        help='Path to TextToKG JSON file (e.g., texttoKG_cleaned.json)'
    )

    parser.add_argument(
        '--indra-file',
        required=True,
        help='Path to INDRA BEL JSON file (e.g., indra_bel_cleaned.json)'
    )

    parser.add_argument(
        '--index',
        type=str,
        help='Specific index to compare (e.g., "3" or "11"). If not provided, compares all indices.'
    )

    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum match score threshold for comparability (default: 0.5)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Directory to save results (default: current directory)'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'text', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading LLM data from {args.llm_file}...")
    llm_raw = load_json_file(args.llm_file)

    print(f"Loading INDRA data from {args.indra_file}...")
    indra_raw = load_json_file(args.indra_file)

    # Extract statements organized by index and evidence
    llm_data = extract_statements_by_evidence(llm_raw, 'llm')
    indra_data = extract_statements_by_evidence(indra_raw, 'indra')

    # Initialize comparator
    parser_obj = BELParser()
    comparator = BELComparator(parser_obj)

    # Determine which indices to process
    if args.index:
        indices = [args.index]
        if args.index not in llm_data and args.index not in indra_data:
            print(f"Warning: Index '{args.index}' not found in either dataset", file=sys.stderr)
            sys.exit(1)
    else:
        indices = sorted(set(llm_data.keys()) | set(indra_data.keys()))

    print(f"Comparing {len(indices)} indices with threshold {args.threshold}...")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each index
    all_results = {}

    for idx in indices:
        print(f"\nProcessing index {idx}...")
        result = compare_index(idx, llm_data, indra_data, comparator, args.threshold)
        all_results[idx] = result

        # Save individual index results
        if args.format in ['json', 'both']:
            json_path = output_dir / f"comparison_index_{idx}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"  Saved JSON results to {json_path}")

        if args.format in ['text', 'both']:
            text_path = output_dir / f"comparison_index_{idx}.txt"
            report = format_summary_report(result)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"  Saved text report to {text_path}")

            # Also print to console
            print("\n" + report)

    # Save combined results if processing multiple indices
    if len(indices) > 1:
        combined_path = output_dir / "comparison_all_indices.json"
        with open(combined_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nSaved combined results to {combined_path}")

        # Create overall summary
        total_llm = sum(r['aggregate_summary']['total_llm_statements'] for r in all_results.values())
        total_indra = sum(r['aggregate_summary']['total_indra_statements'] for r in all_results.values())
        total_exact = sum(r['aggregate_summary']['total_exact_matches'] for r in all_results.values())
        total_core = sum(r['aggregate_summary']['total_core_matches'] for r in all_results.values())
        total_llm_only = sum(r['aggregate_summary']['total_llm_only'] for r in all_results.values())
        total_indra_only = sum(r['aggregate_summary']['total_indra_only'] for r in all_results.values())

        print("\n" + "=" * 80)
        print("OVERALL SUMMARY (ALL INDICES)")
        print("=" * 80)
        print(f"Total indices compared:       {len(indices)}")
        print(f"Total LLM statements:         {total_llm}")
        print(f"Total INDRA statements:       {total_indra}")
        print(f"Total exact matches:          {total_exact}")
        print(f"Total core matches:           {total_core}")
        print(f"Total LLM-only statements:    {total_llm_only}")
        print(f"Total INDRA-only statements:  {total_indra_only}")
        if total_llm > 0:
            print(f"Overall LLM precision:        {(total_exact + total_core) / total_llm:.2%}")
        if total_indra > 0:
            print(f"Overall INDRA precision:      {(total_exact + total_core) / total_indra:.2%}")
        print("=" * 80)

    print("\n✓ Comparison complete!")


if __name__ == '__main__':
    main()
