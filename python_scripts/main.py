#!/usr/bin/env python3
import argparse
import sys
import logging
import re
from indra_download_extract import fetch_pmc_article, setup_output_directory, save_to_json
from get_indra_statements import process_nxml_file
from sentence_level_extraction import extract_sentences, llm_processing, create_combined_results
from convert_to_cx2 import convert_to_cx2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def validate_pmc_id(pmc_id):
    pattern = r'^PMC\d+$'
    if not re.match(pattern, pmc_id):
        raise ValueError("Invalid PMC ID format. It should start with 'PMC' followed by digits.")


def main(pmc_id):
    """
    Main function to process a PMC article and extract interaction data.

    Args:
        pmc_id (str): PubMed Central ID of the article to process.
    """
    try:
        validate_pmc_id(pmc_id)
        logging.info(f"Setting up output directory for {pmc_id}")
        output_dir = setup_output_directory(pmc_id)

        logging.info(f"Fetching XML file for {pmc_id}")
        xml_file = fetch_pmc_article(pmc_id, output_dir)

        logging.info("Processing XML file with Reach to get INDRA statements")
        indra_statements = process_nxml_file(xml_file)

        logging.info("Extracting sentences from INDRA statements")
        sentences = extract_sentences(indra_statements)
        selected_keys = sorted(sentences.keys())

        logging.info("Processing sentences with LLM model")
        llm_results = llm_processing(selected_keys, sentences)
        llm_results_filename = f'llm_results_{pmc_id}.json'
        save_to_json(llm_results, llm_results_filename, output_dir)

        logging.info("Combining extracted results into subject-interaction_type-object")
        llm_combined_results = create_combined_results(llm_results["LLM_extractions"])
        llm_combined_results_filename = f'llm_combined_results_{pmc_id}.json'
        save_to_json(llm_combined_results, llm_combined_results_filename, output_dir)

        logging.info("Converting results to CX2 format")
        cx2_network = convert_to_cx2(llm_combined_results)
        net_cx = cx2_network.to_cx2()
        cx2_filename = f'llm_network_{pmc_id}.cx'
        save_to_json(net_cx, cx2_filename, output_dir)

        logging.info("Processing completed successfully.")

    except ValueError as ve:
        logging.error(ve)
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PMC articles to extract interaction data "
                                                 "and convert to CX2 format.")
    parser.add_argument("pmc_id", help="PubMed Central ID of the article to process (e.g., PMC1234567)")
    args = parser.parse_args()

    main(args.pmc_id)
