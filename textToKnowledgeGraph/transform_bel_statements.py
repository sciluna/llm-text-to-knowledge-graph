import re


def parse_bel_statement(bel_statement):
    pattern = r'([a-zA-Z]+\([^\)]+\))\s+(\w+)\s+([a-zA-Z]+\([^\)]+\))'
    match = re.match(pattern, bel_statement)
    if match:
        source = match.group(1)
        interaction = match.group(2)
        target = match.group(3)
        return source, interaction, target
    return None, None, None


def process_llm_results(llm_data):
    extracted_results = []
    for entry in llm_data["LLM_extractions"]:
        text = entry["text"]
        for result in entry["Results"]:
            bel_statement = result["bel_statement"]
            evidence = result["evidence"]
            source, interaction, target = parse_bel_statement(bel_statement)
            if source and interaction and target:
                extracted_results.append({
                    "source": source,
                    "interaction": interaction,
                    "target": target,
                    "text": text,
                    "evidence": evidence
                })
    # Debugging: Print extracted results
    return extracted_results
