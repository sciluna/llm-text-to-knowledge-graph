
import urllib
import json

# This gets information about official gene symbols.

def get_all_gene_symbols(gene_symbol):
    url = f"https://rest.genenames.org/fetch/symbol/{gene_symbol}"
    headers = {"Accept": "application/json"}
    
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode())
            # Extract relevant information from the response
            if 'response' in result and 'docs' in result['response'] and len(result['response']['docs']) > 0:
                gene_info = result['response']['docs'][0]
                prev_symbols = gene_info.get('prev_symbol', [])
                alias_symbols = gene_info.get('alias_symbol', [])
                return prev_symbols, alias_symbols  # Return both previous and alias symbols
            else:
                return None, None  # No symbols found
    except Exception as e:
        print("Error detail: ", e)
        return None, None
    
#
