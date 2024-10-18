import os
import json
import requests
import os.path
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

pmc_url = 'https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi'


def get_xml(pmc_id):
    """Returns XML for the article corresponding to a PMC ID."""
    if pmc_id.upper().startswith('PMC'):
        pmc_id = pmc_id[3:]
    # Request params
    params = {}
    params['verb'] = 'GetRecord'
    params['identifier'] = 'oai:pubmedcentral.nih.gov:%s' % pmc_id
    params['metadataPrefix'] = 'pmc'
    # Submit the request
    res = requests.get(pmc_url, params)
    if not res.status_code == 200:
        logger.warning("Couldn't download %s" % pmc_id)
        return None
    # Read the bytestream
    xml_bytes = res.content
    # Check for any XML errors; xml_str should still be bytes
    #tree = ET.XML(xml_bytes, parser=UTB())
    tree = ET.XML(xml_bytes)
    xmlns = "http://www.openarchives.org/OAI/2.0/"
    err_tag = tree.find('{%s}error' % xmlns)
    if err_tag is not None:
        err_code = err_tag.attrib['code']
        err_text = err_tag.text
        logger.warning('PMC client returned with error %s: %s'
                       % (err_code, err_text))
        return None
    # If no error, return the XML as a unicode string
    else:
        return xml_bytes.decode('utf-8')


def setup_output_directory(pmc_id):
    # Get the absolute path to the directory where the script is running
    script_dir = os.path.dirname(__file__)
    # Navigate to the main project directory (assuming the script is in a subdirectory of the main project directory)
    project_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    # Set up the output directory within the 'results' directory of the project
    output_dir = os.path.join(project_dir, 'results', pmc_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def save_to_json(data, filename, output_dir):
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"File saved successfully to {file_path}")


def fetch_pmc_article(pmc_id, output_dir):
    xml_string = get_xml(pmc_id)
    if xml_string is None:
        print("Failed to fetch or parse XML.")
        return None
    output_path = f"{output_dir}/{pmc_id}.xml"
    with open(output_path, "w") as file:
        file.write(xml_string)
    print(f"File saved successfully to {output_path}")
    return output_path
