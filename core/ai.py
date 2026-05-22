from collections.abc import Sequence
from functools import lru_cache

from asgiref.sync import async_to_sync
from django.conf import settings
from pydantic_ai import Agent, Embedder
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider


@lru_cache
def _openrouter_provider() -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key=settings.OPENROUTER_API_KEY,
        app_url=settings.OPENROUTER_APP_URL,
        app_title=settings.OPENROUTER_APP_TITLE,
    )


def _content_model(model_name: str | None = None) -> OpenRouterModel:
    return OpenRouterModel(
        model_name or settings.AI_CONTENT_MODEL,
        provider=_openrouter_provider(),
    )


def generate_text(
    prompt: str,
    *,
    system_prompt: str | Sequence[str] = (),
    model_name: str | None = None,
) -> str:
    agent = Agent(_content_model(model_name), system_prompt=system_prompt)
    result = agent.run_sync(prompt)
    return result.output.strip()


def generate_structured[OutputT](
    prompt: str,
    output_type: type[OutputT],
    *,
    system_prompt: str | Sequence[str] = (),
    model_name: str | None = None,
) -> OutputT:
    agent = Agent(
        _content_model(model_name),
        output_type=output_type,
        system_prompt=system_prompt,
    )
    result = agent.run_sync(prompt)
    return result.output


@lru_cache
def _embedding_model(model_name: str | None = None) -> OpenAIEmbeddingModel:
    provider = OpenAIProvider(
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
    )
    return OpenAIEmbeddingModel(
        model_name or settings.AI_EMBEDDING_MODEL,
        provider=provider,
    )


def _embedder(model_name: str | None = None) -> Embedder:
    return Embedder(_embedding_model(model_name))


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
