#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class XAICrawler(BaseCrawler):
    def __init__(self):
        super().__init__('xai')
        
        # xAI (Grok) 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'grok-2': {
                'name': 'Grok 2',
                'description': 'xAI flagship model with enhanced reasoning and real-time knowledge',
                'context_window': 131072,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'real-time-data', 'humor'],
                'modalities': ['text'],
                'release_date': '2024-08-13',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 10.00
            },
            'grok-2-vision': {
                'name': 'Grok 2 Vision',
                'description': 'Grok 2 with advanced vision capabilities for image understanding',
                'context_window': 131072,
                'max_output': 8192,
                'features': ['chat', 'vision', 'reasoning', 'real-time-data', 'humor'],
                'modalities': ['text', 'image'],
                'release_date': '2024-08-13',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 10.00
            },
            'grok-1.5-vision': {
                'name': 'Grok 1.5 Vision',
                'description': 'Enhanced version with vision capabilities and improved reasoning',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'reasoning', 'real-time-data'],
                'modalities': ['text', 'image'],
                'release_date': '2024-04-12',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 10.00
            },
            'grok-1.5': {
                'name': 'Grok 1.5',
                'description': 'Improved version with better coding and math capabilities',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'reasoning', 'coding', 'math'],
                'modalities': ['text'],
                'release_date': '2024-03-28',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 10.00
            },
            'grok-1': {
                'name': 'Grok 1',
                'description': 'Original Grok model with witty and rebellious personality',
                'context_window': 8192,
                'max_output': 4096,
                'features': ['chat', 'humor', 'real-time-data'],
                'modalities': ['text'],
                'release_date': '2023-11-04',
                'status': 'deprecated',
                'input_price': 2.00,
                'output_price': 10.00
            },
            'grok-beta': {
                'name': 'Grok Beta',
                'description': 'Early access model with experimental features',
                'context_window': 25000,
                'max_output': 4096,
                'features': ['chat', 'reasoning', 'experimental'],
                'modalities': ['text'],
                'release_date': '2023-12-07',
                'status': 'beta',
                'input_price': 5.00,
                'output_price': 15.00
            }
        }
        
        # xAI만의 특별한 기능들
        self.special_capabilities = {
            'real_time_data': {
                'models': ['grok-2', 'grok-2-vision', 'grok-1.5-vision', 'grok-1'],
                'description': 'Access to real-time information via X platform'
            },
            'humor_personality': {
                'models': ['grok-2', 'grok-2-vision', 'grok-1', 'grok-beta'],
                'description': 'Witty and humorous conversational style'
            },
            'rebellious_mode': {
                'models': ['grok-1', 'grok-beta'],
                'description': 'Willing to answer spicy questions that others avoid'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """xAI 모델 정보 수집"""
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
            
            # Grok만의 특별 기능 추가
            model_data['grok_features'] = self.get_grok_features(model_id)
            
            # X 플랫폼 통합 정보
            model_data['x_integration'] = self.get_x_integration_info(model_id)
            
            models.append(model_data)
        
        return models
    
    def get_use_cases(self, model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'grok-2': [
                'Real-time news analysis',
                'Social media insights',
                'Current events discussion',
                'Trend analysis',
                'Interactive conversations',
                'Research with live data'
            ],
            'grok-2-vision': [
                'Image analysis with context',
                'Visual content creation',
                'Meme generation and analysis',
                'Social media content review',
                'Real-time image understanding'
            ],
            'grok-1.5-vision': [
                'Document analysis',
                'Chart and graph interpretation',
                'Visual Q&A',
                'Educational content creation'
            ],
            'grok-1.5': [
                'Coding assistance',
                'Mathematical problem solving',
                'Technical discussions',
                'Educational tutoring'
            ],
            'grok-1': [
                'Casual conversations',
                'Entertainment discussions',
                'Humorous content generation',
                'Alternative perspectives'
            ],
            'grok-beta': [
                'Experimental features testing',
                'Edge case discussions',
                'Unconventional problem solving'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'grok-2': '2024-07',
            'grok-2-vision': '2024-07',
            'grok-1.5-vision': '2024-03',
            'grok-1.5': '2024-03',
            'grok-1': '2023-10',
            'grok-beta': '2023-11'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_grok_features(self, model_id: str) -> List[str]:
        """Grok만의 특별한 기능들"""
        features_map = {
            'grok-2': [
                'Witty personality',
                'Real-time X data access',
                'Trend awareness',
                'Anti-woke stance',
                'Rebellious answers'
            ],
            'grok-2-vision': [
                'Visual humor understanding',
                'Meme analysis',
                'Image-based real-time context',
                'Visual trend detection'
            ],
            'grok-1.5-vision': [
                'Enhanced visual reasoning',
                'Document understanding',
                'Multi-modal humor'
            ],
            'grok-1.5': [
                'Improved reasoning',
                'Better coding abilities',
                'Enhanced math skills'
            ],
            'grok-1': [
                'Original personality',
                'Unfiltered responses',
                'Humorous interactions'
            ],
            'grok-beta': [
                'Experimental features',
                'Cutting-edge capabilities',
                'Unpredictable responses'
            ]
        }
        
        return features_map.get(model_id, [])
    
    def get_x_integration_info(self, model_id: str) -> Dict:
        """X 플랫폼 통합 정보"""
        integration_info = {
            'grok-2': {
                'real_time_access': True,
                'x_data_sources': ['tweets', 'trends', 'news'],
                'update_frequency': 'real-time',
                'content_filtering': 'minimal'
            },
            'grok-2-vision': {
                'real_time_access': True,
                'x_data_sources': ['tweets', 'images', 'trends'],
                'update_frequency': 'real-time',
                'content_filtering': 'minimal'
            },
            'grok-1.5-vision': {
                'real_time_access': True,
                'x_data_sources': ['tweets', 'trends'],
                'update_frequency': 'hourly',
                'content_filtering': 'light'
            },
            'grok-1.5': {
                'real_time_access': False,
                'x_data_sources': [],
                'update_frequency': 'none',
                'content_filtering': 'moderate'
            }
        }
        
        return integration_info.get(model_id, {
            'real_time_access': False,
            'x_data_sources': [],
            'update_frequency': 'none',
            'content_filtering': 'standard'
        })
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            details = self.model_info[model_id].copy()
            
            # 성능 벤치마크 추가 (공개된 정보 기반)
            benchmarks = self.get_benchmark_scores(model_id)
            if benchmarks:
                details['benchmarks'] = benchmarks
            
            # 독특한 특성 추가
            details['personality_traits'] = self.get_personality_traits(model_id)
            
            return details
        return {}
    
    def get_benchmark_scores(self, model_id: str) -> Dict:
        """모델 벤치마크 점수"""
        benchmarks = {
            'grok-2': {
                'mmlu': 84.0,
                'gsm8k': 88.5,
                'humaneval': 72.4,
                'math': 56.8,
                'reading_comprehension': 89.2
            },
            'grok-1.5': {
                'mmlu': 73.0,
                'gsm8k': 82.3,
                'humaneval': 63.2,
                'math': 42.5
            }
        }
        
        return benchmarks.get(model_id, {})
    
    def get_personality_traits(self, model_id: str) -> List[str]:
        """모델의 성격적 특징"""
        traits_map = {
            'grok-2': [
                'Witty and humorous',
                'Curious and inquisitive',
                'Rebellious streak',
                'Anti-establishment',
                'Direct and honest'
            ],
            'grok-2-vision': [
                'Visually witty',
                'Creative with images',
                'Meme-savvy',
                'Culturally aware'
            ],
            'grok-1': [
                'Original rebel personality',
                'Unfiltered responses',
                'Dark humor capable',
                'Question authority'
            ]
        }
        
        return traits_map.get(model_id, ['Standard AI assistant'])

if __name__ == "__main__":
    crawler = XAICrawler()
    crawler.run()