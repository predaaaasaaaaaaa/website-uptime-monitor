# src/database/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    chat_id: int
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Website:
    id: Optional[int]
    chat_id: int
    url: str
    name: Optional[str] = None
    enabled: bool = True
    last_status: Optional[str] = None
    last_checked: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.name is None:
            self.name = self.url


@dataclass
class History:
    id: Optional[int]
    website_id: int
    status: str  # 'up' or 'down'
    response_time: Optional[float] = None  # in seconds
    error_message: Optional[str] = None
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.now()
