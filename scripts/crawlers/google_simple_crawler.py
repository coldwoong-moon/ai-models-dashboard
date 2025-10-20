#!/usr/bin/env python3
"""
Google AI 모델 크롤러 - requests만 사용
Google Gemini API로 모델 목록을 가져오고, 가격은 하드코딩
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleSimpleCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('google')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.api_key = os.getenv('GOOGLE_AI_API_KEY') or os.getenv('GOOGLE_API_KEY')

        # 2025년 1월 최신 가격 정보 (per 1M tokens)
        self.pricing_data = {
            # Gemini 2.0
            'gemini-2.0-flash-exp': {'input': 0.0, 'output': 0.0, 'context': 1000000, 'max_output': 8192},

            # Gemini 1.5 Pro
            'gemini-1.5-pro': {'input': 1.25, 'output': 5.00, 'context': 2000000, 'max_output': 8192},
            'gemini-1.5-pro-latest': {'input': 1.25, 'output': 5.00, 'context': 2000000, 'max_output': 8192},
            'gemini-1.5-pro-002': {'input': 1.25, 'output': 5.00, 'context': 2000000, 'max_output': 8192},

            # Gemini 1.5 Flash
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.30, 'context': 1000000, 'max_output': 8192},
            'gemini-1.5-flash-latest': {'input': 0.075, 'output': 0.30, 'context': 1000000, 'max_output': 8192},
            'gemini-1.5-flash-002': {'input': 0.075, 'output': 0.30, 'context': 1000000, 'max_output': 8192},
            'gemini-1.5-flash-8b': {'input': 0.0375, 'output': 0.15, 'context': 1000000, 'max_output': 8192},

            # Gemini 1.0 Pro
            'gemini-1.0-pro': {'input': 0.50, 'output': 1.50, 'context': 32760, 'max_output': 2048},
            'gemini-1.0-pro-latest': {'input': 0.50, 'output': 1.50, 'context': 32760, 'max_output': 2048},
            'gemini-1.0-pro-vision': {'input': 0.25, 'output': 0.50, 'context': 16384, 'max_output': 2048},

            # Text Embedding
            'text-embedding-004': {'input': 0.025, 'output': 0.0, 'context': 2048, 'max_output': 0},
        }

        # 모델별 메타데이터
        self.model_metadata = {
            'gemini-2.0-flash-exp': {
                'name': 'Gemini 2.0 Flash (Experimental)',
                'description': 'Next generation model with multimodal capabilities (experimental)',
                'features': ['chat', 'vision', 'video', 'audio', 'code-execution', 'reasoning'],
                'modalities': ['text', 'image', 'video', 'audio'],
                'release_date': '2024-12-11',
                'status': 'experimental'
            },
            'gemini-1.5-pro': {
                'name': 'Gemini 1.5 Pro',
                'description': 'Most capable model with best quality and features',
                'features': ['chat', 'vision', 'video', 'audio', 'long-context', 'reasoning'],
                'modalities': ['text', 'image', 'video', 'audio'],
                'release_date': '2024-02-15',
                'status': 'ga'
            },
            'gemini-1.5-flash': {
                'name': 'Gemini 1.5 Flash',
                'description': 'Fast and versatile multimodal model for scaling',
                'features': ['chat', 'vision', 'video', 'audio', 'fast', 'long-context'],
                'modalities': ['text', 'image', 'video', 'audio'],
                'release_date': '2024-05-14',
                'status': 'ga'
            },
            'gemini-1.5-flash-8b': {
                'name': 'Gemini 1.5 Flash-8B',
                'description': 'Smaller, faster, and more cost-effective model',
                'features': ['chat', 'vision', 'fast', 'cost-effective', 'long-context'],
                'modalities': ['text', 'image'],
                'release_date': '2024-10-03',
                'status': 'ga'
            },
            'gemini-1.0-pro': {
                'name': 'Gemini 1.0 Pro',
                'description': 'Previous generation text model',
                'features': ['chat', 'text-only'],
                'modalities': ['text'],
                'release_date': '2023-12-13',
                'status': 'legacy'
            },
            'gemini-1.0-pro-vision': {
                'name': 'Gemini 1.0 Pro Vision',
                'description': 'Previous generation multimodal model',
                'features': ['chat', 'vision'],
                'modalities': ['text', 'image'],
                'release_date': '2023-12-13',
                'status': 'legacy'
            },
            'text-embedding-004': {
                'name': 'Text Embedding 004',
                'description': 'Latest text embedding model',
                'features': ['embedding', 'semantic-search'],
                'modalities': ['text'],
                'release_date': '2024-05-14',
                'status': 'ga'
            }
        }

    def fetch_models(self) -> List[Dict]:
        """Google AI 모델 정보 수집"""
        models = []

        # API 사용 가능 시 API로 모델 목록 확인
        if self.api_key:
            try:
                api_models = self.fetch_from_api()
                models = self.process_api_models(api_models)
                print(f"✅ Fetched {len(models)} models from Google AI API")
            except Exception as e:
                print(f"⚠️  API fetch failed ({e}), using hardcoded data")
                models = self.get_fallback_models()
        else:
            print(f"⚠️  No API key, using hardcoded data")
            models = self.get_fallback_models()

        return models

    def fetch_from_api(self) -> List[Dict]:
        """Google AI API에서 모델 목록 가져오기"""
        params = {'key': self.api_key}

        response = self.session.get(self.api_url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get('models', [])

    def process_api_models(self, api_models: List[Dict]) -> List[Dict]:
        """API 모델 데이터 처리"""
        processed_models = []

        for model in api_models:
            # API는 "models/gemini-pro" 형식으로 반환
            full_name = model.get('name', '')
            model_id = full_name.split('/')[-1] if '/' in full_name else full_name

            # Gemini 및 임베딩 모델만 포함
            if not self.should_include_model(model_id):
                continue

            # 기본 모델 ID 추출
            base_id = self.get_base_model_id(model_id)

            # 가격 정보 가져오기
            pricing = self.pricing_data.get(model_id) or self.pricing_data.get(base_id)
            if not pricing:
                # 가격 정보가 없는 모델은 기본값 설정
                continue

            # 메타데이터 가져오기
            metadata = self.model_metadata.get(base_id, {})

            model_data = {
                'id': model_id,
                'name': metadata.get('name', self.format_model_name(model_id)),
                'description': metadata.get('description', model.get('description', 'Google AI model')),
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
        include_patterns = ['gemini', 'text-embedding']

        # 제외할 패턴
        exclude_patterns = ['aqa', 'embedding-preview']

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
        """버전 번호를 제거한 기본 모델 ID"""
        import re
        # -001, -002 등 제거
        base_id = re.sub(r'-\d{3}$', '', model_id)
        # -latest 제거
        base_id = re.sub(r'-latest$', '', base_id)
        return base_id

    def format_model_name(self, model_id: str) -> str:
        """모델 ID를 표시 이름으로 변환"""
        base_id = self.get_base_model_id(model_id)

        name_map = {
            'gemini-2.0-flash-exp': 'Gemini 2.0 Flash (Experimental)',
            'gemini-1.5-pro': 'Gemini 1.5 Pro',
            'gemini-1.5-flash': 'Gemini 1.5 Flash',
            'gemini-1.5-flash-8b': 'Gemini 1.5 Flash-8B',
            'gemini-1.0-pro': 'Gemini 1.0 Pro',
            'gemini-1.0-pro-vision': 'Gemini 1.0 Pro Vision',
            'text-embedding-004': 'Text Embedding 004'
        }

        return name_map.get(base_id, model_id.replace('-', ' ').title())

    def get_use_cases(self, base_model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'gemini-2.0-flash-exp': ['Experimental features', 'Advanced multimodal', 'Code execution', 'Real-time reasoning'],
            'gemini-1.5-pro': ['Complex reasoning', 'Long document analysis', 'Video understanding', 'Research tasks'],
            'gemini-1.5-flash': ['Fast responses', 'Multimodal chat', 'High volume', 'Cost-effective'],
            'gemini-1.5-flash-8b': ['Simple tasks', 'High throughput', 'Budget-friendly', 'Quick queries'],
            'gemini-1.0-pro': ['Basic chat', 'Text generation', 'Legacy applications'],
            'gemini-1.0-pro-vision': ['Image understanding', 'Visual Q&A', 'Legacy multimodal'],
            'text-embedding-004': ['Semantic search', 'Document similarity', 'Retrieval systems']
        }

        return use_cases_map.get(base_model_id, [])

    def get_fallback_models(self) -> List[Dict]:
        """하드코딩된 모델 데이터"""
        fallback_models = []

        # 주요 모델만 포함
        main_models = ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash',
                      'gemini-1.5-flash-8b', 'gemini-1.0-pro', 'text-embedding-004']

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
    crawler = GoogleSimpleCrawler()
    crawler.run()
