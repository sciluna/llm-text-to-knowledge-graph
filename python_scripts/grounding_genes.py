# import os
import json
from gilda import annotate


def load_json_data(filepath):
    """Load JSON data from a file."""
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def annotate_paragraphs_in_json(data):   
    """
    Accepts JSON data (a dictionary) directly, annotates each entry's text using Gilda,
    and returns a dictionary with the annotated data.

    The expected input is a dict with structure similar to:
    {
      "1": {"text": "Some text..."},
      "2": {"text": "More text..."},
      ...
    }
    """
    annotated_data = {}

    # Process each entry in the input data
    for key_str, entry_obj in data.items():
        text_to_annotate = entry_obj["text"]

        # Annotate the text with Gilda
        gilda_annots = annotate(text=text_to_annotate)  # Ensure the 'annotate' function is imported or defined

        # Gather top matches (db, id, entry_name) only
        annots_as_list = []
        for ann in gilda_annots:
            if ann.matches:
                top_match = ann.matches[0]
                best_obj = {
                    "matched_text": ann.text,                
                    "db": top_match.term.db,
                    "id": top_match.term.id,
                    "entry_name": top_match.term.entry_name,
                    "score": top_match.score
                }
                # if top_match.score > threshold:  # Only include matches with a score > 0.7
                annots_as_list.append(best_obj)

        # Construct the new entry
        annotated_data[key_str] = {
            "text": text_to_annotate,
            "annotations": annots_as_list
        }

    return annotated_data


def process_annotations(data):
    """
    Accepts JSON data (a dictionary) directly, processes LLM extractions,
    and updates annotations by constructing URLs for each annotation.

    The expected input is a dict with structure:
    { "LLM_extractions": [ {...}, {...}, ... ] }
    """
    llm_extractions = data.get("LLM_extractions", [])
    new_extractions = []

    for item in llm_extractions:
        # Skip if "Results" is empty (no BEL statements)
        results = item.get("Results", [])
        if not results:
            continue

        # Process annotations for the item
        annotations = item.get("annotations", [])
        transformed_annotations = []
        for ann in annotations:
            db = ann.get("db", "")
            the_id = ann.get("id", "")

            if ":" in the_id:
                # The ID already has its prefix (e.g., "CHEBI:15846")
                final_id = the_id
            else:
                # Combine db and id (e.g., "HGNC:14929")
                final_id = f"{db}:{the_id}" if db and the_id else (db or the_id)

            # Construct the full URI using identifiers.org
            url = f"https://identifiers.org/{final_id}"
            new_ann = {
                "url": url,
                "entry_name": ann.get("entry_name")
            }
            transformed_annotations.append(new_ann)

        # Build a new item retaining the necessary information
        new_item = {
            "Index": item.get("Index"),
            "text": item.get("text"),
            "Results": results,
            "annotations": transformed_annotations
        }
        new_extractions.append(new_item)

    # Wrap the new extractions in the top-level structure
    processed_data = {"LLM_extractions": new_extractions}
    return processed_data


# Example usage:
# if __name__ == "__main__":
#     input_file = "results/review_paper1_cleaned.json"        
#     output_file = "results/review_paper1_annotated.json"
#     annotate_paragraphs_in_json(input_file, output_json_path=output_file)
