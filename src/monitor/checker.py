# src/monitor/checker.py
import httpx
import logging
from dataclasses import dataclass
from typing import Optional

import config
from src.database import Website

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a website check"""
    website_id: int
    url: str
    status: str  # 'up' or 'down'
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None


class WebsiteChecker:
    """Website uptime checker"""
    
    def __init__(self, timeout: int = None):
        self.timeout = timeout or config.REQUEST_TIMEOUT_SECONDS
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Website-Uptime-Monitor/1.0'
            }
        )
    
    async def check(self, website: Website) -> CheckResult:
        """Check if website is up"""
        try:
            logger.debug(f"Checking {website.url}")
            
            # Use HEAD request for faster checking
            response = await self.client.head(website.url)
            
            response_time = response.elapsed.total_seconds()
            
            # Consider up if status code is 2xx
            if 200 <= response.status_code < 300:
                status = 'up'
                error_message = None
            else:
                status = 'down'
                error_message = f"HTTP {response.status_code}"
            
            logger.info(f"{website.url}: {status} ({response.status_code}) - {response_time:.2f}s")
            
            return CheckResult(
                website_id=website.id,
                url=website.url,
                status=status,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_message
            )
            
        except httpx.TimeoutException:
            logger.warning(f"{website.url}: timeout after {self.timeout}s")
            return CheckResult(
                website_id=website.id,
                url=website.url,
                status='down',
                error_message=f"Timeout after {self.timeout}s"
            )
            
        except httpx.RequestError as e:
            logger.warning(f"{website.url}: request error - {e}")
            return CheckResult(
                website_id=website.id,
                url=website.url,
                status='down',
                error_message=str(e)
            )
        
        except Exception as e:
            logger.error(f"{website.url}: unexpected error - {e}")
            return CheckResult(
                website_id=website.id,
                url=website.url,
                status='down',
                error_message=str(e)
            )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
