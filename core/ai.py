from collections.abc import Sequence
from functools import lru_cache

from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic_ai import Agent, Embedder
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider


def _content_model_settings(model_name: str | None = None) -> tuple[str, str, str, str]:
    return (
        model_name or settings.AI_CONTENT_MODEL,
        settings.OPENROUTER_API_KEY,
        settings.OPENROUTER_APP_URL,
        settings.OPENROUTER_APP_TITLE,
    )


@lru_cache
def _openrouter_provider(api_key: str, app_url: str, app_title: str) -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key=api_key,
        app_url=app_url,
        app_title=app_title,
    )


@lru_cache
def _cached_content_model(
    model_name: str,
    api_key: str,
    app_url: str,
    app_title: str,
) -> OpenRouterModel:
    return OpenRouterModel(
        model_name,
        provider=_openrouter_provider(api_key, app_url, app_title),
    )


def _content_model(model_name: str | None = None) -> OpenRouterModel:
    return _cached_content_model(*_content_model_settings(model_name))


@lru_cache
def _text_agent(
    model_name: str,
    api_key: str,
    app_url: str,
    app_title: str,
) -> Agent:
    return Agent(_cached_content_model(model_name, api_key, app_url, app_title))


@lru_cache
def _structured_agent[OutputT](
    model_name: str,
    api_key: str,
    app_url: str,
    app_title: str,
    output_type: type[OutputT],
) -> Agent:
    return Agent(
        _cached_content_model(model_name, api_key, app_url, app_title),
        output_type=output_type,
    )


def generate_text(
    prompt: str,
    *,
    system_prompt: str | Sequence[str] = (),
    model_name: str | None = None,
) -> str:
    if system_prompt:
        agent = Agent(_content_model(model_name), system_prompt=system_prompt)
    else:
        agent = _text_agent(*_content_model_settings(model_name))
    result = agent.run_sync(prompt)
    return result.output.strip()


def generate_structured[OutputT](
    prompt: str,
    output_type: type[OutputT],
    *,
    system_prompt: str | Sequence[str] = (),
    model_name: str | None = None,
) -> OutputT:
    if system_prompt:
        agent = Agent(
            _content_model(model_name),
            output_type=output_type,
            system_prompt=system_prompt,
        )
    else:
        agent = _structured_agent(*_content_model_settings(model_name), output_type)
    result = agent.run_sync(prompt)
    return result.output


def _embedding_model_settings(model_name: str | None = None) -> tuple[str, str, str]:
    return (
        model_name or settings.AI_EMBEDDING_MODEL,
        settings.OPENROUTER_BASE_URL,
        settings.OPENROUTER_API_KEY,
    )


@lru_cache
def _cached_embedding_model(model_name: str, base_url: str, api_key: str) -> OpenAIEmbeddingModel:
    provider = OpenAIProvider(
        base_url=base_url,
        api_key=api_key,
    )
    return OpenAIEmbeddingModel(
        model_name,
        provider=provider,
    )


@lru_cache
def _cached_embedder(model_name: str, base_url: str, api_key: str) -> Embedder:
    return Embedder(_cached_embedding_model(model_name, base_url, api_key))


def _embedder(model_name: str | None = None) -> Embedder:
    return _cached_embedder(*_embedding_model_settings(model_name))


async def embed_query_async(query: str | Sequence[str], *, model_name: str | None = None) -> list[list[float]]:
    result = await _embedder(model_name).embed_query(query)
    return [list(embedding) for embedding in result.embeddings]


async def embed_documents_async(
    documents: str | Sequence[str],
    *,
    model_name: str | None = None,
) -> list[list[float]]:
    result = await _embedder(model_name).embed_documents(documents)
    return [list(embedding) for embedding in result.embeddings]


def embed_text(text: str, *, model_name: str | None = None) -> list[float]:
    return async_to_sync(embed_query_async)(text, model_name=model_name)[0]


def embed_texts(texts: Sequence[str], *, model_name: str | None = None) -> list[list[float]]:
    return async_to_sync(embed_documents_async)(texts, model_name=model_name)
