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

class MistralWebScraper(WebScraperBase):
    """Mistral AI 웹사이트에서 모델 정보를 스크래핑"""
    
    def __init__(self):
        super().__init__('mistral')
        self.pricing_url = "https://mistral.ai/pricing/"
        
    async def scrape_models(self) -> List[Dict[str, Any]]:
        """Mistral 모델 정보 스크래핑"""
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
        
        # 테이블 형태의 정보도 확인
        tables = soup.find_all('table')
        for table in tables:
            if self.is_pricing_table(table):
                table_models = await self.extract_models_from_table(table)
                models.extend(table_models)
        
        # 모델 목록 섹션 찾기
        model_lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile('models?-list'))
        for model_list in model_lists:
            list_models = await self.extract_models_from_list(model_list)
            models.extend(list_models)
        
        # 중복 제거 및 병합
        models = self.merge_duplicate_models(models)
        
        # 기본 모델이 없으면 하드코딩된 데이터 추가
        if not models:
            models = self.get_fallback_models()
        
        return models
    
    def is_pricing_table(self, table) -> bool:
        """테이블이 가격 정보를 포함하는지 확인"""
        text = table.get_text().lower()
        return any(keyword in text for keyword in ['price', 'cost', 'token', '$', 'eur', '€'])
    
    async def extract_model_from_card(self, card) -> Dict[str, Any]:
        """카드에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름 찾기
        title_elem = card.find(['h2', 'h3', 'h4'], class_=re.compile('title|name|heading'))
        if not title_elem:
            # 텍스트에서 모델 이름 찾기
            text = card.get_text()
            model_match = re.search(r'(Mistral\s+(?:Large|Medium|Small|7B|8x7B|8x22B)|Pixtral|Codestral|Embed)', text, re.I)
            if model_match:
                model_name = model_match.group(1)
            else:
                return None
        else:
            model_name = title_elem.get_text(strip=True)
        
        if 'mistral' in model_name.lower() or 'pixtral' in model_name.lower() or 'codestral' in model_name.lower():
            model_data['name'] = self.clean_model_name(model_name)
            model_data['id'] = self.name_to_id(model_data['name'])
        else:
            return None
        
        # 설명 추출
        desc_elem = card.find(['p', 'div'], class_=re.compile('description|subtitle'))
        if desc_elem:
            model_data['description'] = desc_elem.get_text(strip=True)
        
        # 가격 정보 추출
        price_info = self.extract_pricing_from_card(card)
        if price_info:
            model_data.update(price_info)
        
        # 스펙 정보 추출
        spec_info = self.extract_specs_from_card(card)
        if spec_info:
            model_data.update(spec_info)
        
        if model_data.get('input_price', 0) > 0 or model_data.get('id'):
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
        
        # 컬럼 인덱스 매핑
        col_mapping = {}
        for i, header in enumerate(headers):
            if 'model' in header or 'name' in header:
                col_mapping['model'] = i
            elif 'input' in header:
                col_mapping['input'] = i
            elif 'output' in header:
                col_mapping['output'] = i
            elif 'context' in header or 'window' in header:
                col_mapping['context'] = i
            elif 'description' in header:
                col_mapping['description'] = i
        
        # 데이터 행 파싱
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            
            model_data = {}
            
            # 모델 이름
            if 'model' in col_mapping and col_mapping['model'] < len(cells):
                model_name = cells[col_mapping['model']].get_text(strip=True)
                if 'mistral' in model_name.lower() or 'pixtral' in model_name.lower() or 'codestral' in model_name.lower():
                    model_data['name'] = self.clean_model_name(model_name)
                    model_data['id'] = self.name_to_id(model_data['name'])
            
            # 가격 정보
            if 'input' in col_mapping and col_mapping['input'] < len(cells):
                model_data['input_price'] = self.extract_price(cells[col_mapping['input']].get_text(strip=True))
            
            if 'output' in col_mapping and col_mapping['output'] < len(cells):
                model_data['output_price'] = self.extract_price(cells[col_mapping['output']].get_text(strip=True))
            
            # 컨텍스트 윈도우
            if 'context' in col_mapping and col_mapping['context'] < len(cells):
                model_data['context_window'] = self.extract_context_window(cells[col_mapping['context']].get_text(strip=True))
            
            # 설명
            if 'description' in col_mapping and col_mapping['description'] < len(cells):
                model_data['description'] = cells[col_mapping['description']].get_text(strip=True)
            
            if 'id' in model_data:
                self.add_default_values(model_data)
                models.append(model_data)
        
        return models
    
    async def extract_models_from_list(self, model_list) -> List[Dict[str, Any]]:
        """리스트에서 모델 정보 추출"""
        models = []
        
        # 리스트 항목 찾기
        items = model_list.find_all(['li', 'div'], recursive=False)
        
        for item in items:
            text = item.get_text()
            if any(name in text.lower() for name in ['mistral', 'pixtral', 'codestral']):
                model_data = self.extract_model_from_text(text)
                if model_data:
                    models.append(model_data)
        
        return models
    
    def extract_pricing_from_card(self, card) -> Dict[str, float]:
        """카드에서 가격 정보 추출"""
        pricing = {}
        
        # 가격 요소 찾기
        price_elements = card.find_all(['span', 'div', 'p'], text=re.compile(r'[€$]\s*[\d.]+'))
        
        prices = []
        for elem in price_elements:
            price = self.extract_price(elem.get_text(strip=True))
            if price > 0:
                prices.append(price)
        
        if len(prices) >= 2:
            pricing['input_price'] = prices[0]
            pricing['output_price'] = prices[1]
        elif len(prices) == 1:
            # 단일 가격인 경우, 용도 확인
            text = card.get_text().lower()
            if 'input' in text:
                pricing['input_price'] = prices[0]
            elif 'output' in text:
                pricing['output_price'] = prices[0]
            else:
                # 기본적으로 input으로 가정
                pricing['input_price'] = prices[0]
                pricing['output_price'] = prices[0] * 3  # output은 보통 더 비쌈
        
        return pricing
    
    def extract_specs_from_card(self, card) -> Dict[str, Any]:
        """카드에서 스펙 정보 추출"""
        specs = {}
        
        # 스펙 항목 찾기
        spec_items = card.find_all(['li', 'div', 'span'])
        
        for item in spec_items:
            text = item.get_text(strip=True)
            
            # 컨텍스트 윈도우
            if 'context' in text.lower() or 'window' in text.lower() or 'tokens' in text.lower():
                context = self.extract_context_window(text)
                if context:
                    specs['context_window'] = context
            
            # 파라미터 수
            param_match = re.search(r'(\d+)B\s*param', text, re.I)
            if param_match:
                specs['parameters'] = f"{param_match.group(1)}B"
        
        return specs
    
    def extract_model_from_text(self, text: str) -> Dict[str, Any]:
        """텍스트에서 모델 정보 추출"""
        model_data = {}
        
        # 모델 이름 패턴
        model_patterns = [
            r'(Mistral\s+Large\s*2?)',
            r'(Mistral\s+Medium)',
            r'(Mistral\s+Small)',
            r'(Mistral\s+7B)',
            r'(Mistral\s+8x7B)',
            r'(Mistral\s+8x22B)',
            r'(Pixtral\s*(?:12B)?)',
            r'(Codestral\s*(?:Mamba)?)',
            r'(Mistral\s+Embed)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                model_data['name'] = self.clean_model_name(match.group(1))
                model_data['id'] = self.name_to_id(model_data['name'])
                break
        
        if 'id' not in model_data:
            return None
        
        # 가격 정보 추출
        price_match = re.findall(r'[€$]\s*([\d.]+)', text)
        if len(price_match) >= 2:
            model_data['input_price'] = float(price_match[0])
            model_data['output_price'] = float(price_match[1])
        elif len(price_match) == 1:
            model_data['input_price'] = float(price_match[0])
            model_data['output_price'] = float(price_match[0]) * 3
        
        self.add_default_values(model_data)
        return model_data
    
    def extract_price(self, text: str) -> float:
        """텍스트에서 가격 추출"""
        # €0.1 / 1M tokens
        # $0.1
        
        text = text.strip()
        price_match = re.search(r'[€$]\s*([\d.]+)', text)
        if price_match:
            return float(price_match.group(1))
        
        # 숫자만 있는 경우
        num_match = re.search(r'([\d.]+)', text)
        if num_match:
            return float(num_match.group(1))
        
        return 0.0
    
    def clean_model_name(self, name: str) -> str:
        """모델 이름 정리"""
        # 불필요한 문자 제거
        name = re.sub(r'[^\w\s-]', '', name).strip()
        
        # 정규화
        name_map = {
            'Mistral Large': 'Mistral Large',
            'Mistral Large 2': 'Mistral Large 2',
            'Mistral Medium': 'Mistral Medium',
            'Mistral Small': 'Mistral Small',
            'Mistral 7B': 'Mistral 7B',
            'Mixtral 8x7B': 'Mixtral 8x7B',
            'Mistral 8x7B': 'Mixtral 8x7B',
            'Mixtral 8x22B': 'Mixtral 8x22B',
            'Mistral 8x22B': 'Mixtral 8x22B',
            'Pixtral': 'Pixtral 12B',
            'Pixtral 12B': 'Pixtral 12B',
            'Codestral': 'Codestral',
            'Codestral Mamba': 'Codestral Mamba',
            'Mistral Embed': 'Mistral Embed'
        }
        
        for pattern, replacement in name_map.items():
            if pattern.lower() in name.lower():
                return replacement
        
        return name
    
    def name_to_id(self, name: str) -> str:
        """모델 이름을 ID로 변환"""
        id_map = {
            'Mistral Large': 'mistral-large-latest',
            'Mistral Large 2': 'mistral-large-2',
            'Mistral Medium': 'mistral-medium',
            'Mistral Small': 'mistral-small-latest',
            'Mistral 7B': 'open-mistral-7b',
            'Mixtral 8x7B': 'open-mixtral-8x7b',
            'Mixtral 8x22B': 'open-mixtral-8x22b',
            'Pixtral 12B': 'pixtral-12b',
            'Codestral': 'codestral-latest',
            'Codestral Mamba': 'codestral-mamba',
            'Mistral Embed': 'mistral-embed'
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
            model_data['status'] = self.determine_status(model_id)
        
        # 컨텍스트 윈도우
        if 'context_window' not in model_data:
            model_data['context_window'] = self.get_default_context_window(model_id)
        
        # 최대 출력
        if 'max_output' not in model_data:
            model_data['max_output'] = self.get_max_output(model_id)
        
        # 가격 (기본값)
        if 'input_price' not in model_data:
            default_pricing = self.get_default_pricing(model_id)
            model_data.update(default_pricing)
    
    def get_model_description(self, model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'mistral-large-latest': 'Top-tier reasoning model for complex tasks',
            'mistral-large-2': 'Latest generation large model with 123B parameters',
            'mistral-medium': 'Balanced model for general tasks',
            'mistral-small-latest': 'Cost-efficient model for simple tasks',
            'open-mistral-7b': 'Open-weight 7B parameter model',
            'open-mixtral-8x7b': 'Mixture of experts model with 8x7B parameters',
            'open-mixtral-8x22b': 'Large mixture of experts model with 8x22B parameters',
            'pixtral-12b': 'Multimodal model for text and image understanding',
            'codestral-latest': 'Specialized model for code generation',
            'codestral-mamba': 'Code model with Mamba architecture',
            'mistral-embed': 'Text embedding model'
        }
        
        return descriptions.get(model_id, 'Mistral AI language model')
    
    def get_model_features(self, model_id: str) -> List[str]:
        """모델 기능 반환"""
        features_map = {
            'mistral-large-latest': ['chat', 'reasoning', 'complex-tasks', 'multilingual', 'function-calling'],
            'mistral-large-2': ['chat', 'reasoning', 'complex-tasks', 'multilingual', 'function-calling', 'long-context'],
            'mistral-medium': ['chat', 'general-purpose', 'multilingual'],
            'mistral-small-latest': ['chat', 'fast', 'cost-efficient', 'multilingual'],
            'open-mistral-7b': ['chat', 'open-source', 'customizable'],
            'open-mixtral-8x7b': ['chat', 'mixture-of-experts', 'efficient', 'multilingual'],
            'open-mixtral-8x22b': ['chat', 'mixture-of-experts', 'powerful', 'multilingual'],
            'pixtral-12b': ['chat', 'vision', 'multimodal', 'image-understanding'],
            'codestral-latest': ['coding', 'code-generation', 'fill-in-the-middle', 'multilingual-code'],
            'codestral-mamba': ['coding', 'mamba-architecture', 'efficient'],
            'mistral-embed': ['embeddings', 'semantic-search', 'retrieval']
        }
        
        return features_map.get(model_id, ['chat'])
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'latest' in model_id:
            return 'ga'
        elif 'medium' in model_id:
            return 'deprecated'  # Mistral Medium은 deprecated
        else:
            return 'ga'
    
    def get_default_context_window(self, model_id: str) -> int:
        """기본 컨텍스트 윈도우 반환"""
        context_map = {
            'mistral-large-latest': 128000,
            'mistral-large-2': 128000,
            'mistral-medium': 32000,
            'mistral-small-latest': 32000,
            'open-mistral-7b': 32000,
            'open-mixtral-8x7b': 32000,
            'open-mixtral-8x22b': 65536,
            'pixtral-12b': 128000,
            'codestral-latest': 32000,
            'codestral-mamba': 256000,
            'mistral-embed': 8192
        }
        
        return context_map.get(model_id, 32000)
    
    def get_max_output(self, model_id: str) -> int:
        """최대 출력 토큰 수 반환"""
        return 4096  # Mistral 모델들의 일반적인 최대 출력
    
    def get_default_pricing(self, model_id: str) -> Dict[str, float]:
        """기본 가격 정보 반환"""
        pricing = {
            'mistral-large-latest': {'input_price': 3.00, 'output_price': 9.00},
            'mistral-large-2': {'input_price': 3.00, 'output_price': 9.00},
            'mistral-medium': {'input_price': 2.70, 'output_price': 8.10},
            'mistral-small-latest': {'input_price': 0.20, 'output_price': 0.60},
            'open-mistral-7b': {'input_price': 0.20, 'output_price': 0.20},
            'open-mixtral-8x7b': {'input_price': 0.50, 'output_price': 0.50},
            'open-mixtral-8x22b': {'input_price': 2.00, 'output_price': 6.00},
            'pixtral-12b': {'input_price': 0.15, 'output_price': 0.15},
            'codestral-latest': {'input_price': 0.20, 'output_price': 0.60},
            'codestral-mamba': {'input_price': 0.20, 'output_price': 0.60},
            'mistral-embed': {'input_price': 0.10, 'output_price': 0.10}
        }
        
        return pricing.get(model_id, {'input_price': 1.00, 'output_price': 3.00})
    
    def merge_duplicate_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 모델 병합"""
        merged = {}
        
        for model in models:
            model_id = model.get('id')
            if not model_id:
                continue
            
            if model_id in merged:
                # 더 완전한 정보 유지
                existing = merged[model_id]
                for key, value in model.items():
                    if value and not existing.get(key):
                        existing[key] = value
            else:
                merged[model_id] = model
        
        return list(merged.values())
    
    def get_fallback_models(self) -> List[Dict[str, Any]]:
        """스크래핑 실패 시 사용할 기본 모델"""
        models = []
        
        # 기본 모델 정보
        default_models = [
            ('Mistral Large', 'mistral-large-latest'),
            ('Mistral Small', 'mistral-small-latest'),
            ('Mixtral 8x7B', 'open-mixtral-8x7b'),
            ('Mixtral 8x22B', 'open-mixtral-8x22b'),
            ('Pixtral 12B', 'pixtral-12b'),
            ('Codestral', 'codestral-latest')
        ]
        
        for name, model_id in default_models:
            model_data = {
                'id': model_id,
                'name': name
            }
            self.add_default_values(model_data)
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


class MistralCrawlerV2(BaseCrawler):
    """웹 스크래핑을 사용하는 새로운 Mistral 크롤러"""
    
    def __init__(self):
        super().__init__('mistral')
        self.scraper = MistralWebScraper()
        
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
                if 'vision' in model.get('features', []) or 'pixtral' in model.get('id', ''):
                    modalities.append('image')
                model['modalities'] = modalities
                
                # 기본값 설정
                model.setdefault('release_date', '')
                model.setdefault('parameters', '')
                
            return models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        models = self.fetch_models()
        for model in models:
            if model.get('id') == model_id:
                return model
        return {}


if __name__ == "__main__":
    crawler = MistralCrawlerV2()
    crawler.run()