#!/usr/bin/env python3
"""
Systematisches Code-Audit für KI-Backend
Prüft auf häufige Fehlerquellen BEVOR sie in Production landen.

Nutzung:
  python scripts/code_audit.py

Exit-Codes:
  0 = Keine Probleme
  1 = Errors gefunden
  2 = Critical Issues gefunden
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set

class CodeAuditor:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.issues: List[Tuple[str, str, int, str]] = []
        self.files_checked = 0
        
    def add_issue(self, severity: str, file: str, line: int, message: str):
        self.issues.append((severity, file, line, message))
    
    def get_python_files(self) -> List[Path]:
        exclude_dirs = {'venv', '.venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
        files = []
        for py_file in self.root_dir.rglob("*.py"):
            if not any(ex in py_file.parts for ex in exclude_dirs):
                files.append(py_file)
        return sorted(files)
    
    def check_syntax(self, filepath: Path) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
            return True
        except SyntaxError as e:
            self.add_issue("CRITICAL", str(filepath), e.lineno or 0, f"SyntaxError: {e.msg}")
            return False
        except Exception as e:
            self.add_issue("ERROR", str(filepath), 0, f"Parse error: {e}")
            return False
    
    def check_orphan_regex_lines(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            return
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"^\s+r'\\b\w+.*'\s*,?\s*(#.*)?$", line):
                prev_line = lines[i-2].strip() if i > 1 else ""
                if not prev_line.endswith(('[', '(', ',')) and '=' not in prev_line:
                    self.add_issue("ERROR", str(filepath), i, 
                        f"Verwaiste Regex-Zeile: {stripped[:60]}...")
    
    def check_duplicate_lines(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            return
        
        prev_line = ""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and stripped == prev_line and len(stripped) > 30:
                if not stripped.startswith('#') and not stripped.startswith('"') and not stripped.startswith("'"):
                    self.add_issue("WARNING", str(filepath), i, f"Duplizierte Zeile: {stripped[:50]}...")
            prev_line = stripped
    
    def check_common_typos(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            return
        
        typos = [
            (r'\bimoprt\b', 'import'), (r'\bretrun\b', 'return'), (r'\bexcpet\b', 'except'),
            (r'\bTreu\b', 'True'), (r'\bFlase\b', 'False'), (r'\bNoen\b', 'None'), (r'\bpritn\b', 'print'),
        ]
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                continue
            for pattern, correct in typos:
                if re.search(pattern, line):
                    self.add_issue("ERROR", str(filepath), i, f"Tippfehler: sollte '{correct}' sein")
    
    def check_indentation_issues(self, filepath: Path):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except:
            return
        
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith('#'):
                leading = line[:len(line) - len(line.lstrip())]
                if '\t' in leading and ' ' in leading:
                    self.add_issue("ERROR", str(filepath), i, "Gemischte Tabs und Spaces")
    
    def run_full_audit(self) -> Dict:
        print("=" * 60)
        print("🔍 KI-Backend Code Audit")
        print("=" * 60)
        
        py_files = self.get_python_files()
        print(f"\n📁 {len(py_files)} Python-Dateien gefunden\n")
        
        for filepath in py_files:
            self.files_checked += 1
            if not self.check_syntax(filepath):
                continue
            self.check_orphan_regex_lines(filepath)
            self.check_duplicate_lines(filepath)
            self.check_common_typos(filepath)
            self.check_indentation_issues(filepath)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        critical = [i for i in self.issues if i[0] == "CRITICAL"]
        errors = [i for i in self.issues if i[0] == "ERROR"]
        warnings = [i for i in self.issues if i[0] == "WARNING"]
        
        print("\n" + "=" * 60)
        print("📊 AUDIT ERGEBNIS")
        print("=" * 60)
        print(f"\n✅ Dateien geprüft: {self.files_checked}")
        print(f"🔴 CRITICAL: {len(critical)}")
        print(f"🟠 ERROR: {len(errors)}")
        print(f"🟡 WARNING: {len(warnings)}")
        
        if critical:
            print("\n🔴 CRITICAL ISSUES:")
            for sev, file, line, msg in critical:
                print(f"  {file}:{line} - {msg}")
        
        if errors:
            print("\n🟠 ERRORS:")
            for sev, file, line, msg in errors:
                print(f"  {file}:{line} - {msg}")
        
        if warnings:
            print("\n🟡 WARNINGS:")
            for sev, file, line, msg in warnings[:20]:
                print(f"  {file}:{line} - {msg}")
            if len(warnings) > 20:
                print(f"  ... und {len(warnings) - 20} weitere")
        
        if not self.issues:
            print("\n✅ Keine Probleme gefunden!")
        
        return {"files_checked": self.files_checked, "critical": len(critical), "errors": len(errors), "warnings": len(warnings)}

if __name__ == "__main__":
    auditor = CodeAuditor(".")
    result = auditor.run_full_audit()
    sys.exit(2 if result["critical"] > 0 else 1 if result["errors"] > 0 else 0)
