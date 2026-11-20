import pytest

from relay.tasks.handlers import execute_registered_task


def test_echo_handler():
    assert execute_registered_task("demo.echo", {"value": 3}) == {"echo": {"value": 3}}


def test_add_handler():
    assert execute_registered_task("demo.add", {"left": 2, "right": 3}) == {"sum": 5}


def test_process_text_handler():
    result = execute_registered_task("demo.process_text", {"text": "hello relay"})
    assert result["length"] == 11
    assert result["word_count"] == 2
    assert result["uppercase"] == "HELLO RELAY"


def test_unknown_task_handler():
    with pytest.raises(ValueError, match="Unknown task type"):
        execute_registered_task("demo.unknown", {})
