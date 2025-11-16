# RAG Agent with Armenian Language Support

This application provides a voice-based conversational AI agent that answers questions from a custom knowledge base in Armenian.

## Features

- **RAG-based Agent:** The agent uses a Retrieval Augmented Generation (RAG) approach to answer questions based on a custom knowledge base.
- **Armenian Language Support:** The agent can understand and respond in Armenian.
- **Custom Knowledge Base:** The knowledge base can be built from local documents (e.g., Markdown, PDF).
- **PDF Upload:** Users can upload PDF documents to update the knowledge base in real-time.
- **Internet Search Fallback:** If an answer is not found in the custom knowledge base, the agent can fall back to a general internet search.

## Setup

1.  **Install uv (recommended):**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

2.  **Create virtual environment with Python 3.12:**
    ```powershell
    cd app
    uv venv --python 3.12
    ```
    **Note:** Python 3.14 is not yet supported by all dependencies. Use Python 3.12 or 3.13.

3.  **Install dependencies:**
    ```powershell
    uv pip install -r requirements.txt
    ```

4.  **Configure API keys:**
    Create a `.env` file in the `app` directory with your Google AI API key:
    ```
    GEMINI_API_KEY=your_google_ai_api_key_here
    GOOGLE_API_KEY=your_google_ai_api_key_here
    ```
    **Note:** Both keys are required for different components.
    
    Get your API key from: https://makersuite.google.com/app/apikey

5.  **Prepare Knowledge Base:**
    Place your initial knowledge base documents in the `app/downloads` directory. The application will use `fsm-faq.md` by default if it exists.

6.  **Run the application:**
    ```powershell
    .\.venv\Scripts\Activate.ps1
    python -m uvicorn main:app --reload
    ```

7.  **Open in browser:**
    Navigate to `http://localhost:8000`

## Usage

1.  **Start a conversation:** Click the "Start Mic" button and speak to the agent in Armenian.
2.  **Ask questions:** Ask questions related to the content of your knowledge base.
3.  **Upload new documents:** Use the "Choose File" button to select a PDF document and upload it to the knowledge base. The agent will then be able to answer questions about the content of the uploaded document.

## Technical Details

- **Backend:** Python, FastAPI, google-adk, llama-index
- **Frontend:** HTML, CSS, JavaScript, Web Audio API
- **AI:** Gemini Pro, Gemini Embeddings