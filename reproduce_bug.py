import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Simulate a long conversation with tool use
messages = []
for i in range(40):
    messages.append({"role": "user", "content": f"Iteration {i}"})
    # Manually adding tool_use blocks to simulate an agent history
    # The error was at message 75, which means roughly 37 iterations of user/assistant
    messages.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": f"Thinking {i}"
            },
            {
                "type": "tool_use",
                "id": f"tool_id_{i % 10}",  # Intentional collision every 10 iterations
                "name": "some_tool",
                "input": {"arg": i}
            }
        ]
    })
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": f"tool_id_{i % 10}",
                "content": f"Result {i}"
            }
        ]
    })

try:
    print(f"Sending request with {len(messages)} messages...")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=messages,
        tools=[{
            "name": "some_tool",
            "description": "A dummy tool",
            "input_schema": {
                "type": "object",
                "properties": {"arg": {"type": "integer"}}
            }
        }]
    )
    print("Success!")
except Exception as e:
    print(f"Caught expected error: {e}")
