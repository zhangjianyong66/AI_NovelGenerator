import pytest

import llm_adapters
from llm_adapters import create_llm_adapter


def test_openai_compatible_clients_use_project_user_agent(monkeypatch):
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured["chat"] = kwargs

    class FakeAzureChatOpenAI:
        def __init__(self, **kwargs):
            captured["azure"] = kwargs

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["openai"] = kwargs

    monkeypatch.setattr(llm_adapters, "ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr(llm_adapters, "AzureChatOpenAI", FakeAzureChatOpenAI)
    monkeypatch.setattr(llm_adapters, "OpenAI", FakeOpenAI)

    llm_adapters._create_chat_openai(model="test-model")
    llm_adapters._create_azure_chat_openai(azure_deployment="test-deployment")
    llm_adapters._create_openai_client(api_key="test-key")

    assert captured["chat"]["default_headers"] == llm_adapters.OPENAI_COMPATIBLE_DEFAULT_HEADERS
    assert captured["azure"]["default_headers"] == llm_adapters.OPENAI_COMPATIBLE_DEFAULT_HEADERS
    assert captured["openai"]["default_headers"] == llm_adapters.OPENAI_COMPATIBLE_DEFAULT_HEADERS


def test_openai_adapter_ignores_invalid_system_proxy_when_project_proxy_disabled(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "socks://127.0.0.1:10808")
    monkeypatch.delenv("OPENAI_PROXY", raising=False)

    try:
        create_llm_adapter(
            interface_format="OpenAI",
            base_url="https://example.invalid/v1",
            model_name="test-model",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1024,
            timeout=30,
        )
    except ValueError as exc:
        if "Unknown scheme for proxy URL" in str(exc):
            pytest.fail("OpenAI adapter should not read system proxy when project proxy is disabled")
        raise


def test_azure_openai_adapter_ignores_invalid_system_proxy_when_project_proxy_disabled(monkeypatch):
    monkeypatch.setenv("ALL_PROXY", "socks://127.0.0.1:10808")
    monkeypatch.delenv("OPENAI_PROXY", raising=False)
    base_url = (
        "https://example.openai.azure.com/openai/deployments/"
        "test-deployment/chat/completions?api-version=2024-02-15-preview"
    )

    try:
        create_llm_adapter(
            interface_format="Azure OpenAI",
            base_url=base_url,
            model_name="test-model",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1024,
            timeout=30,
        )
    except ValueError as exc:
        if "Unknown scheme for proxy URL" in str(exc):
            pytest.fail("Azure OpenAI adapter should not read system proxy when project proxy is disabled")
        raise
