# -*- coding: utf-8 -*-
"""@tool decorator schema synthesis and JSON Schema validation."""

from typing import List, Optional

import pytest

from dashscope.agentstudio.tools import ToolSpec, tool

jsonschema = pytest.importorskip("jsonschema")


def _validate(schema):
    # Validator factory raises if the schema itself is invalid.
    jsonschema.Draft7Validator.check_schema(schema)


# ---------------------------------------------------------------------------
# Tests from test_agentstudio_tools_decorator.py
# ---------------------------------------------------------------------------


def test_tool_decorator_basic_schema():
    @tool
    def get_weather(city: str, unit: str = "C") -> str:
        """Look up the weather for a city."""

        return f"sunny {city} {unit}"

    spec: ToolSpec = get_weather.__tool_spec__
    assert spec.name == "get_weather"
    assert spec.description == "Look up the weather for a city."
    schema = spec.parameters
    assert schema["type"] == "object"
    assert schema["properties"]["city"] == {"type": "string"}
    # ``unit`` has a default so the schema records it.
    assert schema["properties"]["unit"]["type"] == "string"
    assert schema["properties"]["unit"]["default"] == "C"
    assert schema["required"] == ["city"]


def test_tool_decorator_optional_and_list():
    @tool(name="search", description="Custom desc")
    def _search(q: str, limit: Optional[int] = None, tags: List[str] = None):
        return [q, limit, tags]

    spec = _search.__tool_spec__
    assert spec.name == "search"
    assert spec.description == "Custom desc"
    props = spec.parameters["properties"]
    assert props["q"] == {"type": "string"}
    # Optional[int] -> integer with default=None
    assert props["limit"] == {"type": "integer", "default": None}
    # List[str] -> array of strings
    assert props["tags"] == {
        "type": "array",
        "items": {"type": "string"},
        "default": None,
    }
    assert spec.parameters["required"] == ["q"]


def test_tool_descriptor_round_trip():
    @tool
    def identity(text: str) -> str:
        """Echo."""
        return text

    desc = identity.__tool_spec__.to_descriptor()
    assert (
        "type" not in desc
    ), "BMA backend does not accept 'type' field for custom tools"
    assert desc["name"] == "identity"
    assert desc["input_schema"]["properties"]["text"] == {"type": "string"}


# ---------------------------------------------------------------------------
# Tests from test_agentstudio_tools_schema.py
# ---------------------------------------------------------------------------


def test_simple_tool_schema_is_valid_draft7():
    @tool
    def get_weather(city: str) -> str:
        """Look up the weather for a city."""
        return f"sunny in {city}"

    spec = get_weather.__tool_spec__
    _validate(spec.parameters)
    assert spec.parameters["type"] == "object"
    assert spec.parameters["properties"]["city"]["type"] == "string"
    assert spec.parameters["required"] == ["city"]
    assert spec.parameters["additionalProperties"] is False


def test_default_value_is_emitted_into_schema():
    @tool
    def search(q: str, limit: int = 10) -> str:
        """Search the index."""
        return f"{q}{limit}"

    schema = search.__tool_spec__.parameters
    _validate(schema)
    assert schema["properties"]["limit"]["default"] == 10
    assert "limit" not in schema["required"]


def test_optional_strips_none_keeps_inner_type():
    @tool
    def lookup(name: str, hint: Optional[int] = None) -> str:
        """Look something up."""
        return f"{name}{hint}"

    schema = lookup.__tool_spec__.parameters
    _validate(schema)
    assert schema["properties"]["hint"]["type"] == "integer"
    assert (
        schema["properties"]["hint"]["default"] is None
    )  # None default is preserved
    assert "hint" not in schema["required"]


def test_list_inner_type_is_validated():
    @tool
    def tag(names: List[str]) -> str:
        """Tag inputs."""
        return str(names)

    schema = tag.__tool_spec__.parameters
    _validate(schema)
    assert schema["properties"]["names"] == {
        "type": "array",
        "items": {"type": "string"},
    }


def test_args_block_populates_per_param_descriptions():
    @tool
    def make_order(item: str, qty: int = 1) -> str:
        """Place a supply order.

        Args:
            item: SKU identifier of the product to order.
            qty: How many units to request. Defaults to 1.
        """
        return f"{item}{qty}"

    schema = make_order.__tool_spec__.parameters
    _validate(schema)
    assert schema["properties"]["item"]["description"] == (
        "SKU identifier of the product to order."
    )
    assert (
        "How many units to request"
        in schema["properties"]["qty"]["description"]
    )
    # Top-level summary trims the Args section
    assert make_order.__tool_spec__.description == "Place a supply order."


def test_sphinx_style_param_descriptions():
    @tool
    def fetch(url: str, timeout: float = 5.0) -> str:
        """Fetch a URL.

        :param url: The fully qualified URL to download.
        :param timeout: Per-request timeout in seconds.
        """
        return f"{url}{timeout}"

    schema = fetch.__tool_spec__.parameters
    _validate(schema)
    assert (
        schema["properties"]["url"]["description"]
        == "The fully qualified URL to download."
    )
    assert (
        schema["properties"]["timeout"]["description"]
        == "Per-request timeout in seconds."
    )
    assert fetch.__tool_spec__.description == "Fetch a URL."


def test_descriptor_round_trip_validates_arguments():
    @tool
    def ping(host: str, count: int = 1) -> str:
        """Ping a host."""
        return f"{host}{count}"

    schema = ping.__tool_spec__.to_descriptor()["input_schema"]
    _validate(schema)
    # valid args
    jsonschema.validate({"host": "example.com"}, schema)
    jsonschema.validate({"host": "example.com", "count": 3}, schema)
    # invalid args -- additionalProperties=False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"host": "x", "extra": True}, schema)
    # missing required
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"count": 3}, schema)
    # type mismatch
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"host": 123}, schema)
