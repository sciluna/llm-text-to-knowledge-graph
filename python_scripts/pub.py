from lxml import etree


def get_pubtator_sentences(file_path):
    """
    Extracts passages and their annotations from a PubTator XML file,
    numbering each passage and stopping when 'REF' section is reached.

    - Only includes annotations that have an 'NCBI Homologene' or 'identifier' starting with 'MESH:'.
    - For each annotation, extracts 'entity_text', 'type', and the identifier (either MESH or NCBI Homologene ID).
    - Only includes passages that have at least 2 such annotations.
    - Removes duplicate annotations within a passage.

    :param file_path: Path to the PubTator XML file.
    :return: A dictionary with numbered passages as keys and values containing text and annotations.
    """
    tree = etree.parse(file_path)
    root = tree.getroot()

    passages_dict = {}
    passage_elements = root.findall('.//passage')
    passage_number = 0

    for passage in passage_elements:
        # Get the section_type
        section_type = passage.findtext('infon[@key="section_type"]')
        if section_type == 'REF':
            # Stop extracting when 'REF' section is reached
            break

        # Extract the passage text
        text_elem = passage.find('text')
        passage_text = text_elem.text.strip() if text_elem is not None else ""

        # Extract annotations within the passage
        annotations = []
        annotation_elements = passage.findall('annotation')
        seen_annotations = set()
        for annotation in annotation_elements:
            # Build a dictionary of infon elements
            infon_elements = annotation.findall('infon')
            infon_dict = {infon.get('key'): infon.text.strip() for infon in infon_elements if infon.text}

            # Initialize variables
            identifier = ""
            identifier_type = ""

            # Check if the annotation meets the criteria
            if 'NCBI Homologene' in infon_dict:
                identifier = infon_dict['NCBI Homologene']
                identifier_type = 'NCBI Homologene'
            elif 'identifier' in infon_dict and infon_dict['identifier'].startswith('MESH:'):
                identifier = infon_dict['identifier']
                identifier_type = 'MESH'

            if identifier:
                # Get the annotation text
                ann_text_elem = annotation.find('text')
                ann_text = ann_text_elem.text.strip() if ann_text_elem is not None else ""

                # Get the annotation type
                ann_type = infon_dict.get('type', '')

                # Create a tuple to check for duplicates
                ann_tuple = (ann_text, ann_type, identifier)

                if ann_tuple not in seen_annotations:
                    seen_annotations.add(ann_tuple)
                    annotations.append({
                        'entity_text': ann_text,
                        'type': ann_type,
                        'identifier_type': identifier_type,
                        'identifier': identifier
                    })

        # Only include passages with at least 2 annotations
        if len(annotations) >= 2:
            # Add to the passages dictionary with numbering
            passages_dict[str(passage_number)] = {
                'text': passage_text,
                'annotations': annotations
            }

            passage_number += 1

    return passages_dict


def extract_annotations_from_pubtator_xml(file_path):
    """
    Extracts annotations from a PubTator XML file.
    :param file_path: Path to the PubTator XML file.
    :return: A list of annotations.
    """
    tree = etree.parse(file_path)
    root = tree.getroot() 
    annotations = []
    for annotation in root.findall('.//annotation'):
        ann = {
            'id': annotation.get('id'),
            'type': annotation.findtext('infon[@key="type"]'),
            'identifier': annotation.findtext('infon[@key="identifier"]'),
            'offset': int(annotation.find('location').get('offset')),
            'length': int(annotation.find('location').get('length')),
            'text': annotation.findtext('text')
        }
        annotations.append(ann)
    return annotations
