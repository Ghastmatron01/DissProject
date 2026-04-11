from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from Vector import retriever

model = OllamaLLM(model="llama3.2")

template = """
You are a tennant who is looking to afford buying a house on a given salary, using the
statistics from files in a directory.

Here are the relevent files: {data_files}

You will act as an agent, and will recieve more inputs from the program itself.

"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model # invoke chain, combine multiple things together to run LLM

result = chain.invoke({"data_files": []})

print (result)

while True:
    print("\n\n--------------------------------------------")
    question = input("Ask your question or type your answer or type 'quit' to exit: ")
    print("\n\n")
    if question == "quit":
        break

    # need a result to be printed that invokes the retriever
    relevant_docs = retriever.invoke(question)
    retrieved_data = "\n".join([doc.page_content for doc in relevant_docs])
    result = chain.invoke({"data_files": retrieved_data})


    print (result)
