import os
import logging
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBaseManager:
    def __init__(self, storage_dir="./storage", documents_dir="./downloads"):
        self.storage_dir = storage_dir
        self.documents_dir = documents_dir
        self.index = None

        # Configure LlamaIndex settings
        Settings.llm = Gemini(api_key=os.environ.get("GOOGLE_API_KEY"))
        Settings.embed_model = GeminiEmbedding(api_key=os.environ.get("GOOGLE_API_KEY"), model_name="models/text-embedding-004")

    def build_index(self, initial_doc_path="fsm-faq.md"):
        """Builds the vector store index from documents."""
        logger.info("Building knowledge base index...")
        if not os.path.exists(self.storage_dir):
            logger.info("No existing storage found. Creating new index.")
            # Load documents and create the index
            # For initial build, we use the provided FAQ file
            if os.path.exists(initial_doc_path):
                documents = SimpleDirectoryReader(input_files=[initial_doc_path]).load_data()
                logger.info(f"Loaded initial document: {initial_doc_path}")
            else:
                documents = []
            
            # Also load any documents already in the downloads directory
            if os.path.exists(self.documents_dir):
                documents.extend(SimpleDirectoryReader(self.documents_dir).load_data())
                logger.info(f"Loaded documents from {self.documents_dir}")

            if documents:
                self.index = VectorStoreIndex.from_documents(documents)
                self.index.storage_context.persist(persist_dir=self.storage_dir)
                logger.info(f"Created and persisted index with {len(documents)} documents.")
            else:
                # Create an empty index if no documents are available
                self.index = VectorStoreIndex.from_documents([])
                self.index.storage_context.persist(persist_dir=self.storage_dir)
                logger.info("Created and persisted an empty index.")
        else:
            # Load the existing index
            logger.info("Loading existing index from storage.")
            storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
            self.index = load_index_from_storage(storage_context)
            logger.info("Index loaded successfully.")

    def query(self, query_text):
        """Queries the knowledge base."""
        if self.index is None:
            self.build_index()
        
        logger.info(f"Querying knowledge base for: '{query_text}'")
        query_engine = self.index.as_query_engine()
        response = query_engine.query(query_text)
        logger.info(f"Received response from knowledge base.")
        return str(response)
