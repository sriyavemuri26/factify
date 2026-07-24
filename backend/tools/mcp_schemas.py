from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


# 1. Matches semantic_search(query: str, top_k: int = 5)
class SemanticSearchInput(BaseModel):
    query: str = Field(
        ..., 
        description="The natural language claim or question to verify against stored news articles using OpenAI text-embedding-3-small."
    )
    top_k: int = Field(
        default=5, 
        description="Number of relevant document matches to retrieve via Supabase RPC 'match_documents'."
    )


# 2. Matches fetch_news_articles(query: str, language: str = 'en', page_size: int = 100)
class IngestNewsInput(BaseModel):
    query: str = Field(
        ..., 
        description="Topic query to fetch news via NewsAPI, embed via text-embedding-3-small, and insert into Supabase."
    )
    language: str = Field(
        default="en", 
        description="Language code for news filtering."
    )
    page_size: int = Field(
        default=10, 
        description="Number of articles to fetch, embed, and store."
    )


# 3. Matches process_documents(documents: List[Dict[str, Any]])
class IngestDocumentInput(BaseModel):
    title: str = Field(..., description="Title of the article or document.")
    content: str = Field(..., description="Raw text content to embed and store in the 'documents' table.")
    url: Optional[str] = Field(None, description="Direct URL source.")
    source_name: Optional[str] = Field(None, description="Publisher or news outlet name.")


# 4. Web Search Fallback Node for Corrective RAG
class WebSearchFallbackInput(BaseModel):
    query: str = Field(
        ..., 
        description="Fallback web search query executed when internal vector store context relevance score falls below threshold."
    )


def get_mcp_tool_definitions() -> List[Dict[str, Any]]:
    """Returns MCP-compliant tool definitions mapped directly to Factify's Supabase vector store, NewsAPI pipeline, and web search fallback."""
    return [
        {
            "name": "semantic_search",
            "description": "Runs vector similarity search against Supabase 'documents' using OpenAI embeddings (RPC match_documents with match_threshold=0.4).",
            "inputSchema": SemanticSearchInput.model_json_schema()
        },
        {
            "name": "fetch_news_articles",
            "description": "Fetches news articles via NewsAPI, generates text-embedding-3-small vectors, and writes rows to Supabase.",
            "inputSchema": IngestNewsInput.model_json_schema()
        },
        {
            "name": "process_documents",
            "description": "Ingests, vectorizes, and stores individual custom documents into Supabase.",
            "inputSchema": IngestDocumentInput.model_json_schema()
        },
        {
            "name": "web_search_fallback",
            "description": "Performs external live web search to verify claims when internal database context is insufficient.",
            "inputSchema": WebSearchFallbackInput.model_json_schema()
        }
    ]