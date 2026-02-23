import uuid
from ventureoracle.llm.client import ensure_unique_tool_ids

def test_ensure_unique_tool_ids():
    messages = [
        {"role": "user", "content": "hello"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "using tool"},
                {"type": "tool_use", "id": "collision_1", "name": "test_tool", "input": {}}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "collision_1", "content": "result 1"}
            ]
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "using tool again"},
                {"type": "tool_use", "id": "collision_1", "name": "test_tool", "input": {}}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "collision_1", "content": "result 2"}
            ]
        }
    ]

    new_messages = ensure_unique_tool_ids(messages)

    # Check length
    assert len(new_messages) == len(messages)

    # Extract new IDs
    tool_use_ids = []
    tool_result_ids = []

    for msg in new_messages:
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if block["type"] == "tool_use":
                    tool_use_ids.append(block["id"])
                elif block["type"] == "tool_result":
                    tool_result_ids.append(block["tool_use_id"])

    # All tool_use IDs must be unique
    assert len(tool_use_ids) == 2
    assert tool_use_ids[0] != tool_use_ids[1]
    assert tool_use_ids[0].startswith("tool_")
    assert tool_use_ids[1].startswith("tool_")

    # Linkage must be preserved
    assert tool_result_ids[0] == tool_use_ids[0]
    assert tool_result_ids[1] == tool_use_ids[1]

def test_consecutive_duplicate_tool_ids():
    # Test case where Claude hallucinates identical tool IDs consecutively
    # BEFORE any tool results are returned.
    messages = [
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "duplicate_id", "name": "tool_A", "input": {}},
            ]
        },
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "duplicate_id", "name": "tool_B", "input": {}},
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "duplicate_id", "content": "result A"}
            ]
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "duplicate_id", "content": "result B"}
            ]
        }
    ]
    
    new_messages = ensure_unique_tool_ids(messages)
    
    use_ids = []
    result_ids = []
    
    for msg in new_messages:
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if block["type"] == "tool_use":
                    use_ids.append(block["id"])
                elif block["type"] == "tool_result":
                    result_ids.append(block["tool_use_id"])
                    
    # Must have 2 unique tool_use IDs
    assert len(use_ids) == 2
    assert use_ids[0] != use_ids[1]
    
    # Must have 2 unique tool_result IDs
    assert len(result_ids) == 2
    
    # Tool results must map to the tool uses IN ORDER
    assert use_ids[0] == result_ids[0]
    assert use_ids[1] == result_ids[1]

    print("All tool ID uniqueness tests passed!")

if __name__ == "__main__":
    test_ensure_unique_tool_ids()
    test_consecutive_duplicate_tool_ids()
