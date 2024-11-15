import requests
import time
from typing import Dict, List, Optional


def get_pmcid_from_pmid(pmids: List[str], email: str) -> Dict[str, Optional[str]]:
    """
    Look up PMC IDs for a list of PubMed IDs using NCBI's E-utilities.
    Args:
        pmids: List of PubMed IDs as strings
        email: Your email address (required by NCBI)
    Returns:
        Dictionary mapping PMIDs to their PMCIDs (or None if no PMCID exists)
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    results = {}

    # Process PMIDs in batches of 50 to respect NCBI's guidelines
    batch_size = 50

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        params = {
            'db': 'pubmed',
            'id': ','.join(batch),
            'retmode': 'xml',
            'tool': 'python_pmid_lookup',
            'email': email
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()

            # Parse the XML response
            xml_data = response.text

            # Extract PMCIDs using basic string operations
            # This is a simple approach - for production use, consider using xml.etree.ElementTree
            for pmid in batch:
                pmc_start = xml_data.find(f'<PMID>{pmid}</PMID>')
                if pmc_start == -1:
                    results[pmid] = None
                    continue
                pmc_tag = '<ArticleId IdType="pmc">'
                pmc_start = xml_data.find(pmc_tag, pmc_start)

                if pmc_start != -1:
                    pmc_start += len(pmc_tag)
                    pmc_end = xml_data.find('</ArticleId>', pmc_start)
                    pmcid = xml_data[pmc_start:pmc_end].strip()
                    results[pmid] = pmcid
                else:
                    results[pmid] = None

        except requests.exceptions.RequestException as e:
            print(f"Error processing batch starting with PMID {batch[0]}: {str(e)}")
            for pmid in batch:
                results[pmid] = None
        # Sleep to respect NCBI's rate limit (max 3 requests per second)
        time.sleep(0.34)
    return results


def main():
    # Example usage
    pmids = []

    with open('papers/adrenocortical_carcinoma_pmids.txt', 'r') as file:
        for line in file:
            # Strip any whitespace and ensure the line isn't empty
            pmid = line.strip()
            if pmid.isdigit():  # Check if the line contains only digits
                pmids.append(pmid)

    email = "fjames@idekerlab.ucsd.edu"

    print("Looking up PMCIDs...")
    results = get_pmcid_from_pmid(pmids, email)

    print("\nResults:")
    for pmid, pmcid in results.items():
        if pmcid:
            print(f"PMID: {pmid} -> PMCID: {pmcid}")
        else:
            print(f"PMID: {pmid} -> No PMCID found")


if __name__ == "__main__":
    main()
