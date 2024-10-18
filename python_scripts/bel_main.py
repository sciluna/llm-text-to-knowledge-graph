from bel_statements import process_bel_file
from sentence_level_extraction import llm_bel_processing, combine_llm_and_bel_extractions
from indra_download_extract import save_to_json, setup_output_directory


pmid = 'pmid1292803'
output_dir = setup_output_directory(pmid)

file_path = 'papers/pmid1292803.bel'
modified_sentences, bel_data = process_bel_file(file_path)

sentence_results_filename = 'sentences_only.json'
sentence_with_extractions_filename = 'sentences_with_extractions.json'

save_to_json(modified_sentences, sentence_results_filename, output_dir)
save_to_json(bel_data, sentence_with_extractions_filename, output_dir)

llm_results = llm_bel_processing(modified_sentences)

llm_filename = 'llm_results.json'
save_to_json(llm_results, llm_filename, output_dir)

combined_results = combine_llm_and_bel_extractions(llm_results, bel_data)
combined_results_filename = 'combined_outputs.json'
save_to_json(combined_results, combined_results_filename, output_dir)
