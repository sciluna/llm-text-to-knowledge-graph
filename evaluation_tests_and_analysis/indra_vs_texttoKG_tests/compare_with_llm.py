"""Compare LLM and INDRA statements for semantic similarity using OpenAI."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - dependency issue should be explicit
    raise SystemExit(
        "The openai package is required. Install dependencies via `uv run --script compare_statements.py --help`."
    ) from exc


SCORE_TO_RATING = {0: "low", 2: "partial", 4: "good"}


@dataclass
class SimilarityDecision:
    index: Optional[int]
    score: Optional[int]
    explanation: str

    @property
    def rating(self) -> str:
        if self.score is None:
            return "none_comparable"
        return SCORE_TO_RATING.get(self.score, "none_comparable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare LLM statements against INDRA statements (JSON input) grouped by evidence."
        )
    )
    parser.add_argument(
        "--llm",
        required=True,
        help="Path to the LLM JSON file (e.g. texttoKG_cleaned.json)",
    )
    parser.add_argument(
        "--indra",
        required=True,
        help="Path to the INDRA JSON file (e.g. indra_bel_cleaned.json)",
    )
    parser.add_argument(
        "--output",
        default="comparison_output.json",
        help="Path to write the comparison JSON output",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI model to use for comparisons (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip OpenAI calls (mark all comparisons as none_comparable).",
    )
    return parser.parse_args()


def sanitize(value: Optional[str]) -> str:
    return value.strip() if value else ""


def load_json_files(llm_path: str, indra_path: str):
    """Load and merge LLM + INDRA JSONs into comparable structures."""
    try:
        with open(llm_path, "r", encoding="utf-8") as f:
            llm_data = json.load(f)
        with open(indra_path, "r", encoding="utf-8") as f:
            indra_data = json.load(f)
    except FileNotFoundError as exc:
        raise SystemExit(f"Could not find one of the JSON files: {exc}") from exc

    # Create mapping for INDRA entries by Index
    indra_map = {str(entry["Index"]): entry for entry in indra_data}
    merged_rows = []

    for llm_entry in llm_data:
        idx = str(llm_entry["Index"])
        llm_results = llm_entry.get("Result", [])
        indra_entry = indra_map.get(idx, {})
        evidences = indra_entry.get("evidences", [])

        for llm_result in llm_results:
            evidence = llm_result.get("evidence", "")
            llm_stmt = llm_result.get("bel_statement", "")
            # For matching INDRA evidence(s)
            if evidences:
                for ev_obj in evidences:
                    for indra_result in ev_obj.get("Results", []):
                        merged_rows.append({
                            "index": idx,
                            "evidence": evidence or ev_obj.get("Evidence", ""),
                            "llm_statement": llm_stmt,
                            "indra_statement": indra_result.get("bel_statement", "")
                        })
            else:
                # No INDRA match found
                merged_rows.append({
                    "index": idx,
                    "evidence": evidence,
                    "llm_statement": llm_stmt,
                    "indra_statement": ""
                })
    return merged_rows


def extract_json_object(text: str) -> Dict[str, object]:
    """Extract the first JSON object present in *text*."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in response")
    fragment = text[start: end + 1]
    return json.loads(fragment)


def call_openai(
    client: OpenAI,
    model: str,
    llm_statement: str,
    indra_statements: List[str],
) -> SimilarityDecision:
    numbered_candidates = "\n".join(
        f"{idx}. {candidate}" for idx, candidate in enumerate(indra_statements)
    )
    user_prompt = (
        "You will receive one query statement followed by numbered candidate statements. "
        "Choose the single candidate that is most semantically similar to the query. "
        "If none are comparable, respond accordingly. Return only JSON with fields: "
        '\"match_index\" (integer index of the best candidate or null), '
        '\"similarity\" (one of 0, 2, 4 for low/partial/good similarity or "none"), '
        '\"explanation\" (1-2 sentences describing why the similarity rating was assigned). '
        "Respect the following mapping: 0 -> low similarity, 2 -> partial similarity, 4 -> good similarity. "
        "Use \"similarity\": \"none\" and \"match_index\": null if none are comparable.\n\n"
        f"Query statement:\n{llm_statement}\n\n"
        f"Candidate statements:\n{numbered_candidates}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert analyst. Respond with valid JSON only, without commentary or markdown."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=200,
    )
    message = response.choices[0].message.content or ""
    payload = extract_json_object(message)
    raw_index = payload.get("match_index")
    raw_score = payload.get("similarity")
    explanation = str(payload.get("explanation", "")).strip()

    index: Optional[int]
    if raw_index is None:
        index = None
    else:
        try:
            index = int(raw_index)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid match_index in response: {raw_index!r}") from exc

    score: Optional[int]
    if isinstance(raw_score, str):
        raw_score_lower = raw_score.lower()
        if raw_score_lower in {"none", "none_comparable"}:
            score = None
        else:
            try:
                score = int(raw_score)
            except ValueError as exc:
                raise ValueError(f"Invalid similarity score in response: {raw_score!r}") from exc
    else:
        score = int(raw_score) if raw_score is not None else None

    if index is not None and (index < 0 or index >= len(indra_statements)):
        raise ValueError(
            f"OpenAI selected index {index}, which is outside 0..{len(indra_statements) - 1}"
        )

    if score is not None and score not in SCORE_TO_RATING:
        raise ValueError(f"Unexpected similarity score: {score}")

    return SimilarityDecision(index=index, score=score, explanation=explanation)


