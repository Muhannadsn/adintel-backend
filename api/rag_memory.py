#!/usr/bin/env python3
"""
RAG Memory Module
Handles interaction with a ChromaDB vector store and Ollama embeddings.
"""

import requests
import chromadb
from typing import List, Dict, Any

class RAGMemory:
    """A client to manage and query a RAG vector store."""

    def __init__(
        self,
        collection_name: str = "product_knowledge",
        db_path: str = "./rag_db",
        ollama_host: str = "http://localhost:11434",
        embedding_model: str = "mxbai-embed-large"
    ):
        """
        Initialize the RAG memory client.

        Args:
            collection_name: The name of the collection in ChromaDB.
            db_path: The file path to store the ChromaDB database.
            ollama_host: The URL for the Ollama API.
            embedding_model: The name of the embedding model to use in Ollama.
        """
        print(f"🧠 Initializing RAG memory...")
        self.db_path = db_path
        self.collection_name = collection_name
        self.ollama_host = ollama_host
        self.embedding_model = embedding_model
        self.api_url = f"{ollama_host}/api/embeddings"

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        print(f"✅ RAG memory initialized. Collection '{self.collection_name}' has {self.collection.count()} items.")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a given text using Ollama."""
        try:
            response = requests.post(
                self.api_url,
                json={"model": self.embedding_model, "prompt": text},
                timeout=90
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except requests.RequestException as e:
            print(f"❌ Error getting embedding from Ollama: {e}")
            return []

    def add_document(self, product_name: str, document_text: str, metadata: Dict[str, Any]):
        """
        Add or update a document in the vector store.

        Args:
            product_name: The unique identifier for the document (e.g., "NutriBullet").
            document_text: The rich text to be embedded.
            metadata: A dictionary of structured data to store alongside the vector.
        """
        embedding = self._get_embedding(document_text)
        if not embedding:
            print(f"⚠️  Could not generate embedding for '{product_name}'. Skipping.")
            return

        # Using upsert to add new or update existing documents
        self.collection.upsert(
            ids=[product_name],
            embeddings=[embedding],
            documents=[document_text],
            metadatas=[metadata]
        )

    def search(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Perform a semantic search in the vector store.

        Args:
            query_text: The text to search for.
            n_results: The number of results to return.

        Returns:
            A list of search results.
        """
        query_embedding = self._get_embedding(query_text)
        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results for easier use
        formatted_results = []
        if results and results.get('ids'):
            for i, result_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "id": result_id,
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })
        return formatted_results
