"""
Mock Evidence Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json


class MockEvidenceRepository:
    """Mock implementation of evidence repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load evidences from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'evidences.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def get_all(self) -> List[dict]:
        """Get all evidences"""
        return self._load_data()
    
    def get_by_use_case_id(self, use_case_id: Optional[int] = None) -> List[dict]:
        """Get evidences by use case ID (None returns all)"""
        data = self._load_data()
        if use_case_id is None:
            return data
        return [
            e for e in data
            if e.get('use_case_id') == use_case_id
        ]


class MockEvaluationReportRepository:
    """Mock implementation of evaluation report repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load evaluation reports from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'evaluation_reports.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def get_all(self) -> List[dict]:
        """Get all evaluation reports"""
        return self._load_data()
    
    def get_by_use_case_id(self, use_case_id: Optional[int] = None) -> List[dict]:
        """Get evaluation reports by use case ID (None returns all)"""
        data = self._load_data()
        if use_case_id is None:
            return data
        return [
            r for r in data
            if r.get('use_case_id') == use_case_id
        ]
