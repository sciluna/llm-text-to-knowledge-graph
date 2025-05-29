import json
import pandas as pd
from collections import Counter

# Review files (aligned by index, all saw the same statements in the same order)
review_files = {
    "Augustin": "scored_review_lists/augustin_review.json",
    "Clara": "scored_review_lists/clara_review.json",
    "JungHo": "scored_review_lists/jungho_review.json",
    "Nicole": "scored_review_lists/nicole_review.json",
    "Xiaoyu": "scored_review_lists/xiaoyu_review.json"
}

# Load reviews for each reviewer
review_lists = {
    name: json.load(open(path))["review_list"]["scores"]
    for name, path in review_files.items()
}

# Load additional metadata (evidence and BEL statement) from the first reviewer (assumed consistent across all)
first_reviewer = list(review_files.keys())[0]
metadata_reviews = json.load(open(review_files[first_reviewer]))["reviews"]

# Assume all reviewers have the same number of statements
num_statements = len(next(iter(review_lists.values())))
summary = []

for i in range(num_statements):
    entry = {
        "Index": i + 1,
        "Total Reviewers": len(review_files),
        "BEL Statement": metadata_reviews[i].get("bel_expression", ""),
        "Evidence": metadata_reviews[i].get("evidence", "")
    }

    all_correct_count = 0
    fingerprints = []
    error_counter = Counter()

    for reviewer, reviews in review_lists.items():
        scores = reviews[i]["scores"]
        if scores.get("all_correct", False):
            all_correct_count += 1

        # Set of criteria marked as True (excluding comments)
        fingerprint = frozenset(k for k, v in scores.items() if v is True and k != "comments")
        fingerprints.append(fingerprint)

        for k, v in scores.items():
            if k not in {"comments", "all_correct"} and v is True:
                error_counter[k] += 1

    # Determine most common fingerprint and consensus count
    fingerprint_counts = Counter(fingerprints)
    most_common_fp, consensus_count = fingerprint_counts.most_common(1)[0]

    entry["All Correct Count"] = all_correct_count
    entry["Consensus Count"] = consensus_count
    entry["Agreed Criteria"] = sorted(most_common_fp)
    entry["Error Summary"] = dict(error_counter)

    summary.append(entry)

df = pd.DataFrame(summary)
df.to_csv("review_consensus_with_evidence.csv", index=False)
