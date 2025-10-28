# RAG System Integration Plan

This document outlines the plan to fully integrate the RAG (Retrieval-Augmented Generation) memory system into the ad analysis pipeline.

### **Objective**

To increase the efficiency and accuracy of the analysis pipeline by creating a self-improving feedback loop. The system will first consult an internal knowledge base (RAG memory) before performing expensive external validation (web searches), and will automatically capture new knowledge.

---

## **Phase 1: RAG System Implementation (Completed)**

*   **Status:** 100% Complete.
*   **Summary:** The core components of the RAG system have been created and successfully tested in isolation.
    *   `api/rag_memory.py`: A client for interacting with the ChromaDB vector store.
    *   `update_rag_index.py`: A script for populating the RAG index from a data source.

---

## **Phase 2: Core Integration (The "Read Path")**

*   **Objective:** Modify the `WebSearchValidator` to query the RAG memory before performing a live web search.
*   **File to Modify:** `api/web_search.py`
*   **Steps:**
    1.  **Inject `RAGMemory` Client:** The `WebSearchValidator` class will be updated to accept an instance of the `RAGMemory` client in its `__init__` method.
    2.  **Query RAG First:** The `validate_product` method will be modified. Its first action will be to call `rag_memory.search()` with the product name.
    3.  **Conditional Logic:** If the search returns a high-confidence result from the RAG memory, that result will be formatted and returned immediately. The subsequent DuckDuckGo web search and LLM validation steps will be skipped entirely.

---

## **Phase 3: Knowledge Capture (The "Write Path")**

*   **Objective:** Capture newly validated knowledge from the pipeline to be fed back into the RAG system.
*   **File to Modify:** `run_analysis.py` (The main pipeline orchestrator).
*   **Steps:**
    1.  **Identify New Knowledge:** After the main analysis loop completes, iterate through the results.
    2.  **Filter for Cacheable Items:** Identify all analyses where the `WebSearchValidator` was used and returned a result with the flag `"cache_this": true`.
    3.  **Write to Pending Queue:** Create a new function to append these validated JSON objects to a simple, append-only log file named `pending_knowledge.jsonl`. This file will serve as the queue for the indexing script.

---

## **Phase 4: Closing the Feedback Loop**

*   **Objective:** Automate the process of updating the RAG index with the newly captured knowledge.
*   **File to Modify:** `update_rag_index.py`
*   **Steps:**
    1.  **Read from Queue:** Modify the script to read and parse the `pending_knowledge.jsonl` file instead of the current hardcoded list.
    2.  **Process and Index:** Use the existing logic to transform and index each item from the queue.
    3.  **Archive Processed Items:** After successful indexing, the script should clear or archive the `pending_knowledge.jsonl` file to prevent re-indexing.

---

## **Confidence Levels & Weak Areas**

*   ### **Overall Confidence: High**
    *   The plan is based on a detailed audit of the existing code. The integration points are clearly identified, and the proposed changes are modular.

*   ### **Weak Area 1: Modifying `run_analysis.py`**
    *   **Concern:** This is the most complex step. `run_analysis.py` orchestrates the main pipeline, and inserting the "write-to-queue" logic requires careful implementation to avoid disrupting the existing workflow. There is a moderate risk of introducing a bug if the data handling is not precise.
    *   **Mitigation:** The new logic will be encapsulated in its own function and placed at the very end of the script's execution to minimize impact.

*   ### **Weak Area 2: Concurrency in Knowledge Queue**
    *   **Concern:** Using a simple `jsonl` file as a queue is not robust for concurrent operations. If multiple instances of the analysis pipeline were to run simultaneously, they could corrupt the `pending_knowledge.jsonl` file.
    *   **Mitigation:** For the project's current state (single-process execution), this is acceptable. The plan acknowledges this is a simplification, and a more robust solution (like a SQLite database or a message queue) would be a necessary upgrade for future multi-process scaling.

*   ### **Weak Area 3: Dependency Conflict**
    *   **Concern:** The installation of `chromadb` introduced a `urllib3` version conflict with the `selenium` package. While this did not cause an installation failure, it poses a low-risk threat of causing unexpected runtime errors in the Selenium-based scrapers.
    *   **Mitigation:** This should be monitored. If scraper-related issues arise, a dependency resolution (e.g., pinning `urllib3` to a compatible version for both packages) will be required.
