from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0
)

response = llm.invoke("Say hello in Hinglish.")

print(response.content)