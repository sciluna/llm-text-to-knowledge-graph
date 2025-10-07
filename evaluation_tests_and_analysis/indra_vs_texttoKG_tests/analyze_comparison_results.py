#!/usr/bin/env python3
"""Analyze comparison results and generate statistics and CSV exports.

This script processes the comparison results JSON files to generate:
1. Comprehensive statistics about matches
2. CSV export of all core matches for easy review
3. Summary reports by match type
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_comparison_results(results_dir: Path) -> Dict:
    """Load all comparison results from JSON files."""
    # Try to load combined results first
    combined_file = results_dir / "comparison_all_indices.json"
    if combined_file.exists():
        with open(combined_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Otherwise, load individual index files
    results = {}
    for json_file in sorted(results_dir.glob("comparison_index_*.json")):
        if json_file.name != "comparison_all_indices.json":
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results[data['index']] = data

    return results


def collect_all_matches(results: Dict) -> Dict[str, List[Dict]]:
    """Collect all matches organized by type."""
    matches_by_type = {
        'exact': [],
        'core': [],
        'llm_only': [],
        'indra_only': []
    }

    for index, index_data in results.items():
        for evidence, ev_result in index_data.get('evidence_results', {}).items():
            matches = ev_result.get('matches', {})

            for match_type in ['exact', 'core', 'llm_only', 'indra_only']:
                for match in matches.get(match_type, []):
                    # Add context information
                    match_with_context = {
                        'index': index,
                        'evidence': evidence,
                        **match
                    }
                    matches_by_type[match_type].append(match_with_context)

    return matches_by_type


def calculate_statistics(results: Dict, matches_by_type: Dict) -> Dict:
    """Calculate comprehensive statistics."""
    stats = {
        'total_indices': len(results),
        'total_evidence_texts': 0,
        'total_llm_statements': 0,
        'total_indra_statements': 0,
        'total_exact_matches': len(matches_by_type['exact']),
        'total_core_matches': len(matches_by_type['core']),
        'total_llm_only': len(matches_by_type['llm_only']),
        'total_indra_only': len(matches_by_type['indra_only']),
        'indices_with_matches': 0,
        'indices_with_exact_matches': 0,
        'indices_with_core_matches': 0,
        'core_match_score_distribution': defaultdict(int),
        'core_match_details': {
            'modification_match': 0,
            'activity_match': 0,
            'relationship_compatible': 0,
        }
    }

    indices_with_matches = set()
    indices_with_exact = set()
    indices_with_core = set()

    for index, index_data in results.items():
        agg = index_data.get('aggregate_summary', {})
        stats['total_llm_statements'] += agg.get('total_llm_statements', 0)
        stats['total_indra_statements'] += agg.get('total_indra_statements', 0)
        stats['total_evidence_texts'] += index_data.get('n_evidence_texts', 0)

        if agg.get('total_exact_matches', 0) > 0:
            indices_with_exact.add(index)
            indices_with_matches.add(index)

        if agg.get('total_core_matches', 0) > 0:
            indices_with_core.add(index)
            indices_with_matches.add(index)

    stats['indices_with_matches'] = len(indices_with_matches)
    stats['indices_with_exact_matches'] = len(indices_with_exact)
    stats['indices_with_core_matches'] = len(indices_with_core)

    # Analyze core match details
    for match in matches_by_type['core']:
        score = match.get('score', 0)
        # Round to 2 decimal places for bucketing
        score_bucket = round(score, 2)
        stats['core_match_score_distribution'][score_bucket] += 1

        details = match.get('details', {})
        if details.get('modification_match'):
            stats['core_match_details']['modification_match'] += 1
        if details.get('activity_match'):
            stats['core_match_details']['activity_match'] += 1
        if details.get('relationship_compatible'):
            stats['core_match_details']['relationship_compatible'] += 1

    # Calculate percentages
    if stats['total_llm_statements'] > 0:
        stats['llm_precision'] = (stats['total_exact_matches'] + stats['total_core_matches']) / stats['total_llm_statements']
    else:
        stats['llm_precision'] = 0

    if stats['total_indra_statements'] > 0:
        stats['indra_precision'] = (stats['total_exact_matches'] + stats['total_core_matches']) / stats['total_indra_statements']
    else:
        stats['indra_precision'] = 0

    return stats


def export_core_matches_csv(matches: List[Dict], output_file: Path):
    """Export core matches to CSV for easy review."""
    if not matches:
        print("No core matches to export")
        return

    fieldnames = [
        'index',
        'evidence',
        'llm_statement',
        'indra_statement',
        'score',
        'modification_match',
        'activity_match',
        'relationship_match',
        'relationship_compatible',
        'subject_entities_match',
        'object_entities_match',
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for match in matches:
            details = match.get('details', {})
            components = details.get('components', {})

            row = {
                'index': match.get('index', ''),
                'evidence': match.get('evidence', '')[:200],  # Truncate long evidence
                'llm_statement': match.get('llm_statement', ''),
                'indra_statement': match.get('indra_statement', ''),
                'score': match.get('score', 0),
                'modification_match': details.get('modification_match', False),
                'activity_match': details.get('activity_match', False),
                'relationship_match': details.get('relationship_match', False),
                'relationship_compatible': details.get('relationship_compatible', False),
                'subject_entities_match': components.get('subject_entities_match', False),
                'object_entities_match': components.get('object_entities_match', False),
            }
            writer.writerow(row)

    print(f"Core matches exported to {output_file}")


def export_all_matches_csv(matches_by_type: Dict, output_file: Path):
    """Export all matches (including LLM-only and INDRA-only) to CSV."""
    fieldnames = [
        'match_type',
        'index',
        'evidence',
        'llm_statement',
        'indra_statement',
        'score',
        'modification_match',
        'activity_match',
        'relationship_match',
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for match_type in ['exact', 'core', 'llm_only', 'indra_only']:
            for match in matches_by_type[match_type]:
                details = match.get('details', {})

                row = {
                    'match_type': match_type,
                    'index': match.get('index', ''),
                    'evidence': match.get('evidence', '')[:200],
                    'llm_statement': match.get('llm_statement', '') or '',
                    'indra_statement': match.get('indra_statement', '') or '',
                    'score': match.get('score', 0),
                    'modification_match': details.get('modification_match', ''),
                    'activity_match': details.get('activity_match', ''),
                    'relationship_match': details.get('relationship_match', ''),
                }
                writer.writerow(row)

    print(f"All matches exported to {output_file}")


def print_statistics(stats: Dict):
    """Print formatted statistics report."""
    print("=" * 80)
    print("COMPARISON RESULTS STATISTICS")
    print("=" * 80)
    print()

    print("CORPUS OVERVIEW:")
    print(f"  Total indices analyzed:              {stats['total_indices']}")
    print(f"  Total evidence texts:                {stats['total_evidence_texts']}")
    print(f"  Total LLM statements:                {stats['total_llm_statements']}")
    print(f"  Total INDRA statements:              {stats['total_indra_statements']}")
    print()

    print("MATCH SUMMARY:")
    print(f"  Exact matches:                       {stats['total_exact_matches']}")
    print(f"  Core matches:                        {stats['total_core_matches']}")
    print(f"  LLM-only statements:                 {stats['total_llm_only']}")
    print(f"  INDRA-only statements:               {stats['total_indra_only']}")
    print()

    print("PRECISION METRICS:")
    print(f"  LLM precision:                       {stats['llm_precision']:.2%}")
    print(f"  INDRA precision:                     {stats['indra_precision']:.2%}")
    print()

    print("COVERAGE:")
    print(f"  Indices with any matches:            {stats['indices_with_matches']} / {stats['total_indices']}")
    print(f"  Indices with exact matches:          {stats['indices_with_exact_matches']} / {stats['total_indices']}")
    print(f"  Indices with core matches:           {stats['indices_with_core_matches']} / {stats['total_indices']}")
    print()

    if stats['total_core_matches'] > 0:
        print("CORE MATCH DETAILS:")
        print(f"  With modification match:             {stats['core_match_details']['modification_match']} / {stats['total_core_matches']} ({stats['core_match_details']['modification_match']/stats['total_core_matches']:.1%})")
        print(f"  With activity match:                 {stats['core_match_details']['activity_match']} / {stats['total_core_matches']} ({stats['core_match_details']['activity_match']/stats['total_core_matches']:.1%})")
        print(f"  With relationship compatible:        {stats['core_match_details']['relationship_compatible']} / {stats['total_core_matches']} ({stats['core_match_details']['relationship_compatible']/stats['total_core_matches']:.1%})")
        print()

        print("CORE MATCH SCORE DISTRIBUTION:")
        for score in sorted(stats['core_match_score_distribution'].keys(), reverse=True):
            count = stats['core_match_score_distribution'][score]
            pct = count / stats['total_core_matches']
            print(f"  Score {score:.2f}:                          {count} ({pct:.1%})")
        print()

    print("=" * 80)


def save_statistics_json(stats: Dict, output_file: Path):
    """Save statistics to JSON file."""
    # Convert defaultdict to regular dict for JSON serialization
    stats_for_json = dict(stats)
    stats_for_json['core_match_score_distribution'] = dict(stats['core_match_score_distribution'])

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats_for_json, f, indent=2)

    print(f"Statistics saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze BEL comparison results and generate statistics and CSV exports.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze results and export core matches
  %(prog)s --results-dir ./comparison_results/

  # Export all matches to CSV
  %(prog)s --results-dir ./comparison_results/ --export-all

  # Save statistics to JSON
  %(prog)s --results-dir ./comparison_results/ --save-stats
        """
    )

    parser.add_argument(
        '--results-dir',
        type=str,
        default='./comparison_results/',
        help='Directory containing comparison results (default: ./comparison_results/)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./comparison_results/',
        help='Directory to save exports (default: ./comparison_results/)'
    )

    parser.add_argument(
        '--export-all',
        action='store_true',
        help='Export all matches (including LLM-only and INDRA-only) to CSV'
    )

    parser.add_argument(
        '--save-stats',
        action='store_true',
        help='Save statistics to JSON file'
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load comparison results
    print(f"Loading comparison results from {results_dir}...")
    results = load_comparison_results(results_dir)

    if not results:
        print("Error: No comparison results found", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded results for {len(results)} indices")

    # Collect all matches
    matches_by_type = collect_all_matches(results)

    # Calculate statistics
    stats = calculate_statistics(results, matches_by_type)

    # Print statistics
    print()
    print_statistics(stats)

    # Export core matches CSV (always done)
    core_matches_file = output_dir / "core_matches.csv"
    export_core_matches_csv(matches_by_type['core'], core_matches_file)

    # Export all matches CSV if requested
    if args.export_all:
        all_matches_file = output_dir / "all_matches.csv"
        export_all_matches_csv(matches_by_type, all_matches_file)

    # Save statistics JSON if requested
    if args.save_stats:
        stats_file = output_dir / "statistics.json"
        save_statistics_json(stats, stats_file)

    print()
    print("✓ Analysis complete!")


if __name__ == '__main__':
    main()
