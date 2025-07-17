#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import asyncio
from typing import Dict, List, Any
from crawlers.web_scraper_base import WebScraperBase
from crawlers.base_crawler import BaseCrawler
import re
from datetime import datetime

class OpenAIWebScraper(WebScraperBase):
    """OpenAI 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('openai')
        self.pricing_url = "https://openai.com/api/pricing/"
        self.models_url = "https://platform.openai.com/docs/models"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """OpenAI 모델 정보 스크래핑"""
        models = []
        
        try:
            # 가격 페이지에서 모델 정보 추출
            html = await self.fetch_html(self.pricing_url, use_playwright=True)
            soup = self.parse_html(html)
            
            # 가격 테이블 찾기
            pricing_sections = soup.find_all(['section', 'div'], class_=re.compile('pricing|model'))
            
            for section in pricing_sections:
                # 모델 카드 찾기
                model_cards = section.find_all(['div', 'article'], class_=re.compile('card|model|pricing-item'))
                
                for card in model_cards:
                    model_data = await self.extract_model_from_card(card)
                    if model_data:
                        models.append(model_data)
            
            # 테이블 형태의 가격 정보도 확인
            tables = soup.find_all('table')
            for table in tables:
                table_models = await self.extract_models_from_table(table)
                models.extend(table_models)
        
        except Exception as e:
            print(f"Web scraping failed: {e}, using fallback data")
            
        # 스크래핑 실패 시 기본 데이터 사용
        if not models:
            models = self.get_fallback_models()
        
        return models
    
    async def extract_model_from_card(self, card) -> Dict[str, Any]:
        """카드 요소에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름
        name_elem = card.find(['h2', 'h3', 'h4', 'div'], class_=re.compile('title|name|heading'))
        if name_elem:
            model_data['name'] = name_elem.get_text(strip=True)
            model_data['id'] = self.name_to_id(model_data['name'])
        
        # 설명
        desc_elem = card.find(['p', 'div'], class_=re.compile('description|subtitle'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 가격 정보
        price_elems = card.find_all(['span', 'div'], class_=re.compile('price|cost'))
        prices = []
        for elem in price_elems:
            price_text = elem.get_text(strip=True)
            if '$' in price_text:
                prices.append(self.clean_price_string(price_text))
        
        if len(prices) >= 2:
            model_data['input_price'] = prices[0]
            model_data['output_price'] = prices[1]
        
        # 컨텍스트 윈도우
        context_elem = card.find(text=re.compile(r'\d+[KkMm]\s*(?:tokens|context)', re.I))
        if context_elem:
            model_data['context_window'] = self.extract_context_window(str(context_elem))
        
        # 기능 추출
        model_data['features'] = self.extract_features_from_element(card)
        
        return model_data if 'id' in model_data else None
    
    async def extract_models_from_table(self, table) -> List[Dict[str, Any]]:
        """테이블에서 모델 정보 추출"""
        models = []
        rows = table.find_all('tr')
        
        # 헤더 찾기
        headers = []
        header_row = table.find('thead')
        if header_row:
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        elif rows:
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
            rows = rows[1:]
        
        # 데이터 행 파싱
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
                
            model_data = {}
            
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                
                if i < len(headers):
                    header = headers[i]
                    
                    if 'model' in header or i == 0:
                        model_data['name'] = text
                        model_data['id'] = self.name_to_id(text)
                    elif 'input' in header:
                        model_data['input_price'] = self.clean_price_string(text)
                    elif 'output' in header:
                        model_data['output_price'] = self.clean_price_string(text)
                    elif 'context' in header or 'token' in header:
                        model_data['context_window'] = self.extract_context_window(text)
            
            if 'id' in model_data and model_data.get('input_price', 0) > 0:
                # 기본값 추가
                model_data['description'] = self.get_default_description(model_data['id'])
                model_data['features'] = self.get_default_features(model_data['id'])
                model_data['status'] = self.determine_status(model_data['id'])
                models.append(model_data)
        
        return models
    
    async def scrape_pricing(self) -> Dict[str, Dict[str, float]]:
        """가격 정보만 스크래핑"""
        pricing = {}
        models = await self.scrape_models()
        
        for model in models:
            if 'id' in model and 'input_price' in model:
                pricing[model['id']] = {
                    'input': model.get('input_price', 0),
                    'output': model.get('output_price', 0)
                }
        
        return pricing
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        # 예: "GPT-4o" -> "gpt-4o"
        id_map = {
            'GPT-4o': 'gpt-4o',
            'GPT-4o mini': 'gpt-4o-mini',
            'GPT-4 Turbo': 'gpt-4-turbo',
            'GPT-4': 'gpt-4',
            'GPT-3.5 Turbo': 'gpt-3.5-turbo',
            'o1-preview': 'o1-preview',
            'o1-mini': 'o1-mini'
        }
        
        return id_map.get(name, name.lower().replace(' ', '-'))
    
    def extract_features_from_element(self, element) -> List[str]:
        """요소에서 기능 추출"""
        features = []
        text = element.get_text().lower()
        
        feature_keywords = {
            'vision': ['vision', 'image', 'visual'],
            'function-calling': ['function', 'tools'],
            'json-mode': ['json', 'structured'],
            'reasoning': ['reasoning', 'think', 'o1'],
            'fast': ['fast', 'quick', 'speed', 'mini'],
            'chat': ['chat', 'conversation'],
            'coding': ['code', 'programming']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature)
        
        return features if features else ['chat']
    
    def get_default_description(self, model_id: str) -> str:
        """기본 설명 반환"""
        descriptions = {
            'gpt-4o': 'Most capable model with multimodal abilities',
            'gpt-4o-mini': 'Affordable small model for fast tasks',
            'o1-preview': 'Reasoning model for complex tasks',
            'o1-mini': 'Fast reasoning model for coding',
            'gpt-4-turbo': 'High-intelligence model',
            'gpt-4': 'Advanced model for complex tasks',
            'gpt-3.5-turbo': 'Fast model for simple tasks'
        }
        
        return descriptions.get(model_id, 'OpenAI language model')
    
    def get_default_features(self, model_id: str) -> List[str]:
        """기본 기능 반환"""
        features_map = {
            'gpt-4o': ['chat', 'vision', 'function-calling', 'json-mode'],
            'gpt-4o-mini': ['chat', 'vision', 'function-calling', 'fast'],
            'o1-preview': ['reasoning', 'complex-tasks'],
            'o1-mini': ['reasoning', 'coding', 'fast'],
            'gpt-4-turbo': ['chat', 'vision', 'function-calling'],
            'gpt-4': ['chat', 'function-calling'],
            'gpt-3.5-turbo': ['chat', 'function-calling', 'fast']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'preview' in model_id:
            return 'preview'
        elif any(old in model_id for old in ['0301', '0314']):
            return 'deprecated'
        else:
            return 'ga'
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델 데이터 (2025년 1월 최신)"""
        return [
            {
                'id': 'gpt-4o',
                'name': 'GPT-4o',
                'description': 'Most capable multimodal model with vision and advanced reasoning',
                'input_price': 2.50,
                'output_price': 10.00,
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode', 'multimodal'],
                'status': 'ga'
            },
            {
                'id': 'gpt-4o-mini',
                'name': 'GPT-4o mini',
                'description': 'Affordable multimodal model with vision capabilities',
                'input_price': 0.15,
                'output_price': 0.60,
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode', 'fast', 'multimodal'],
                'status': 'ga'
            },
            {
                'id': 'o1',
                'name': 'o1',
                'description': 'Advanced reasoning model for complex problem-solving',
                'input_price': 15.00,
                'output_price': 60.00,
                'context_window': 200000,
                'max_output': 100000,
                'features': ['reasoning', 'complex-tasks', 'thinking', 'math', 'coding'],
                'status': 'ga'
            },
            {
                'id': 'o1-mini',
                'name': 'o1-mini',
                'description': 'Fast reasoning model optimized for coding and STEM',
                'input_price': 3.00,
                'output_price': 12.00,
                'context_window': 128000,
                'max_output': 65536,
                'features': ['reasoning', 'coding', 'fast', 'thinking', 'math', 'stem'],
                'status': 'ga'
            },
            {
                'id': 'gpt-4-turbo',
                'name': 'GPT-4 Turbo',
                'description': 'Previous generation high-intelligence model with vision',
                'input_price': 10.00,
                'output_price': 30.00,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'status': 'ga'
            },
            {
                'id': 'gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'description': 'Fast and cost-effective model for simple tasks',
                'input_price': 0.50,
                'output_price': 1.50,
                'context_window': 16385,
                'max_output': 4096,
                'features': ['chat', 'function-calling', 'fast', 'cost-effective'],
                'status': 'ga'
            }
        ]


class OpenAICrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 OpenAI 크롤러"""
    
    def __init__(self):
        super().__init__('openai')
        self.scraper = OpenAIWebScraper()
        
    def fetch_models(self) -> List[Dict]:
        """비동기 스크래퍼를 동기적으로 실행"""
        return asyncio.run(self._fetch_models_async())
    
    async def _fetch_models_async(self) -> List[Dict]:
        """모델 정보 비동기 스크래핑"""
        async with self.scraper:
            models = await self.scraper.scrape_models()
            
            # 추가 정보 보완
            for model in models:
                # 모달리티 추가
                if 'features' in model:
                    model['modalities'] = ['text']
                    if 'vision' in model['features']:
                        model['modalities'].append('image')
                
                # 기본값 설정
                model.setdefault('max_output', 4096)
                model.setdefault('release_date', '')
                model.setdefault('status', 'ga')
                
            return models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        models = self.fetch_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return {}


if __name__ == "__main__":
    crawler = OpenAICrawlerV2()
    crawler.run()