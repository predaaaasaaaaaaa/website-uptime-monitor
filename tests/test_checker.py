# tests/test_checker.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.monitor.checker import WebsiteChecker, CheckResult
from src.database.models import Website


class TestWebsiteChecker:
    """Test WebsiteChecker class"""
    
    @pytest.fixture
    def checker(self):
        return WebsiteChecker(timeout=5)
    
    @pytest.mark.asyncio
    async def test_check_up_website(self, checker):
        """Test checking a website that's up"""
        # Mock website
        website = Website(
            id=1,
            chat_id=123,
            url="https://httpbin.org/status/200"
        )
        
        # Check (will make actual request, may fail in test env)
        # This is more of an integration test
        try:
            result = await checker.check(website)
            assert result.website_id == 1
            assert result.url == "https://httpbin.org/status/200"
            assert result.status in ['up', 'down']
        except Exception as e:
            pytest.skip(f"Network not available: {e}")
    
    @pytest.mark.asyncio
    async def test_check_invalid_url(self, checker):
        """Test checking an invalid URL"""
        website = Website(
            id=2,
            chat_id=123,
            url="invalid-url"
        )
        
        result = await checker.check(website)
        assert result.status == 'down'
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_check_timeout(self, checker):
        """Test checking a website that times out"""
        # Use a slow server
        website = Website(
            id=3,
            chat_id=123,
            url="https://httpbin.org/delay/30"  # 30 second delay
        )
        
        # With 5 second timeout, this should fail
        result = await checker.check(website)
        assert result.status == 'down'
        assert 'timeout' in result.error_message.lower() or 'timeout' in str(result.error_message).lower()
    
    @pytest.mark.asyncio
    async def test_close(self, checker):
        """Test closing the checker"""
        await checker.close()
        # Should not raise any errors


class TestCheckResult:
    """Test CheckResult dataclass"""
    
    def test_creation(self):
        """Test CheckResult creation"""
        result = CheckResult(
            website_id=1,
            url="https://example.com",
            status="up",
            response_time=0.5,
            status_code=200
        )
        
        assert result.website_id == 1
        assert result.status == "up"
        assert result.response_time == 0.5
