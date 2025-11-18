# -*- coding: utf-8 -*-
"""
Knowledge Base Loader für KI-Sicherheit.jetzt
Lädt strukturierte KB-Inhalte aus JSON-Dateien und stellt sie für Prompts bereit.

Basiert auf: optimierungskonzept_v2.md, Teil 7.2
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)


class KnowledgeBaseLoader:
    """Lädt und verwaltet KB-Inhalte aus JSON-Dateien"""
    
    def __init__(self, kb_dir: str = "knowledge_base"):
        """
        Args:
            kb_dir: Verzeichnis mit KB-JSON-Dateien
        """
        self.kb_dir = Path(kb_dir)
        self._cache: Dict[str, Any] = {}
        
        if not self.kb_dir.exists():
            log.warning(f"KB directory not found: {self.kb_dir}")
    
    def load_kb_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Lädt eine einzelne KB-JSON-Datei.
        
        Args:
            filename: Name der JSON-Datei (z.B. "four_pillars.json")
            
        Returns:
            Dict mit KB-Inhalten oder None bei Fehler
        """
        # Cache-Check
        if filename in self._cache:
            cached_data = self._cache[filename]
            return cached_data if isinstance(cached_data, dict) else None
        
        file_path = self.kb_dir / filename
        
        if not file_path.exists():
            log.warning(f"KB file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return None

            self._cache[filename] = data
            log.debug(f"Loaded KB: {filename}")
            return data
            
        except Exception as exc:
            log.error(f"Failed to load KB file {filename}: {exc}")
            return None
    
    def get_four_pillars(self) -> Dict[str, Any]:
        """Lädt die 4 Säulen der KI-Einführung"""
        return self.load_kb_file("four_pillars.json") or {
            "title": "4 Säulen der KI-Einführung",
            "pillars": []
        }
    
    def get_legal_pitfalls(self) -> Dict[str, Any]:
        """Lädt die Legal Pitfalls (10-Punkte-Checkliste)"""
        return self.load_kb_file("legal_pitfalls.json") or {
            "title": "Legal Pitfalls",
            "checklist": []
        }
    
    def get_three_phase_model(self) -> Dict[str, Any]:
        """Lädt das 3-Phasen-Modell (Test → Pilot → Rollout)"""
        return self.load_kb_file("three_phase_model.json") or {
            "title": "3-Phasen-Modell",
            "phases": []
        }
    
    def get_roi_framework(self) -> Dict[str, Any]:
        """Lädt das ROI-Framework"""
        return self.load_kb_file("roi_framework.json") or {
            "title": "ROI-Framework",
            "components": []
        }
    
    def get_ten_20_70(self) -> Dict[str, Any]:
        """Lädt die 10-20-70-Formel"""
        return self.load_kb_file("ten_20_70.json") or {
            "title": "10-20-70 Formel",
            "breakdown": {}
        }
    
    def get_stakeholder_matrix(self) -> Dict[str, Any]:
        """Lädt die Stakeholder-Matrix"""
        return self.load_kb_file("stakeholder_matrix.json") or {
            "title": "Stakeholder-Matrix",
            "quadrants": []
        }
    
    def get_quick_win_matrix(self) -> Dict[str, Any]:
        """Lädt die Quick-Win-Matrix (Impact/Aufwand)"""
        return self.load_kb_file("quick_win_matrix.json") or {
            "title": "Quick-Win-Matrix",
            "criteria": []
        }
    
    def get_all_kb_for_prompt(self, section_name: str) -> Dict[str, Any]:
        """
        Lädt alle relevanten KB-Inhalte für einen bestimmten Prompt.
        
        Args:
            section_name: Name der Section (z.B. "quick_wins", "roadmap")
            
        Returns:
            Dict mit allen relevanten KB-Inhalten in UPPERCASE Keys
        """
        # Mapping: Section → benötigte KB-Dateien
        section_kb_mapping = {
            "executive_summary": [
                "four_pillars", "vision_framework", "wertversprechen"
            ],
            "quick_wins": [
                "three_phase_model", "roi_framework", "quick_win_matrix"
            ],
            "roadmap": [
                "three_phase_model", "ten_20_70", "stakeholder_matrix"
            ],
            "risks": [
                "legal_pitfalls", "dsgvo_basics", "eu_ai_act"
            ],
            "compliance": [
                "legal_pitfalls", "dsgvo_basics", "eu_ai_act"
            ],
            "business": [
                "roi_framework", "zeitgewinn_calc", "sensitivitaet"
            ],
            "recommendations": [
                "four_pillars", "ten_20_70", "kmu_spezifika"
            ],
            "data_readiness": [
                "data_strategy", "quality_dimensions", "etl_elt"
            ],
            "org_change": [
                "stakeholder_matrix", "change_principles", "skill_programs"
            ],
            "pilot_plan": [
                "three_phase_model", "deliverables", "acceptance_criteria"
            ],
            "gamechanger": [
                "vision_framework", "wertversprechen", "transferpotenzial"
            ],
            "costs_overview": [
                "capex_opex", "tco_analysis", "break_even"
            ],
        }
        
        kb_files = section_kb_mapping.get(section_name, [])
        result: Dict[str, Any] = {}
        
        for kb_name in kb_files:
            kb_data = self.load_kb_file(f"{kb_name}.json")
            if kb_data:
                # Konvertiere zu UPPERCASE Key für Template
                key = f"KB_{kb_name.upper()}_JSON"
                result[key] = kb_data
        
        return result
    
    def get_consolidated_kb(self) -> Dict[str, Any]:
        """
        Lädt alle wichtigen KB-Inhalte auf einmal (für Performance).
        
        Returns:
            Dict mit allen KB-Inhalten in UPPERCASE Keys
        """
        kb_files = [
            "four_pillars",
            "legal_pitfalls",
            "three_phase_model",
            "roi_framework",
            "ten_20_70",
            "stakeholder_matrix",
            "quick_win_matrix",
            "vision_framework",
            "wertversprechen",
            "dsgvo_basics",
            "eu_ai_act",
            "kmu_spezifika",
        ]
        
        result: Dict[str, Any] = {}
        
        for kb_name in kb_files:
            kb_data = self.load_kb_file(f"{kb_name}.json")
            if kb_data:
                key = f"KB_{kb_name.upper()}_JSON"
                result[key] = kb_data
        
        return result


# Globale Instanz (Singleton-Pattern)
_kb_loader: Optional[KnowledgeBaseLoader] = None


def get_kb_loader(kb_dir: str = "knowledge_base") -> KnowledgeBaseLoader:
    """
    Gibt die globale KB-Loader-Instanz zurück (Singleton).
    
    Args:
        kb_dir: Verzeichnis mit KB-JSON-Dateien (nur beim ersten Aufruf relevant)
        
    Returns:
        KnowledgeBaseLoader Instanz
    """
    global _kb_loader
    if _kb_loader is None:
        _kb_loader = KnowledgeBaseLoader(kb_dir)
    return _kb_loader


# Convenience-Funktionen für häufig verwendete KB-Inhalte
def get_kb_for_section(section_name: str) -> Dict[str, Any]:
    """Lädt alle relevanten KB-Inhalte für einen Prompt"""
    loader = get_kb_loader()
    return loader.get_all_kb_for_prompt(section_name)


def get_all_kb() -> Dict[str, Any]:
    """Lädt alle KB-Inhalte auf einmal (Performance-Optimierung)"""
    loader = get_kb_loader()
    return loader.get_consolidated_kb()
