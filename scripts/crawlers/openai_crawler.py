#!/usr/bin/env python3
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import re
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

class OpenAICrawler(BaseCrawler):
    def __init__(self):
        super().__init__('openai')
        self.api_url = "https://api.openai.com/v1/models"
        self.pricing_url = "https://openai.com/api/pricing"
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # 가격 정보 (2025년 1월 기준, API에서 제공하지 않으므로 하드코딩)
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
        
        # 모델별 상세 정보
        self.model_details = {
            'gpt-4o': {
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'release_date': '2024-05-13'
            },
            'gpt-4o-mini': {
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode', 'fast'],
                'release_date': '2024-07-18'
            },
            'o1-preview': {
                'context_window': 128000,
                'max_output': 32768,
                'features': ['reasoning', 'complex-tasks', 'thinking'],
                'release_date': '2024-09-12'
            },
            'o1-mini': {
                'context_window': 128000,
                'max_output': 65536,
                'features': ['reasoning', 'coding', 'fast', 'thinking'],
                'release_date': '2024-09-12'
            },
            'gpt-4-turbo': {
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'release_date': '2024-04-09'
            },
            'gpt-4': {
                'context_window': 8192,
                'max_output': 8192,
                'features': ['chat', 'function-calling'],
                'release_date': '2023-03-14'
            },
            'gpt-3.5-turbo': {
                'context_window': 16385,
                'max_output': 4096,
                'features': ['chat', 'function-calling', 'json-mode', 'fast'],
                'release_date': '2022-11-30'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """OpenAI API에서 모델 정보 수집"""
        models = []
        
        # API를 통한 실시간 모델 목록 가져오기
        if self.api_key:
            try:
                api_models = self.fetch_from_api()
                models = self.process_api_models(api_models)
            except Exception as e:
                print(f"Failed to fetch from API: {e}")
                models = self.get_fallback_models()
        else:
            print("No OpenAI API key found, using fallback data")
            models = self.get_fallback_models()
        
        return models
    
    def fetch_from_api(self) -> List[Dict]:
        """OpenAI API에서 모델 목록 가져오기"""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = self.session.get(self.api_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def process_api_models(self, api_models: List[Dict]) -> List[Dict]:
        """API 모델 데이터 처리"""
        processed_models = []
        
        for model in api_models:
            model_id = model.get('id', '')
            
            # GPT 및 o1 모델만 필터링 (deprecated 제외)
            if not self.should_include_model(model_id):
                continue
            
            # 기본 모델 ID 추출 (날짜 버전 제거)
            base_model_id = self.get_base_model_id(model_id)
            
            model_data = {
                'id': model_id,
                'name': self.format_model_name(model_id),
                'description': self.get_model_description(base_model_id),
                'status': self.determine_status(model_id),
                'created': model.get('created', 0),
                'owned_by': model.get('owned_by', 'openai')
            }
            
            # 가격 정보 추가
            if model_id in self.pricing_data:
                model_data['input_price'] = self.pricing_data[model_id]['input']
                model_data['output_price'] = self.pricing_data[model_id]['output']
            elif base_model_id in self.pricing_data:
                model_data['input_price'] = self.pricing_data[base_model_id]['input']
                model_data['output_price'] = self.pricing_data[base_model_id]['output']
            else:
                # 가격 정보가 없는 모델은 제외
                continue
            
            # 상세 정보 추가
            if base_model_id in self.model_details:
                details = self.model_details[base_model_id]
                model_data.update({
                    'context_window': details.get('context_window', 8192),
                    'max_output': details.get('max_output', 4096),
                    'features': details.get('features', ['chat']),
                    'release_date': details.get('release_date', '')
                })
            else:
                # 기본값 설정
                model_data.update({
                    'context_window': 8192,
                    'max_output': 4096,
                    'features': self.extract_features(model_id),
                    'release_date': ''
                })
            
            # 모달리티 추가
            model_data['modalities'] = self.extract_modalities(model_data.get('features', []))
            
            processed_models.append(model_data)
        
        return processed_models
    
    def should_include_model(self, model_id: str) -> bool:
        """모델을 포함할지 여부 결정"""
        # 포함할 모델 패턴
        include_patterns = ['gpt-4', 'gpt-3.5', 'o1-', 'gpt-4o']
        
        # 제외할 패턴
        exclude_patterns = [
            'instruct',  # 구버전 instruct 모델
            'davinci', 'curie', 'babbage', 'ada',  # 레거시 모델
            '0301', '0314',  # 2023년 3월 이전 모델
            'whisper', 'tts', 'dall-e',  # 다른 종류의 모델
            'embedding'  # 임베딩 모델
        ]
        
        model_id_lower = model_id.lower()
        
        # 제외 패턴 체크
        for pattern in exclude_patterns:
            if pattern in model_id_lower:
                return False
        
        # 포함 패턴 체크
        for pattern in include_patterns:
            if pattern in model_id_lower:
                return True
        
        return False
    
    def get_base_model_id(self, model_id: str) -> str:
        """날짜 버전을 제거한 기본 모델 ID 반환"""
        # 날짜 패턴 제거 (예: -20240409, -0613 등)
        base_id = re.sub(r'-\d{4}-\d{2}-\d{2}', '', model_id)
        base_id = re.sub(r'-\d{4}', '', base_id)
        return base_id
    
    def format_model_name(self, model_id: str) -> str:
        """모델 ID를 보기 좋은 이름으로 변환"""
        name_map = {
            'gpt-4o': 'GPT-4o',
            'gpt-4o-mini': 'GPT-4o mini',
            'o1-preview': 'o1-preview',
            'o1-mini': 'o1-mini',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'gpt-4': 'GPT-4',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo'
        }
        
        base_id = self.get_base_model_id(model_id)
        return name_map.get(base_id, model_id)
    
    def get_model_description(self, base_model_id: str) -> str:
        """모델 설명 반환"""
        descriptions = {
            'gpt-4o': 'Most capable model with multimodal abilities, optimized for speed',
            'gpt-4o-mini': 'Affordable small model for fast, lightweight tasks',
            'o1-preview': 'Reasoning model for complex tasks in science, coding, and math',
            'o1-mini': 'Faster, cheaper reasoning model particularly good at coding',
            'gpt-4-turbo': 'Previous generation high-intelligence model',
            'gpt-4': 'Previous generation model for complex tasks',
            'gpt-3.5-turbo': 'Fast, inexpensive model for simple tasks'
        }
        
        return descriptions.get(base_model_id, 'OpenAI language model')
    
    def determine_status(self, model_id: str) -> str:
        """모델 상태 결정"""
        if 'preview' in model_id:
            return 'preview'
        elif any(old in model_id for old in ['0301', '0314', '0613']):
            return 'deprecated'
        else:
            return 'ga'
    
    def extract_features(self, model_id: str) -> List[str]:
        """모델 ID에서 기능 추출"""
        features = ['chat']  # 기본값
        
        model_id_lower = model_id.lower()
        
        if 'turbo' in model_id_lower:
            features.append('fast')
        if '32k' in model_id_lower or '16k' in model_id_lower:
            features.append('long-context')
        if 'o1' in model_id_lower:
            features.extend(['reasoning', 'thinking'])
        if 'mini' in model_id_lower:
            features.append('lightweight')
        if 'gpt-4' in model_id_lower:
            features.append('advanced')
        
        return list(set(features))
    
    def extract_modalities(self, features: List[str]) -> List[str]:
        """기능에서 모달리티 추출"""
        modalities = ['text']  # 기본값
        
        if 'vision' in features:
            modalities.append('image')
        
        return modalities
    
    def get_fallback_models(self) -> List[Dict]:
        """API 호출 실패 시 사용할 기본 모델 목록"""
        fallback_models = []
        
        for model_id, details in self.model_details.items():
            if model_id in self.pricing_data:
                model_data = {
                    'id': model_id,
                    'name': self.format_model_name(model_id),
                    'description': self.get_model_description(model_id),
                    'input_price': self.pricing_data[model_id]['input'],
                    'output_price': self.pricing_data[model_id]['output'],
                    'context_window': details['context_window'],
                    'max_output': details['max_output'],
                    'features': details['features'],
                    'modalities': self.extract_modalities(details['features']),
                    'release_date': details['release_date'],
                    'status': 'ga' if 'preview' not in model_id else 'preview'
                }
                fallback_models.append(model_data)
        
        return fallback_models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        base_model_id = self.get_base_model_id(model_id)
        if base_model_id in self.model_details:
            return self.model_details[base_model_id]
        return {}

if __name__ == "__main__":
    # 웹 스크래핑 버전 사용
    from openai_web_scraper import OpenAICrawlerV2
    crawler = OpenAICrawlerV2()
    crawler.run()