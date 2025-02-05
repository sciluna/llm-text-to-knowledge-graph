import sys
import re
import argparse
import logging
from ndex2.client import Ndex2
from convert_to_cx2 import convert_to_cx2
from pub import get_pubtator_paragraphs, download_pubtator_xml
from sentence_level_extraction import llm_bel_processing
from indra_download_extract import save_to_json, setup_output_directory
from transform_bel_statements import process_llm_results


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def validate_pmc_id(pmc_id):
    pattern = r'^PMC\d+$'
    if not re.match(pattern, pmc_id):
        raise ValueError("Invalid PMC ID format. It should start with 'PMC' followed by digits.")


def process_paper_to_bel_cx2(pmc_id, style_path=None):
    """
    Process a single PMC ID to generate a CX2 network.

    Args:
        pmc_id (str): The PubMed Central ID of the article to process.
        style_path (str, optional): Path to the style JSON file for network styling.

    Returns:
        cx2 network or FALSE
    """
    try:
        validate_pmc_id(pmc_id)
        logging.info(f"Setting up output directory for {pmc_id}")
        output_dir = setup_output_directory(pmc_id)

        file_path = download_pubtator_xml(pmc_id, output_dir)
        if not file_path:
            logging.error("Aborting process due to download failure.")
            return

        logging.info("Processing xml file to get text paragraphs")
        paragraphs = get_pubtator_paragraphs(file_path)

        logging.info("Processing paragraphs with LLM-BEL model")
        llm_results = llm_bel_processing(paragraphs)

        logging.info("Processing LLM results to generate CX2 network")
        extracted_results = process_llm_results(llm_results)
        cx2_network = convert_to_cx2(extracted_results, style_path=style_path)
        cx2_network.set_name(f"{pmc_id}_bel_graph")

        logging.info(f"Processing completed successfully for {pmc_id}.")
        return cx2_network

    except ValueError as ve:
        logging.error(ve)
        sys.exit(1)
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
        return False
