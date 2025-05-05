
def parse_bel_statement(bel_statement):
    bel_statement = bel_statement.strip()

    def extract_expression(s, start):
        # Skip leading whitespace
        while start < len(s) and s[start].isspace():
            start += 1
        # Read the function name (letters only)
        func_start = start
        while start < len(s) and s[start].isalpha():
            start += 1
        func_name = s[func_start:start]
        # The next character must be an opening parenthesis
        if start >= len(s) or s[start] != '(':
            return None, start
        # Now extract the entire expression, including nested parentheses
        stack = []
        expr_start = start  # position of first '('
        while start < len(s):
            if s[start] == '(':
                stack.append('(')
            elif s[start] == ')':
                if not stack:
                    # Unbalanced; return None
                    return None, start
                stack.pop()
                if not stack:
                    start += 1  # include the closing parenthesis
                    break
            start += 1
        # Return the complete expression (function name + arguments)
        expr = func_name + s[expr_start:start]
        return expr, start

    # Extract left (source) expression
    left_expr, idx = extract_expression(bel_statement, 0)
    if left_expr is None:
        return None, None, None

    # Skip whitespace to get the relation word
    while idx < len(bel_statement) and bel_statement[idx].isspace():
        idx += 1
    rel_start = idx
    while idx < len(bel_statement) and not bel_statement[idx].isspace():
        idx += 1
    relation = bel_statement[rel_start:idx]

    # Skip whitespace and extract right (target) expression
    while idx < len(bel_statement) and bel_statement[idx].isspace():
        idx += 1
    right_expr, idx = extract_expression(bel_statement, idx)
    if right_expr is None:
        return None, None, None

    return left_expr, relation, right_expr


def process_llm_results(llm_data):
    extracted_results = []
    for entry in llm_data.get("LLM_extractions", []):
        text = entry.get("text", "")
        for result in entry.get("Results", []):
            bel_stmt = result.get("bel_statement", "")
            evidence = result.get("evidence", "")
            source, interaction, target = parse_bel_statement(bel_stmt)
            if not source or not interaction or not target:
                # If parsing fails, skip or handle differently
                continue

            extracted_results.append({
                "source": source,
                "interaction": interaction,
                "target": target,
                "text": text,
                "evidence": evidence
            })

        # for annots in entry["annotations"]:
        #     entry_name = annots["entry_name"]
        #     url = annots["url"]
        #     extracted_results.append({
        #         "entry_name": entry_name,
        #         "url": url
        #     })  

    return extracted_results
