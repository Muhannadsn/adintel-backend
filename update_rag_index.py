#!/usr/bin/env python3
"""
RAG Index Updater
Reads newly discovered knowledge and adds it to the RAG vector store.
"""

import json
from api.rag_memory import RAGMemory
from typing import Dict, Any

# --- SIMULATED PENDING KNOWLEDGE QUEUE ---
# In a real system, this data would come from a log file or a database table
# populated by your main analysis pipeline.
PENDING_KNOWLEDGE_QUEUE = [
    {
      "product_name": "Nutribullet",
      "product_type": "physical_product",
      "category": "Kitchen Appliances",
      "confidence": 0.95,
      "metadata": {
          "reasoning": "Validated via web search. It's a popular brand of personal blenders.",
          "search_source": "duckduckgo"
      }
    },
    {
      "product_name": "Smash Me",
      "product_type": "restaurant",
      "category": "Burgers & Fast Food",
      "confidence": 0.98,
      "metadata": {
          "reasoning": "Known local burger joint in Doha.",
          "search_source": "internal_catalog"
      }
    },
    {
      "product_name": "Talabat Pro",
      "product_type": "subscription",
      "category": "Platform Subscription Service",
      "confidence": 0.99,
      "metadata": {
          "reasoning": "Official subscription service for the Talabat platform.",
          "search_source": "internal_rules"
      }
    }
]

def transform_to_document(item: Dict[str, Any]) -> tuple[str, Dict]:
    """
    Transforms a structured knowledge item into a text document and metadata.

    Returns:
        A tuple of (document_text, metadata).
    """
    product_name = item.get("product_name", "Unknown")
    product_type = item.get("product_type", "unknown")
    category = item.get("category", "Uncategorized")
    reasoning = item.get("metadata", {}).get("reasoning", "")

    # Create a rich text document for better semantic embedding
    document_text = (
        f"{product_name} is a {product_type} classified under the {category} category. "
        f"{reasoning}"
    )

    # Metadata to be stored directly with the vector
    metadata = {
        "product_type": product_type,
        "category": category,
        "confidence": item.get("confidence", 0.0),
        "source": item.get("metadata", {}).get("search_source", "unknown")
    }
    return document_text, metadata


def main():
    """Main function to run the indexing process."""
    print("🚀 Starting RAG index update process...")
    rag_memory = RAGMemory()

    for item in PENDING_KNOWLEDGE_QUEUE:
        product_name = item.get("product_name")
        if not product_name:
            continue

        print(f"   - Indexing '{product_name}'...")
        document_text, metadata = transform_to_document(item)
        rag_memory.add_document(product_name, document_text, metadata)

    print("✅ RAG index update process complete.")
    return rag_memory


if __name__ == "__main__":
    # Run the main indexing process
    memory = main()

    # --- VERIFICATION STEP ---
    # Now, let's test if the indexing worked by performing a search.
    print("\n\n🧪 Verifying index with a test search...")
    search_query = "What is a good blender brand?"
    print(f"   Searching for: '{search_query}'")

    results = memory.search(search_query, n_results=1)

    if results:
        print("\n✅ Test search successful! Found results:")
        print(json.dumps(results, indent=2))
    else:
        print("\n❌ Test search failed. No results found.")
