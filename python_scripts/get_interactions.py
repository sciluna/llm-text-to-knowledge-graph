import warnings
import os
import argparse
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
# from model import extraction_model 
from bel_model import bel_extraction_model

warnings.filterwarnings("ignore")

_hidden = argparse.ArgumentParser(add_help=False)
_hidden.add_argument("--prompt_file", type=str, default=None,
                     help="Path to a custom prompt file")
cli_args, _ = _hidden.parse_known_args()
# use user’s prompt_file if provided, else default:
filepath = cli_args.prompt_file or 'minimal_prompt_1.txt'


def get_prompt(identifier, filepath):
    # Determine the absolute path to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate to the main project directory by going up one level
    project_dir = os.path.dirname(script_dir)

    # Construct the absolute path to the prompt file in the main 'data' directory
    absolute_filepath = os.path.join(project_dir, 'data', filepath)

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


filepath = 'minimal_prompt_1.txt'
prompt_identifier = 'general prompt'
prompt = get_prompt(prompt_identifier, filepath)

ann_prompt = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("human", "{text} | Annotations: {annotations}")
])


bel_extraction_chain = ann_prompt | bel_extraction_model | JsonKeyOutputFunctionsParser(key_name="interactions")
