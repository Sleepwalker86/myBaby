"""
Route für Sprachwechsel (i18n)
"""
from flask import Blueprint, redirect, request, session, url_for
from app.i18n import set_language, SUPPORTED_LANGUAGES

bp = Blueprint('i18n', __name__)


@bp.route('/set-language/<lang>')
def set_lang(lang):
    """
    Setzt die Sprache und leitet zur vorherigen Seite zurück.
    
    Args:
        lang: Sprachcode (z.B. 'de', 'en')
    
    Returns:
        redirect: Zurück zur vorherigen Seite oder zur Startseite
    """
    # Validiere Sprache
    if lang in SUPPORTED_LANGUAGES:
        set_language(lang)
    
    # Zurück zur vorherigen Seite oder zur Startseite
    referer = request.referrer
    if referer:
        return redirect(referer)
    return redirect(url_for('main.index'))

