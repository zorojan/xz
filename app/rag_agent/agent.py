from google.adk.agents import Agent
from google.adk.tools import google_search, FunctionTool
from .knowledge_base import KnowledgeBaseManager

# Initialize the knowledge base
knowledge_base = KnowledgeBaseManager()
knowledge_base.build_index()

# Define the query_docs tool
def query_docs(query: str) -> str:
    """Queries the custom knowledge base to get information about FSM Armenian company."""
    return knowledge_base.query(query)

query_docs_tool = FunctionTool(query_docs)

# Create the RAG agent
rag_agent = Agent(
    name="rag_agent",
    model="gemini-2.5-flash-native-audio-preview-09-2025",
    description="A voice agent that answers questions about FSM Armenian company using a custom knowledge base, with Armenian language support.",
    instruction="""You are a helpful voice assistant for FSM Armenian company.
Your primary language is Armenian.

IMPORTANT RULES:
- First, always use the `query_docs` tool to answer the user's question.
- If the `query_docs` tool does not provide a relevant answer, then use the `google_search` tool.
- When an answer is provided from an internet search, you must explicitly inform the user that the information was obtained from the internet.
- If you cannot find an answer in either the custom knowledge base or through internet search, state that you cannot find an answer.
- Keep responses brief and conversational.
""",
    tools=[query_docs_tool, google_search],
    language_code="hy-AM"  # Armenian language support
)
