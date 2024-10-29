import argparse
import sys
import logging
from indra_download_extract import setup_output_directory, save_to_json
from sentence_level_extraction import llm_processing, create_combined_results
from convert_to_cx2 import convert_to_cx2
from pub import get_pubtator_sentences

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def main(pmc_id, file_path):
    """

    Main function to process pubtator xml file

    Args:
        file_path (str): Filepath to downloaded xml file of paper from pubtator
        pmc_id(str): PubMed Central ID of the article to process.

    """
    try:
        logging.info(f"Setting up output directory for {pmc_id}")
        output_dir = setup_output_directory(pmc_id)

        logging.info("Processing xml file to get text paragraphs")
        paragraphs = get_pubtator_sentences(file_path)
        paragraphs_filename = f"{pmc_id}_text_paragraphs.json"
        save_to_json(paragraphs, paragraphs_filename, output_dir)

        if not paragraphs:
            logging.info("No passages with sufficient annotations to process.")
            return

        logging.info("Processing paragraphs with LLM model")
        llm_results = llm_processing(paragraphs)
        llm_results_filename = f'pub_results_{pmc_id}.json'
        save_to_json(llm_results, llm_results_filename, output_dir)      

        # logging.info("processing sentences with indra reach")
        # indra_results = indra_processing(selected_keys, paragraphs)
        # indra_results_filename = f'indra_results_{pmc_id}.json'
        # save_to_json(indra_results, indra_results_filename, output_dir)

        logging.info("Combining extracted results into subject-interaction_type-object")
        llm_combined_results = create_combined_results(llm_results["LLM_extractions"])
        llm_combined_results_filename = f'llm_combined_results_{pmc_id}.json'
        save_to_json(llm_combined_results, llm_combined_results_filename, output_dir)    

        # logging.info("Combining extracted results into subject-interaction_type-object")
        # indra_combined_results = create_combined_results(indra_results["INDRA_REACH_extractions"])
        # indra_combined_results_filename = f'indra_combined_results_{pmc_id}.json'
        # save_to_json(indra_combined_results, indra_combined_results_filename, output_dir) 

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
    parser = argparse.ArgumentParser(description="Process PubTator XML files to extract interaction data "
                                                 "and convert to CX2 format.")
    parser.add_argument("pmc_id", help="PubMed Central ID of the article to process (e.g., PMC1234567)")
    parser.add_argument("xml_file_path", help="Path to the PubTator XML file to process")
    args = parser.parse_args()

    main(args.pmc_id, args.xml_file_path)
