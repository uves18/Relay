from typing import Any, Callable


def echo(payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload}


def add(payload: dict[str, Any]) -> dict[str, Any]:
    left = payload["left"]
    right = payload["right"]
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        raise ValueError("left and right must be numbers")
    return {"sum": left + right}


def process_text(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload["text"]
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return {
        "text": text,
        "length": len(text),
        "word_count": len(text.split()),
        "uppercase": text.upper(),
    }


TASK_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "demo.echo": echo,
    "demo.add": add,
    "demo.process_text": process_text,
}


def execute_registered_task(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    handler = TASK_HANDLERS.get(task_type)
    if handler is None:
        raise ValueError(f"Unknown task type: {task_type}")
    return handler(payload)
