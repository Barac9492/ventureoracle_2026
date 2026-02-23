import anthropic
import os
from dotenv import load_dotenv
from ventureoracle.llm.client import ensure_unique_tool_ids

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

messages = []
for i in range(40):
    messages.append({"role": "user", "content": f"Iteration {i}"})
    messages.append({
        "role": "assistant",
        "content": [
            {"type": "text", "text": f"Thinking {i}"},
            {"type": "tool_use", "id": f"tool_id_{i % 10}", "name": "some_tool", "input": {"arg": i}}
        ]
    })
    messages.append({
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": f"tool_id_{i % 10}", "content": f"Result {i}"}
        ]
    })

messages = ensure_unique_tool_ids(messages)

try:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=messages,
        tools=[{"name": "some_tool", "description": "dummy", "input_schema": {"type": "object", "properties": {"arg": {"type": "integer"}}}}]
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
