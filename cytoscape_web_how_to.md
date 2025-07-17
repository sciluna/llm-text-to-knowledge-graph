# How-To: textToKnowledgeGraph Cytoscape Web App

## Overview

## Cytoscape Web

## Service Apps

## Installing the textToKnowledgeGraph App

The URL for the textToKnowledgeGraph service is:  https://cd.ndexbio.org/cy/cytocontainer/v1/llm_text_to_knowledge_graph

On the menubar, choose Apps -> Manage Apps and paste the URL into the "Enter a new external service URL" input box.

The service will respond and register itself in your environment.

## Using the App

### Using OpenAI API Key

- Cytoscape Web transmits your API Key to the backend textToKnowledgeGraph service with each request: our server does not store the key.
- In your browser, the key stays in the Cytoscape Web's local storage. It will be cleared if you...

**Is my key secure?**

### Running it with a PubMed Central ID

This may take a while! Cytoscape Web waits for the service to respond with the knowledge graph. Expect to wait a few minutes.
