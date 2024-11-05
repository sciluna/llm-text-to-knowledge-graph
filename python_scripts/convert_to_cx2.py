import pandas as pd
import json
from ndex2.cx2 import PandasDataFrameToCX2NetworkFactory
from ndex2.client import Ndex2


def convert_to_cx2(extracted_results):
    # Initialize lists to store extracted data
    source_list = []
    target_list = []
    interaction_list = []
    evidence_list = []

    # Extract data directly from the JSON structure
    for entry in extracted_results:
        # Access source, interaction, and target directly
        source = entry.get("source")
        interaction = entry.get("interaction")
        target = entry.get("target")
        text = entry.get("text")
        # Ensure all fields are present before appending
        if source and interaction and target:
            source_list.append(source)
            target_list.append(target)
            interaction_list.append(interaction)
            text = evidence_list.append(text)

    # Create a DataFrame for CX2 conversion
    df = pd.DataFrame({
        'source': source_list,
        'target': target_list,
        'interaction': interaction_list,
        'text': evidence_list
    })

    # Convert DataFrame to CX2 network format
    factory = PandasDataFrameToCX2NetworkFactory()
    cx2_network = factory.get_cx2network(df, source_field='source', target_field='target', 
                                         edge_interaction='interaction')
    return cx2_network


if __name__ == "main":
    with open('results/pmc3898398/llm_combined50_results.json', 'r') as file:
        json_data = json.load(file)
    cx2_network = convert_to_cx2(json_data)
    cx2_network.set_name('Indra_50_sentences_network')
    net_cx = cx2_network.to_cx2()

    # Create an NDEx client instance with your credentials
    client = Ndex2(username='favour.ujames196@gmail.com', password='Fujames17')
    client.save_new_cx2_network(net_cx)

    # new_network = json.dumps(cx2_network.to_cx2(), indent=2)
    # with open('cx2.cx', 'w') as file:
    #     file.write(new_network)
