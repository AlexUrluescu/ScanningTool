from langchain_ollama import ChatOllama
from core.state import State
from tools.index import get_jsonplaceholder_post

llm = ChatOllama(model="llama3.2", temperature=0)
tools = [get_jsonplaceholder_post]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: State) -> State:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}