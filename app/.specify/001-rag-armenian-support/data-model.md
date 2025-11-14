# Data Model

This feature does not introduce any new structured data models that require a database.

The primary data entities are the documents that form the knowledge base for the RAG agent. These documents are unstructured and will be managed by `llama-index`.

## Document

*   **Description:** A document in the knowledge base.
*   **Attributes:**
    *   `content`: The text content of the document.
    *   `metadata`: File name, path, etc.
*   **Storage:** Stored on the filesystem in the `./downloads` directory.
