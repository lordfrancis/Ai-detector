"""Shared type aliases for analysis dictionaries."""

from __future__ import annotations

from typing import Any, TypeAlias


Rule: TypeAlias = dict[str, Any]
RuleMatch: TypeAlias = dict[str, Any]
ParagraphScore: TypeAlias = dict[str, Any]
DocumentScore: TypeAlias = dict[str, Any]
AnalysisResult: TypeAlias = dict[str, Any]
