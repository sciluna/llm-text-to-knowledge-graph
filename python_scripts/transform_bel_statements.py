import json
import re
from convert_to_cx2 import convert_to_cx2


def parse_bel_statement(bel_statement):
    pattern = r'([a-zA-Z]+\([^\)]+\))\s+(\w+)\s+([a-zA-Z]+\([^\)]+\))'
    match = re.match(pattern, bel_statement)
    if match:
        source = match.group(1)
        interaction = match.group(2)
        target = match.group(3)
        return source, interaction, target
    return None, None, None


def process_llm_results(llm_json_path):
    with open(llm_json_path, 'r') as f:
        llm_data = json.load(f)

    extracted_results = []
    for entry in llm_data["LLM_extractions"]:
        for result in entry["Results"]:
            bel_statement = result["bel_statement"]
            source, interaction, target = parse_bel_statement(bel_statement)
            if source and interaction and target:
                extracted_results.append({
                    "source": source,
                    "interaction": interaction,
                    "target": target
                })
    # Debugging: Print extracted results
    print("Extracted Results:")
    return extracted_results


llm_json_path = 'results/pmid12928037/llm_results.json'
extracted_results = process_llm_results(llm_json_path)

cx2_network = convert_to_cx2(extracted_results)

# Save CX2 network to file
with open('llm_network.cx2', 'w') as f:
    json.dump(cx2_network.to_cx2(), f, indent=2)
print("CX2 network saved to 'llm_network.cx2'.")