def group_rows(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, object]]:
    """Organize rows by evidence with helper structures for downstream processing."""
    grouped: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {
            "llm_rows": defaultdict(list),
            "indra_candidates": [],
        }
    )

    for idx, row in enumerate(rows):
        evidence = sanitize(row.get("evidence"))
        llm_statement = sanitize(row.get("llm_statement"))
        indra_statement = sanitize(row.get("indra_statement"))

        bucket = grouped[evidence]
        if llm_statement:
            bucket["llm_rows"][llm_statement].append(idx)
        if indra_statement and indra_statement not in bucket["indra_candidates"]:
            bucket["indra_candidates"].append(indra_statement)

    return grouped


def main() -> None:
    args = parse_args()
    load_dotenv()

    rows = rows = load_json_files(args.llm, args.indra)
    grouped = group_rows(rows)

    # Prepare result placeholders per row.
    augmented: List[Dict[str, str]] = [dict(row) for row in rows]
    row_annotations = [
        {
            "similarity_rating": "none_comparable",
            "match_type": "not_compared",
            "similarity_rating_reason": "",
        }
        for _ in rows
    ]

    # Initial classification for rows lacking either statement.
    for idx, row in enumerate(rows):
        llm_statement = sanitize(row.get("llm_statement"))
        indra_statement = sanitize(row.get("indra_statement"))
        if llm_statement and not indra_statement:
            row_annotations[idx]["match_type"] = "llm_only"
            row_annotations[idx]["similarity_rating_reason"] = (
                "No INDRA statement available for comparison."
            )
        elif indra_statement and not llm_statement:
            row_annotations[idx]["match_type"] = "indra_only"
            row_annotations[idx]["similarity_rating_reason"] = (
                "No LLM statement available for comparison."
            )
        elif not llm_statement and not indra_statement:
            row_annotations[idx]["similarity_rating_reason"] = "Row has no statements to compare."

    client: Optional[OpenAI] = None
    if not args.dry_run:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit(
                "OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=<your key> or use --dry-run."
            )
        client = OpenAI(api_key=api_key)

    for evidence, structures in grouped.items():
        indra_candidates: List[str] = structures["indra_candidates"]
        if not indra_candidates:
            # No INDRA statements to compare against for this evidence.
            for _, indices in structures["llm_rows"].items():
                for idx in indices:
                    row_annotations[idx]["match_type"] = "llm_only"
                    row_annotations[idx]["similarity_rating"] = "none_comparable"
                    row_annotations[idx]["similarity_rating_reason"] = (
                        "No INDRA statements available for this evidence."
                    )
            continue

        for llm_statement, indices in structures["llm_rows"].items():
            if args.dry_run or client is None:
                decision = SimilarityDecision(index=None, score=None, explanation="dry_run")
            else:
                try:
                    decision = call_openai(client, args.model, llm_statement, indra_candidates)
                except Exception as exc:  # pragma: no cover - runtime protection
                    print(
                        f"[warning] Failed to obtain similarity for evidence '{evidence}': {exc}",
                        file=sys.stderr,
                    )
                    decision = SimilarityDecision(index=None, score=None, explanation="Model request failed.")

            if decision.index is None:
                reason = (
                    decision.explanation
                    if decision.explanation
                    else "Model reported no comparable INDRA statements."
                )
                for idx in indices:
                    if row_annotations[idx]["match_type"] not in {"llm_only", "indra_only"}:
                        row_annotations[idx]["match_type"] = "not_compared"
                        row_annotations[idx]["similarity_rating"] = "none_comparable"
                        row_annotations[idx]["similarity_rating_reason"] = reason
                continue

            chosen_indra = indra_candidates[decision.index]
            fallback_reason = (
                "A different INDRA statement was selected as the closest match."
            )
            for idx in indices:
                row_indra = sanitize(rows[idx].get("indra_statement"))
                if row_indra == chosen_indra:
                    row_annotations[idx]["match_type"] = "most_similar"
                    row_annotations[idx]["similarity_rating"] = decision.rating
                    row_annotations[idx]["similarity_rating_reason"] = (
                        decision.explanation or "Model selected this pair as most similar."
                    )
                elif row_annotations[idx]["match_type"] not in {"llm_only", "indra_only"}:
                    row_annotations[idx]["match_type"] = "not_compared"
                    row_annotations[idx]["similarity_rating"] = "none_comparable"
                    row_annotations[idx]["similarity_rating_reason"] = fallback_reason

    fieldnames = list(rows[0].keys()) + [
        "similarity_rating",
        "match_type",
        "similarity_rating_reason",
    ]
    try:
        with open(args.output, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row, annotation in zip(augmented, row_annotations):
                row.update(annotation)
                writer.writerow(row)
    except OSError as exc:
        raise SystemExit(f"Failed to write output CSV: {exc}") from exc

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
