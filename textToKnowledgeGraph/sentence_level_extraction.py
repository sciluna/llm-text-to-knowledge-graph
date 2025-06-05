import os
import json
import time
import logging
from .get_interactions import build_bel_extraction_chain, load_prompt
from functools import lru_cache

logger = logging.getLogger(__name__)


def load_json_data(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data


@lru_cache(maxsize=6)
def _build_chain_cached(prompt_file, prompt_identifier, api_key, prompt_mtime):
    """
    Real chain builder wrapped by lru_cache.
    `prompt_mtime` is only used to make the cache key unique when the
    file changes; we never use its value inside the function body.
    """
    prompt_txt = load_prompt(prompt_file, prompt_identifier)
    return build_bel_extraction_chain(prompt_txt, api_key)


def _build_chain(prompt_file, prompt_identifier, api_key):
    """
    Get the BEL extraction chain for (file, identifier), rebuilding
    automatically if the file was edited since last time.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    absolute_filepath = os.path.join(project_dir, 'data', prompt_file)

    try:
        mtime = os.path.getmtime(prompt_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    return _build_chain_cached(absolute_filepath, prompt_file, prompt_identifier, mtime, api_key)


# Initialize dictionaries to store the results
llm_results = {}


#Extracting BEL interactions from sentences with annotations using llm
def llm_bel_processing(paragraphs, api_key, 
                       prompt_file="prompt_file_v6.txt",
                       prompt_identifier="general prompt"):
    bel_extraction_chain = _build_chain(prompt_file, prompt_identifier, api_key)
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
    logger.info(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return llm_results
