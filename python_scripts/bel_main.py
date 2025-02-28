import sys
import os
import re
import argparse
import logging
from ndex2.client import Ndex2
from convert_to_cx2 import convert_to_cx2
from pub import get_pubtator_paragraphs, download_pubtator_xml
from process_text_file import process_paper
from sentence_level_extraction import llm_ann_processing
from grounding_genes import annotate_paragraphs_in_json, process_annotations
from indra_download_extract import save_to_json, setup_output_directory
from transform_bel_statements import process_llm_results

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def validate_pmc_id(pmc_id):
    pattern = r'^PMC\d+$'
    if not re.match(pattern, pmc_id):
        raise ValueError("Invalid PMC ID format. It should start with 'PMC' followed by digits.")


def process_pmc_document(pmc_id, ndex_email=None, ndex_password=None, style_path=None, upload_to_ndex=False):
    """
    Process a document given a PMC ID.
    Steps:
      1. Validate PMC ID and set up the output directory.
      2. Download the PubTator XML and extract paragraphs.
      3. Annotate paragraphs using Gilda (passing JSON data directly).
      4. Process annotated paragraphs through the LLM-BEL model.
      5. Process annotations to generate node URLs.
      6. Convert results to a CX2 network and optionally upload to NDEx.
    """
    validate_pmc_id(pmc_id)
    logging.info(f"Setting up output directory for {pmc_id}")
    output_dir = setup_output_directory(pmc_id)

    file_path = download_pubtator_xml(pmc_id, output_dir)
    if not file_path:
        logging.error("Aborting process due to download failure.")
        return False

    logging.info("Processing XML file to extract text paragraphs")
    paragraphs = get_pubtator_paragraphs(file_path)
    paragraphs_filename = f"{pmc_id}_pub_paragraphs.json"
    save_to_json(paragraphs, paragraphs_filename, output_dir)

    logging.info("Annotating paragraphs using Gilda")
    annotated_paragraphs = annotate_paragraphs_in_json(paragraphs)
    annotated_filename = f"{pmc_id}_annotated_paragraphs.json"
    save_to_json(annotated_paragraphs, annotated_filename, output_dir)

    logging.info("Processing annotated paragraphs with the LLM-BEL model")
    llm_results = llm_ann_processing(annotated_paragraphs)
    llm_filename = 'llm_results.json'
    save_to_json(llm_results, llm_filename, output_dir)

    logging.info("Processing annotations to extract node URLs")
    processed_annotations = process_annotations(llm_results)

    logging.info("Generating CX2 network")
    extracted_results = process_llm_results(processed_annotations)
    cx2_network = convert_to_cx2(extracted_results, style_path=style_path)
    cx2_network.set_name('LLM Text to Knowledge Graph for publication: ' + str(pmc_id))
    cx2_filename = 'cx2_network.cx'
    save_to_json(cx2_network.to_cx2(), cx2_filename, output_dir)

    if upload_to_ndex:
        if not ndex_email or not ndex_password:
            logging.error("NDEx email and password are required to upload.")
            return False
        logging.info("Uploading CX2 network to NDEx")
        client = Ndex2(username=ndex_email, password=ndex_password)
        client.save_new_cx2_network(cx2_network.to_cx2())

    logging.info(f"Processing completed successfully for {pmc_id}.")
    return True


