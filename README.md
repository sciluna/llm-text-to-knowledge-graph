# textToKnowledgeGraph

A Python package to generate BEL statements and CX2 networks from scientific text.

## Table of Contents

- [Project Description](#project-description)
- [Dependencies](#dependencies)
- [Glossary](#glossary)
- [Installation](#installation)
- [Methodology](#methodology)
  - [Features Available](#features-available)
  - [BEL Generation](#bel-generation)
  - [CX2 Network Generation](#cx2-network-generation)
  - [Uploading to NDEx](#uploading-to-ndex)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [Interactive Python](#interactive-python)
- [Expected Output](#expected-output)
- [Notes](#notes)

## Project Description

`textToKnowledgeGraph` is a Python package that converts natural language scientific text into structured knowledge graphs using advanced language models (LLMs). It is designed to:

- Generate BEL statements from scientific text.
- Extract entities and interactions to build knowledge graphs.
- Convert interactions into CX2 network format for visualization.
- Optionally upload the generated networks to NDEx.

## Dependencies

- Python >= 3.11
- langchain==0.3.13
- langchain_core==0.3.27
- langchain_openai==0.2.13
- lxml==5.2.1
- ndex2>=3.8.0,<4.0.0
- pandas
- pydantic==2.10.4
- python-dotenv==1.0.1
- Requests==2.32.3

## Glossary

- **BEL (Biological Expression Language):** A language for representing scientific findings in a computable format. [Learn More](https://language.bel.bio/)
- **CX2 (Cytoscape Exchange Format 2):** A JSON-based format for storing and exchanging network data. [Learn More](http://manual.cytoscape.org/en/stable/Supported_Network_File_Formats.html#cx2)
- **PMCID:** A unique identifier for articles in PubMed Central. [Learn More](https://www.ncbi.nlm.nih.gov/pmc/)
- **NDEx:** An online resource for sharing, storing, and visualizing biological networks. [Learn More](https://www.ndexbio.org)
- **LangChain:** A framework to build applications powered by language models. [Learn More](https://python.langchain.com/docs/introduction/)
- **Cytoscape:** An open-source platform for network visualization and analysis. [Learn More](https://cytoscape.org)
- **Knowledge Graph:** A structured graph representation of entities and relationships.
- **Pubtator:** A tool for extracting and annotating biomedical entities from scientific literature. [Learn More](https://www.ncbi.nlm.nih.gov/research/pubtator/)
- **OpenAI:** An AI research lab providing access to advanced language models. [Learn More](https://www.openai.com)

## Installation

Install the package via pip:

```bash
pip install textToKnowledgeGraph
```

## Methodology

### Features Available

- **BEL Generation**: Extracts biological interactions from scientific papers and generates BEL statements.  
- **CX2 Network Generation**: Converts extracted interactions into CX2 network format for visualization in Cytoscape.  
- **Uploading to NDEx**: Uploads the generated CX2 networks to NDEx for sharing and visualization.

### BEL Generation

**Input**:  

- The user provides one or more PMC IDs and/or local file paths (PDF or TXT) along with an OpenAI API key.  
- If a PMC ID is provided, the tool fetches the XML version of the scientific paper from PubTator’s API.  
- If a PDF/TXT path is provided, the tool extracts the text using MarkItDown.

**Processing**:  

- The text is broken down into paragraphs and annotated.  
- The prompt for the model is defined in a prompt file, which directs the LLM on how to extract BEL statements.

**Output**:  

- The extracted BEL statements are saved in JSON files.  
- The results are converted into a CX2 network format for visualization in Cytoscape.

### CX2 Network Generation

Converts extracted interactions into CX2 network format for visualization in Cytoscape.

### Uploading to NDEx

Uploads the generated CX2 networks to NDEx for sharing and visualization.  
In order to use this function, you need to provide your NDEx email and password as an argument.

### Usage

The package supports processing multiple documents in one run and requires an OpenAI API key.

**Parameters**:

- **api_key (required)**: Your OpenAI API key used for LLM calls.
- **pmc_ids (optional, list)**: A list of PMC IDs to process.
- **pdf_paths (optional, list)**: A list of PDF file paths to process.
- **txt_paths (optional, list)**: A list of TXT file paths to process.
- **ndex_email (optional)**: NDEx account email for authentication.
- **ndex_password (optional)**: NDEx account password for authentication.
- **upload_to_ndex (flag)**: If set, uploads the generated networks to NDEx.
- **style_path (optional)**: Path to a Cytoscape style JSON file; defaults to the file in the `data` directory.

### Command Line

```bash
python -m textToKnowledgeGraph.main \
  --api_key YOUR_OPENAI_API_KEY \
  --pmc_ids PMC123456 PMC234567 \
  --pdf_paths /path/to/paper1.pdf /path/to/paper2.pdf \
  --txt_paths /path/to/document1.txt \
  --ndex_email <your_email@example.com> \
  --ndex_password your_password \
  --upload_to_ndex
```

### Interactive Python

```python
from textToKnowledgeGraph import main

main(
    api_key="YOUR_OPENAI_API_KEY",
    pmc_ids=["PMC123456", "PMC234567"],
    pdf_paths=["/path/to/paper1.pdf", "/path/to/paper2.pdf"],
    txt_paths=["/path/to/document1.txt"],
    ndex_email="<your_email@example.com>",  # optional
    ndex_password="your_password",        # optional
    style_path=None,                      # uses default style file if None
    upload_to_ndex=False
)
```

## Expected Output

- **BEL Statements**: Extracted from the processed documents.
- **CX2 Networks**: Generated for each input and saved in a dedicated `results/` directory named after each document or PMC ID.
- **NDEx Upload**: If enabled, the networks will be uploaded to NDEx.
- **Example of CX2 network**:
![CX2 network image of paper:PMC8354587](https://github.com/ndexbio/llm-text-to-knowledge-graph/blob/main/PMC8354587_image.png?raw=true)

## Notes

- The default style file is located at `<repo_root>/data/cx_style.json`. You can override this with the `--style_path` parameter.
- Make sure your input files exist and that your API key is valid.
- The package logs detailed processing steps and total runtime for batch processing.