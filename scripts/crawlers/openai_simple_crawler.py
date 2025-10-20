#!/usr/bin/env python3
"""
OpenAI 모델 크롤러 - requests만 사용 (Playwright 불필요)
공식 API로 모델 목록을 가져오고, 가격은 하드코딩
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class OpenAISimpleCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('openai')
        self.api_url = "https://api.openai.com/v1/models"
        self.api_key = os.getenv('OPENAI_API_KEY')

        # 2025년 1월 최신 가격 정보 (per 1M tokens)
        self.pricing_data = {
            # GPT-4o 시리즈
            'gpt-4o': {'input': 2.50, 'output': 10.00, 'context': 128000, 'max_output': 16384},
            'gpt-4o-2024-11-20': {'input': 2.50, 'output': 10.00, 'context': 128000, 'max_output': 16384},
            'gpt-4o-2024-08-06': {'input': 2.50, 'output': 10.00, 'context': 128000, 'max_output': 16384},
            'gpt-4o-2024-05-13': {'input': 5.00, 'output': 15.00, 'context': 128000, 'max_output': 16384},
            'chatgpt-4o-latest': {'input': 5.00, 'output': 15.00, 'context': 128000, 'max_output': 16384},

            # GPT-4o mini 시리즈
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60, 'context': 128000, 'max_output': 16384},
            'gpt-4o-mini-2024-07-18': {'input': 0.15, 'output': 0.60, 'context': 128000, 'max_output': 16384},

            # o1 시리즈 (추론 모델)
            'o1': {'input': 15.00, 'output': 60.00, 'context': 200000, 'max_output': 100000},
            'o1-2024-12-17': {'input': 15.00, 'output': 60.00, 'context': 200000, 'max_output': 100000},
            'o1-preview': {'input': 15.00, 'output': 60.00, 'context': 128000, 'max_output': 32768},
            'o1-preview-2024-09-12': {'input': 15.00, 'output': 60.00, 'context': 128000, 'max_output': 32768},
            'o1-mini': {'input': 3.00, 'output': 12.00, 'context': 128000, 'max_output': 65536},
            'o1-mini-2024-09-12': {'input': 3.00, 'output': 12.00, 'context': 128000, 'max_output': 65536},

            # GPT-4 Turbo 시리즈
            'gpt-4-turbo': {'input': 10.00, 'output': 30.00, 'context': 128000, 'max_output': 4096},
            'gpt-4-turbo-2024-04-09': {'input': 10.00, 'output': 30.00, 'context': 128000, 'max_output': 4096},
            'gpt-4-turbo-preview': {'input': 10.00, 'output': 30.00, 'context': 128000, 'max_output': 4096},
            'gpt-4-0125-preview': {'input': 10.00, 'output': 30.00, 'context': 128000, 'max_output': 4096},
            'gpt-4-1106-preview': {'input': 10.00, 'output': 30.00, 'context': 128000, 'max_output': 4096},

            # GPT-4 시리즈
            'gpt-4': {'input': 30.00, 'output': 60.00, 'context': 8192, 'max_output': 8192},
            'gpt-4-0613': {'input': 30.00, 'output': 60.00, 'context': 8192, 'max_output': 8192},

            # GPT-3.5 Turbo 시리즈
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50, 'context': 16385, 'max_output': 4096},
            'gpt-3.5-turbo-0125': {'input': 0.50, 'output': 1.50, 'context': 16385, 'max_output': 4096},
            'gpt-3.5-turbo-1106': {'input': 1.00, 'output': 2.00, 'context': 16385, 'max_output': 4096},
        }

        # 모델별 메타데이터
        self.model_metadata = {
            'gpt-4o': {
                'name': 'GPT-4o',
                'description': 'Most capable multimodal model, optimized for speed',
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-05-13',
                'status': 'ga'
            },
            'gpt-4o-mini': {
                'name': 'GPT-4o mini',
                'description': 'Affordable small model for fast, lightweight tasks',
                'features': ['chat', 'vision', 'function-calling', 'json-mode', 'fast'],
                'modalities': ['text', 'image'],
                'release_date': '2024-07-18',
                'status': 'ga'
            },
            'o1': {
                'name': 'o1',
                'description': 'Most advanced reasoning model for complex tasks',
                'features': ['reasoning', 'complex-tasks', 'thinking', 'coding', 'math'],
                'modalities': ['text'],
                'release_date': '2024-12-17',
                'status': 'ga'
            },
            'o1-preview': {
                'name': 'o1-preview',
                'description': 'Reasoning model for complex tasks in science, coding, and math',
                'features': ['reasoning', 'complex-tasks', 'thinking'],
                'modalities': ['text'],
                'release_date': '2024-09-12',
                'status': 'ga'
            },
            'o1-mini': {
                'name': 'o1-mini',
                'description': 'Faster, cheaper reasoning model particularly good at coding',
                'features': ['reasoning', 'coding', 'fast', 'thinking'],
                'modalities': ['text'],
                'release_date': '2024-09-12',
                'status': 'ga'
            },
            'gpt-4-turbo': {
                'name': 'GPT-4 Turbo',
                'description': 'Previous generation high-intelligence model',
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-04-09',
                'status': 'ga'
            },
            'gpt-4': {
                'name': 'GPT-4',
                'description': 'Previous generation model for complex tasks',
                'features': ['chat', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2023-03-14',
                'status': 'legacy'
            },
            'gpt-3.5-turbo': {
                'name': 'GPT-3.5 Turbo',
                'description': 'Fast, inexpensive model for simple tasks',
                'features': ['chat', 'function-calling', 'json-mode', 'fast'],
                'modalities': ['text'],
                'release_date': '2022-11-30',
                'status': 'ga'
            }
        }

    def fetch_models(self) -> List[Dict]:
        """OpenAI 모델 정보 수집"""
        models = []

        # API 사용 가능 시 API로 모델 목록 확인
        if self.api_key:
            try:
                api_models = self.fetch_from_api()
                models = self.process_api_models(api_models)
                print(f"✅ Fetched {len(models)} models from OpenAI API")
            except Exception as e:
                print(f"⚠️  API fetch failed ({e}), using hardcoded data")
                models = self.get_fallback_models()
        else:
            print(f"⚠️  No API key, using hardcoded data")
            models = self.get_fallback_models()

        return models

    def fetch_from_api(self) -> List[Dict]:
        """OpenAI API에서 모델 목록 가져오기"""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = self.session.get(self.api_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data.get('data', [])

    def process_api_models(self, api_models: List[Dict]) -> List[Dict]:
        """API 모델 데이터 처리"""
        processed_models = []

        for model in api_models:
            model_id = model.get('id', '')

            # Chat 모델만 필터링
            if not self.should_include_model(model_id):
                continue

            # 기본 모델 ID 추출
            base_id = self.get_base_model_id(model_id)

            # 가격 정보가 있는 모델만 포함
            pricing = self.pricing_data.get(model_id) or self.pricing_data.get(base_id)
            if not pricing:
                continue

            # 메타데이터 가져오기
            metadata = self.model_metadata.get(base_id, {})

            model_data = {
                'id': model_id,
                'name': metadata.get('name', self.format_model_name(model_id)),
                'description': metadata.get('description', 'OpenAI language model'),
                'input_price': pricing['input'],
                'output_price': pricing['output'],
                'context_window': pricing['context'],
                'max_output': pricing['max_output'],
                'features': metadata.get('features', ['chat']),
                'modalities': metadata.get('modalities', ['text']),
                'release_date': metadata.get('release_date', ''),
                'status': metadata.get('status', 'ga'),
                'use_cases': self.get_use_cases(base_id)
            }

            processed_models.append(model_data)

        return processed_models

    def should_include_model(self, model_id: str) -> bool:
        """모델 포함 여부 결정"""
        # 포함할 패턴
        include_patterns = ['gpt-4', 'gpt-3.5', 'o1']

        # 제외할 패턴
        exclude_patterns = [
            'instruct', 'davinci', 'curie', 'babbage', 'ada',
            'whisper', 'tts', 'dall-e', 'embedding', 'text-embedding'
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
        """날짜 버전을 제거한 기본 모델 ID"""
        import re
        base_id = re.sub(r'-\d{4}-\d{2}-\d{2}', '', model_id)
        base_id = re.sub(r'-\d{4}', '', base_id)
        return base_id

    def format_model_name(self, model_id: str) -> str:
        """모델 ID를 표시 이름으로 변환"""
        base_id = self.get_base_model_id(model_id)
        name_map = {
            'gpt-4o': 'GPT-4o',
            'gpt-4o-mini': 'GPT-4o mini',
            'o1': 'o1',
            'o1-preview': 'o1-preview',
            'o1-mini': 'o1-mini',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'gpt-4': 'GPT-4',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo'
        }
        return name_map.get(base_id, model_id)

    def get_use_cases(self, base_model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'gpt-4o': ['Multimodal understanding', 'Complex tasks', 'Vision analysis', 'Fast responses'],
            'gpt-4o-mini': ['Simple tasks', 'Quick responses', 'Cost optimization', 'High volume'],
            'o1': ['Advanced reasoning', 'Math and science', 'Complex coding', 'Research'],
            'o1-preview': ['Complex reasoning', 'Research tasks', 'Scientific analysis'],
            'o1-mini': ['Code generation', 'Debugging', 'Fast reasoning', 'STEM tasks'],
            'gpt-4-turbo': ['Long context', 'Vision tasks', 'Complex instructions'],
            'gpt-4': ['Complex tasks', 'High-quality outputs', 'Detailed analysis'],
            'gpt-3.5-turbo': ['Simple chat', 'Quick tasks', 'Budget-friendly', 'High volume']
        }
        return use_cases_map.get(base_model_id, [])

    def get_fallback_models(self) -> List[Dict]:
        """하드코딩된 모델 데이터"""
        fallback_models = []

        # 주요 모델만 포함
        main_models = ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-preview', 'o1-mini',
                      'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo']

        for model_id in main_models:
            if model_id in self.pricing_data and model_id in self.model_metadata:
                pricing = self.pricing_data[model_id]
                metadata = self.model_metadata[model_id]

                model_data = {
                    'id': model_id,
                    'name': metadata['name'],
                    'description': metadata['description'],
                    'input_price': pricing['input'],
                    'output_price': pricing['output'],
                    'context_window': pricing['context'],
                    'max_output': pricing['max_output'],
                    'features': metadata['features'],
                    'modalities': metadata['modalities'],
                    'release_date': metadata['release_date'],
                    'status': metadata['status'],
                    'use_cases': self.get_use_cases(model_id)
                }
                fallback_models.append(model_data)

        return fallback_models

    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        base_id = self.get_base_model_id(model_id)

        if base_id in self.model_metadata:
            metadata = self.model_metadata[base_id]
            pricing = self.pricing_data.get(model_id) or self.pricing_data.get(base_id, {})

            return {
                **metadata,
                **pricing,
                'id': model_id
            }

        return {}

if __name__ == "__main__":
    crawler = OpenAISimpleCrawler()
    crawler.run()
