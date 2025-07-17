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

class GoogleWebScraper(WebScraperBase):
    """Google AI 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('google')
        self.pricing_url = "https://ai.google.dev/pricing"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """Google 모델 정보 스크래핑"""
        models = []
        
        # 페이지 가져오기
        html = await self.fetch_html(self.pricing_url, use_playwright=True)
        soup = self.parse_html(html)
        
        # 가격 카드 찾기
        pricing_cards = soup.find_all(['div', 'section'], class_=re.compile('pricing|model|card'))
        
        for card in pricing_cards:
            model_data = await self.extract_model_from_card(card)
            if model_data:
                models.append(model_data)
        
        # 테이블 형태의 가격 정보도 확인
        tables = soup.find_all('table')
        for table in tables:
            table_models = await self.extract_models_from_table(table)
            models.extend(table_models)
        
        # JavaScript에서 데이터 추출 시도
        script_data = self.extract_json_from_script(soup, 'models')
        if script_data:
            script_models = self.process_script_data(script_data)
            models.extend(script_models)
        
        # 중복 제거
        seen = set()
        unique_models = []
        for model in models:
            if model.get('id') and model['id'] not in seen:
                seen.add(model['id'])
                unique_models.append(model)
        
        # 스크래핑 실패 시 기본 데이터 사용
        if not unique_models:
            unique_models = self.get_fallback_models()
        
        return unique_models
    
    async def extract_model_from_card(self, card) -> Dict[str, Any]:
        """카드 요소에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름
        name_elem = card.find(['h2', 'h3', 'h4'], class_=re.compile('title|name|heading'))
        if not name_elem:
            name_elem = card.find(text=re.compile(r'Gemini|PaLM', re.I))
        
        if name_elem:
            if isinstance(name_elem, str):
                model_name = name_elem.strip()
            else:
                model_name = name_elem.get_text(strip=True)
            
            model_data['name'] = self.clean_model_name(model_name)
            model_data['id'] = self.name_to_id(model_data['name'])
        
        # 설명
        desc_elem = card.find(['p', 'div'], class_=re.compile('description|subtitle'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 가격 정보 찾기
        price_info = self.extract_pricing_from_element(card)
        if price_info:
            model_data.update(price_info)
        
        # 컨텍스트 윈도우
        context_info = self.extract_context_from_element(card)
        if context_info:
            model_data['context_window'] = context_info
        
        # 기능 추출
        model_data['features'] = self.extract_features_from_element(card)
        
        return model_data if 'id' in model_data else None
    
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
                
                if 'model' in header or i == 0:
                    model_data['name'] = self.clean_model_name(text)
                    model_data['id'] = self.name_to_id(model_data['name'])
                elif 'input' in header and ('price' in header or '$' in text):
                    model_data['input_price'] = self.extract_price_value(text)
                elif 'output' in header and ('price' in header or '$' in text):
                    model_data['output_price'] = self.extract_price_value(text)
                elif 'context' in header or 'token' in header:
                    model_data['context_window'] = self.extract_context_window(text)
                elif 'free' in header:
                    # 무료 티어 정보
                    model_data['free_tier'] = text
            
            if 'id' in model_data:
                # 추가 정보 보완
                model_data['description'] = self.get_model_description(model_data['id'])
                model_data['features'] = self.get_model_features(model_data['id'])
                model_data['status'] = self.determine_status(model_data['id'])
                model_data.setdefault('max_output', 8192)
                
                # 가격이 없는 경우 기본값 설정
                if 'input_price' not in model_data:
                    pricing = self.get_default_pricing(model_data['id'])
                    model_data.update(pricing)
                
                if model_data.get('input_price', 0) > 0 or model_data.get('free_tier'):
                    models.append(model_data)
        
        return models
    
    def extract_pricing_from_element(self, element) -> Dict[str, float]:
        """요소에서 가격 정보 추출"""
        pricing = {}
        
        # 가격 텍스트 찾기
        price_texts = element.find_all(text=re.compile(r'\$[\d.]+'))
        
        if len(price_texts) >= 2:
            # 보통 첫 번째가 input, 두 번째가 output
            pricing['input_price'] = self.extract_price_value(price_texts[0])
            pricing['output_price'] = self.extract_price_value(price_texts[1])
        elif len(price_texts) == 1:
            # 하나만 있으면 input으로 가정
            pricing['input_price'] = self.extract_price_value(price_texts[0])
            pricing['output_price'] = pricing['input_price'] * 2  # 일반적으로 output이 더 비쌈
        
        # 또는 구조화된 가격 요소 찾기
        input_elem = element.find(['span', 'div'], text=re.compile('input|prompt', re.I))
        if input_elem:
            input_price = input_elem.find_next(text=re.compile(r'\$[\d.]+'))
            if input_price:
                pricing['input_price'] = self.extract_price_value(input_price)
        
        output_elem = element.find(['span', 'div'], text=re.compile('output|completion', re.I))
        if output_elem:
            output_price = output_elem.find_next(text=re.compile(r'\$[\d.]+'))
            if output_price:
                pricing['output_price'] = self.extract_price_value(output_price)
        
        return pricing
    
    def extract_context_from_element(self, element) -> int:
        """요소에서 컨텍스트 윈도우 크기 추출"""
        # 다양한 패턴으로 컨텍스트 찾기
        patterns = [
            r'(\d+)[Kk]\s*(?:tokens|context)',
            r'(\d+),?(\d+)\s*(?:tokens|context)',
            r'context.*?(\d+)[Kk]',
            r'up to\s*(\d+)[Kk]'
        ]
        
        text = element.get_text()
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                if 'k' in match.group(0).lower():
                    return int(match.group(1)) * 1000
                else:
                    # 콤마가 있는 경우 처리
                    num_str = match.group(0).replace(',', '')
                    num_match = re.search(r'\d+', num_str)
                    if num_match:
                        return int(num_match.group(0))
        
        return 0
    
    def extract_price_value(self, text: str) -> float:
        """텍스트에서 가격 값 추출"""
        # $0.00125 / 1k tokens -> 1.25 (per 1M)
        # $1.25 / 1M tokens -> 1.25
        
        price_match = re.search(r'\$?([\d.]+)', text)
        if not price_match:
            return 0.0
        
        price = float(price_match.group(1))
        
        # 단위 확인
        if '1k' in text.lower() or '/k' in text.lower():
            # 1K 토큰당 가격 -> 1M 토큰당으로 변환
            price = price * 1000
        elif '1m' not in text.lower() and '/m' not in text.lower():
            # 단위가 명시되지 않은 경우, 보통 1M 토큰당
            pass
        
        return price
    
    def clean_model_name(self, name: str) -> str:
        """모델 이름 정리"""
        # 특수 문자 및 추가 정보 제거
        name = re.sub(r'\([^)]+\)', '', name).strip()
        name = re.sub(r'\[[^\]]+\]', '', name).strip()
        
        # 정규화
        name_map = {
            'Gemini 1.5 Pro': 'Gemini 1.5 Pro',
            'Gemini 1.5 Flash': 'Gemini 1.5 Flash',
            'Gemini 1.5 Flash-8B': 'Gemini 1.5 Flash-8B',
            'Gemini Pro': 'Gemini 1.0 Pro',
            'Gemini Pro Vision': 'Gemini Pro Vision',
            'PaLM 2': 'PaLM 2',
            'Gemini Exp 1206': 'Gemini Exp 1206',
            'Gemini 2.0 Flash': 'Gemini 2.0 Flash'
        }
        
        for pattern, replacement in name_map.items():
            if pattern.lower() in name.lower():
                return replacement
        
        return name
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        id_map = {
            'Gemini 1.5 Pro': 'gemini-1.5-pro',
            'Gemini 1.5 Flash': 'gemini-1.5-flash',
            'Gemini 1.5 Flash-8B': 'gemini-1.5-flash-8b',
            'Gemini 1.0 Pro': 'gemini-pro',
            'Gemini Pro Vision': 'gemini-pro-vision',
            'Gemini Exp 1206': 'gemini-exp-1206',
            'Gemini 2.0 Flash': 'gemini-2.0-flash',
            'PaLM 2': 'text-bison-001'
        }
        
        return id_map.get(name, name.lower().replace(' ', '-'))
    
    def extract_features_from_element(self, element) -> List[str]:
        """요소에서 기능 추출"""
        features = ['chat']
        text = element.get_text().lower()
        
        feature_keywords = {
            'vision': ['vision', 'image', 'visual', 'multimodal'],
            'video': ['video'],
            'audio': ['audio', 'speech'],
            'function-calling': ['function', 'tools'],
            'json-mode': ['json', 'structured'],
            'fast': ['fast', 'quick', 'flash'],
            'reasoning': ['reasoning', 'thinking'],
            'long-context': ['1m', '2m', 'million', 'long context'],
            'coding': ['code', 'programming'],
            'multilingual': ['multilingual', '100+ languages']
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in text for keyword in keywords):
                features.append(feature)
        
        return list(set(features))
    
    def get_model_description(self, model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'gemini-1.5-pro': 'Advanced model with 2M context window for complex tasks',
            'gemini-1.5-flash': 'Fast and efficient model optimized for speed',
            'gemini-1.5-flash-8b': 'Smallest and fastest Gemini model',
            'gemini-pro': 'Versatile model for text generation',
            'gemini-pro-vision': 'Multimodal model for text and image understanding',
            'gemini-exp-1206': 'Experimental model with enhanced capabilities',
            'gemini-2.0-flash': 'Next generation flash model with improved performance',
            'text-bison-001': 'PaLM 2 for text generation'
        }
        
        return descriptions.get(model_id, 'Google AI language model')
    
    def get_model_features(self, model_id: str) -> List[str]:
        """모델 기능 반환"""
        features_map = {
            'gemini-1.5-pro': ['chat', 'vision', 'audio', 'video', 'function-calling', 'json-mode', 'long-context', 'coding'],
            'gemini-1.5-flash': ['chat', 'vision', 'audio', 'video', 'function-calling', 'fast', 'coding'],
            'gemini-1.5-flash-8b': ['chat', 'vision', 'function-calling', 'fast', 'lightweight'],
            'gemini-pro': ['chat', 'function-calling'],
            'gemini-pro-vision': ['chat', 'vision', 'multimodal'],
            'gemini-exp-1206': ['chat', 'vision', 'experimental', 'advanced'],
            'gemini-2.0-flash': ['chat', 'vision', 'fast', 'next-gen'],
            'text-bison-001': ['chat', 'text-generation']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'exp' in model_id:
            return 'experimental'
        elif '2.0' in model_id:
            return 'preview'
        elif 'palm' in model_id or 'bison' in model_id:
            return 'legacy'
        else:
            return 'ga'
    
    def get_default_pricing(self, model_id: str) -> Dict[str, float]:
        """기본 가격 정보 반환"""
        pricing = {
            'gemini-1.5-pro': {'input_price': 1.25, 'output_price': 5.00},
            'gemini-1.5-flash': {'input_price': 0.075, 'output_price': 0.30},
            'gemini-1.5-flash-8b': {'input_price': 0.0375, 'output_price': 0.15},
            'gemini-pro': {'input_price': 0.50, 'output_price': 1.50},
            'gemini-pro-vision': {'input_price': 0.50, 'output_price': 1.50},
            'text-bison-001': {'input_price': 0.50, 'output_price': 0.50}
        }
        
        return pricing.get(model_id, {'input_price': 0, 'output_price': 0})
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델 데이터 (2025년 1월 최신)"""
        return [
            {
                'id': 'gemini-2.0-flash',
                'name': 'Gemini 2.0 Flash',
                'description': 'Next generation multimodal model with enhanced capabilities',
                'input_price': 0.075,
                'output_price': 0.30,
                'context_window': 1000000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'video', 'function-calling', 'fast', 'next-gen', 'multimodal'],
                'status': 'ga'
            },
            {
                'id': 'gemini-1.5-pro',
                'name': 'Gemini 1.5 Pro',
                'description': 'Advanced model with 2M context window for complex reasoning',
                'input_price': 1.25,
                'output_price': 5.00,
                'context_window': 2097152,
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'video', 'function-calling', 'json-mode', 'long-context', 'coding', 'reasoning'],
                'status': 'ga'
            },
            {
                'id': 'gemini-1.5-flash',
                'name': 'Gemini 1.5 Flash',
                'description': 'Fast and efficient multimodal model for production use',
                'input_price': 0.075,
                'output_price': 0.30,
                'context_window': 1000000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'video', 'function-calling', 'fast', 'coding', 'multimodal'],
                'status': 'ga'
            },
            {
                'id': 'gemini-1.5-flash-8b',
                'name': 'Gemini 1.5 Flash-8B',
                'description': 'Smallest and fastest Gemini model for lightweight tasks',
                'input_price': 0.0375,
                'output_price': 0.15,
                'context_window': 1000000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'function-calling', 'fast', 'lightweight', 'cost-effective'],
                'status': 'ga'
            },
            {
                'id': 'gemini-exp-1206',
                'name': 'Gemini Exp 1206',
                'description': 'Experimental model with enhanced reasoning capabilities',
                'input_price': 1.25,
                'output_price': 5.00,
                'context_window': 2097152,
                'max_output': 8192,
                'features': ['chat', 'vision', 'experimental', 'advanced-reasoning', 'research'],
                'status': 'experimental'
            }
        ]
    
    def process_script_data(self, data: Dict) -> List[Dict[str, Any]]:
        """스크립트에서 추출한 데이터 처리"""
        models = []
        
        if isinstance(data, dict) and 'models' in data:
            for model_data in data['models']:
                processed = self.convert_script_model(model_data)
                if processed:
                    models.append(processed)
        
        return models
    
    def convert_script_model(self, model_data: Dict) -> Dict[str, Any]:
        """스크립트 모델 데이터를 표준 형식으로 변환"""
        if not isinstance(model_data, dict):
            return None
        
        converted = {
            'id': model_data.get('id', ''),
            'name': self.clean_model_name(model_data.get('name', '')),
            'description': model_data.get('description', ''),
            'input_price': model_data.get('inputPrice', 0),
            'output_price': model_data.get('outputPrice', 0),
            'context_window': model_data.get('contextWindow', 0),
            'max_output': model_data.get('maxOutput', 8192),
            'features': model_data.get('features', ['chat']),
            'status': model_data.get('status', 'ga')
        }
        
        if not converted['id']:
            converted['id'] = self.name_to_id(converted['name'])
        
        return converted if converted['id'] else None
    
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


class GoogleCrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 Google 크롤러"""
    
    def __init__(self):
        super().__init__('google')
        self.scraper = GoogleWebScraper()
        
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
                features = model.get('features', [])
                
                if 'vision' in features:
                    modalities.append('image')
                if 'audio' in features:
                    modalities.append('audio')
                if 'video' in features:
                    modalities.append('video')
                
                model['modalities'] = modalities
                
                # 컨텍스트 윈도우 기본값
                if not model.get('context_window'):
                    if 'gemini-1.5' in model.get('id', ''):
                        model['context_window'] = 2097152  # 2M
                    else:
                        model['context_window'] = 32768
                
                # 기본값 설정
                model.setdefault('release_date', '')
                
            return models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        models = self.fetch_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return {}


if __name__ == "__main__":
    crawler = GoogleCrawlerV2()
    crawler.run()