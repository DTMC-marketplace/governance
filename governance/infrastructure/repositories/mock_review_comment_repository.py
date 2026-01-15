"""
Mock Review Comment Repository Implementation
"""
from typing import List, Optional
from pathlib import Path
import json


class MockReviewCommentRepository:
    """Mock implementation of review comment repository"""
    
    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._cache = None
    
    def _load_data(self) -> List[dict]:
        """Load review comments from JSON file"""
        if self._cache is None:
            filepath = self._data_dir / 'review_comments.json'
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            else:
                self._cache = []
        return self._cache
    
    def get_all(self) -> List[dict]:
        """Get all review comments"""
        return self._load_data()
    
    def get_by_use_case_id(self, use_case_id: Optional[int] = None) -> List[dict]:
        """Get review comments by use case ID (None returns all)"""
        data = self._load_data()
        if use_case_id is None:
            return data
        return [
            c for c in data
            if c.get('use_case_id') == use_case_id
        ]
