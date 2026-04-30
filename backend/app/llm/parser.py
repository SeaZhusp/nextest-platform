def extract_content(data: dict) -> str:
    msg = data["choices"][0]["message"]
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            c.get("text", "")
            for c in content
            if c.get("type") == "text"
        )
    return ""


def extract_delta(chunk: dict) -> str:
    delta = chunk["choices"][0].get("delta", {})
    content = delta.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            c.get("text", "")
            for c in content
            if c.get("type") == "text"
        )
    return ""
