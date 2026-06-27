from app.shared.config import get_llm_provider_name


def create_provider():
    """根据环境变量创建 LLM Provider 实例。"""
    name = get_llm_provider_name()
    if name == "openai":
        from app.domains.llm_gateway.infrastructure.openai_provider import OpenAIProvider
        return OpenAIProvider()
    else:
        from app.domains.llm_gateway.infrastructure.mock_provider import MockProvider
        return MockProvider()
