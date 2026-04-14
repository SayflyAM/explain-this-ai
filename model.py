"""ExplainThis NLP service layer.

This module provides a clean NLP architecture for bilingual (Arabic/English)
text explanation. It is designed to match the software architecture goals:
- clear separation from web layer
- model routing by language
- startup model initialization
- no long-term user data storage
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol


class Explainer(Protocol):
	"""Contract for any text explanation model adapter."""

	def explain(self, text: str) -> str:
		"""Return a simplified explanation for input text."""


@dataclass(frozen=True)
class ExplanationResult:
	"""Structured response returned by the NLP service."""

	language: str
	simplified_text: str
	key_points: List[str]
	model_source: str


class RuleBasedExplainer:
	"""Fast fallback explainer used when external NLP models are unavailable."""

	def __init__(self, language: str) -> None:
		self.language = language

	def explain(self, text: str) -> str:
		cleaned = _normalize_text(text)
		if not cleaned:
			return "No input text was provided."

		short = _truncate(cleaned, 420)
		if self.language == "arabic":
			return (
				"Simplified explanation (AR fallback): "
				f"{short}. This version keeps the core meaning in clearer terms."
			)

		return (
			"Simplified explanation (EN fallback): "
			f"{short}. This version keeps the core meaning in simpler wording."
		)


class TransformersExplainer:
	"""Adapter around Hugging Face text2text-generation pipeline."""

	def __init__(self, model_name: str, language: str) -> None:
		self.model_name = model_name
		self.language = language

		# Imported lazily so the project can still run without transformers.
		from transformers import pipeline

		self._pipe = pipeline("text2text-generation", model=model_name)

	def explain(self, text: str) -> str:
		cleaned = _normalize_text(text)
		if not cleaned:
			return "No input text was provided."

		prompt = self._build_prompt(cleaned)
		output = self._pipe(
			prompt,
			max_new_tokens=180,
			do_sample=False,
			truncation=True,
		)
		generated = output[0].get("generated_text", "").strip()
		return generated or cleaned

	def _build_prompt(self, text: str) -> str:
		if self.language == "arabic":
			return f"Simplify this Arabic text with clear wording: {text}"
		return f"Simplify this English text with clear wording: {text}"


class ExplainThisNLPService:
	"""Main NLP orchestration service for ExplainThis."""

	def __init__(self) -> None:
		self._models: Dict[str, Explainer] = {}
		self._model_sources: Dict[str, str] = {}
		self._load_models_once()

	def _load_models_once(self) -> None:
		"""Load language models during startup (single initialization)."""
		# Candidate models are selected to keep architecture clear and modular.
		model_candidates = {
			"english": "google/flan-t5-base",
			"arabic": "UBC-NLP/AraT5v2-base-1024",
		}

		for language, model_name in model_candidates.items():
			try:
				self._models[language] = TransformersExplainer(
					model_name=model_name,
					language=language,
				)
				self._model_sources[language] = f"transformers:{model_name}"
			except Exception:
				self._models[language] = RuleBasedExplainer(language=language)
				self._model_sources[language] = "fallback:rule-based"

	def detect_language(self, text: str) -> str:
		"""Detect input language with a lightweight Arabic script heuristic."""
		if not text.strip():
			return "english"

		arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
		latin_chars = len(re.findall(r"[A-Za-z]", text))

		if arabic_chars > latin_chars:
			return "arabic"
		return "english"

	def explain_text(self, text: str, language: Optional[str] = None) -> ExplanationResult:
		"""Generate simplified explanation and extracted key points."""
		cleaned = _normalize_text(text)
		selected_language = language or self.detect_language(cleaned)
		selected_language = selected_language if selected_language in self._models else "english"

		model = self._models[selected_language]
		simplified = model.explain(cleaned)
		key_points = _extract_key_points(cleaned, max_points=3)

		return ExplanationResult(
			language=selected_language,
			simplified_text=simplified,
			key_points=key_points,
			model_source=self._model_sources[selected_language],
		)


def _normalize_text(text: str) -> str:
	"""Normalize whitespace while preserving readable sentence boundaries."""
	return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, max_len: int) -> str:
	if len(text) <= max_len:
		return text
	return text[: max_len - 3].rstrip() + "..."


def _extract_key_points(text: str, max_points: int = 3) -> List[str]:
	"""Extract up to max_points important-looking sentences.

	This is intentionally lightweight for MVP behavior and easy maintenance.
	"""
	if not text:
		return []

	parts = re.split(r"(?<=[.!?\u061F])\s+", text)
	candidates = [p.strip() for p in parts if len(p.strip()) > 30]
	if not candidates:
		fallback = _truncate(text, 120)
		return [fallback] if fallback else []

	selected = candidates[:max_points]
	return [_truncate(item, 160) for item in selected]


def create_nlp_service() -> ExplainThisNLPService:
	"""Factory function used by the web layer during startup."""
	return ExplainThisNLPService()

