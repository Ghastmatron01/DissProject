# Will allow us to do a vector search through databases, to give them correct data quickly
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd

average_price = pd.read_csv("data/housing_long.csv")
average_earnings = pd.read_csv("data/earnings_2025_awe.csv")

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

db_location = "data/chroma_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    ids = []

    for i, row in average_price.iterrows():
        document = Document(
            page_content=row["Region"] + " " + str(row["Price"]),
            metadata={"Time Period": row["Time period"]},
            id=str(i)
        )
        ids.append(str(i))
        documents.append(document)

    for i, row in average_earnings.iterrows():
        document = Document(
            page_content="Earnings " + str(row["Month"]) + " " + str(row["Public excl. Financial Services AWE"]),
            metadata={"Month": row["Month"]},
            id=str(i + len(average_price))
        )
        ids.append(str(i + len(average_price)))
        documents.append(document)

vector_store = Chroma(
    collection_name="average_housing_prices",
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents, ids=ids)

retriever = vector_store.as_retriever(
    search_kwargs={"k": 15}
)
