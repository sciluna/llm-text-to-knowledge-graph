import os
import json
from get_interactions import build_bel_extraction_chain, load_prompt
import time
from functools import lru_cache


def load_json_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data


@lru_cache(maxsize=6)
def _build_chain_cached(prompt_file, prompt_identifier, prompt_mtime):
    """
    Real chain builder wrapped by lru_cache.
    `prompt_mtime` is only used to make the cache key unique when the
    file changes; we never use its value inside the function body.
    """
    prompt_txt = load_prompt(prompt_file, prompt_identifier)
    return build_bel_extraction_chain(prompt_txt)


def _build_chain(prompt_file, prompt_identifier):
    """
    Get the BEL extraction chain for (file, identifier), rebuilding
    automatically if the file was edited since last time.
    """
    try:
        mtime = os.path.getmtime(prompt_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    return _build_chain_cached(prompt_file, prompt_identifier, mtime)


# Initialize dictionaries to store the results
llm_results = {}


def llm_ann_processing(paragraphs, prompt_file="prompt_file_v6.txt",
                       prompt_identifier="general prompt"):
    """
Processes a dictionary of paragraphs to extract BEL (Biological Expression Language) functions using a language model.

Args:
    paragraphs (dict): A dictionary where each key is an index and each value is a dictionary containing:
        - 'text' (str): The sentence or paragraph to process.
        - 'annotations' (list, optional): A list of annotations associated with the text.

Returns:
    dict: A dictionary with a single key "LLM_extractions" mapping to a list of extraction results. 
          Each result is a dictionary containing:
            - "Index": The index of the paragraph.
            - "text": The original sentence or paragraph.
            - "Results": The output from the BEL extraction chain.
            - "annotations": The annotations associated with the text.
"""
    bel_extraction_chain = _build_chain(prompt_file, prompt_identifier)
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
