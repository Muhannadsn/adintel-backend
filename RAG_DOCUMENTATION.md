
# Project Documentation: RAG Memory System

This document outlines the implementation of the Retrieval-Augmented Generation (RAG) memory system.

## Overview

The RAG memory system provides a long-term, self-improving knowledge base for the ad analysis pipeline. It stores and retrieves information about brands, products, and other entities, allowing the system to become faster and more accurate over time by reducing reliance on external validation.

## Files Created

1.  **`api/rag_memory.py`**: This module contains the `RAGMemory` class, which acts as a client for the ChromaDB vector store. It handles embedding generation via Ollama, and provides methods to `add_document` and `search` for information.

2.  **`update_rag_index.py`**: This is a standalone script used to populate and update the RAG index. It reads from a (currently simulated) `PENDING_KNOWLEDGE_QUEUE`, transforms the data into a suitable format, and uses the `RAGMemory` client to add it to the vector store.

## How to Interact and Integrate

**1. Updating the Knowledge Base:**

To add new information to the memory, new knowledge items should be added to the `PENDING_KNOWLEDGE_QUEUE` in `update_rag_index.py`. Then, run the script from the terminal:

```bash
python update_rag_index.py
```

**2. Using the RAG System in Agents:**

To use the RAG system within an agent (e.g., for validation), import and instantiate the `RAGMemory` class. The `search()` method can then be used to query the knowledge base.

**Example:**

```python
from api.rag_memory import RAGMemory

# Instantiate the client
memory = RAGMemory()

# Perform a search
results = memory.search("What is Nutribullet?", n_results=1)

if results:
    print(f"Found in memory: {results[0]['document']}")
else:
    print("Entity not found in memory.")

```
