
from typing import Annotated, TypedDict, Optional
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    document_images: list[str]  # base64-encoded images
    extracted_data: Optional[dict]
    document_type: Optional[str]