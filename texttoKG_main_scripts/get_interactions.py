import warnings
import os
# import argparse
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from bel_model import bel_extraction_model

warnings.filterwarnings("ignore")


# Function to read the prompt from a file based on an identifier
def get_prompt(identifier, filepath):
    # Determine the absolute path to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the main project directory by going up one level
    project_dir = os.path.dirname(script_dir)

    # Construct the absolute path to the prompt file in the main 'data' directory
    absolute_filepath = os.path.join(project_dir, 'prompts', filepath)

    with open(absolute_filepath, 'rb') as file:
        content = file.read()

    # Check for BOM and remove it
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    lines = content.decode('utf-8').splitlines()
    prompt = []
    capture = False
    for line in lines:
        if line.strip().startswith('#') and identifier in line:
            capture = True
            continue
        if capture:
            if line.strip().startswith('#') and len(prompt) > 0:
                break
            prompt.append(line)
    return ''.join(prompt)


def load_prompt(prompt_file="prompt_file_v6.txt",
                prompt_identifier="general prompt") -> str:
    """Return just the system‑prompt text (one string)."""
    return get_prompt(prompt_identifier, prompt_file)


def build_bel_extraction_chain(prompt_text: str):
    """
    Creates and returns a BEL (Biological Expression Language) extraction processing chain.

    This function constructs a prompt template for a chat-based language model, using the provided
    system prompt text. The template expects user input containing a text and its annotations.
    The resulting chain processes the input through a BEL extraction model and parses the output
    to extract the "interactions" key from the model's JSON response.

    Args:
        prompt_text (str): The system prompt text to guide the BEL extraction process.

    Returns:
        A composed chain that takes annotated text as input, runs BEL extraction, and outputs
        the extracted interactions in structured format.
    """
    ann_prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "{text} | Annotations: {annotations}")
    ])
    return ann_prompt | bel_extraction_model | JsonKeyOutputFunctionsParser(key_name="interactions")
