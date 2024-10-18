import pytest
import sys
from os.path import abspath, dirname

# Add the python_scripts directory to the sys.path
sys.path.insert(0, abspath(dirname(__file__) + '/../python_scripts'))

from hgnc_grounding import ground_gene_symbol

@pytest.mark.parametrize("input_symbol, expected_output", [
    ("TP53", ("TP53", True)),
    ("p53", ("TP53", False)),
    ("BRCA1", ("BRCA1", True)),
    ("NonExistentGene", (False, False)),
])
def test_ground_gene_symbol(input_symbol, expected_output):
    result = ground_gene_symbol(input_symbol)
    assert result == expected_output

if __name__ == "__main__":
    pytest.main([__file__])
