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
from bs4 import NavigableString

class AnthropicWebScraper(WebScraperBase):
    """Anthropic 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('anthropic')
        self.models_url = "https://docs.anthropic.com/en/docs/about-claude/models"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """Anthropic 모델 정보 스크래핑"""
        models = []
        
        # 페이지 가져오기 (JavaScript 렌더링 필요)
        html = await self.fetch_html(self.models_url, use_playwright=True)
        soup = self.parse_html(html)
        
        # 테이블 찾기
        tables = soup.find_all('table')
        
        for table in tables:
            # 모델 정보가 있는 테이블인지 확인
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            
            if any('model' in h for h in headers):
                table_models = await self.extract_models_from_table(table)
                models.extend(table_models)
        
        # 추가로 카드 형태의 정보도 확인
        model_sections = soup.find_all(['section', 'div'], class_=re.compile('model|feature'))
        for section in model_sections:
            if self.is_model_section(section):
                model_data = await self.extract_model_from_section(section)
                if model_data:
                    models.append(model_data)
        
        # 스크래핑 실패 시 기본 데이터 사용
        if not models:
            models = self.get_fallback_models()
        
        return models
    
    def is_model_section(self, section) -> bool:
        """섹션이 모델 정보를 담고 있는지 확인"""
        text = section.get_text().lower()
        return any(model in text for model in ['claude-3', 'claude 3', 'opus', 'sonnet', 'haiku'])
    
    async def extract_models_from_table(self, table) -> List[Dict[str, Any]]:
        """테이블에서 모델 정보 추출"""
        models = []
        rows = table.find_all('tr')
        
        # 헤더 인덱스 찾기
        headers = []
        header_row = table.find('thead')
        if header_row:
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        elif rows:
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(['th', 'td'])]
            rows = rows[1:]
        
        # 컬럼 인덱스 매핑
        col_mapping = {
            'model': None,
            'context': None,
            'input': None,
            'output': None,
            'training': None,
            'release': None
        }
        
        for i, header in enumerate(headers):
            if 'model' in header or 'name' in header:
                col_mapping['model'] = i
            elif 'context' in header or 'window' in header or 'token' in header:
                col_mapping['context'] = i
            elif 'input' in header and '$' in headers[i]:
                col_mapping['input'] = i
            elif 'output' in header and '$' in headers[i]:
                col_mapping['output'] = i
            elif 'training' in header or 'cutoff' in header:
                col_mapping['training'] = i
            elif 'release' in header or 'launch' in header:
                col_mapping['release'] = i
        
        # 데이터 행 파싱
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            model_data = {}
            
            # 모델 이름
            if col_mapping['model'] is not None and col_mapping['model'] < len(cells):
                model_name = cells[col_mapping['model']].get_text(strip=True)
                model_data['name'] = self.clean_model_name(model_name)
                model_data['id'] = self.name_to_id(model_data['name'])
            
            # 컨텍스트 윈도우
            if col_mapping['context'] is not None and col_mapping['context'] < len(cells):
                context_text = cells[col_mapping['context']].get_text(strip=True)
                model_data['context_window'] = self.extract_context_window(context_text)
            
            # 가격 정보
            if col_mapping['input'] is not None and col_mapping['input'] < len(cells):
                input_text = cells[col_mapping['input']].get_text(strip=True)
                model_data['input_price'] = self.extract_price(input_text)
            
            if col_mapping['output'] is not None and col_mapping['output'] < len(cells):
                output_text = cells[col_mapping['output']].get_text(strip=True)
                model_data['output_price'] = self.extract_price(output_text)
            
            # 학습 데이터 날짜
            if col_mapping['training'] is not None and col_mapping['training'] < len(cells):
                model_data['training_cutoff'] = cells[col_mapping['training']].get_text(strip=True)
            
            # 출시일
            if col_mapping['release'] is not None and col_mapping['release'] < len(cells):
                model_data['release_date'] = cells[col_mapping['release']].get_text(strip=True)
            
            if 'id' in model_data and model_data.get('input_price', 0) > 0:
                # 추가 정보 보완
                model_data['description'] = self.get_model_description(model_data['id'])
                model_data['features'] = self.get_model_features(model_data['id'])
                model_data['status'] = self.determine_status(model_data['id'])
                model_data['max_output'] = self.get_max_output(model_data['id'])
                
                models.append(model_data)
        
        return models
    
    async def extract_model_from_section(self, section) -> Dict[str, Any]:
        """섹션에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름 찾기
        headings = section.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings:
            text = heading.get_text(strip=True)
            if 'claude' in text.lower():
                model_data['name'] = self.clean_model_name(text)
                model_data['id'] = self.name_to_id(model_data['name'])
                break
        
        if 'id' not in model_data:
            return None
        
        # 설명 추출
        desc_elem = section.find(['p', 'div'], class_=re.compile('description|intro'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 스펙 정보 추출
        spec_items = section.find_all(['li', 'div'], class_=re.compile('spec|feature'))
        for item in spec_items:
            text = item.get_text(strip=True)
            
            # 컨텍스트 윈도우
            if 'context' in text.lower() or 'token' in text.lower():
                model_data['context_window'] = self.extract_context_window(text)
            
            # 가격
            if '$' in text:
                if 'input' in text.lower():
                    model_data['input_price'] = self.extract_price(text)
                elif 'output' in text.lower():
                    model_data['output_price'] = self.extract_price(text)
        
        # 가격 정보가 있는 경우에만 반환
        if model_data.get('input_price', 0) > 0:
            # 기본값 추가
            model_data.setdefault('description', self.get_model_description(model_data['id']))
            model_data.setdefault('features', self.get_model_features(model_data['id']))
            model_data.setdefault('status', self.determine_status(model_data['id']))
            model_data.setdefault('context_window', 200000)
            model_data.setdefault('max_output', 4096)
            
            return model_data
        
        return None
    
    def clean_model_name(self, name: str) -> str:
        """모델 이름 정리"""
        # 괄호 안의 내용 제거
        name = re.sub(r'\([^)]+\)', '', name).strip()
        
        # 특수 문자 제거
        name = re.sub(r'[^\w\s\.-]', '', name).strip()
        
        # 정규화
        name_map = {
            'Claude 3.5 Sonnet': 'Claude 3.5 Sonnet',
            'Claude 3.5 Haiku': 'Claude 3.5 Haiku',
            'Claude 3 Opus': 'Claude 3 Opus',
            'Claude 3 Sonnet': 'Claude 3 Sonnet',
            'Claude 3 Haiku': 'Claude 3 Haiku',
            'Claude 2.1': 'Claude 2.1',
            'Claude 2.0': 'Claude 2.0',
            'Claude Instant': 'Claude Instant'
        }
        
        for pattern, replacement in name_map.items():
            if pattern.lower() in name.lower():
                return replacement
        
        return name
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        id_map = {
            'Claude 3.5 Sonnet': 'claude-3-5-sonnet-20241022',
            'Claude 3.5 Haiku': 'claude-3-5-haiku-20241022',
            'Claude 3 Opus': 'claude-3-opus-20240229',
            'Claude 3 Sonnet': 'claude-3-sonnet-20240229',
            'Claude 3 Haiku': 'claude-3-haiku-20240307',
            'Claude 2.1': 'claude-2.1',
            'Claude 2.0': 'claude-2.0',
            'Claude Instant': 'claude-instant-1.2'
        }
        
        return id_map.get(name, name.lower().replace(' ', '-'))
    
    def extract_price(self, text: str) -> float:
        """텍스트에서 가격 추출"""
        # $X.XX / 1M tokens 형태
        price_match = re.search(r'\$?([\d.]+)', text)
        if price_match:
            return float(price_match.group(1))
        return 0.0
    
    def get_model_description(self, model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'claude-3-5-sonnet-20241022': 'Most intelligent model, combining top-tier performance with improved speed',
            'claude-3-5-haiku-20241022': 'Fast and affordable model for everyday tasks',
            'claude-3-opus-20240229': 'Powerful model for complex tasks and research',
            'claude-3-sonnet-20240229': 'Balanced model for general use',
            'claude-3-haiku-20240307': 'Fastest and most compact model',
            'claude-2.1': 'Previous generation model with 200K context',
            'claude-2.0': 'Previous generation model',
            'claude-instant-1.2': 'Fast and efficient for simple tasks'
        }
        
        return descriptions.get(model_id, 'Anthropic language model')
    
    def get_model_features(self, model_id: str) -> List[str]:
        """모델 기능 반환"""
        features_map = {
            'claude-3-5-sonnet-20241022': ['chat', 'coding', 'analysis', 'creative-writing', 'vision', 'computer-use'],
            'claude-3-5-haiku-20241022': ['chat', 'coding', 'fast', 'vision'],
            'claude-3-opus-20240229': ['chat', 'coding', 'analysis', 'research', 'complex-reasoning', 'vision'],
            'claude-3-sonnet-20240229': ['chat', 'coding', 'analysis', 'vision'],
            'claude-3-haiku-20240307': ['chat', 'fast', 'lightweight', 'vision'],
            'claude-2.1': ['chat', 'long-context', 'analysis'],
            'claude-2.0': ['chat', 'analysis'],
            'claude-instant-1.2': ['chat', 'fast', 'simple-tasks']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'claude-2' in model_id or 'instant' in model_id:
            return 'legacy'
        else:
            return 'ga'
    
    def get_max_output(self, model_id: str) -> int:
        """최대 출력 토큰 수 반환"""
        max_outputs = {
            'claude-3-5-sonnet-20241022': 8192,
            'claude-3-5-haiku-20241022': 8192,
            'claude-3-opus-20240229': 4096,
            'claude-3-sonnet-20240229': 4096,
            'claude-3-haiku-20240307': 4096,
            'claude-2.1': 4096,
            'claude-2.0': 4096,
            'claude-instant-1.2': 4096
        }
        
        return max_outputs.get(model_id, 4096)
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델 데이터 (2025년 1월 최신)"""
        return [
            {
                'id': 'claude-3-5-sonnet-20241022',
                'name': 'Claude 3.5 Sonnet',
                'description': 'Most intelligent model with advanced reasoning, coding, and vision capabilities',
                'input_price': 3.00,
                'output_price': 15.00,
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'coding', 'analysis', 'creative-writing', 'vision', 'computer-use', 'reasoning'],
                'modalities': ['text', 'image'],
                'release_date': '2024-10-22',
                'training_cutoff': '2024-04',
                'status': 'ga'
            },
            {
                'id': 'claude-3-5-haiku-20241022',
                'name': 'Claude 3.5 Haiku',
                'description': 'Fast and affordable model with vision capabilities for everyday tasks',
                'input_price': 1.00,
                'output_price': 5.00,
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'coding', 'fast', 'vision', 'cost-effective'],
                'modalities': ['text', 'image'],
                'status': 'ga'
            },
            {
                'id': 'claude-3-opus-20240229',
                'name': 'Claude 3 Opus',
                'description': 'Most powerful model for complex reasoning and research tasks',
                'input_price': 15.00,
                'output_price': 75.00,
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'coding', 'analysis', 'research', 'complex-reasoning', 'vision', 'creative-writing'],
                'modalities': ['text', 'image'],
                'release_date': '2024-02-29',
                'training_cutoff': '2023-08',
                'status': 'ga'
            },
            {
                'id': 'claude-3-sonnet-20240229',
                'name': 'Claude 3 Sonnet',
                'description': 'Balanced model for general purpose tasks with good performance',
                'input_price': 3.00,
                'output_price': 15.00,
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'coding', 'analysis', 'vision', 'general-purpose'],
                'modalities': ['text', 'image'],
                'release_date': '2024-02-29',
                'training_cutoff': '2023-08',
                'status': 'ga'
            },
            {
                'id': 'claude-3-haiku-20240307',
                'name': 'Claude 3 Haiku',
                'description': 'Fastest and most compact model for simple tasks',
                'input_price': 0.25,
                'output_price': 1.25,
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'fast', 'lightweight', 'vision', 'simple-tasks'],
                'modalities': ['text', 'image'],
                'release_date': '2024-03-07',
                'training_cutoff': '2023-08',
                'status': 'ga'
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


class AnthropicCrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 Anthropic 크롤러"""
    
    def __init__(self):
        super().__init__('anthropic')
        self.scraper = AnthropicWebScraper()
        
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
                model['modalities'] = ['text']
                if 'vision' in model.get('features', []):
                    model['modalities'].append('image')
                
                # 기본값 설정
                model.setdefault('release_date', '')
                model.setdefault('training_cutoff', '')
                
            return models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        models = self.fetch_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return {}


if __name__ == "__main__":
    crawler = AnthropicCrawlerV2()
    crawler.run()