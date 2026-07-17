import os
import logging
from newsapi import NewsApiClient
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
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Raise an error if any required environment variable is missing
if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, NEWS_API_KEY, OPENAI_API_KEY]):
    raise EnvironmentError("One or more required environment variables are missing.")

# Initialize clients for Supabase, NewsAPI, and OpenAI
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Function to fetch news articles from NewsAPI
def fetch_news_articles(query: str, language: str = "en", page_size: int = 100):
    """
    Fetch news articles from NewsAPI based on a query.

    Args:
        query (str): The search query for fetching news articles.
        language (str): The language of the news articles (default is "en").
        page_size (int): The number of articles to fetch (default is 10)."""
    
    results = newsapi.get_everything(
        q=query,
        language=language,
        sort_by="relevancy",
        page_size=page_size
    )

    logging.debug(f"NewsAPI Connected! First article found.")

    articles = results.get("articles", [])

    for idx, article in enumerate(articles):
        title = article.get("title")
        content = article.get("content")
        url = article.get("url")
        source_name = article.get("source", {}).get("name")

        logging.debug(f" [{idx + 1}] Embedding: {title[:50]}...")

        # Generate embedding for the content using OpenAI
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        embedding_vector = embedding_response.data[0].embedding
        
        logging.debug(f"OpenAI Generated vector!")

        # Insert the article into the Supabase database
        supabase.table("documents").insert({
            "title": title,
            "content": content,
            "url": url,
            "source_name": source_name,
            "embedding": embedding_vector
        }).execute()

        logging.debug(f"Supabase Row written successfully!")

if __name__ == "__main__":
    fetch_news_articles("Artificial Intelligence", language="en", page_size=10)



