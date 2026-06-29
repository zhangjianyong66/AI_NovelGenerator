import pytest

from llm_adapters import create_llm_adapter


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
