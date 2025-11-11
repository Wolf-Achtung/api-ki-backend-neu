# -*- coding: utf-8 -*-
"""
services/research_html.py
-------------------------
HTML-Generierung für Research-Ergebnisse.

Usage:
    from services.research_html import items_to_html, items_to_table
    
    html = items_to_html(results, title="KI-Tools")
    table_html = items_to_table(results, headers=["Tool", "URL", "Beschreibung"])
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import html as html_lib


def items_to_html(
    items: List[Dict[str, Any]], 
    title: Optional[str] = None,
    max_snippet_length: int = 200
) -> str:
    """
    Konvertiert Result-Items zu HTML-Liste.
    
    Args:
        items: Liste von Dicts mit keys: title, url, snippet
        title: Optionaler Titel über der Liste
        max_snippet_length: Max. Länge des Snippets
        
    Returns:
        HTML-String mit <ul>-Liste
    """
    if not items:
        return "<p class='text-muted'>Keine aktuellen Einträge gefunden.</p>"
    
    html_parts = []
    
    if title:
        html_parts.append(f"<h4>{html_lib.escape(title)}</h4>")
    
    html_parts.append("<ul>")
    
    for item in items:
        title_text = html_lib.escape(item.get("title") or item.get("url") or "Ohne Titel")
        url = html_lib.escape(item.get("url") or "")
        snippet = html_lib.escape((item.get("snippet") or "")[:max_snippet_length])
        
        if snippet and len(item.get("snippet", "")) > max_snippet_length:
            snippet += "..."
        
        html_parts.append(
            f'<li>'
            f'<a href="{url}" rel="noopener noreferrer" target="_blank">{title_text}</a>'
        )
        
        if snippet:
            html_parts.append(
                f'<br><span class="small text-muted">{snippet}</span>'
            )
        
        html_parts.append('</li>')
    
    html_parts.append("</ul>")
    
    return "\n".join(html_parts)


def items_to_table(
    items: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
    columns: Optional[List[str]] = None,
    table_class: str = "table table-striped"
) -> str:
    """
    Konvertiert Result-Items zu HTML-Tabelle.
    
    Args:
        items: Liste von Dicts
        headers: Optionale Header-Labels (default: columns als Header)
        columns: Dict-Keys die als Spalten verwendet werden (default: ["title", "url"])
        table_class: CSS-Klassen für <table>-Tag
        
    Returns:
        HTML-String mit <table>
    """
    if not items:
        return "<p class='text-muted'>Keine Einträge vorhanden.</p>"
    
    # Default columns
    if columns is None:
        columns = ["title", "url"]
    
    # Default headers = columns
    if headers is None:
        headers = [col.replace("_", " ").title() for col in columns]
    
    html_parts = [f'<table class="{table_class}">']
    
    # Header
    html_parts.append("<thead><tr>")
    for header in headers:
        html_parts.append(f"<th>{html_lib.escape(header)}</th>")
    html_parts.append("</tr></thead>")
    
    # Body
    html_parts.append("<tbody>")
    for item in items:
        html_parts.append("<tr>")
        
        for col in columns:
            value = item.get(col, "")
            
            # Special handling für URLs
            if col == "url" and value:
                cell_html = f'<a href="{html_lib.escape(value)}" rel="noopener noreferrer" target="_blank">Link</a>'
            else:
                # Kürze lange Texte
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                cell_html = html_lib.escape(str(value))
            
            html_parts.append(f"<td>{cell_html}</td>")
        
        html_parts.append("</tr>")
    html_parts.append("</tbody>")
    
    html_parts.append("</table>")
    
    return "\n".join(html_parts)


def create_empty_message(message: str = "Keine Ergebnisse gefunden") -> str:
    """
    Erstellt HTML für leere Ergebnisse.
    
    Args:
        message: Nachricht die angezeigt werden soll
        
    Returns:
        HTML-String mit Info-Alert
    """
    return f'<div class="alert alert-info">{html_lib.escape(message)}</div>'


def create_error_message(error: str) -> str:
    """
    Erstellt HTML für Fehler-Meldung.
    
    Args:
        error: Fehlermeldung
        
    Returns:
        HTML-String mit Error-Alert
    """
    return f'<div class="alert alert-danger">Fehler: {html_lib.escape(error)}</div>'


def create_loading_message(message: str = "Daten werden geladen...") -> str:
    """
    Erstellt HTML für Loading-State.
    
    Args:
        message: Nachricht während des Ladens
        
    Returns:
        HTML-String mit Spinner
    """
    return f'''
    <div class="text-center py-4">
        <div class="spinner-border" role="status">
            <span class="sr-only">{html_lib.escape(message)}</span>
        </div>
        <p class="mt-2">{html_lib.escape(message)}</p>
    </div>
    '''
