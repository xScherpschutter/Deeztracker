"""
Translation system for Deeztracker.
Provides bilingual support (English/Spanish) using dictionary-based translations.
"""

from .translator import Translator, AVAILABLE_LANGUAGES, LANGUAGE_NAMES

__all__ = ["Translator", "AVAILABLE_LANGUAGES", "LANGUAGE_NAMES"]
