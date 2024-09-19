from indra_download_extract import fetch_pmc_article, setup_output_directory, save_to_json
from get_indra_statements import process_nxml_file
from sentence_level_extraction import extract_sentences, llm_processing, create_combined_results
from convert_to_cx2 import convert_to_cx2

pmc_id = 'PMC3898398'

# Ensure the output directory exists
output_dir = setup_output_directory(pmc_id)

# get the xml file of the pmc_id
xml_file = fetch_pmc_article(pmc_id)

# process the xml file with reach to get the indra statements 
file_name = xml_file
indra_statements = process_nxml_file(file_name=file_name)

# processing the statements to get just the sentences
sentences = extract_sentences(indra_statements)
selected_keys = sorted(sentences.keys())[:]

# process sentences with llm model
llm_results = llm_processing(selected_keys, sentences)
json_data = save_to_json(llm_results, 'llm_results.json')

# combines extracted results into subject-interaction_type-object
llm_combined_results = create_combined_results(llm_results["LLM_extractions"])
save_to_json(llm_combined_results, 'llm_combined_results.json')


# convert results to cx2 format
cx2_network = convert_to_cx2(llm_combined_results)
net_cx = cx2_network.to_cx2()
save_to_json(net_cx, 'llm_network.cx')
