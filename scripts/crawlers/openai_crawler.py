#!/usr/bin/env python3
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import re
from typing import Dict, List

class OpenAICrawler(BaseCrawler):
    def __init__(self):
        super().__init__('openai')
        self.pricing_url = "https://openai.com/api/pricing"
        
        # OpenAI 모델 정보 (공식 문서 기반)
        self.model_info = {
            'gpt-4o': {
                'name': 'GPT-4o',
                'description': 'Most capable model with multimodal abilities, optimized for speed',
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-05-13',
                'status': 'ga'
            },
            'gpt-4o-mini': {
                'name': 'GPT-4o mini',
                'description': 'Affordable small model for fast, lightweight tasks',
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-07-18',
                'status': 'ga'
            },
            'o1-preview': {
                'name': 'o1-preview',
                'description': 'Reasoning model for complex tasks in science, coding, and math',
                'context_window': 128000,
                'max_output': 32768,
                'features': ['reasoning', 'complex-tasks'],
                'modalities': ['text'],
                'release_date': '2024-09-12',
                'status': 'preview'
            },
            'o1-mini': {
                'name': 'o1-mini',
                'description': 'Faster, cheaper reasoning model particularly good at coding',
                'context_window': 128000,
                'max_output': 65536,
                'features': ['reasoning', 'coding', 'fast'],
                'modalities': ['text'],
                'release_date': '2024-09-12',
                'status': 'preview'
            },
            'gpt-4-turbo': {
                'name': 'GPT-4 Turbo',
                'description': 'Previous generation high-intelligence model',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-04-09',
                'status': 'ga'
            },
            'gpt-4': {
                'name': 'GPT-4',
                'description': 'Previous generation model for complex tasks',
                'context_window': 8192,
                'max_output': 8192,
                'features': ['chat', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2023-03-14',
                'status': 'ga'
            },
            'gpt-3.5-turbo': {
                'name': 'GPT-3.5 Turbo',
                'description': 'Fast, inexpensive model for simple tasks',
                'context_window': 16385,
                'max_output': 4096,
                'features': ['chat', 'function-calling', 'json-mode'],
                'modalities': ['text'],
                'release_date': '2022-11-30',
                'status': 'ga'
            }
        }
        
        # 2025년 1월 기준 가격 정보
        self.pricing_data = {
            'gpt-4o': {'input': 2.50, 'output': 10.00},
            'gpt-4o-2024-11-20': {'input': 2.50, 'output': 10.00},
            'gpt-4o-2024-08-06': {'input': 2.50, 'output': 10.00},
            'gpt-4o-2024-05-13': {'input': 5.00, 'output': 15.00},
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
            'gpt-4o-mini-2024-07-18': {'input': 0.15, 'output': 0.60},
            'o1-preview': {'input': 15.00, 'output': 60.00},
            'o1-preview-2024-09-12': {'input': 15.00, 'output': 60.00},
            'o1-mini': {'input': 3.00, 'output': 12.00},
            'o1-mini-2024-09-12': {'input': 3.00, 'output': 12.00},
            'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
            'gpt-4-turbo-2024-04-09': {'input': 10.00, 'output': 30.00},
            'gpt-4-turbo-preview': {'input': 10.00, 'output': 30.00},
            'gpt-4-0125-preview': {'input': 10.00, 'output': 30.00},
            'gpt-4-1106-preview': {'input': 10.00, 'output': 30.00},
            'gpt-4': {'input': 30.00, 'output': 60.00},
            'gpt-4-0613': {'input': 30.00, 'output': 60.00},
            'gpt-4-0314': {'input': 30.00, 'output': 60.00},
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
            'gpt-3.5-turbo-0125': {'input': 0.50, 'output': 1.50},
            'gpt-3.5-turbo-1106': {'input': 1.00, 'output': 2.00},
            'gpt-3.5-turbo-0613': {'input': 1.50, 'output': 2.00},
            'gpt-3.5-turbo-16k-0613': {'input': 3.00, 'output': 4.00}
        }
    
    def fetch_models(self) -> List[Dict]:
        """OpenAI 모델 정보 수집"""
        models = []
        
        # API를 통한 실시간 모델 목록 가져오기 시도
        if os.getenv('OPENAI_API_KEY'):
            try:
                api_models = self.fetch_from_api()
                # API 모델과 로컬 정보 병합
                for api_model in api_models:
                    model_id = api_model['id']
                    base_model_id = model_id.split('-202')[0]  # 날짜 버전 제거
                    
                    if base_model_id in self.model_info:
                        model_data = self.model_info[base_model_id].copy()
                        model_data['id'] = model_id
                        
                        # 가격 정보 추가
                        if model_id in self.pricing_data:
                            model_data['input_price'] = self.pricing_data[model_id]['input']
                            model_data['output_price'] = self.pricing_data[model_id]['output']
                        elif base_model_id in self.pricing_data:
                            model_data['input_price'] = self.pricing_data[base_model_id]['input']
                            model_data['output_price'] = self.pricing_data[base_model_id]['output']
                        
                        models.append(model_data)
            except Exception as e:
                print(f"Failed to fetch from API: {e}")
        
        # API 호출이 실패하거나 API 키가 없는 경우 로컬 데이터 사용
        if not models:
            for model_id, info in self.model_info.items():
                model_data = info.copy()
                model_data['id'] = model_id
                
                # 가격 정보 추가
                if model_id in self.pricing_data:
                    model_data['input_price'] = self.pricing_data[model_id]['input']
                    model_data['output_price'] = self.pricing_data[model_id]['output']
                
                models.append(model_data)
        
        # 웹 페이지에서 최신 가격 정보 스크래핑 시도
        try:
            web_pricing = self.scrape_pricing_page()
            if web_pricing:
                for model in models:
                    if model['id'] in web_pricing:
                        model['input_price'] = web_pricing[model['id']]['input']
                        model['output_price'] = web_pricing[model['id']]['output']
        except Exception as e:
            print(f"Failed to scrape pricing page: {e}")
        
        return models
    
    def fetch_from_api(self) -> List[Dict]:
        """OpenAI API에서 모델 목록 가져오기"""
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        
        response = self.session.get(
            "https://api.openai.com/v1/models",
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        # GPT 모델만 필터링
        gpt_models = [
            model for model in data.get('data', [])
            if any(model['id'].startswith(prefix) for prefix in ['gpt-', 'o1-'])
        ]
        
        return gpt_models
    
    def scrape_pricing_page(self) -> Dict:
        """가격 페이지에서 최신 정보 스크래핑"""
        response = self.session.get(self.pricing_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        pricing_data = {}
        
        # OpenAI 가격 페이지 구조에 맞춰 스크래핑
        # 실제 구조는 변경될 수 있으므로 try-except로 보호
        try:
            pricing_sections = soup.find_all('div', class_='pricing-table')
            for section in pricing_sections:
                rows = section.find_all('tr')
                for row in rows:
                    model_cell = row.find('td', class_='model-name')
                    input_cell = row.find('td', class_='input-price')
                    output_cell = row.find('td', class_='output-price')
                    
                    if model_cell and input_cell and output_cell:
                        model_name = model_cell.text.strip()
                        pricing_data[model_name] = {
                            'input': self.parse_price(input_cell.text),
                            'output': self.parse_price(output_cell.text)
                        }
        except:
            # 스크래핑 실패 시 기본 데이터 사용
            pass
        
        return pricing_data
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        base_model_id = model_id.split('-202')[0]
        if base_model_id in self.model_info:
            return self.model_info[base_model_id]
        return {}

if __name__ == "__main__":
    crawler = OpenAICrawler()
    crawler.run()