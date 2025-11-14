# Feature Specification: RAG-Prioritized Conversational Agent

## 1. Overview

This feature introduces a new conversational agent that prioritizes answering user queries from a custom knowledge base (RAG - Retrieval Augmented Generation) before resorting to general internet search. This allows the application to provide context-specific answers based on proprietary or curated information.

## 2. User Stories

*   As a user, I want the conversational agent to first search for information in a custom knowledge base, so that I can get answers based on my own documents before it searches the public internet.
*   As a user, I want to be able to upload new documents (e.g., PDFs) to update the custom knowledge base, so that the agent's knowledge remains current and relevant.

## 3. Functional Requirements

### 3.1. RAG Agent Creation and Workflow

*   A new `google.adk.agents.Agent`, named `rag_agent`, will be created.
*   The `rag_agent` will replace the existing `google_search_agent` as the primary "live" agent in `app/main.py`.
*   The `rag_agent` will have access to two tools:
    *   `query_docs`: A new `google.adk.tools.FunctionTool` that queries the custom knowledge base.
    *   `google_search`: The existing `google.adk.tools.google_search` tool for general internet search.
*   The `rag_agent`'s instructions will prioritize `query_docs`:
    1.  First, always attempt to use the `query_docs` tool to answer the user's question.
    2.  If the `query_docs` tool does not provide a relevant answer, then use the `google_search` tool.

### 3.2. Custom Knowledge Base Management

*   The custom knowledge base will be built using `llama-index` and `GeminiEmbedding` (as demonstrated in the user's RAG example).
*   The initial custom knowledge base will be based on an FAQ document about "FSM Armenian company" (e.g., `fsm-faq.md`).
*   A new FastAPI endpoint will be added to `app/main.py` to handle PDF uploads.
*   When a PDF is uploaded to this endpoint:
    *   The PDF will be saved to a designated directory (e.g., `./downloads`).
    *   The `llama-index` will be rebuilt to incorporate the new document.

### 3.3. Frontend Updates

*   The `adk-streaming-ws` frontend (`app/static/index.html` and `app/static/js/app.js`) will be updated.
*   A user interface element for uploading PDF files will be added to `app/static/index.html`.
*   `app/static/js/app.js` will be modified to:
    *   Capture uploaded PDF files.
    *   Base64 encode the PDF content.
    *   Send the Base64 encoded PDF data to the new FastAPI upload endpoint.

## 4. Non-Functional Requirements

*   **Performance:** The RAG agent should respond to queries within acceptable conversational latency.
*   **Scalability:** The `llama-index` solution should be able to handle a growing number of documents in the custom knowledge base.
*   **Reliability:** The PDF upload and index rebuilding process should be robust and handle potential errors gracefully.

## 5. Technical Details

*   **Backend:**
    *   Python 3.x
    *   `FastAPI`
    *   `google-adk`
    *   `llama-index`
    *   `llama-index-llms-gemini`
    *   `llama-index-embeddings-gemini`
    *   `google-genai`
*   **Frontend:**
    *   HTML, CSS, JavaScript
    *   Web Audio API
    *   `Chart.js` (existing)

## 6. Out of Scope

*   Changes to the `detail_analysis_agent`'s core functionality.
*   Advanced document processing (e.g., OCR for scanned PDFs) beyond what `llama-index` natively supports.
*   User authentication or authorization for PDF uploads (initially, this will be a simple endpoint).

## 7. Open Questions / Decisions

*   What is the desired maximum size or number of documents for the custom knowledge base?
*   Should there be any validation on the content of uploaded PDFs?
*   How should conflicts be handled if multiple users upload documents simultaneously (for index rebuilding)? (Initial assumption: simple overwrite/rebuild, no complex locking).
