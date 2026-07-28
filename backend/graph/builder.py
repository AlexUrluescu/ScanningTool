from langgraph.graph import StateGraph, START, END
from core.state import State
from graph.nodes import extract_onboarding_data, validate_output


def create_graph():
    """Simplified pipeline: extract → validate → done."""
    graph_builder = StateGraph(State)

    graph_builder.add_node("extract_onboarding_data", extract_onboarding_data)
    graph_builder.add_node("validate_output", validate_output)

    graph_builder.add_edge(START, "extract_onboarding_data")
    graph_builder.add_edge("extract_onboarding_data", "validate_output")
    graph_builder.add_edge("validate_output", END)

    return graph_builder.compile()