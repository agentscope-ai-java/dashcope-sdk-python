# -*- coding: utf-8 -*-
"""Unit tests for Vault, Credential, DeleteResponse, Agent.system_prompt."""

from dashscope.agentstudio.resources._helpers import (
    _coerce_vault,
    _coerce_credential,
)
from dashscope.agentstudio.types import (
    Agent,
    Credential,
    CredentialAuth,
    DeleteResponse,
    Environment,
    File,
    Networking,
    Vault,
)


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------


def test_vault_coerce_parses_all_fields():
    payload = {
        "id": "vlt_1",
        "type": "vault",
        "display_name": "my-vault",
        "metadata": {"team": "backend"},
        "created_at": "2026-06-29T10:00:00Z",
        "updated_at": "2026-06-29T10:00:00Z",
        "archived_at": None,
        "request_id": "req_1",
    }
    v = _coerce_vault(payload)
    assert isinstance(v, Vault)
    assert v.id == "vlt_1"
    assert v.display_name == "my-vault"
    assert v.metadata == {"team": "backend"}
    assert v.archived_at is None


def test_vault_skips_none_fields_in_repr():
    v = Vault(id="vlt_1", display_name="demo")
    r = repr(v)
    assert "id='vlt_1'" in r
    assert "display_name='demo'" in r
    assert "archived_at" not in r  # None fields omitted


# ---------------------------------------------------------------------------
# CredentialAuth — three auth types
# ---------------------------------------------------------------------------


def test_credential_auth_environment_variable():
    auth = CredentialAuth(
        type="environment_variable",
        secret_name="OPENAI_API_KEY",
        secret_value="sk-xxx",
        networking={"type": "unrestricted"},
    )
    assert auth.type == "environment_variable"
    assert auth.secret_name == "OPENAI_API_KEY"
    assert isinstance(auth.networking, Networking)
    assert auth.networking.type == "unrestricted"


def test_credential_auth_static_bearer():
    auth = CredentialAuth(
        type="static_bearer",
        token="Bearer eyJhbGci...",
    )
    assert auth.type == "static_bearer"
    assert auth.token == "Bearer eyJhbGci..."
    assert auth.networking is None


def test_credential_auth_mcp_oauth():
    auth = CredentialAuth(
        type="mcp_oauth",
        mcp_server_url="https://mcp.example.com/oauth",
    )
    assert auth.type == "mcp_oauth"
    assert auth.mcp_server_url == "https://mcp.example.com/oauth"


def test_credential_auth_secret_value_not_returned_by_server():
    """Server stores secret_value write-only."""
    auth = CredentialAuth(
        type="environment_variable",
        secret_name="KEY",
        # secret_value intentionally absent (server doesn't return it)
    )
    assert auth.secret_value is None


# ---------------------------------------------------------------------------
# Credential — nested auth parsing
# ---------------------------------------------------------------------------


def test_credential_coerce_wraps_auth_dict():
    payload = {
        "id": "vcrd_1",
        "type": "vault_credential",
        "vault_id": "vlt_1",
        "display_name": "OpenAI Key",
        "auth": {
            "type": "environment_variable",
            "secret_name": "OPENAI_API_KEY",
            "networking": {"type": "restricted"},
        },
        "created_at": "2026-06-29T10:00:00Z",
        "updated_at": "2026-06-29T10:00:00Z",
        "metadata": {"service": "openai"},
        "archived_at": None,
        "request_id": "req_1",
    }
    c = _coerce_credential(payload)
    assert isinstance(c, Credential)
    assert c.id == "vcrd_1"
    assert c.vault_id == "vlt_1"
    assert isinstance(c.auth, CredentialAuth)
    assert c.auth.type == "environment_variable"
    assert isinstance(c.auth.networking, Networking)
    assert c.auth.networking.type == "restricted"


def test_credential_coerce_static_bearer():
    payload = {
        "id": "vcrd_2",
        "type": "vault_credential",
        "vault_id": "vlt_1",
        "auth": {"type": "static_bearer", "token": "Bearer xyz"},
        "display_name": "API Token",
    }
    c = _coerce_credential(payload)
    assert c.auth.type == "static_bearer"
    assert c.auth.token == "Bearer xyz"


# ---------------------------------------------------------------------------
# DeleteResponse
# ---------------------------------------------------------------------------


def test_delete_response_fields():
    dr = DeleteResponse(id="vlt_1", type="vault_deleted", request_id="req_1")
    assert dr.id == "vlt_1"
    assert dr.type == "vault_deleted"
    assert dr.request_id == "req_1"


def test_delete_response_repr_skips_none():
    dr = DeleteResponse(id="x", type="deleted")
    assert "request_id" not in repr(dr)


# ---------------------------------------------------------------------------
# Agent.system_prompt property alias (gotcha: create param is system_prompt,
# field is system, property bridges them)
# ---------------------------------------------------------------------------


def test_agent_system_prompt_is_alias_for_system():
    agent = Agent(
        id="agent_1",
        name="demo",
        model={"id": "qwen-plus"},
        system="你是一个助手。",
    )
    assert agent.system == "你是一个助手。"
    assert agent.system_prompt == agent.system


def test_agent_system_prompt_none_when_system_unset():
    agent = Agent(id="agent_1", name="demo", model={"id": "qwen-plus"})
    assert agent.system is None
    assert agent.system_prompt is None


# ---------------------------------------------------------------------------
# Environment config nested parsing
# ---------------------------------------------------------------------------


def test_environment_config_nested_objects():
    env = Environment(
        id="env_1",
        name="python-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
            "packages": {"pip": ["pandas", "numpy"]},
        },
    )
    assert env.config.type == "cloud"
    assert isinstance(env.config.networking, Networking)
    assert env.config.networking.type == "unrestricted"
    assert env.config.packages.pip == ["pandas", "numpy"]


# ---------------------------------------------------------------------------
# File model
# ---------------------------------------------------------------------------


def test_file_model_fields():
    f = File(
        id="file_1",
        filename="doc.pdf",
        size_bytes=1024,
        mime_type="application/pdf",
        status="checking",
    )
    assert f.id == "file_1"
    assert f.filename == "doc.pdf"
    assert f.size_bytes == 1024
    assert f.status == "checking"
    assert f.downloadable is None  # not set
