import json
import pandas as pd
from collections import Counter

# Review files (update the paths if needed)
review_files = {
    "Augustin": "evaluation_tests/augustin_review.json",
    "Clara": "evaluation_tests/clara_rev.json",
    "JungHo": "evaluation_tests/jungho_rev.json",
    "Nicole": "evaluation_tests/nicole_rev.json",
    "Xiaoyu": "evaluation_tests/Zhao_review.json"
}


# Load all scores
review_lists = {
    name: json.load(open(path))["scores"]
    for name, path in review_files.items()
}

# Assume all reviewers have the same number of statements
num_statements = len(next(iter(review_lists.values())))
summary = []

for i in range(num_statements):
    entry = {
        "Index": i + 1,
        "Total Reviewers": len(review_files)
    }

    all_correct_count = 0
    fingerprints = []
    error_counter = Counter()

    for reviewer, reviews in review_lists.items():
        scores = reviews[i]["scores"]
        if scores["all_correct"]:
            all_correct_count += 1

        # Set of criteria marked as True
        fingerprint = frozenset(k for k, v in scores.items() if v is True and k != "comments")
        fingerprints.append(fingerprint)

        for k, v in scores.items():
            if k not in {"comments", "all_correct"} and v is True:
                error_counter[k] += 1

    # Determine consensus count and criteria
    fingerprint_counts = Counter(fingerprints)
    most_common_fp, consensus_count = fingerprint_counts.most_common(1)[0]

    entry["All Correct Count"] = all_correct_count
    entry["Consensus Count"] = consensus_count
    entry["Agreed Criteria"] = sorted(most_common_fp)
    entry["Error Summary"] = dict(error_counter)

    summary.append(entry)

# Convert to DataFrame and save
df = pd.DataFrame(summary)
df.to_csv("review_consensus.csv", index=False)
print("Saved consensus table to 'review_consensus.csv'")
