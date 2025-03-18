import os
import json
import warnings
import time
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from get_interactions import prompt
warnings.filterwarnings("ignore")

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


# Define a function that adds a delay to API calls
def delayed_completion(model_type: str, delay_in_seconds: float = 1, **kwargs):
    """Delay a completion by a specified amount of time and return appropriate model.""" 
    time.sleep(delay_in_seconds)

    if model_type.lower() == "openai":
        return ChatOpenAI(**kwargs)
    elif model_type.lower() == "anthropic":
        return ChatAnthropic(**kwargs)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


# Rate limiting parameters
rate_limit_per_minute = 3
delay = 60.0 / rate_limit_per_minute


# Pydantic schema definition for BEL extraction
class BELInteraction(BaseModel):
    """BEL interaction extracted from the sentence."""
    bel_statement: str = Field(..., description="A BEL formatted statement representing an interaction.")
    evidence: str = Field(
        ..., 
        description="The exact sentence from which the interacting subject and object is taken from"
    )


class BELInteractions(BaseModel):
    """BEL interaction collection for a sentence."""
    interactions: List[BELInteraction]


# Function to create the appropriate model with structured output
def create_extraction_model(model_provider: str = "openai"):
    """Create a model based on the specified provider with structured output."""
    if model_provider.lower() == "openai":
        model = delayed_completion(
            model_type="openai",
            delay_in_seconds=delay,
            model="gpt-4o",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
    elif model_provider.lower() == "anthropic":
        model = delayed_completion(
            model_type="anthropic",
            delay_in_seconds=delay,
            model="claude-3-5-haiku-latest",
            temperature=0,
            anthropic_api_key=ANTHROPIC_API_KEY
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

    # Apply structured output to the model
    return model.with_structured_output(BELInteractions)


ann_prompt = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("human", "{text} | Annotations: {annotations}")
])


# Function to create the extraction chain
def create_extraction_chain(model_provider=None):
    """Create an extraction chain using the specified model provider."""
    if model_provider is None:
        raise ValueError("model_provider must be specified ('openai' or 'anthropic')")
    model = create_extraction_model(model_provider)

    # Add a response validator step
    def validate_response(response):
        if not hasattr(response, 'interactions'):
            print("Response missing 'interactions' field - creating default")
            return BELInteractions(interactions=[])
        return response

    return ann_prompt | model | validate_response


# Function to process text and return JSON
def process_text_to_json(input_text, annotations="", model_provider=None):
    if model_provider is None:
        raise ValueError("model_provider must be specified ('openai' or 'anthropic')")

    extraction_chain = create_extraction_chain(model_provider)

    try:
        # Get the structured result (Pydantic object)
        result = extraction_chain.invoke({
            "text": input_text,
            "annotations": annotations
        })

        # Convert the Pydantic object to a JSON string
        return result.model_dump_json(indent=2)

    except Exception as e:
        print(f"Error processing text: {e}")

        # Return a valid default structure that matches your expected format
        default_result = BELInteractions(interactions=[])
        return default_result.model_dump_json(indent=2)


def llm_processing(paragraphs, model_provider=None):
    if model_provider is None:
        raise ValueError("model_provider must be specified ('openai' or 'anthropic')")

    llm_results = {"LLM_extractions": []}
    start_time = time.time()

    # Loop through the paragraphs dictionary
    for index, paragraph_info in paragraphs.items():
        sentence = paragraph_info['text']
        annotations = paragraph_info.get('annotations', [])  # Default to empty list if no annotations

        # Filter out MESH / MESHD annotations
        filtered_annotations = [
            ann for ann in annotations
            if ann.get("db") not in ("MESH", "MESHD")
        ]

        # Use process_text_to_json to get JSON string
        json_result = process_text_to_json(sentence, filtered_annotations, model_provider)

        # Parse the JSON string back to a Python dictionary
        results_dict = json.loads(json_result)

        # Extract just the interactions array from the nested structure
        interactions = results_dict.get('interactions', [])

        # Add to the results collection with the flattened structure
        llm_results["LLM_extractions"].append({
            "Index": index,
            "text": sentence,
            "Results": interactions,
            "annotations": filtered_annotations
        })

    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_minutes = elapsed_time / 60
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_minutes:.2f} minutes)")
    return llm_results
