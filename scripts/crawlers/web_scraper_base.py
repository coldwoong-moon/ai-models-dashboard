import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import re
from playwright.async_api import async_playwright
import time

class WebScraperBase(ABC):
    """웹 스크래핑을 위한 베이스 클래스"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.session = None
        self.browser = None
        self.context = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
    
    async def fetch_html(self, url: str, use_playwright: bool = False, wait_selector: str = None) -> str:
        """HTML 페이지 가져오기"""
        if use_playwright:
            return await self.fetch_with_playwright(url, wait_selector=wait_selector)
        else:
            return await self.fetch_with_aiohttp(url)
    
    async def fetch_with_aiohttp(self, url: str) -> str:
        """aiohttp를 사용하여 페이지 가져오기"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        async with self.session.get(url, headers=headers) as response:
            return await response.text()
    
    async def fetch_with_playwright(self, url: str, wait_selector: str = None) -> str:
        """Playwright를 사용하여 JavaScript 렌더링 페이지 가져오기"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
        
        page = await self.context.new_page()
        await page.goto(url, wait_until='networkidle')
        
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000, state='attached')
            except Exception as e:
                print(f"Warning: Timeout waiting for selector '{wait_selector}'")
        else:
            # 페이지가 완전히 로드될 때까지 대기
            await page.wait_for_timeout(3000)
        
        content = await page.content()
        await page.close()
        
        return content
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """HTML 파싱"""
        return BeautifulSoup(html, 'html.parser')
    
    def extract_json_from_script(self, soup: BeautifulSoup, pattern: str) -> Optional[Dict]:
        """스크립트 태그에서 JSON 데이터 추출"""
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and pattern in script.string:
                # JSON 데이터 추출 시도
                match = re.search(r'{[^{}]*}', script.string)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        continue
        
        return None
    
    def clean_price_string(self, price_str: str) -> float:
        """가격 문자열을 숫자로 변환"""
        # 예: "$2.50 / 1M tokens" -> 2.50
        # "€1,234.56" -> 1234.56
        if not price_str:
            return 0.0
            
        # 통화 기호 및 텍스트 제거
        price_str = re.sub(r'[^\d.,]', '', price_str)
        
        # 콤마를 소수점으로 변환 (유럽 형식 처리)
        if ',' in price_str and '.' not in price_str:
            price_str = price_str.replace(',', '.')
        else:
            # 천 단위 구분자 제거
            price_str = price_str.replace(',', '')
        
        try:
            return float(price_str)
        except ValueError:
            return 0.0
    
    def extract_context_window(self, text: str) -> int:
        """텍스트에서 컨텍스트 윈도우 크기 추출"""
        # 패턴: "128K", "1M", "200,000", "200K tokens" 등
        patterns = [
            r'(\d+(?:,\d+)?)\s*[Kk](?:\s*tokens)?',  # 128K, 128k tokens
            r'(\d+(?:,\d+)?)\s*[Mm](?:\s*tokens)?',  # 1M, 1m tokens
            r'(\d+(?:,\d+)?)\s*tokens',              # 128000 tokens
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group(1).replace(',', '')
                num = int(num_str)
                
                if 'k' in match.group(0).lower():
                    return num * 1000
                elif 'm' in match.group(0).lower():
                    return num * 1000000
                else:
                    return num
        
        return 0
    
    @abstractmethod
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """각 제공업체의 모델 정보 스크래핑 (구현 필요)"""
        pass
    
    @abstractmethod
    async def scrape_pricing(self) -> Dict[str, Dict[str, float]]:
        """각 제공업체의 가격 정보 스크래핑 (구현 필요)"""
        pass