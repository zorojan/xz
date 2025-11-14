# Tasks: RAG Agent with Armenian Language Support

This task list is generated from the implementation plan and feature specification.

## Dependencies

The user stories are largely independent and can be implemented in parallel, with the exception that US1 and US2 should be completed before US3.

*   US1 (Armenian Language) and US2 (RAG Agent) can be worked on in parallel.
*   US3 (PDF Upload) depends on the completion of US2.

## Parallel Execution Examples

*   **US1 & US2:** While one developer works on configuring the agent for Armenian language support (US1), another can implement the core RAG agent logic (US2).
*   **US3:** The frontend UI for PDF upload can be developed in parallel with the backend endpoint implementation.

## Implementation Strategy

The implementation will follow an MVP approach, focusing on delivering the core RAG agent with Armenian language support first (US1 and US2). The PDF upload functionality (US3) will be implemented as a fast-follow.

---

## Phase 1: Setup

- [x] T001 Create `app/rag_agent` directory.
- [x] T002 Create `app/storage` directory for `llama-index` data.
- [x] T003 Create `app/downloads` directory for uploaded documents.
- [x] T004 Update `app/requirements.txt` to include `llama-index`, `llama-index-llms-gemini`, and `llama-index-embeddings-gemini`.
- [x] T005 [P] Delete the `app/detail_agent` directory.
- [x] T006 [P] Remove UI elements related to trend analysis from `app/static/index.html`.

## Phase 2: Foundational (RAG Knowledge Base)

- [x] T007 Implement a `KnowledgeBaseManager` class in a new file `app/rag_agent/knowledge_base.py` to handle `llama-index` setup, document loading, and querying.
- [x] T008 Implement a `build_index` method in `KnowledgeBaseManager` to create the initial knowledge base from `fsm-faq.md`.
- [x] T009 Implement a `query` method in `KnowledgeBaseManager` that will be used by the `query_docs` tool.

## Phase 3: User Story 1 (Armenian Language)

**Goal:** As a user, I want to interact with the agent in Armenian.
**Test Criteria:** The agent should respond accurately in Armenian to questions asked in Armenian.

- [x] T010 [US1] Configure the `rag_agent` model in `app/rag_agent/agent.py` to support Armenian language (`hy-AM`).
- [x] T011 [US1] Update the agent's system instructions to handle Armenian conversation.

## Phase 4: User Story 2 (RAG Agent)

**Goal:** As a user, I want the agent to answer questions based on a custom knowledge base.
**Test Criteria:** The agent should answer questions from the FSM FAQ correctly and fall back to internet search when necessary.

- [x] T012 [US2] Create the `rag_agent` in `app/rag_agent/agent.py`, including the `query_docs` and `google_search` tools.
- [x] T013 [US2] Implement the `query_docs` `FunctionTool` which will use the `KnowledgeBaseManager`.
- [x] T014 [US2] Update `app/main.py` to remove the `detail_agent` and replace the `google_search_agent` with the new `rag_agent`.

## Phase 5: User Story 3 (PDF Upload)

**Goal:** As a user, I want to be able to upload new documents to update the knowledge base.
**Test Criteria:** After uploading a PDF, the agent should be able to answer questions based on its content.

- [x] T015 [P] [US3] Implement the `/upload-pdf` endpoint in `app/main.py` as defined in `openapi.yaml`. This endpoint should use the `KnowledgeBaseManager` to update the index.
- [x] T016 [P] [US3] Add a PDF upload form to `app/static/index.html`.
- [x] T017 [US3] Implement the client-side logic in `app/static/js/app.js` to handle PDF selection and upload to the `/upload-pdf` endpoint.

## Phase 6: Polish

- [x] T018 Add comprehensive error handling for the PDF upload endpoint and client-side logic.
- [x] T019 Add logging to the `KnowledgeBaseManager` and the PDF upload endpoint.
- [x] T020 Update `README.md` with instructions for the new RAG agent and PDF upload feature.
