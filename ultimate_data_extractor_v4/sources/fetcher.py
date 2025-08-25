import asyncio
import random
import re
from typing import Any, Dict, List, Optional

try:
    import aiohttp  # type: ignore
except Exception:  # pragma: no cover
    aiohttp = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

from ..infrastructure.rate_limit import RateLimitManager
from ..models.source_models import ContentType, EnhancedDataSource


class Fetcher:
    def __init__(self, max_concurrent: int = 16):
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None if aiohttp else None
        self.rate_limiter = RateLimitManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def __aenter__(self):
        if aiohttp:
            connector = aiohttp.TCPConnector(limit=self.max_concurrent, limit_per_host=8)
            timeout = aiohttp.ClientTimeout(total=60, connect=20)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def fetch_content(self, url: str, source: EnhancedDataSource) -> Optional[Dict[str, Any]]:
        await self.rate_limiter.wait_if_needed(source.name, source.rate_limit)
        content_type = self._detect_content_type_from_url(url)

        if not self.session or not aiohttp:
            return {"content": "", "success": False, "error": "HTTP client unavailable"}

        try:
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": self._get_accept_header(content_type),
                "Accept-Language": "en-US,en;q=0.9",
            }
            async with self.session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {"content": "", "success": False, "error": f"HTTP {resp.status}"}

                if content_type == ContentType.JSON or "application/json" in (resp.headers.get("Content-Type") or ""):
                    text = await resp.text()
                    return {"content": text, "content_type": ContentType.JSON, "success": True}

                if content_type in (ContentType.PDF, ContentType.EXCEL, ContentType.CSV):
                    data = await resp.read()
                    return {"content": data, "content_type": content_type, "success": True, "binary": True}

                html = await resp.text()
                return {
                    "content": self._extract_text_from_html(html),
                    "title": self._extract_title_from_html(html),
                    "content_type": ContentType.HTML,
                    "success": True,
                }
        except asyncio.TimeoutError:
            return {"content": "", "success": False, "error": "Timeout"}
        except Exception as e:
            return {"content": "", "success": False, "error": str(e)}

    @staticmethod
    def _detect_content_type_from_url(url: str) -> ContentType:
        u = url.lower()
        if u.endswith(".pdf"):
            return ContentType.PDF
        if u.endswith((".xlsx", ".xls")):
            return ContentType.EXCEL
        if u.endswith(".csv"):
            return ContentType.CSV
        if u.endswith(".json"):
            return ContentType.JSON
        if "api" in u and ("json" in u or "data" in u):
            return ContentType.API
        return ContentType.HTML

    @staticmethod
    def _get_accept_header(content_type: ContentType) -> str:
        if content_type == ContentType.JSON:
            return "application/json"
        if content_type == ContentType.CSV:
            return "text/csv"
        if content_type == ContentType.XML:
            return "application/xml"
        return "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        if not BeautifulSoup:
            return re.sub(r"<[^>]+>", " ", html)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "menu",
            "form",
            "input",
            "button",
            "iframe",
            "noscript",
            "meta",
            "link",
        ]):
            try:
                tag.decompose()
            except Exception:
                pass
        text = soup.get_text(separator=" ", strip=True)
        lines: List[str] = []
        for line in text.splitlines():
            cleaned = re.sub(r"\s+", " ", line.strip())
            if cleaned and len(cleaned) > 3:
                lines.append(cleaned)
        return "\n".join(lines)

    @staticmethod
    def _extract_title_from_html(html: str) -> str:
        if not BeautifulSoup:
            return "Extracted Content"
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text().strip()
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text().strip()
        return "Extracted Content"

