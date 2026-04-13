"""
Vector store setup for semantic search across housing and earnings data.
Uses Ollama embeddings with ChromaDB for fast retrieval.
"""

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd

# Load the cleaned CSV datasets produced by Data_Extraction
average_price = pd.read_csv("data/housing_long.csv")
average_earnings = pd.read_csv("data/earnings_2025_awe.csv")

# Initialise the embedding model (runs locally via Ollama)
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Path where ChromaDB persists its index on disk
db_location = "data/chroma_langchain_db"

# Only build documents on first run (when the DB folder does not exist yet)
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    ids = []

    # -- Housing price documents --
    for i, row in average_price.iterrows():
        document = Document(
            page_content=row["Region"] + " " + str(row["Price"]),
            metadata={"Time Period": row["Time period"]},
            id=str(i)
        )
        ids.append(str(i))
        documents.append(document)

    # -- Earnings documents (offset IDs to avoid collisions) --
    for i, row in average_earnings.iterrows():
        document = Document(
            page_content="Earnings " + str(row["Month"]) + " " + str(row["Public excl. Financial Services AWE"]),
            metadata={"Month": row["Month"]},
            id=str(i + len(average_price))
        )
        ids.append(str(i + len(average_price)))
        documents.append(document)

# Connect to (or create) the persistent vector store
vector_store = Chroma(
    collection_name="average_housing_prices",
    persist_directory=db_location,
    embedding_function=embeddings
)

# Insert documents on first run
if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)

# Retriever returns the top 15 most relevant documents per query
retriever = vector_store.as_retriever(
    search_kwargs={"k": 15}
)
