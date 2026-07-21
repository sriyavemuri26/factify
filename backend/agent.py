from ast import If
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from backend.search import semantic_search
from backend.ingestion import process_documents
from typing import List, Dict, Any, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ddgs import DDGS

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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
    temperature=0.2
)

# State Schema for the Factify Agent
class GraphState(TypedDict):
    question: str
    documents: List[Dict[str, Any]]
    grade: str            # Values: 'yes' (relevant) or 'no' (needs correction)
    generation: str

# State Nodes for the Factify Agent

def retrieve_node(state: GraphState) -> Dict[str, Any]:
    """Pull relevant context data vectors from Supabase."""

    # Store the question in the state
    question = state["question"]
    logger.debug(f"Fetching vectors for: '{question}'")
    
    # Generate documents using semantic search
    docs = semantic_search(question, top_k=3)

    return {"documents": docs, "question": question}

def grade_node(state: GraphState) -> Dict[str, Any]:
    """Zero-shot evaluation to verify if documents are actually relevant."""
    # Store the question and documents in the state
    question = state["question"]
    docs = state["documents"]
    logger.debug(f"Grading document relevance against query: '{question}'")
    
    # If no documents were retrieved, return a 'no' grade immediately
    if not docs:
        return {"grade": "no", "documents": docs}
        
    # Join the content of all documents to form a single context string
    context= "\n".join([doc.get("content", "") for doc in docs])
    
    # Specialized system prompt for zero-shot grading of document relevance
    system_prompt = (
        "You are an elite automated zero-shot verification agent.\n"
        "Grade whether the following context contains information directly relevant to answering the user's question.\n"
        "Respond with EXACTLY one word: 'yes' or 'no'. No punctuation, no explanation."
    )
    user_prompt = f"User Question: {question}\n\nRetrieved Context:\n{context}"
    
    # Provide the system and user prompts to the LLM for evaluation
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    # Extract the final grade from the LLM's response and log it
    final_grade = response.content.strip().lower()
    logger.debug(f"Is context safe and relevant?: {final_grade.upper()}")
    
    return {"grade": final_grade, "documents": docs}

def web_search_correct_node(state: GraphState) -> Dict[str, Any]:
    """Fires a real-time query out to the live web using DuckDuckGo's dedicated news index."""

    # Store the question in the state
    question = state["question"]
    logger.warning("Vector DB failed relevance test. Fetching live news articles...")
    
    corrected_documents = []
    
    try:
        # Initialize zero-auth live news/text fetcher
        with DDGS() as ddgs:
            try:
                text_results = list(ddgs.text(question, max_results=10))
                for item in text_results:
                    body = item.get("body") or item.get("snippet") or ""
                    if body:
                        corrected_documents.append({
                            "title": item.get("title", "Web Result"),
                            "content": body,
                            "url": item.get("href") or item.get("url") or "",
                            "source_name": "DuckDuckGo Web Search"
                        })
            except Exception as te:
                logger.warning(f"DDGS Text search issue: {str(te)}")

            try:
                news_results = list(ddgs.news(question, max_results=10))
                for item in news_results:
                    body = item.get("body") or item.get("snippet") or ""
                    if body:
                        corrected_documents.append({
                            "title": item.get("title", "News Result"),
                            "content": body,
                            "url": item.get("url") or "",
                            "source_name": item.get("source", "DuckDuckGo News")
                        })
            except Exception as ne:
                logger.warning(f"DDGS News 403/Rate-Limit encountered: {str(ne)}")

            # If corrected documents were found, cache them into Supabase for future queries
            if corrected_documents:
                logger.debug("Caching corrected documents into Supabase for future queries...")
                process_documents(corrected_documents)
    
    except Exception as e:
        logger.error(f"Web search correction execution faulted: {str(e)}")

    # If no corrected documents were found, provide a fallback notice  
    if not corrected_documents:
        corrected_documents = [{
            "title": "Fallback Status Notice",
            "content": "No real-time secondary documentation could be securely verified for this target query.",
            "source_name": "System Security Desk"
        }]

    return {"documents": corrected_documents, "question": question}

