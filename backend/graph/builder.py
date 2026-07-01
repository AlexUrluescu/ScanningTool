from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from core.state import State
from graph.nodes import call_model
from tools.index import get_jsonplaceholder_post

def create_graph():
    graph_builder = StateGraph(State)
    tools = [get_jsonplaceholder_post]

    graph_builder.add_node("agent", call_model)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", tools_condition)
    graph_builder.add_edge("tools", "agent")

    return graph_builder.compile()