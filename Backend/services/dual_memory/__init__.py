"""
Kogna Dual Memory System
========================

User-centric memory with two stores:
1. Conversational Memory - Chat history, preferences, session context
2. Business Knowledge Memory - Facts, risks, metrics, company info
"""

from .memory_system import (
    UserMemorySystem,
    ConversationalMemory,
    BusinessKnowledgeMemory,
    FactType,
    RiskSeverity,
    EmbeddingProvider,
)

from .fact_extraction import FactExtractor, ExtractionResult

__all__ = [
    "UserMemorySystem",
    "ConversationalMemory",
    "BusinessKnowledgeMemory",
    "FactType",
    "RiskSeverity",
    "EmbeddingProvider",
    "FactExtractor",
    "ExtractionResult",
]
