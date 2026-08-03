from server.tools import search_knowledge as _search_knowledge_module

TOOLS = {
    "search_knowledge": {
        "handler": _search_knowledge_module.search_knowledge,
        "requires_confirmation": False,
        "description": (
            "Search the internal support knowledge base for articles relevant to a "
            "question or ticket. Always try this before answering from memory."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to look up.",
                }
            },
            "required": ["query"],
        },
    },
}


def openai_tool_defs():
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": tool["description"],
                "parameters": tool["schema"],
            },
        }
        for name, tool in TOOLS.items()
    ]


def validate_arguments(tool_name, arguments):
    """Return a human-readable problem string, or None if the arguments are valid."""
    tool = TOOLS.get(tool_name)
    if tool is None:
        return f"unknown tool: {tool_name}"
    if not isinstance(arguments, dict):
        return "arguments must be a JSON object"
    schema = tool["schema"]
    properties = schema["properties"]
    for key in schema.get("required", []):
        if key not in arguments or arguments[key] in ("", None):
            return f"missing required argument: {key}"
    unknown = set(arguments) - set(properties)
    if unknown:
        return f"unknown arguments: {sorted(unknown)}"
    for key, spec in properties.items():
        if key not in arguments:
            continue
        if spec.get("type") == "string" and not isinstance(arguments[key], str):
            return f"argument '{key}' must be a string"
        if "enum" in spec and arguments[key] not in spec["enum"]:
            return f"argument '{key}' must be one of {spec['enum']}"
    return None