def process_file_document(file_path, ndex_email=None, ndex_password=None, style_path=None, upload_to_ndex=False):
    """
    Process a document given a file path (PDF or TXT).
    Steps:
      1. Set up the output directory using the file's base name.
      2. Process the file to extract paragraphs.
      3. Annotate paragraphs using Gilda (passing JSON data directly).
      4. Process annotated paragraphs with the LLM-BEL model.
      5. Process annotations to generate node URLs.
      6. Convert results to a CX2 network and optionally upload to NDEx.
    """
    output_name = os.path.splitext(os.path.basename(file_path))[0]
    logging.info(f"Setting up output directory for file: {output_name}")
    output_dir = setup_output_directory(output_name)

    logging.info("Processing file to extract paragraphs")
    paragraphs = process_paper(file_path)
    paragraphs_filename = "processed_paragraphs.json"
    save_to_json(paragraphs, paragraphs_filename, output_dir)

    logging.info("Annotating paragraphs using Gilda")
    annotated_paragraphs = annotate_paragraphs_in_json(paragraphs)
    annotated_filename = "annotated_paragraphs.json"
    save_to_json(annotated_paragraphs, annotated_filename, output_dir)

    logging.info("Processing annotated paragraphs with the LLM-BEL model")
    llm_results = llm_ann_processing(annotated_paragraphs)
    llm_filename = 'llm_results.json'
    save_to_json(llm_results, llm_filename, output_dir)

    logging.info("Processing annotations to extract node URLs")
    processed_annotations = process_annotations(llm_results)

    logging.info("Generating CX2 network")
    extracted_results = process_llm_results(processed_annotations)
    cx2_network = convert_to_cx2(extracted_results, style_path=style_path)
    cx2_network.set_name('LLM Text to Knowledge Graph for publication: ' + output_name)
    cx2_filename = 'cx2_network.cx'
    save_to_json(cx2_network.to_cx2(), cx2_filename, output_dir)

    if upload_to_ndex:
        if not ndex_email or not ndex_password:
            logging.error("NDEx email and password are required to upload.")
            return False
        logging.info("Uploading CX2 network to NDEx")
        client = Ndex2(username=ndex_email, password=ndex_password)
        client.save_new_cx2_network(cx2_network.to_cx2())

    logging.info(f"Processing completed successfully for {output_name}.")
    return True


def process_document(pmc_id=None, pdf_path=None, txt_path=None, ndex_email=None, ndex_password=None, 
                     style_path=None, upload_to_ndex=False):
    """
    Determines the input type (PMC ID or file path) and routes to the appropriate processing function.
    Exactly one of pmc_id, pdf_path, or txt_path should be provided.
    """
    inputs_provided = sum([1 for i in [pmc_id, pdf_path, txt_path] if i])
    if inputs_provided != 1:
        raise ValueError("Please provide exactly one input: either pmc_id or pdf_path/txt_path.")

    if pmc_id:
        return process_pmc_document(pmc_id, ndex_email, ndex_password, upload_to_ndex, style_path=style_path)
    else:
        file_path = pdf_path or txt_path
        return process_file_document(file_path, ndex_email, ndex_password, upload_to_ndex, style_path=style_path)


if __name__ == "__main__":
    # set the default style path
    script_dir = os.path.dirname(os.path.abspath(__file__))  # path to python_scripts
    repo_dir = os.path.abspath(os.path.join(script_dir, os.pardir))  # move one level up
    default_style_path = os.path.join(repo_dir, 'data', 'cx_style.json')

    parser = argparse.ArgumentParser(
        description="Process a document (PMC, PDF, or TXT) to extract BEL statements and generate a CX2 network."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pmc_id", 
                       type=str, 
                       help="PMC ID of the article to process")
    group.add_argument("--pdf_path", 
                       type=str, 
                       help="Path to the PDF file to process")
    group.add_argument("--txt_path", 
                       type=str, 
                       help="Path to the text file to process")

    parser.add_argument("--ndex_email", 
                        type=str, 
                        help="NDEx account email for authentication")
    parser.add_argument("--ndex_password", 
                        type=str, 
                        help="NDEx account password for authentication")
    parser.add_argument("--style_path", 
                        type=str, 
                        default=default_style_path, 
                        help="Path to the JSON file containing the Cytoscape visual style (optional)")

    parser.add_argument("--upload_to_ndex", 
                        action="store_true", 
                        help="Flag to upload the CX2 network to NDEx")

    args = parser.parse_args()

    success = process_document(
        pmc_id=args.pmc_id,
        pdf_path=args.pdf_path,
        txt_path=args.txt_path,
        ndex_email=args.ndex_email,
        ndex_password=args.ndex_password,
        style_path=args.style_path,
        upload_to_ndex=args.upload_to_ndex
    )

    if not success:
        sys.exit(1)
