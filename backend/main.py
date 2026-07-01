# main.py
from graph.builder import create_graph

def run_chat():
    # 1. Initialize the graph
    app = create_graph()
    
    # 2. Get user input
    user_input = "Get post number 3 from JSONPlaceholder and show me the raw JSON."

    # 3. Invoke the graph
    result = app.invoke({"messages": [{"role": "user", "content": user_input}]})

    # 4. Print outputs
    print("\n--- Full message trace ---")
    for msg in result["messages"]:
        role = getattr(msg, "type", "unknown")
        print(f"\n[{role}]")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print("tool_calls:", msg.tool_calls)
        print(msg.content)

    print("\n--- Final answer ---")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    run_chat()