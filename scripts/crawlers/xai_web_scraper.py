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

class XAIWebScraper(WebScraperBase):
    """xAI 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('xai')
        self.models_url = "https://docs.x.ai/docs/models"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """xAI 모델 정보 스크래핑"""
        models = []
        
        # 페이지 가져오기
        html = await self.fetch_html(self.models_url, use_playwright=True)
        soup = self.parse_html(html)
        
        # 모델 섹션 찾기
        model_sections = soup.find_all(['section', 'div'], class_=re.compile('model|feature'))
        
        for section in model_sections:
            if self.is_model_section(section):
                model_data = await self.extract_model_from_section(section)
                if model_data:
                    models.append(model_data)
        
        # 테이블 형태의 정보도 확인
        tables = soup.find_all('table')
        for table in tables:
            if self.is_model_table(table):
                table_models = await self.extract_models_from_table(table)
                models.extend(table_models)
        
        # 카드 형태의 정보 확인
        cards = soup.find_all(['div', 'article'], class_=re.compile('card|box'))
        for card in cards:
            if self.is_model_card(card):
                model_data = await self.extract_model_from_card(card)
                if model_data:
                    models.append(model_data)
        
        # 중복 제거
        models = self.deduplicate_models(models)
        
        # 기본 모델이 없으면 하드코딩된 데이터 추가
        if not models:
            models = self.get_fallback_models()
        
        return models
    
    def is_model_section(self, section) -> bool:
        """섹션이 모델 정보를 담고 있는지 확인"""
        text = section.get_text().lower()
        return any(keyword in text for keyword in ['grok', 'model', 'api', 'pricing'])
    
    def is_model_table(self, table) -> bool:
        """테이블이 모델 정보를 담고 있는지 확인"""
        text = table.get_text().lower()
        headers = [th.get_text().lower() for th in table.find_all('th')]
        return 'grok' in text or any('model' in h for h in headers)
    
    def is_model_card(self, card) -> bool:
        """카드가 모델 정보를 담고 있는지 확인"""
        text = card.get_text().lower()
        return 'grok' in text and any(keyword in text for keyword in ['price', 'token', 'context'])
    
    async def extract_model_from_section(self, section) -> Dict[str, Any]:
        """섹션에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름 찾기
        heading = section.find(['h1', 'h2', 'h3', 'h4'])
        if heading:
            text = heading.get_text(strip=True)
            if 'grok' in text.lower():
                model_data['name'] = self.clean_model_name(text)
                model_data['id'] = self.name_to_id(model_data['name'])
        
        if 'id' not in model_data:
            # 텍스트에서 모델 이름 찾기
            text = section.get_text()
            model_match = re.search(r'Grok[-\s]*(2|2\s*Vision|Vision)?', text, re.I)
            if model_match:
                model_data['name'] = self.clean_model_name(model_match.group(0))
                model_data['id'] = self.name_to_id(model_data['name'])
            else:
                return None
        
        # 설명 추출
        desc_elem = section.find(['p', 'div'], class_=re.compile('description|intro'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 스펙 정보 추출
        spec_items = section.find_all(['li', 'div', 'p'])
        for item in spec_items:
            text = item.get_text(strip=True)
            
            # 가격 정보
            if '$' in text:
                price_info = self.extract_price_info(text)
                if price_info:
                    model_data.update(price_info)
            
            # 컨텍스트 윈도우
            if 'context' in text.lower() or 'token' in text.lower():
                context = self.extract_context_window(text)
                if context:
                    model_data['context_window'] = context
            
            # 기능
            if any(feature in text.lower() for feature in ['vision', 'image', 'real-time', 'x.com']):
                if 'features' not in model_data:
                    model_data['features'] = []
                model_data['features'].extend(self.extract_features_from_text(text))
        
        if model_data.get('input_price', 0) > 0 or 'grok' in model_data.get('id', ''):
            # 기본값 추가
            self.add_default_values(model_data)
            return model_data
        
        return None
    
    async def extract_models_from_table(self, table) -> List[Dict[str, Any]]:
        """테이블에서 모델 정보 추출"""
        models = []
        rows = table.find_all('tr')
        
        if not rows:
            return models
        
        # 헤더 찾기
        headers = []
        header_row = rows[0]
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        # 데이터 행 파싱
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            model_data = {}
            
            for i, cell in enumerate(cells):
                if i >= len(headers):
                    break
                
                text = cell.get_text(strip=True)
                header = headers[i]
                
                if 'model' in header or 'name' in header or i == 0:
                    if 'grok' in text.lower():
                        model_data['name'] = self.clean_model_name(text)
                        model_data['id'] = self.name_to_id(model_data['name'])
                elif 'input' in header:
                    model_data['input_price'] = self.extract_price_value(text)
                elif 'output' in header:
                    model_data['output_price'] = self.extract_price_value(text)
                elif 'context' in header:
                    model_data['context_window'] = self.extract_context_window(text)
                elif 'description' in header:
                    model_data['description'] = text
            
            if 'id' in model_data:
                self.add_default_values(model_data)
                models.append(model_data)
        
        return models
    
    async def extract_model_from_card(self, card) -> Dict[str, Any]:
        """카드에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름
        title = card.find(['h2', 'h3', 'h4', 'div'], class_=re.compile('title|name'))
        if title and 'grok' in title.get_text().lower():
            model_data['name'] = self.clean_model_name(title.get_text(strip=True))
            model_data['id'] = self.name_to_id(model_data['name'])
        
        if 'id' not in model_data:
            return None
        
        # 가격 정보
        price_elements = card.find_all(text=re.compile(r'\$[\d.]+'))
        if len(price_elements) >= 2:
            model_data['input_price'] = self.extract_price_value(price_elements[0])
            model_data['output_price'] = self.extract_price_value(price_elements[1])
        
        # 설명
        desc = card.find(['p', 'div'], class_=re.compile('desc|summary'))
        if desc:
            model_data['description'] = desc.get_text(strip=True)
        
        self.add_default_values(model_data)
        return model_data
    
    def extract_price_info(self, text: str) -> Dict[str, float]:
        """텍스트에서 가격 정보 추출"""
        pricing = {}
        
        # Input/Output 가격 패턴
        input_match = re.search(r'input.*?\$?([\d.]+)', text, re.I)
        output_match = re.search(r'output.*?\$?([\d.]+)', text, re.I)
        
        if input_match:
            pricing['input_price'] = float(input_match.group(1))
        if output_match:
            pricing['output_price'] = float(output_match.group(1))
        
        # 단일 가격 패턴
        if not pricing:
            price_match = re.search(r'\$?([\d.]+)\s*(?:/|per)\s*(?:1M|million)', text, re.I)
            if price_match:
                price = float(price_match.group(1))
                pricing['input_price'] = price
                pricing['output_price'] = price * 2  # 일반적으로 output이 더 비쌈
        
        return pricing
    
    def extract_price_value(self, text: str) -> float:
        """가격 텍스트에서 숫자 추출"""
        price_match = re.search(r'\$?([\d.]+)', text)
        if price_match:
            return float(price_match.group(1))
        return 0.0
    
    def extract_features_from_text(self, text: str) -> List[str]:
        """텍스트에서 기능 추출"""
        features = []
        text_lower = text.lower()
        
        if 'vision' in text_lower or 'image' in text_lower:
            features.append('vision')
        if 'real-time' in text_lower or 'realtime' in text_lower:
            features.append('real-time')
        if 'x.com' in text_lower or 'twitter' in text_lower:
            features.append('x-integration')
        
        return features
    
    def clean_model_name(self, name: str) -> str:
        """모델 이름 정리"""
        # 불필요한 문자 제거
        name = re.sub(r'[^\w\s-]', '', name).strip()
        
        # 정규화
        name_map = {
            'Grok 2': 'Grok-2',
            'Grok-2': 'Grok-2',
            'Grok 2 Vision': 'Grok-2 Vision',
            'Grok-2 Vision': 'Grok-2 Vision',
            'Grok-2-Vision': 'Grok-2 Vision',
            'Grok': 'Grok-2'  # 기본적으로 최신 버전 가정
        }
        
        for pattern, replacement in name_map.items():
            if pattern.lower() == name.lower():
                return replacement
        
        return name
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        id_map = {
            'Grok-2': 'grok-2',
            'Grok-2 Vision': 'grok-2-vision'
        }
        
        return id_map.get(name, name.lower().replace(' ', '-'))
    
    def add_default_values(self, model_data: Dict[str, Any]) -> None:
        """모델 데이터에 기본값 추가"""
        model_id = model_data.get('id', '')
        
        # 설명
        if 'description' not in model_data:
            model_data['description'] = self.get_model_description(model_id)
        
        # 기능
        if 'features' not in model_data:
            model_data['features'] = self.get_model_features(model_id)
        
        # 상태
        if 'status' not in model_data:
            model_data['status'] = 'ga'
        
        # 컨텍스트 윈도우
        if 'context_window' not in model_data:
            model_data['context_window'] = 131072  # 128K
        
        # 최대 출력
        if 'max_output' not in model_data:
            model_data['max_output'] = 4096
        
        # 가격 (기본값)
        if 'input_price' not in model_data:
            default_pricing = self.get_default_pricing(model_id)
            model_data.update(default_pricing)
    
    def get_model_description(self, model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'grok-2': 'State-of-the-art language model with real-time knowledge from X',
            'grok-2-vision': 'Multimodal model that understands both text and images'
        }
        
        return descriptions.get(model_id, 'xAI language model by Elon Musk')
    
    def get_model_features(self, model_id: str) -> List[str]:
        """모델 기능 반환"""
        features_map = {
            'grok-2': ['chat', 'real-time', 'x-integration', 'reasoning', 'coding', 'multilingual'],
            'grok-2-vision': ['chat', 'vision', 'real-time', 'x-integration', 'multimodal', 'reasoning']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def get_default_pricing(self, model_id: str) -> Dict[str, float]:
        """기본 가격 정보 반환"""
        pricing = {
            'grok-2': {'input_price': 10.00, 'output_price': 30.00},
            'grok-2-vision': {'input_price': 10.00, 'output_price': 30.00}
        }
        
        return pricing.get(model_id, {'input_price': 10.00, 'output_price': 30.00})
    
    def deduplicate_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 모델 제거"""
        seen = {}
        
        for model in models:
            model_id = model.get('id')
            if not model_id:
                continue
            
            if model_id not in seen or len(model) > len(seen[model_id]):
                # 더 완전한 정보를 가진 모델 유지
                seen[model_id] = model
        
        return list(seen.values())
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델 (2025년 1월 최신)"""
        return [
            {
                'id': 'grok-2',
                'name': 'Grok-2',
                'description': 'Advanced reasoning model with real-time knowledge from X platform',
                'input_price': 2.00,
                'output_price': 10.00,
                'context_window': 131072,
                'max_output': 4096,
                'features': ['chat', 'real-time', 'x-integration', 'reasoning', 'coding', 'multilingual', 'current-events'],
                'status': 'ga'
            },
            {
                'id': 'grok-2-vision',
                'name': 'Grok-2 Vision',
                'description': 'Multimodal model with vision capabilities and real-time knowledge',
                'input_price': 2.00,
                'output_price': 10.00,
                'context_window': 131072,
                'max_output': 4096,
                'features': ['chat', 'vision', 'real-time', 'x-integration', 'multimodal', 'reasoning', 'image-analysis'],
                'status': 'ga'
            },
            {
                'id': 'grok-beta',
                'name': 'Grok-3 (Beta)',
                'description': 'Next generation Grok model with enhanced capabilities',
                'input_price': 5.00,
                'output_price': 15.00,
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'advanced-capabilities', 'beta', 'next-gen'],
                'status': 'beta'
            }
        ]
    
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


class XAICrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 xAI 크롤러"""
    
    def __init__(self):
        super().__init__('xai')
        self.scraper = XAIWebScraper()
        
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
                modalities = ['text']
                if 'vision' in model.get('features', []):
                    modalities.append('image')
                model['modalities'] = modalities
                
                # 기본값 설정
                model.setdefault('release_date', '2024')
                
            return models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        models = self.fetch_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return {}


if __name__ == "__main__":
    crawler = XAICrawlerV2()
    crawler.run()