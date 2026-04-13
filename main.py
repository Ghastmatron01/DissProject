"""
Early prototype entry point - uses OllamaLLM with a simple prompt
and vector retriever for basic Q&A. This file predates the full
agent pipeline built in Resident_Agent.py.
"""

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from Vector import retriever

# Initialise the text-completion LLM (note: Resident_Agent uses ChatOllama instead)
model = OllamaLLM(model="llama3.2")

# Basic prompt template that feeds retrieved data into the model
template = """
You are a tennant who is looking to afford buying a house on a given salary, using the
statistics from files in a directory.

Here are the relevent files: {data_files}

You will act as an agent, and will recieve more inputs from the program itself.

"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model  # Combine prompt and model into a runnable chain

# Initial invocation with no data (just to prime the model)
result = chain.invoke({"data_files": []})
print(result)

# --------------------------------------------------------------------
#  Interactive Q&A loop
# --------------------------------------------------------------------

while True:
    print("\n\n--------------------------------------------")
    question = input("Ask your question or type your answer or type 'quit' to exit: ")
    print("\n\n")
    if question == "quit":
        break

    # Retrieve the most relevant documents from the vector store
    relevant_docs = retriever.invoke(question)
    retrieved_data = "\n".join([doc.page_content for doc in relevant_docs])

    # Feed retrieved context into the chain alongside the question
    result = chain.invoke({"data_files": retrieved_data})
    print(result)
