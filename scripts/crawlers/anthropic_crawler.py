#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class AnthropicCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('anthropic')
        
        # Anthropic 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'claude-3-5-sonnet-20241022': {
                'name': 'Claude 3.5 Sonnet',
                'description': 'Most intelligent model, combining top-tier performance with improved speed',
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'tool-use', 'json-mode', 'computer-use'],
                'modalities': ['text', 'image'],
                'release_date': '2024-10-22',
                'status': 'ga',
                'input_price': 3.00,
                'output_price': 15.00
            },
            'claude-3-5-haiku-20241022': {
                'name': 'Claude 3.5 Haiku',
                'description': 'Fast and affordable model for everyday tasks',
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'tool-use', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-11-04',
                'status': 'ga',
                'input_price': 1.00,
                'output_price': 5.00
            },
            'claude-3-opus-20240229': {
                'name': 'Claude 3 Opus',
                'description': 'Powerful model for highly complex tasks',
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'tool-use'],
                'modalities': ['text', 'image'],
                'release_date': '2024-02-29',
                'status': 'ga',
                'input_price': 15.00,
                'output_price': 75.00
            },
            'claude-3-sonnet-20240229': {
                'name': 'Claude 3 Sonnet',
                'description': 'Balanced performance and speed',
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'tool-use'],
                'modalities': ['text', 'image'],
                'release_date': '2024-02-29',
                'status': 'ga',
                'input_price': 3.00,
                'output_price': 15.00
            },
            'claude-3-haiku-20240307': {
                'name': 'Claude 3 Haiku',
                'description': 'Fast, compact model for lightweight tasks',
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'tool-use'],
                'modalities': ['text', 'image'],
                'release_date': '2024-03-07',
                'status': 'ga',
                'input_price': 0.25,
                'output_price': 1.25
            },
            'claude-2.1': {
                'name': 'Claude 2.1',
                'description': 'Previous generation model',
                'context_window': 200000,
                'max_output': 4096,
                'features': ['chat'],
                'modalities': ['text'],
                'release_date': '2023-11-21',
                'status': 'deprecated',
                'input_price': 8.00,
                'output_price': 24.00
            },
            'claude-2.0': {
                'name': 'Claude 2.0',
                'description': 'Previous generation model',
                'context_window': 100000,
                'max_output': 4096,
                'features': ['chat'],
                'modalities': ['text'],
                'release_date': '2023-07-11',
                'status': 'deprecated',
                'input_price': 8.00,
                'output_price': 24.00
            },
            'claude-instant-1.2': {
                'name': 'Claude Instant 1.2',
                'description': 'Fast, affordable model (legacy)',
                'context_window': 100000,
                'max_output': 4096,
                'features': ['chat'],
                'modalities': ['text'],
                'release_date': '2023-08-09',
                'status': 'deprecated',
                'input_price': 0.80,
                'output_price': 2.40
            }
        }
        
        # 특별 기능별 추가 정보
        self.special_features = {
            'computer-use': {
                'models': ['claude-3-5-sonnet-20241022'],
                'description': 'Can control computer interfaces'
            },
            'vision': {
                'models': [
                    'claude-3-5-sonnet-20241022',
                    'claude-3-5-haiku-20241022',
                    'claude-3-opus-20240229',
                    'claude-3-sonnet-20240229',
                    'claude-3-haiku-20240307'
                ],
                'description': 'Can analyze and understand images'
            },
            'tool-use': {
                'models': [
                    'claude-3-5-sonnet-20241022',
                    'claude-3-5-haiku-20241022',
                    'claude-3-opus-20240229',
                    'claude-3-sonnet-20240229',
                    'claude-3-haiku-20240307'
                ],
                'description': 'Can use external tools and functions'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """Anthropic 모델 정보 수집"""
        models = []
        
        for model_id, info in self.model_info.items():
            model_data = info.copy()
            model_data['id'] = model_id
            
            # 사용 사례 추가
            use_cases = self.get_use_cases(model_id)
            if use_cases:
                model_data['use_cases'] = use_cases
            
            # 훈련 데이터 컷오프 추가
            model_data['training_cutoff'] = self.get_training_cutoff(model_id)
            
            models.append(model_data)
        
        return models
    
    def get_use_cases(self, model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'claude-3-5-sonnet-20241022': [
                'Complex reasoning',
                'Creative writing',
                'Code generation',
                'Computer automation',
                'Advanced analysis',
                'Image understanding'
            ],
            'claude-3-5-haiku-20241022': [
                'Customer support',
                'Content moderation',
                'Quick data extraction',
                'Simple automation',
                'Basic image analysis'
            ],
            'claude-3-opus-20240229': [
                'Research analysis',
                'Complex problem solving',
                'Advanced mathematics',
                'Expert-level tasks'
            ],
            'claude-3-sonnet-20240229': [
                'General assistance',
                'Content creation',
                'Data analysis',
                'Code review'
            ],
            'claude-3-haiku-20240307': [
                'Quick responses',
                'Simple queries',
                'Basic tasks',
                'High-volume processing'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def fetch_models(self) -> List[Dict]:
        """하드코딩된 모델 정보 반환"""
        models = []
        for model_id, info in self.model_info.items():
            model_data = {
                'id': model_id,
                'name': info['name'],
                'provider': 'anthropic',
                'description': info['description'],
                'pricing': {
                    'input': info['input_price'],
                    'output': info['output_price'],
                    'unit': '1M tokens'
                },
                'context_window': info['context_window'],
                'max_output': info['max_output'],
                'release_date': info.get('release_date', ''),
                'status': info['status'],
                'features': info['features'],
                'modalities': info['modalities'],
                'use_cases': self.get_use_cases(model_id),
                'training_cutoff': self.get_training_cutoff(model_id)
            }
            models.append(model_data)
        return models
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'claude-3-5-sonnet-20241022': '2024-04',
            'claude-3-5-haiku-20241022': '2024-07',
            'claude-3-opus-20240229': '2023-08',
            'claude-3-sonnet-20240229': '2023-08',
            'claude-3-haiku-20240307': '2023-08',
            'claude-2.1': '2023-01',
            'claude-2.0': '2023-01',
            'claude-instant-1.2': '2023-01'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            return self.model_info[model_id]
        return {}

if __name__ == "__main__":
    # 하드코딩 데이터 사용 (네트워크 제한 환경에서도 안정적)
    crawler = AnthropicCrawler()
    crawler.run()