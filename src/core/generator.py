from __future__ import annotations

from typing import Any

from src.core.base import ProjectConfig
from src.core.retriever import build_query_engine
from src.core.schemas import QueryArtifacts, RAGResponse
from src.core.settings import AppSettings
from loguru import logger



def answer_question(index: Any, question: str, config: ProjectConfig, settings: AppSettings) -> QueryArtifacts:
    logger.debug("Answering question for collection '{}': {}", config.collection_name, question)
    query_engine = build_query_engine(index=index, config=config, settings=settings)
    response = query_engine.query(question)
    logger.debug("Query response from LLM: {}", str(response))
    source_nodes = list(getattr(response, "source_nodes", []) or [])
    sources = _dedupe_sources(source_nodes)
    retrieval_context = _context_snippets(source_nodes)
    evidence = _build_evidence_summary(source_nodes)
    confidence = _infer_confidence(source_nodes)
    logger.debug(
        "Retrieved {} source nodes. Sources: {}. Evidence summary: '{}'. Confidence: '{}'.",
        len(source_nodes),
        sources,
        evidence,
        confidence,
    )
    return QueryArtifacts(
        response=RAGResponse(
            answer=str(response),
            evidence=evidence,
            sources=sources,
            confidence=confidence,
            disclaimer=config.disclaimer,
        ),
        retrieval_context=retrieval_context,
    )


def _dedupe_sources(source_nodes: list[Any]) -> list[str]:
    seen: list[str] = []
    for source_node in source_nodes:
        metadata = getattr(getattr(source_node, "node", None), "metadata", {}) or {}
        source_org = metadata.get("source_org") or metadata.get("source") or "Unknown source"
        source_file = metadata.get("source_file") or metadata.get("title") or "Unknown document"
        page = metadata.get("page")
        label = f"{source_org}: {source_file}"
        if page is not None:
            label = f"{label} (page {page})"
        if label not in seen:
            seen.append(label)
    logger.debug("Deduced {} unique sources from source nodes.", seen)        
    return seen



def _context_snippets(source_nodes: list[Any]) -> list[str]:
    snippets: list[str] = []
    logger.debug("Building context snippets from {} source nodes.", len(source_nodes))
    for source_node in source_nodes[:4]:
        text = getattr(getattr(source_node, "node", None), "text", "") or ""
        snippet = " ".join(text.split())
        if snippet:
            snippets.append(snippet[:500])
    logger.debug("Built {} context snippets.", len(snippets))        
    return snippets


def _build_evidence_summary(source_nodes: list[Any]) -> str:
    if not source_nodes:
        return "No supporting evidence was retrieved."
    snippets = _context_snippets(source_nodes[:2])
    logger.info("Built evidence summary from {} source nodes.", snippets)
    return " | ".join(snippets) if snippets else "Supporting evidence was retrieved."


def _infer_confidence(source_nodes: list[Any]) -> str:
    count = len(source_nodes)
    if count >= 4:
        return "high"
    if count >= 2:
        return "moderate"
    return "low"
