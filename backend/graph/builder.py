"""Build the LangGraph financial report pipeline with OCR loop."""
from langgraph.graph import StateGraph, START, END
from core.state import FinancialState
from graph.nodes import extract_ocr, extract_transactions, should_continue, generate_report


def create_graph():
    """Create the financial report graph.

    Pipeline:
      START → extract_ocr → extract_transactions → [more docs?] ──Yes──→ extract_ocr (loop)
                                                        │
                                                        No
                                                        ↓
                                                  generate_report → END
    """
    graph_builder = StateGraph(FinancialState)

    graph_builder.add_node("extract_ocr", extract_ocr)
    graph_builder.add_node("extract_transactions", extract_transactions)
    graph_builder.add_node("generate_report", generate_report)

    # START → first OCR pass
    graph_builder.add_edge(START, "extract_ocr")
    
    # OCR → Transaction Extraction
    graph_builder.add_edge("extract_ocr", "extract_transactions")

    # After Transaction Extraction: check if more documents → loop or proceed to report
    graph_builder.add_conditional_edges(
        "extract_transactions",
        should_continue,
        {
            "extract_ocr": "extract_ocr",
            "generate_report": "generate_report",
        }
    )

    # Report → END
    graph_builder.add_edge("generate_report", END)

    return graph_builder.compile()