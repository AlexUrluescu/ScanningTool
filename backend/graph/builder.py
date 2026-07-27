from langgraph.graph import StateGraph, START, END
from core.state import State
from graph.nodes import classify_document, extract_onboarding_data, validate_output


def create_graph():
    graph_builder = StateGraph(State)

    graph_builder.add_node("classify_document", classify_document)
    graph_builder.add_node("extract_onboarding_data", extract_onboarding_data)
    graph_builder.add_node("validate_output", validate_output)

    graph_builder.add_edge(START, "classify_document")
    graph_builder.add_edge("classify_document", "extract_onboarding_data")
    graph_builder.add_edge("extract_onboarding_data", "validate_output")
    graph_builder.add_edge("validate_output", END)

    return graph_builder.compile()