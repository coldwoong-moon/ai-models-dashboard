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

class DeepSeekWebScraper(WebScraperBase):
    """DeepSeek 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('deepseek')
        self.pricing_url = "https://platform.deepseek.com/api-docs/pricing/"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """DeepSeek 모델 정보 스크래핑"""
        models = []
        
        # 페이지 가져오기
        html = await self.fetch_html(self.pricing_url, use_playwright=True)
        soup = self.parse_html(html)
        
        # 가격 테이블 찾기
        tables = soup.find_all('table')
        
        for table in tables:
            # 테이블이 가격 정보를 포함하는지 확인
            if self.is_pricing_table(table):
                table_models = await self.extract_models_from_table(table)
                models.extend(table_models)
        
        # 모델 설명 섹션 찾기
        model_sections = soup.find_all(['section', 'div'], class_=re.compile('model|feature|pricing'))
        for section in model_sections:
            model_data = await self.extract_model_from_section(section)
            if model_data:
                models.append(model_data)
        
        # 중복 제거 및 병합
        models = self.merge_duplicate_models(models)
        
        # 스크래핑 실패 시 기본 데이터 사용
        if not models:
            models = self.get_fallback_models()
        
        return models
    
    def is_pricing_table(self, table) -> bool:
        """테이블이 가격 정보를 포함하는지 확인"""
        text = table.get_text().lower()
        return any(keyword in text for keyword in ['price', 'cost', 'token', '$', 'model'])
    
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
        
        # 컬럼 인덱스 찾기
        model_col = None
        input_col = None
        output_col = None
        context_col = None
        cache_input_col = None
        cache_output_col = None
        
        for i, header in enumerate(headers):
            if 'model' in header:
                model_col = i
            elif 'input' in header and 'cache' not in header:
                input_col = i
            elif 'output' in header and 'cache' not in header:
                output_col = i
            elif 'context' in header or 'window' in header:
                context_col = i
            elif 'cache' in header and 'input' in header:
                cache_input_col = i
            elif 'cache' in header and 'output' in header:
                cache_output_col = i
        
        # 데이터 행 파싱
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            model_data = {}
            
            # 모델 이름
            if model_col is not None and model_col < len(cells):
                model_name = cells[model_col].get_text(strip=True)
                model_data['name'] = self.clean_model_name(model_name)
                model_data['id'] = self.name_to_id(model_data['name'])
            
            # 가격 정보
            if input_col is not None and input_col < len(cells):
                model_data['input_price'] = self.extract_price(cells[input_col].get_text(strip=True))
            
            if output_col is not None and output_col < len(cells):
                model_data['output_price'] = self.extract_price(cells[output_col].get_text(strip=True))
            
            # 캐시 가격 (DeepSeek 특유의 기능)
            if cache_input_col is not None and cache_input_col < len(cells):
                model_data['cache_input_price'] = self.extract_price(cells[cache_input_col].get_text(strip=True))
            
            if cache_output_col is not None and cache_output_col < len(cells):
                model_data['cache_output_price'] = self.extract_price(cells[cache_output_col].get_text(strip=True))
            
            # 컨텍스트 윈도우
            if context_col is not None and context_col < len(cells):
                model_data['context_window'] = self.extract_context_window(cells[context_col].get_text(strip=True))
            
            if 'id' in model_data and model_data.get('input_price', 0) > 0:
                # 추가 정보 보완
                model_data['description'] = self.get_model_description(model_data['id'])
                model_data['features'] = self.get_model_features(model_data['id'])
                model_data['status'] = self.determine_status(model_data['id'])
                model_data.setdefault('max_output', self.get_max_output(model_data['id']))
                model_data.setdefault('context_window', self.get_default_context_window(model_data['id']))
                
                models.append(model_data)
        
        return models
    
    async def extract_model_from_section(self, section) -> Dict[str, Any]:
        """섹션에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름 찾기
        heading = section.find(['h1', 'h2', 'h3', 'h4'])
        if heading:
            text = heading.get_text(strip=True)
            if 'deepseek' in text.lower() or 'v3' in text.lower() or 'coder' in text.lower():
                model_data['name'] = self.clean_model_name(text)
                model_data['id'] = self.name_to_id(model_data['name'])
        
        if 'id' not in model_data:
            # 텍스트에서 모델 이름 찾기
            text = section.get_text()
            model_match = re.search(r'DeepSeek[-\s]*(V3|V2\.5|V2|Coder|Chat)', text, re.I)
            if model_match:
                model_data['name'] = self.clean_model_name(model_match.group(0))
                model_data['id'] = self.name_to_id(model_data['name'])
            else:
                return None
        
        # 설명 추출
        desc_elem = section.find(['p', 'div'], class_=re.compile('description|intro|summary'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 가격 정보 추출
        price_info = self.extract_pricing_from_section(section)
        if price_info:
            model_data.update(price_info)
        
        # 스펙 추출
        spec_info = self.extract_specs_from_section(section)
        if spec_info:
            model_data.update(spec_info)
        
        if model_data.get('input_price', 0) > 0:
            # 기본값 추가
            model_data.setdefault('description', self.get_model_description(model_data['id']))
            model_data.setdefault('features', self.get_model_features(model_data['id']))
            model_data.setdefault('status', self.determine_status(model_data['id']))
            model_data.setdefault('context_window', self.get_default_context_window(model_data['id']))
            model_data.setdefault('max_output', self.get_max_output(model_data['id']))
            
            return model_data
        
        return None
    
    def extract_pricing_from_section(self, section) -> Dict[str, float]:
        """섹션에서 가격 정보 추출"""
        pricing = {}
        
        # 가격 패턴 찾기
        price_patterns = [
            (r'input.*?\$?([\d.]+)', 'input_price'),
            (r'output.*?\$?([\d.]+)', 'output_price'),
            (r'cache.*?input.*?\$?([\d.]+)', 'cache_input_price'),
            (r'cache.*?output.*?\$?([\d.]+)', 'cache_output_price')
        ]
        
        text = section.get_text().lower()
        for pattern, key in price_patterns:
            match = re.search(pattern, text)
            if match:
                pricing[key] = float(match.group(1))
        
        return pricing
    
    def extract_specs_from_section(self, section) -> Dict[str, Any]:
        """섹션에서 스펙 정보 추출"""
        specs = {}
        
        # 리스트 항목 찾기
        list_items = section.find_all('li')
        for item in list_items:
            text = item.get_text(strip=True)
            
            # 컨텍스트 윈도우
            if 'context' in text.lower() or 'window' in text.lower():
                context = self.extract_context_window(text)
                if context:
                    specs['context_window'] = context
            
            # 최대 출력
            if 'output' in text.lower() and 'max' in text.lower():
                max_output = self.extract_context_window(text)
                if max_output:
                    specs['max_output'] = max_output
        
        return specs
    
    def clean_model_name(self, name: str) -> str:
        """모델 이름 정리"""
        # 불필요한 문자 제거
        name = re.sub(r'[^\w\s\.-]', '', name).strip()
        
        # 정규화
        name_map = {
            'DeepSeek V3': 'DeepSeek-V3',
            'DeepSeek-V3': 'DeepSeek-V3',
            'DeepSeek V2.5': 'DeepSeek-V2.5',
            'DeepSeek-V2.5': 'DeepSeek-V2.5',
            'DeepSeek V2': 'DeepSeek-V2',
            'DeepSeek-V2': 'DeepSeek-V2',
            'DeepSeek Coder V2': 'DeepSeek-Coder-V2',
            'DeepSeek-Coder-V2': 'DeepSeek-Coder-V2',
            'DeepSeek Chat': 'DeepSeek-Chat',
            'DeepSeek-Chat': 'DeepSeek-Chat'
        }
        
        for pattern, replacement in name_map.items():
            if pattern.lower() in name.lower():
                return replacement
        
        # 기본 정리
        if 'deepseek' in name.lower() and 'deepseek' not in name:
            name = 'DeepSeek-' + name
        
        return name
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        id_map = {
            'DeepSeek-V3': 'deepseek-chat',  # V3가 현재 기본 chat 모델
            'DeepSeek-V2.5': 'deepseek-chat',
            'DeepSeek-V2': 'deepseek-chat-v2',
            'DeepSeek-Coder-V2': 'deepseek-coder',
            'DeepSeek-Chat': 'deepseek-chat'
        }
        
        return id_map.get(name, name.lower().replace(' ', '-'))
    
    def extract_price(self, text: str) -> float:
        """텍스트에서 가격 추출"""
        # $0.14 / 1M tokens
        # 0.14
        
        text = text.strip()
        price_match = re.search(r'\$?([\d.]+)', text)
        if price_match:
            return float(price_match.group(1))
        return 0.0
    
    def get_model_description(self, model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'deepseek-chat': 'DeepSeek-V3: Frontier-level model with 671B parameters, excels at coding and math',
            'deepseek-chat-v2': 'DeepSeek-V2: Previous generation model with strong performance',
            'deepseek-coder': 'DeepSeek-Coder-V2: Specialized model for code generation and analysis'
        }
        
        return descriptions.get(model_id, 'DeepSeek language model')
    
    def get_model_features(self, model_id: str) -> List[str]:
        """모델 기능 반환"""
        features_map = {
            'deepseek-chat': ['chat', 'coding', 'math', 'reasoning', 'long-context', 'multilingual', 'function-calling'],
            'deepseek-chat-v2': ['chat', 'coding', 'math', 'reasoning', 'multilingual'],
            'deepseek-coder': ['coding', 'code-generation', 'code-analysis', 'debugging', 'function-calling']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'v2' in model_id and 'v2.5' not in model_id:
            return 'legacy'
        else:
            return 'ga'
    
    def get_default_context_window(self, model_id: str) -> int:
        """기본 컨텍스트 윈도우 반환"""
        context_map = {
            'deepseek-chat': 64000,  # V3
            'deepseek-chat-v2': 128000,  # V2/V2.5
            'deepseek-coder': 128000
        }
        
        return context_map.get(model_id, 32000)
    
    def get_max_output(self, model_id: str) -> int:
        """최대 출력 토큰 수 반환"""
        return 8192  # DeepSeek 모델들의 일반적인 최대 출력
    
    def merge_duplicate_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 모델 병합"""
        merged = {}
        
        for model in models:
            model_id = model.get('id')
            if not model_id:
                continue
            
            if model_id in merged:
                # 기존 모델과 병합 (더 완전한 정보 유지)
                existing = merged[model_id]
                for key, value in model.items():
                    if value and not existing.get(key):
                        existing[key] = value
            else:
                merged[model_id] = model
        
        return list(merged.values())
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델 (2025년 1월 최신)"""
        return [
            {
                'id': 'deepseek-chat',
                'name': 'DeepSeek-V3',
                'description': 'DeepSeek-V3: 671B parameter model excelling at reasoning, coding, and math',
                'input_price': 0.14,
                'output_price': 0.28,
                'context_window': 64000,
                'max_output': 8192,
                'features': ['chat', 'coding', 'math', 'reasoning', 'long-context', 'multilingual', 'function-calling'],
                'status': 'ga'
            },
            {
                'id': 'deepseek-reasoner',
                'name': 'DeepSeek-R1',
                'description': 'Advanced reasoning model with transparent thinking process',
                'input_price': 0.55,
                'output_price': 2.19,
                'context_window': 64000,
                'max_output': 8192,
                'features': ['reasoning', 'thinking', 'transparent-reasoning', 'math', 'complex-tasks'],
                'status': 'ga'
            },
            {
                'id': 'deepseek-coder',
                'name': 'DeepSeek-Coder-V2',
                'description': 'Specialized model for code generation and analysis',
                'input_price': 0.14,
                'output_price': 0.28,
                'context_window': 128000,
                'max_output': 8192,
                'features': ['coding', 'code-generation', 'code-analysis', 'debugging', 'function-calling'],
                'status': 'ga'
            }
        ]
    
    async def scrape_pricing(self) -> Dict[str, Dict[str, float]]:
        """가격 정보만 스크래핑"""
        pricing = {}
        models = await self.scrape_models()
        
        for model in models:
            if 'id' in model and 'input_price' in model:
                price_data = {
                    'input': model.get('input_price', 0),
                    'output': model.get('output_price', 0)
                }
                
                # 캐시 가격 정보가 있으면 추가
                if 'cache_input_price' in model:
                    price_data['cache_input'] = model['cache_input_price']
                if 'cache_output_price' in model:
                    price_data['cache_output'] = model['cache_output_price']
                
                pricing[model['id']] = price_data
        
        return pricing


class DeepSeekCrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 DeepSeek 크롤러"""
    
    def __init__(self):
        super().__init__('deepseek')
        self.scraper = DeepSeekWebScraper()
        
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
                
                # DeepSeek 특유의 속성 추가
                if 'cache_input_price' in model:
                    if 'features' not in model:
                        model['features'] = []
                    if 'prefix-caching' not in model['features']:
                        model['features'].append('prefix-caching')
                
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
    crawler = DeepSeekCrawlerV2()
    crawler.run()