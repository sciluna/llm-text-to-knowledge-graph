import json
from get_interactions import extraction_chain, bel_extraction_chain
import time


def load_json_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data


# Initialize dictionaries to store the results
llm_results = {}


#extracting interactions from sentences without annotations using llm
def llm_processing(sentences):
    llm_results = {"LLM_extractions": []}
    start_time = time.time()

    # Loop through the sentences dictionary directly
    for index, sentence_info in sentences.items():
        sentence = sentence_info['text']  # Assuming 'text' is the correct key for the sentence
        results = extraction_chain.invoke({
            "text": sentence
        })
        llm_results["LLM_extractions"].append({
            "Index": index,
            "text": sentence,
            "Results": results
        })

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return llm_results


#extracting bel functions using llm
def llm_bel_processing(paragraphs):
    llm_results = {"LLM_extractions": []}
    start_time = time.time()

    # Loop through the sentences dictionary directly
    for index, paragraph_info in paragraphs.items():
        paragraph = paragraph_info['text']  # Assuming 'text' is the correct key for the sentence
        results = bel_extraction_chain.invoke({
            "text": paragraph
        })

        llm_results["LLM_extractions"].append({
            "Index": index,
            "text": paragraph,
            "Results": results
        })

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return llm_results


#extracting interactions from sentences with annotations using llm
def llm_ann_processing(paragraphs):
    llm_results = {"LLM_extractions": []}
    start_time = time.time()

    # Loop through the sentences dictionary directly
    for index, paragraph_info in paragraphs.items():
        sentence = paragraph_info['text']
        annotations = paragraph_info.get('annotations', [])  # Default to empty list if no annotations
        results = bel_extraction_chain.invoke({
            "text": sentence,
            "annotations": annotations
        })
        llm_results["LLM_extractions"].append({
            "Index": index,
            "text": sentence,
            "Results": results,
            "annotations": annotations
        })

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return llm_results
