import re
import json


def extract_bel_data(file_content):
    sentences = {}
    bel_interactions = {}
    current_evidence = ""
    current_bel_interactions = []
    sentence_index = 1
    in_evidence = False

    # Updated regex to handle more citation formats
    citation_pattern = r'\[\d+(?:[-,\u2013]\d+)*\]'

    lines = file_content.splitlines()

    for line in lines:
        line = line.strip()
        # Handle the Evidence sections (Sentences)
        evidence_match = re.match(r'SET Evidence = "(.*)', line)
        if evidence_match:
            # Store the previous evidence and interactions, if present
            if current_evidence and current_bel_interactions:
                # Remove citation numbers from the sentence
                current_evidence = re.sub(citation_pattern, '', current_evidence).strip()
                sentences[sentence_index] = current_evidence
                bel_interactions[sentence_index] = {
                    "sentence": current_evidence,
                    "bel_statements": current_bel_interactions
                }
                sentence_index += 1

            # Start a new evidence section
            current_evidence = evidence_match.group(1)
            current_bel_interactions = []
            in_evidence = True  # We are in a multiline evidence section now

        elif in_evidence and line.endswith('"'):
            # End of the multiline Evidence section
            current_evidence += " " + line.rstrip('"')  # Append and close the evidence
            in_evidence = False

        elif in_evidence:
            # Continuation of a multiline Evidence section
            current_evidence += " " + line.strip()

        # Handle BEL statements (excluding those that start with "SET")
        elif not in_evidence and re.match(r'^[a-zA-Z]', line) and not line.startswith("SET"):
            current_bel_interactions.append(line)

    # Handle the last section if there's remaining evidence and interactions
    if current_evidence and current_bel_interactions:
        # Remove citation numbers from the sentence
        current_evidence = re.sub(citation_pattern, '', current_evidence).strip()
        sentences[sentence_index] = current_evidence
        bel_interactions[sentence_index] = {
            "sentence": current_evidence,
            "bel_statements": current_bel_interactions
        }

    return sentences, bel_interactions


def save_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def process_bel_file(file_path):
    with open(file_path, 'r') as bel_file:
        file_content = bel_file.read()

    # Extract sentences and BEL interactions
    sentences, bel_data = extract_bel_data(file_content)

    # Check if the sentences were extracted correctly
    if not sentences:
        print("No sentences were extracted!")
        return
    else:
        print(f"Extracted {len(sentences)} sentences.")

    # Modify the structure to include the 'text' key for sentences
    modified_sentences = {key: {"text": sentence} for key, sentence in sentences.items()}

    # Check if modified sentences were created correctly
    if not modified_sentences:
        print("No modified sentences were created!")
        return
    else:
        print(f"Modified sentences created successfully with {len(modified_sentences)} entries.")

    # To remove the escaped quotes and process the BEL statements
    cleaned_bel_data = {}

    for index, entry in bel_data.items():
        sentence = entry['sentence']
        bel_statements = entry['bel_statements']
        # Clean the BEL statements (remove slashes from escaped quotes)
        cleaned_bel_statements = []
        for statement in bel_statements:
            cleaned_statement = statement.replace('\\"', '"')  # Remove slashes from escaped quotes
            cleaned_bel_statements.append(cleaned_statement)
        # Add cleaned data to the dictionary
        cleaned_bel_data[index] = {
            "text": sentence,
            "bel_statements": cleaned_bel_statements
        }

    # Check if cleaned BEL data was processed correctly
    if not cleaned_bel_data:
        print("No BEL data was cleaned!")
        return
    else:
        print(f"Cleaned BEL data processed successfully with {len(cleaned_bel_data)} entries.")
    return modified_sentences, cleaned_bel_data
