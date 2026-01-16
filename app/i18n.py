"""
Internationalisierung (i18n) für MyBaby App

Lädt Übersetzungen aus JSON-Dateien und stellt eine zentrale _() Funktion bereit.
"""
import json
import os
from functools import lru_cache
from flask import session, request

# Default-Sprache
DEFAULT_LANGUAGE = 'de'

# Unterstützte Sprachen
SUPPORTED_LANGUAGES = ['de', 'en', 'es']

# Pfad zum translations-Ordner
TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations')

# Cache für geladene Übersetzungen
_translations_cache = {}


def load_translations(lang):
    """
    Lädt Übersetzungen für eine bestimmte Sprache.
    
    Args:
        lang: Sprachcode (z.B. 'de', 'en')
    
    Returns:
        dict: Dictionary mit Übersetzungen oder None bei Fehler
    """
    if lang in _translations_cache:
        return _translations_cache[lang]
    
    # Fallback auf Default-Sprache wenn Sprache nicht unterstützt
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    json_path = os.path.join(TRANSLATIONS_DIR, f'{lang}.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[lang] = translations
            return translations
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Fehler beim Laden der Übersetzungen für {lang}: {e}")
        # Versuche Default-Sprache zu laden
        if lang != DEFAULT_LANGUAGE:
            return load_translations(DEFAULT_LANGUAGE)
        return {}


def get_language():
    """
    Bestimmt die aktuelle Sprache.
    
    Priorität:
    1. Session ('lang')
    2. Browser-Sprache (Accept-Language Header)
    3. Default-Sprache (de)
    
    Returns:
        str: Sprachcode (z.B. 'de', 'en')
    """
    try:
        # 1. Prüfe Session (nur innerhalb Request-Context)
        from flask import has_request_context
        if has_request_context():
            if session.get('lang') in SUPPORTED_LANGUAGES:
                return session['lang']
            
            # 2. Prüfe Browser-Sprache
            if request and hasattr(request, 'headers'):
                accept_language = request.headers.get('Accept-Language', '')
                if accept_language:
                    # Parse Accept-Language Header (z.B. "en-US,en;q=0.9,de;q=0.8")
                    languages = [lang.split(';')[0].strip()[:2] for lang in accept_language.split(',')]
                    for lang in languages:
                        if lang in SUPPORTED_LANGUAGES:
                            return lang
    except RuntimeError:
        # Kein Request-Context verfügbar
        pass
    
    # 3. Default
    return DEFAULT_LANGUAGE


def translate(key, lang=None, **kwargs):
    """
    Übersetzt einen Key in die gewünschte Sprache.
    
    Args:
        key: Übersetzungsschlüssel (z.B. 'nav.dashboard' oder 'common.save')
        lang: Sprachcode (optional, wird automatisch bestimmt wenn nicht angegeben)
        **kwargs: Platzhalter für Formatierung (z.B. amount=100)
    
    Returns:
        str: Übersetzter Text oder der Key selbst wenn nicht gefunden
    
    Examples:
        _('nav.dashboard') -> 'Dashboard'
        _('messages.success.bottle_recorded', amount=100) -> 'Flasche (100 ml) erfasst'
    """
    if lang is None:
        lang = get_language()
    
    translations = load_translations(lang)
    
    # Navigiere durch verschachtelte Keys (z.B. 'nav.dashboard')
    keys = key.split('.')
    value = translations
    
    try:
        for k in keys:
            value = value[k]
        
        # Wenn value ein String ist, formatiere ihn mit kwargs falls vorhanden
        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                # Wenn ein Platzhalter fehlt, gib den formatierten String zurück
                return value
        
        return value
    except (KeyError, TypeError):
        # Fallback: Versuche Default-Sprache
        if lang != DEFAULT_LANGUAGE:
            return translate(key, DEFAULT_LANGUAGE, **kwargs)
        
        # Letzter Fallback: Gib den Key zurück
        return key


def _(key, **kwargs):
    """
    Kurze Alias-Funktion für translate().
    
    Diese Funktion ist global verfügbar in Python-Code und wird
    über einen Context Processor auch in Jinja2-Templates verfügbar gemacht.
    
    Args:
        key: Übersetzungsschlüssel
        **kwargs: Platzhalter für Formatierung
    
    Returns:
        str: Übersetzter Text
    """
    return translate(key, **kwargs)


def set_language(lang):
    """
    Setzt die Sprache in der Session.
    
    Args:
        lang: Sprachcode (z.B. 'de', 'en')
    
    Returns:
        bool: True wenn erfolgreich, False wenn Sprache nicht unterstützt
    """
    if lang in SUPPORTED_LANGUAGES:
        session['lang'] = lang
        return True
    return False

