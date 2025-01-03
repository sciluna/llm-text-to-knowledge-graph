from unittest.mock import patch
from textToKnowledgeGraph.main import process_paper


@patch("textToKnowledgeGraph.main.download_pubtator_xml")
@patch("textToKnowledgeGraph.main.Ndex2.save_new_cx2_network")
def test_process_paper(mock_save_network, mock_download):
    """
    Test the `process_paper` function with mocked dependencies.
    """
    # Mock the download_pubtator_xml function to return a dummy file path
    mock_download.return_value = "/path/to/dummy_file.xml"

    # Mock the save_new_cx2_network function to return True
    mock_save_network.return_value = True

    # Test data
    pmc_id = "PMC0000000"
    ndex_email = "dummy_email"
    ndex_password = "dummy_password"

    # Call the function
    result = process_paper(pmc_id, ndex_email, ndex_password)

    # Assertions
    assert result is not None, "Expected a non-None result"
    assert mock_save_network.called, "save_new_cx2_network should have been called"
    assert mock_download.called, "download_pubtator_xml should have been called"
