# tests/test_database.py
import pytest
import os
import tempfile
from datetime import datetime

from src.database import DatabaseRepository, User, Website, History


class TestDatabaseRepository:
    """Test DatabaseRepository class"""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        db = DatabaseRepository(path)
        yield db
        
        # Cleanup
        os.unlink(path)
    
    def test_user_operations(self, db):
        """Test user add/get operations"""
        # Add user
        user = db.add_user(12345)
        assert user.chat_id == 12345
        assert user.created_at is not None
        
        # Get user
        user2 = db.get_user(12345)
        assert user2 is not None
        assert user2.chat_id == 12345
        
        # Get non-existent user
        user3 = db.get_user(99999)
        assert user3 is None
    
    def test_website_operations(self, db):
        """Test website add/get/remove operations"""
        chat_id = 12345
        
        # Add website
        website = db.add_website(chat_id, "https://example.com", "Example")
        assert website.id is not None
        assert website.url == "https://example.com"
        assert website.name == "Example"
        assert website.enabled is True
        
        # Get user's websites
        websites = db.get_user_websites(chat_id)
        assert len(websites) == 1
        assert websites[0].url == "https://example.com"
        
        # Get website by URL
        website2 = db.get_website_by_url(chat_id, "https://example.com")
        assert website2 is not None
        assert website2.id == website.id
        
        # Remove website
        removed = db.remove_website(chat_id, "https://example.com")
        assert removed is True
        
        # Verify removed
        websites = db.get_user_websites(chat_id)
        assert len(websites) == 0
    
    def test_history_operations(self, db):
        """Test history add/get operations"""
        chat_id = 12345
        
        # Add website first
        website = db.add_website(chat_id, "https://example.com")
        
        # Add history
        history = db.add_history(
            website_id=website.id,
            status="up",
            response_time=0.5
        )
        assert history.id is not None
        assert history.status == "up"
        assert history.response_time == 0.5
        
        # Get history
        history_list = db.get_website_history(website.id)
        assert len(history_list) == 1
        assert history_list[0].status == "up"
    
    def test_website_status_update(self, db):
        """Test updating website status"""
        chat_id = 12345
        website = db.add_website(chat_id, "https://example.com")
        
        # Add history
        db.add_history(website.id, "up", 0.5)
        
        # Update website status
        db.update_website_status(website.id, "up")
        
        # Get updated website
        updated = db.get_website(website.id)
        assert updated.last_status == "up"
    
    def test_get_all_websites(self, db):
        """Test getting all enabled websites"""
        # Add websites for different users
        db.add_user(111)
        db.add_user(222)
        
        db.add_website(111, "https://site1.com")
        db.add_website(222, "https://site2.com")
        
        # Get all websites
        all_websites = db.get_all_websites()
        assert len(all_websites) == 2
    
    def test_last_status(self, db):
        """Test getting last status"""
        chat_id = 12345
        website = db.add_website(chat_id, "https://example.com")
        
        # No history yet
        last = db.get_website_last_status(website.id)
        assert last is None
        
        # Add history
        db.add_history(website.id, "up", 0.5)
        last = db.get_website_last_status(website.id)
        assert last == "up"
        
        # Add more history
        db.add_history(website.id, "down", None, "Connection error")
        last = db.get_website_last_status(website.id)
        assert last == "down"
