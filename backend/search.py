import os
import logging
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Find the root directory and load the .env file
root_dir = Path(__file__).resolve().parent.parent
env_path = root_dir / ".env"

# Load the .env file if it exists, otherwise print a warning message
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print(f"Warning: .env file not found at {env_path}.")

# Setup logger for DEBUGGING
env_logger = os.environ.get("ENV_LOGGER", "INFO").upper()
# Configure logging
logging.basicConfig(level=getattr(logging, env_logger, logging.INFO))
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)

# Get configuration values from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Raise an error if any required environment variable is missing
if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY,  OPENAI_API_KEY]):
    raise EnvironmentError("One or more required environment variables are missing.")

# Initialize clients for Supabase, NewsAPI, and OpenAI
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def semantic_search(query: str, top_k: int = 5):
    """
    Perform a semantic search on the Supabase database using OpenAI embeddings.

    Args:
        query (str): The search query.
        top_k (int): The number of top results to return (default is 5).

    Returns:
        list: A list of dictionaries containing the top_k search results.
    """
    
    # Generate embedding for the query using OpenAI
    embedding_response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_embedding = embedding_response.data[0].embedding

    logger.debug(f"OpenAI Generated query vector! Dimensions: {len(query_embedding)} | Sample: {query_embedding[:3]}")

    # Perform a vector similarity search in Supabase
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.4,
            "match_count": top_k
        }
    ).execute()

    logger.debug(f"Supabase search completed! Retrieved {len(response.data)} results.")

    return response.data

if __name__ == "__main__":
    semantic_search("Is Tesla going to be affected by driverless car regulations?")