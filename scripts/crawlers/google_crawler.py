#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class GoogleCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('google')
        
        # Google AI 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'gemini-2.0-flash-exp': {
                'name': 'Gemini 2.0 Flash (Experimental)',
                'description': 'Next generation multimodal model with enhanced capabilities',
                'context_window': 1048576,  # 1M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'function-calling', 'json-mode', 'multimodal-live'],
                'modalities': ['text', 'image', 'audio', 'video'],
                'release_date': '2024-12-11',
                'status': 'experimental',
                'input_price': 0.00,  # Free during experimental phase
                'output_price': 0.00
            },
            'gemini-1.5-pro': {
                'name': 'Gemini 1.5 Pro',
                'description': 'Advanced multimodal model with long context',
                'context_window': 2097152,  # 2M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'video', 'function-calling', 'json-mode', 'code-execution'],
                'modalities': ['text', 'image', 'audio', 'video'],
                'release_date': '2024-05-14',
                'status': 'ga',
                'input_price': 1.25,  # Per 1M tokens (≤128K context)
                'output_price': 5.00,
                'pricing_tiers': {
                    '128k': {'input': 1.25, 'output': 5.00},
                    '1m': {'input': 2.50, 'output': 10.00},
                    '2m': {'input': 5.00, 'output': 20.00}
                }
            },
            'gemini-1.5-flash': {
                'name': 'Gemini 1.5 Flash',
                'description': 'Fast multimodal model optimized for high-volume tasks',
                'context_window': 1048576,  # 1M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'audio', 'video', 'function-calling', 'json-mode', 'code-execution'],
                'modalities': ['text', 'image', 'audio', 'video'],
                'release_date': '2024-05-24',
                'status': 'ga',
                'input_price': 0.075,  # Per 1M tokens (≤128K context)
                'output_price': 0.30,
                'pricing_tiers': {
                    '128k': {'input': 0.075, 'output': 0.30},
                    '1m': {'input': 0.15, 'output': 0.60}
                }
            },
            'gemini-1.5-flash-8b': {
                'name': 'Gemini 1.5 Flash-8B',
                'description': 'Smaller, faster variant of Flash optimized for speed',
                'context_window': 1048576,  # 1M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-10-03',
                'status': 'ga',
                'input_price': 0.0375,  # Per 1M tokens (≤128K context)
                'output_price': 0.15,
                'pricing_tiers': {
                    '128k': {'input': 0.0375, 'output': 0.15},
                    '1m': {'input': 0.075, 'output': 0.30}
                }
            },
            'gemini-1.0-pro': {
                'name': 'Gemini 1.0 Pro',
                'description': 'First generation Gemini model',
                'context_window': 32768,
                'max_output': 8192,
                'features': ['chat', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2023-12-06',
                'status': 'ga',
                'input_price': 0.50,
                'output_price': 1.50
            },
            'gemini-exp-1206': {
                'name': 'Gemini Experimental 1206',
                'description': 'Experimental model with enhanced reasoning',
                'context_window': 2097152,  # 2M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'reasoning', 'function-calling'],
                'modalities': ['text', 'image'],
                'release_date': '2024-12-06',
                'status': 'experimental',
                'input_price': 0.00,  # Free during experimental
                'output_price': 0.00
            },
            'gemini-exp-1121': {
                'name': 'Gemini Experimental 1121',
                'description': 'Experimental model focused on quality improvements',
                'context_window': 2097152,  # 2M tokens
                'max_output': 8192,
                'features': ['chat', 'vision', 'function-calling'],
                'modalities': ['text', 'image'],
                'release_date': '2024-11-21',
                'status': 'experimental',
                'input_price': 0.00,
                'output_price': 0.00
            },
            'learnlm-1.5-pro-experimental': {
                'name': 'LearnLM 1.5 Pro',
                'description': 'Experimental model optimized for learning and education',
                'context_window': 2097152,  # 2M tokens
                'max_output': 8192,
                'features': ['chat', 'education', 'tutoring'],
                'modalities': ['text'],
                'release_date': '2024-12-19',
                'status': 'experimental',
                'input_price': 0.00,
                'output_price': 0.00
            }
        }
        
        # 특별 기능 정보
        self.special_features = {
            'code-execution': {
                'models': ['gemini-1.5-pro', 'gemini-1.5-flash'],
                'description': 'Can execute Python code in sandboxed environment'
            },
            'multimodal-live': {
                'models': ['gemini-2.0-flash-exp'],
                'description': 'Real-time multimodal streaming capabilities'
            },
            'video-understanding': {
                'models': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash-exp'],
                'description': 'Can analyze and understand video content'
            },
            'audio-understanding': {
                'models': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash-exp'],
                'description': 'Can process and understand audio inputs'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """Google AI 모델 정보 수집"""
        models = []
        
        for model_id, info in self.model_info.items():
            model_data = info.copy()
            model_data['id'] = model_id
            
            # pricing_tiers가 있는 경우 기본 가격 정보 제거
            if 'pricing_tiers' in model_data:
                # 가장 작은 컨텍스트 윈도우의 가격을 기본값으로 사용
                tiers = model_data['pricing_tiers']
                default_tier = sorted(tiers.keys())[0]
                model_data['input_price'] = tiers[default_tier]['input']
                model_data['output_price'] = tiers[default_tier]['output']
            
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
            'gemini-2.0-flash-exp': [
                'Real-time AI agents',
                'Multimodal streaming',
                'Interactive applications',
                'Live translation',
                'Video analysis'
            ],
            'gemini-1.5-pro': [
                'Document analysis',
                'Long-form content',
                'Code generation',
                'Video understanding',
                'Complex reasoning',
                'Data analysis with code execution'
            ],
            'gemini-1.5-flash': [
                'High-volume tasks',
                'Quick responses',
                'Content moderation',
                'Real-time applications',
                'Multimodal chatbots'
            ],
            'gemini-1.5-flash-8b': [
                'Edge deployment',
                'Low-latency applications',
                'Cost-sensitive tasks',
                'Simple multimodal queries'
            ],
            'gemini-1.0-pro': [
                'Text generation',
                'Chatbots',
                'Content creation',
                'Basic reasoning'
            ],
            'learnlm-1.5-pro-experimental': [
                'Educational content',
                'Personalized tutoring',
                'Learning assistance',
                'Curriculum development'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'gemini-2.0-flash-exp': '2024-08',
            'gemini-1.5-pro': '2024-02',
            'gemini-1.5-flash': '2024-05',
            'gemini-1.5-flash-8b': '2024-08',
            'gemini-1.0-pro': '2023-04',
            'gemini-exp-1206': '2024-08',
            'gemini-exp-1121': '2024-08',
            'learnlm-1.5-pro-experimental': '2024-11'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            return self.model_info[model_id]
        return {}

if __name__ == "__main__":
    crawler = GoogleCrawler()
    crawler.run()