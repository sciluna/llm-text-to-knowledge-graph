import os
import json
import time
import os.path
import logging
from indra.sources import reach

logger = logging.getLogger(__name__)


def setup_output_directory(pmc_id=None, file_path=None):
    if pmc_id and file_path:
        raise ValueError("Please provide only pmc_id or file_path, not both.")
    if not pmc_id and not file_path:
        raise ValueError("Either pmc_id or file_path must be provided.")

    # Get the absolute path to the directory where the script is running
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate to the main project directory (assuming the script is in a subdirectory of the main project directory)
    project_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

    # Determine the folder name
    if pmc_id:
        folder_name = pmc_id
    else:
        # Extract the file name (without extension) from file_path
        file_base = os.path.splitext(os.path.basename(file_path))[0]
        folder_name = file_base

    # Set up the output directory within the 'results' directory of the project
    output_dir = os.path.join(project_dir, 'results', folder_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return output_dir


def save_to_json(data, filename, output_dir):
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print(f"File saved successfully to {file_path}") 


def indra_processing(evidence_by_index):
    indra_reach_results = {"INDRA_REACH_extractions": []}
    start_time = time.time()

    # Loop through the sentences dictionary directly
    for index_entry in evidence_by_index:
        index = index_entry["Index"]
        evidences = index_entry["evidences"]

        for evidence_text in evidences:
            # Remove the "evidence: " prefix
            sentence = evidence_text.replace("evidence: ", "", 1).strip()
            reach_processor = reach.process_text(sentence, url=reach.local_text_url)
            stmts = reach_processor.statements
            statements_json = [stmt.to_json() for stmt in stmts]

            indra_reach_results["INDRA_REACH_extractions"].append({
                "Index": index,
                "Evidence": sentence,
                "Results": statements_json
            })

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    print(f"Time taken for indra processing: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return indra_reach_results