def generate_node(state: GraphState) -> Dict[str, Any]:
    """Generate final response using the optimized context pool."""

    # Store the question and documents in the state
    question = state["question"]
    docs = state["documents"]
    logger.debug("Synthesizing grounded response...")
    
    # Format the context documents for inclusion in the system prompt
    formatted_context = ""
    for idx, doc in enumerate(docs):
        formatted_context += f"\n[Document {idx}]\n"
        formatted_context += f"Title: {doc.get('title')}\n"
        formatted_context += f"Source: {doc.get('source_name')}\n"
        formatted_context += f"Content: {doc.get('content')}\n"
        
    # Specialized system prompt for grounded response generation
    system_prompt = (
        "You are Factify, an elite AI assistant that provides accurate and reliable information based on the provided context documents.\n"
        "Use the context documents to answer the user's query.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Do not hallucinate or make up information.\n"
        "2. Use only the information provided in the context documents.\n"
        "3. For every major claim you make in your answer, cite the source name inline with the answer. For example, if you are using information from Document 0, cite it as (Document 0).\n"
        "4. Summarize key facts from the context documents to provide a concise and accurate answer.\n"
        "5. If the answer is completely unknown or not present in the context documents, respond with 'I could not find any relevant information based on your query.'\n"
        f"CONTEXT DOCUMENTS:\n{formatted_context}"
    )
    
    # Provide the system prompt and user question to the LLM for final response generation
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ])
    
    return {"generation": response.content}

def decide_to_generate(state: GraphState) -> str:
    """Evaluates the state's grade to determine graph execution path."""

    # If the grade is 'yes', route to generation; if 'no', route to web search correction
    if state["grade"] == "yes":
        logger.debug("DB data looks solid. Routing straight to Generation.")
        return "generate"
    else:
        logger.warning("DB data graded IRRELEVANT. Routing to Web Search Correction Loop!")
        return "correct"
    
# Workflow Construction for the Factify Agent

workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("grade", grade_node)
workflow.add_node("web_search_correct", web_search_correct_node)
workflow.add_node("generate", generate_node)

# Start with the "retrieve" node, then grade the relevance of the retrieved documents
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade")

# If the grade is "yes", proceed to generate; if "no", go to web search correction
workflow.add_conditional_edges(
    "grade", 
    decide_to_generate,
    {
        "generate": "generate",
        "correct": "web_search_correct"
    }
)

# After web search correction, proceed to generate the final response
workflow.add_edge("web_search_correct", "generate")
workflow.add_edge("generate", END)

# Compile the workflow into an executable agent
factify_agent = workflow.compile()
    
if __name__ == "__main__":
    print("\n" + "="*50)
    print("FACTIFY MULTI-AGENT CORRECTIVE RAG INTERACTIVE TERMINAL")
    print("   Type 'exit' or 'quit' at any time to stop.")
    print("="*50 + "\n")

    while True:
        try:
            # Prompt the user for input
            user_query = input("\nFactify Query > ").strip()
            
            # Allow clean exit conditions
            if user_query.lower() in ["exit", "quit", "q"]:
                print("\nShutting down Factify agent terminal. Goodbye!")
                break
 
            # Skip empty inputs
            if not user_query:
                continue

            # Pass user prompt into the LangGraph state machine
            inputs = {"question": user_query}
            logger.debug(f"Initiating graph workflow for query: '{user_query}'")
            
            # Invoke the graph engine
            final_output = factify_agent.invoke(inputs)
            
            # Print the compiled response
            print("\n" + "="*50)
            print("ANSWER:")
            print("="*50)
            print(final_output.get("generation"))
            print("="*50)

        except KeyboardInterrupt:
            # Graceful exit on Ctrl+C
            print("\nShutting down Factify agent terminal. Goodbye!")
            break

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")