import os
import argparse
import logging
import sys
import time
from bel_main import process_document


def main():
    start_time = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))  # path to batch_processor.py
    repo_dir = os.path.abspath(os.path.join(script_dir, os.pardir))  # move one level up
    default_style_path = os.path.join(repo_dir, 'data', 'cx_style.json')

    parser = argparse.ArgumentParser(
        description="Batch process multiple documents (PMC IDs and/or file paths) through the pipeline."
    )
    parser.add_argument(
        "--pmc_ids",
        nargs="*",
        default=[],
        help="Space-separated list of PMC IDs to process (e.g., PMC123456 PMC234567)."
    )
    parser.add_argument(
        "--file_paths",
        nargs="*",
        default=[],
        help="Space-separated list of file paths (PDF or TXT) to process."
    )
    parser.add_argument("--ndex_email", type=str, help="NDEx account email", default=None)
    parser.add_argument("--ndex_password", type=str, help="NDEx account password", default=None)
    parser.add_argument(
        "--style_path",
        type=str,
        default=default_style_path,
        help="Path to the Cytoscape visual style JSON file (optional)"
    )

    parser.add_argument(
        "--upload_to_ndex",
        action="store_true",
        help="Flag to upload the generated CX2 network to NDEx"
    )
    parser.add_argument(
        "--custom_name",
        type=str,
        default=None,
        help="Custom network name for file inputs; if provided, this name will be used."
    )
    parser.add_argument(
        "--pmid_for_file",
        type=str,
        default=None,
        help="PMID/PMCID for file input to fetch metadata and set network properties."
    )

    args = parser.parse_args()

    # Ensure that at least one input type is provided
    if not args.pmc_ids and not args.file_paths:
        logging.error("No inputs provided. Please specify at least one --pmc_ids or --file_paths.")
        sys.exit(1)

    overall_success = True

    # Process each PMC ID
    for pmc_id in args.pmc_ids:
        logging.info(f"Starting processing for PMC ID: {pmc_id}")
        success = process_document(
            pmc_id=pmc_id,
            ndex_email=args.ndex_email,
            ndex_password=args.ndex_password,
            style_path=args.style_path,
            upload_to_ndex=args.upload_to_ndex
        )
        if not success:
            logging.error(f"Processing failed for PMC ID: {pmc_id}")
            overall_success = False

    # Process each file path
    for file_path in args.file_paths:
        logging.info(f"Starting processing for file: {file_path}")
        success = process_document(
            pdf_path=file_path,  # process_document will treat it as a file input
            ndex_email=args.ndex_email,
            ndex_password=args.ndex_password,
            style_path=args.style_path,
            upload_to_ndex=args.upload_to_ndex,
            custom_name=args.custom_name,
            pmid_for_file=args.pmid_for_file
        )
        if not success:
            logging.error(f"Processing failed for file: {file_path}")
            overall_success = False

    elapsed_time = time.time() - start_time
    logging.info(f"Total elapsed time: {elapsed_time:.2f} seconds")

    if not overall_success:
        logging.error("One or more documents failed to process.")
        sys.exit(1)
    else:
        logging.info("Batch processing completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()
