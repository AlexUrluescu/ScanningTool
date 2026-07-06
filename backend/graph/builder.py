# graph/builder.py
"""Build the LangGraph extraction pipeline."""
from langgraph.graph import StateGraph, START, END
from core.state import State
from graph.nodes import extract_invoice_data, extract_cv_data, validate_output, classify_document

def route_document(state: State):
    doc_type = state.get("document_type", "UNKNOWN")
    if doc_type == "CV":
        return "extract_cv_data"
    else:
        return "extract_invoice_data"

def create_graph():
    """Create the document extraction graph."""
    graph_builder = StateGraph(State)

    graph_builder.add_node("classify_document", classify_document)
    graph_builder.add_node("extract_invoice_data", extract_invoice_data)
    graph_builder.add_node("extract_cv_data", extract_cv_data)
    graph_builder.add_node("validate_output", validate_output)

    graph_builder.add_edge(START, "classify_document")
    
    graph_builder.add_conditional_edges(
        "classify_document",
        route_document,
        {
            "extract_cv_data": "extract_cv_data",
            "extract_invoice_data": "extract_invoice_data"
        }
    )

    graph_builder.add_edge("extract_invoice_data", "validate_output")
    graph_builder.add_edge("extract_cv_data", "validate_output")
    graph_builder.add_edge("validate_output", END)

    return graph_builder.compile()