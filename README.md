# textToKnowledgeGraph

A Python package to generate BEL statements and CX2 networks.

## Table of Contents

- [Project Description](#project-description)
- [Dependecies](#dependecies)
- [Glossary](#glossary)
- [Installation](#installation)
- [Methodology](#methodology)
  - [Features Available](#features-available)
  - [BEL Generation](#bel-generation)
  - [CX2 Network Generation](#cx2-network-generation)
  - [Uploading to NDEx](#uploading-to-ndex)
- [Usage](#usage)

## Project Description

`textToKnowledgeGraph` is a Python package that converts natural language scientific text into structured knowledge graphs using the capabilities of advanced language models (LLMs). It can be used for:

- Generating BEL statements.
- Extracting entities and interactions from scientific text.
- Uploading the generated CX2 networks to NDEx.

## Dependecies

- "Python>=3.11",
- "langchain==0.3.13",
- "langchain_core==0.3.27",
- "langchain_openai==0.2.13",
- "lxml==5.2.1",
- "ndex2>=3.8.0,<4.0.0",
- "pandas",
- "pydantic==2.10.4",
- "python-dotenv==1.0.1",
- "Requests==2.32.3"

## Glossary

These discusses terms that would be used in this documentation:

- BEL (Biological Expression Language): BEL is a structured language used to represent scientific findings, especially in the biomedical domain, in a computable format. Learn More: [BEL Documentation](https://language.bel.bio/)
- CX2 (Cytoscape Exchange Format 2): CX2 is a JSON-based format used for storing and exchanging network data in Cytoscape. Learn More: [CX2 Specification](http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html#cx2)
- PMCID (PubMed Central Identifier): A unique identifier for articles archived in PubMed Central (PMC), a free digital repository of biomedical and life sciences journal literature. Learn More: [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/)
- NDEx (Network Data Exchange): NDEx is an online resource that facilitates the sharing, storage, and visualization of biological networks. Learn More: [NDEx](https://www.ndexbio.org)
- LangChain: LangChain is a framework for developing applications powered by language models. It allows easy integration of language models with data sources and APIs, enabling workflows like knowledge extraction and retrieval. 
Learn More: [LangChain](https://python.langchain.com/docs/introduction/)
- Cytoscape: Cytoscape is an open-source platform for visualizing and analyzing complex networks, including biological pathways, protein interaction networks, and more. Learn More: [Cytoscape](https://cytoscape.org)
- Knowledge Graph: A knowledge graph is a structured representation of knowledge in a graph format, where entities are nodes and relationships are edges. It enables intuitive querying, reasoning, and visualization of complex biological data, aiding in understanding biological systems and facilitating discoveries.
- Pubtator: PubTator is a web-based tool that extracts and annotates biomedical entities and relations from scientific literature. It provides a user-friendly interface for exploring and analyzing scientific texts. Learn More: [PubTator](https://www.ncbi.nlm.nih.gov/research/pubtator/)
- OpenAI: OpenAI is an artificial intelligence research lab that develops advanced language models and other AI technologies. It provides APIs for accessing language models and other AI capabilities. In this project, we are making use of gpt-4o model. Other tests were carried out with gpt-3, gpt-4, and gpt-4o-mini.
Learn More: [OpenAI](https://www.openai.com)

## Installation

Install the package via pip:

```bash
pip install textToKnowledgeGraph
```

## Methodology

- ## Features Available

  - **BEL Generation**: Extracts biological interactions from scientific papers and generates BEL statements.
  - **CX2 Network Generation**: Converts extracted interactions into CX2 network format for visualization in Cytoscape.
  - **Uploading to NDEx**: Uploads the generated CX2 networks to NDEx for sharing and visualization.

<!-- - ## Code WorkFlow -->

- ## BEL Generation

  - The user provides a `PMC ID` and an openai API key as input. This PMC ID is used to fetch the XML version of the scientific paper from pubtator's API. The XML version of the paper is then processed and broken down into a list of dictionaries where each entry contains the index and the text of the paragraph from the XML file. Each entry also contains annotations from the pubtator XML file. This result is saved to a json file.
  - The prompt that directs the model on what to do is defined in a prompt file called `prompt_file_v5.txt` which is processed to extract the prompt that is being passed to the model for instructions on how to extract the BEL statements.
  - **Model Creation**:
    - The `bel_model.py` script defines and initializes the model used to extract BEL statements.
    - It includes schema definitions, API call handling, and model initialization.
    - The `get_interactions.py` script handles the extraction of interactions, prompt processing, and chain initialization.

- ## CX2 Network Generation

  - Converts extracted interactions into CX2 network format for visualization in Cytoscape.

- ## Uploading to NDEx

  - Uploads the generated CX2 networks to NDEx for sharing and visualization. In order to use this function, you need to provide your NDEx email and password as an argument.

## Usage

To install python package:

```bash
pip install textToKnowledgeGraph
```

**Required parameters**:

- **pmc_id**: can only process one at a time

- **api_key**: open_ai api key

**Optional parameters**:

- **ndex_email**: The NDEx email for authentication. ndex_password: The NDEx password for authentication.

**Expected output**:

- **BEL statements**: extracted from the paper
- **CX2 network**: generated from the extracted BEL statements
- **Example of CX2 network**:
![CX2 network image of paper:PMC8354587](https://github.com/ndexbio/llm-text-to-knowledge-graph/blob/main/PMC8354587_image.png?raw=true)

To run in an interactive python environment:

```python
# Process pmcid without uploading to ndex
from textToKnowledgeGraph import process_paper
 
process_paper("PMC8354587","sk-....") 

# Process pmcid and upload to ndex

from textToKnowledgeGraph import process_paper

process_paper("PMC8354587","sk-..", "john_doe@gmail.com", "xxxx", upload_to_ndex=True)
```
