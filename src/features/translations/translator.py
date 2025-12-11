"""
Translator class for managing translations and language switching.
"""

from typing import Callable, Optional
from .languages import en, es


# Available languages - add new languages here
AVAILABLE_LANGUAGES = {
    "en": en.translations,
    "es": es.translations
}

# Language display names
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Español"
}


class Translator:
    """Manages translations and language switching with subscriber notifications."""
    
    def __init__(self, default_language: str = "en"):
        """
        Initialize the translator.
        
        Args:
            default_language: The default language code ('en' or 'es')
        """
        self._current_language = default_language if default_language in AVAILABLE_LANGUAGES else "en"
        self._subscribers: list[Callable[[str], None]] = []
    
    @property
    def current_language(self) -> str:
        """Get the current language code."""
        return self._current_language
    
    def set_language(self, language_code: str) -> None:
        """
        Set the current language and notify subscribers.
        
        Args:
            language_code: The language code to switch to ('en' or 'es')
        """
        if language_code in AVAILABLE_LANGUAGES:
            self._current_language = language_code
            self._notify_subscribers()
    
    def t(self, key: str, **kwargs) -> str:
        """
        Get a translated string for the given key.
        Supports nested keys using dot notation (e.g., 'settings.title').
        Falls back to English if the key is not found in the current language.
        
        Args:
            key: The translation key (supports dot notation)
            **kwargs: Optional format arguments for the string
            
        Returns:
            The translated string, or the key itself if not found
        """
        # Get the current language dictionary
        current_dict = AVAILABLE_LANGUAGES.get(self._current_language, {})
        
        # Try to get from current language
        value = self._get_nested_value(current_dict, key)
        
        # Fallback to English if not found and not already in English
        if value is None and self._current_language != "en":
            english_dict = AVAILABLE_LANGUAGES.get("en", {})
            value = self._get_nested_value(english_dict, key)
        
        # If still not found, return the key itself
        if value is None:
            return key
        
        # Format with kwargs if provided
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value
        
        return value
    
    def _get_nested_value(self, dictionary: dict, key: str) -> Optional[str]:
        """
        Get a value from a nested dictionary using dot notation.
        
        Args:
            dictionary: The dictionary to search
            key: The key in dot notation (e.g., 'settings.title')
            
        Returns:
            The value if found, None otherwise
        """
        keys = key.split('.')
        current = dictionary
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def subscribe(self, callback: Callable[[str], None]) -> None:
        """
        Subscribe to language change notifications.
        
        Args:
            callback: Function to call when language changes, receives language code
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[str], None]) -> None:
        """
        Unsubscribe from language change notifications.
        
        Args:
            callback: The callback function to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self) -> None:
        """Notify all subscribers of a language change."""
        for callback in self._subscribers:
            try:
                callback(self._current_language)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
