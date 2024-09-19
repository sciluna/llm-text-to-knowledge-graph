import argparse
from indra_download_extract import fetch_pmc_article, setup_output_directory, save_to_json
from get_indra_statements import process_nxml_file
from sentence_level_extraction import extract_sentences, llm_processing, create_combined_results
from convert_to_cx2 import convert_to_cx2
import sys
import os


sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def main(pmc_id):
    # Ensure the output directory exists
    output_dir = setup_output_directory(pmc_id)

    # Get the XML file of the pmc_id
    xml_file = fetch_pmc_article(pmc_id, output_dir)

    # Process the XML file with Reach to get the INDRA statements 
    indra_statements = process_nxml_file(xml_file)

    # Processing the statements to get just the sentences
    sentences = extract_sentences(indra_statements)
    selected_keys = sorted(sentences.keys())

    # Process sentences with LLM model
    llm_results = llm_processing(selected_keys, sentences)
    save_to_json(llm_results, 'llm_results.json', output_dir)

    # Combines extracted results into subject-interaction_type-object
    llm_combined_results = create_combined_results(llm_results["LLM_extractions"])
    save_to_json(llm_combined_results, 'llm_combined_results.json', output_dir)

    # Convert results to CX2 format
    cx2_network = convert_to_cx2(llm_combined_results)
    net_cx = cx2_network.to_cx2()
    save_to_json(net_cx, 'llm_network.cx', output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PMC articles to extract interaction data "
                                     "and convert to CX2 format.")

    parser.add_argument("pmc_id", help="PubMed Central ID of the article to process")
    args = parser.parse_args()

    main(args.pmc_id)
