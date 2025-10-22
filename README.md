# textToKnowledgeGraph

A Python package to generate Biological Expression Language (BEL) statements and Cytoscape CX2 networks from scientific text.

textToKnowledgeGraph is also available as a service-based App for Cytoscape Web! [How-To for Cytoscape Web](cytoscape_web_how_to.md) 

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
  - [Network Naming and Metadata](#network-naming-and-metadata)
  - [Command Line Examples](#command-line-examples)
  - [Interactive Python Examples](#interactive-python-examples)
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
- langchain
- langchain_core
- langchain_openai
- lxml==5.2.1
- ndex2>=3.8.0,<4.0.0
- pandas
- pydantic
- python-dotenv
- Requests
- nltk
- gilda
- markitdown[all]
- openai

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
- **Style Customization**: Allows users to specify a custom Cytoscape style JSON file for network visualization. 
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

### Style Customization

The python package uses a default Cytoscape style JSON file located at `<repo_root>/data/cx_style.json`. You can reuse any visual style you’ve created in Cytoscape or any style you would like to implement in your graphs. Export the network that contains this desired style as a CX/CX2 network and point our tool at that exported JSON. Here is how to do it:

- Export your styled network from Cytoscape

1. In Cytoscape Desktop, load the network whose style you want to copy.
2. Go to **File → Export → Network → CX** (or **CX2**) and save the file to your local drive, e.g. `my_network.cx2`.

- Extract the style JSON

1. Open the `.cx` or `.cx2` file in any IDE or text editor of your choice.
2. Locate these two top‐level entries (`"visualProperties"` and/or `"visualEditorProperties"`):

   ```json
   {
     // … other CX2 aspects …
     "visualEditorProperties": [
       /* … your style’s editor definitions … */
     ],
     "visualProperties": [
       /* … your style’s property mappings … */
     ]
   }
   ```

3. Copy those arrays into a new json file called, for example, `custom-style.json`:

   ```json
   {
     "visualEditorProperties": [ 
       /* … paste here … */ 
     ],
     "visualProperties": [ 
       /* … paste here … */ 
     ]
   }
   ```

4. Save `custom-style.json` somewhere in your project workspace.

- Run textToKnowledgeGraph with your style

Use the `--style_path` flag to tell the tool where to load your exported style

The generated CX2 will now carry your custom Cytoscape style, ready to load into Cytoscape Desktop or NDEx with the same look & feel.

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
- **custom_name (optional)**: Custom name for the network; defaults to the timestamp.
- **pmid_for_file (optional)**: In this case, the tool fetches metadata for the provided PMID/PMCID and this is used to set the network name.

### Network Naming and Metadata

When processing a file, there are three options for naming the generated network:

1. Automatic Naming (Default): If you provide no custom name or PMID/PMCID, the network name defaults to a timestamp (e.g., 20250304_1537).

2. Custom Network Name: Provide a custom network name using the --custom_name parameter. The network will use that exact name.

3. Metadata-Based Naming: If you supply a PMID or PMCID via the --pmid_for_file parameter, the package will:

- Fetch metadata (title, abstract, and authors) from E-Utilities.
- Set the network name to the format:
- FirstAuthorLastName et al.: PMID_Number
  For example, if the first author is "Wen‐Cheng Lu" and the PMID is 35080342, the network name will be:
  Lu et al.: 35080342
- Set additional network attributes:
  - description: Combining the paper's title and abstract.
  - reference: Displayed as PMID: 35080342 (with "PMID: " prefixed).
**Note**: When processing a PMC article (using a PMC ID input), the package automatically fetches metadata from E-Utilities. In this case, you do not need to provide the --pmid_for_file parameter because the metadata-based naming is handled internally.

### Command Line Examples

```bash
**Example A: Processing a PMC Article (PMCID_Input)**
python -m textToKnowledgeGraph.main \
  --api_key YOUR_OPENAI_API_KEY \
  --pmc_ids PMC123456 PMC234567 \
  --pdf_paths /path/to/paper1.pdf /path/to/paper2.pdf \
  --txt_paths /path/to/document1.txt \
  --ndex_email <your_email@example.com> \
  --ndex_password your_password \
  --upload_to_ndex
```

```bash
**Example B: Processing Local Files (PDF/TXT_Input)**
python -m textToKnowledgeGraph.main \
  --api_key YOUR_OPENAI_API_KEY \
  --pmc_ids PMC123456 PMC234567 \
  --pdf_paths /path/to/paper1.pdf /path/to/paper2.pdf \
  --txt_paths /path/to/document1.txt \
  --ndex_email <your_email@example.com> \
  --ndex_password your_password \
  --upload_to_ndex \
  --custom_name My_Network \
  --pmid_for_file 35080342
```

### Interactive Python Examples

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
    upload_to_ndex=False,
    custom_name="My_Network",            # optional
    pmid_for_file=35080342,              # optional
)
```

## Expected Output

- **BEL Statements**: Extracted from the processed documents.
- **CX2 Networks**: Generated for each input and saved in a dedicated `results/` directory named after each document or PMC ID.
- **NDEx Upload**: If enabled, the networks will be uploaded to NDEx.
- **Example of CX2 network**:
![CX2 network image of paper:PMC8354587](https://github.com/ndexbio/llm-text-to-knowledge-graph/blob/main/PMC8354587_image.png?raw=true)

## Notes

- Make sure your input files exist and that your API key is valid.
- The package logs detailed processing steps and total runtime for batch processing.
- You may need to run this `python -m nltk.downloader stopwords` to download the NLTK stopwords corpus if you encounter issues with text processing.

## How to change the style of the knowledge graphs
- To change them one at a time, just edit the style in Cytoscape Web or Cytoscape Desktop
- The default style file is located at `<repo_root>/data/cx_style.json`. You can copy and edit this to make your own style file. Then override the default using the `--style_path` parameter.
- An alternative way to do it is to use a network as a style template.
  - You take one knowledge graph, edit its style, and save it to your filesystem.
  - You then add a step to your output pipeline, as shown in the following code example.
  - You extract the visual properties from the style template and insert them into the knowledge graph. (This works because both graphs have the same node and edge properties.)
  - Note that this method uses the CX2 file format.

```python
factory = RawCX2NetworkFactory()
path_to_style_network = os.path.join(os.path.dirname(cellmaps_vnn.__file__), 'my_style_template.cx2')
style_network = factory.get_cx2network(path_to_style_network)
vis_prop = style_network.get_visual_properties()
my_network.set_visual_properties(vis_prop)
my_network.write_as_raw_cx2(my_network_restyled_path)
```
