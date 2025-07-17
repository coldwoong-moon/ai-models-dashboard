#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class DeepSeekCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('deepseek')
        
        # DeepSeek 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'deepseek-v3': {
                'name': 'DeepSeek V3',
                'description': 'Latest flagship model with 671B parameters and enhanced reasoning',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'coding', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2024-12-26',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            },
            'deepseek-v2.5': {
                'name': 'DeepSeek V2.5',
                'description': 'Enhanced version with improved coding and reasoning capabilities',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'coding', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2024-09-05',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            },
            'deepseek-coder-v2': {
                'name': 'DeepSeek Coder V2',
                'description': 'Specialized coding model with 236B parameters',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'coding', 'function-calling', 'code-completion'],
                'modalities': ['text'],
                'release_date': '2024-06-17',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            },
            'deepseek-chat': {
                'name': 'DeepSeek Chat',
                'description': 'General-purpose conversational AI model',
                'context_window': 32768,
                'max_output': 4096,
                'features': ['chat', 'reasoning'],
                'modalities': ['text'],
                'release_date': '2024-01-01',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            },
            'deepseek-coder': {
                'name': 'DeepSeek Coder',
                'description': 'Code-specialized model for programming tasks',
                'context_window': 16384,
                'max_output': 4096,
                'features': ['coding', 'code-completion', 'debug'],
                'modalities': ['text'],
                'release_date': '2024-01-01',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            },
            'deepseek-math': {
                'name': 'DeepSeek Math',
                'description': 'Mathematics and reasoning specialized model',
                'context_window': 32768,
                'max_output': 4096,
                'features': ['reasoning', 'math', 'problem-solving'],
                'modalities': ['text'],
                'release_date': '2024-02-01',
                'status': 'ga',
                'input_price': 0.14,
                'output_price': 0.28
            }
        }
        
        # 모델 카테고리별 특징
        self.model_categories = {
            'flagship': ['deepseek-v3', 'deepseek-v2.5'],
            'coding': ['deepseek-coder-v2', 'deepseek-coder'],
            'reasoning': ['deepseek-math', 'deepseek-v3'],
            'general': ['deepseek-chat']
        }
    
    def fetch_models(self) -> List[Dict]:
        """DeepSeek 모델 정보 수집"""
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
            
            # 특별 기능 추가
            model_data['special_features'] = self.get_special_features(model_id)
            
            models.append(model_data)
        
        return models
    
    def get_use_cases(self, model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'deepseek-v3': [
                'Complex reasoning tasks',
                'Advanced coding projects',
                'Research assistance',
                'Multi-step problem solving',
                'Technical writing',
                'Code review and analysis'
            ],
            'deepseek-v2.5': [
                'General programming',
                'Code generation',
                'Algorithm design',
                'Technical documentation',
                'System architecture'
            ],
            'deepseek-coder-v2': [
                'Software development',
                'Code completion',
                'Bug fixing',
                'Code refactoring',
                'API development',
                'Test generation'
            ],
            'deepseek-chat': [
                'General conversations',
                'Q&A systems',
                'Content creation',
                'Simple reasoning',
                'Educational assistance'
            ],
            'deepseek-coder': [
                'Code completion',
                'Simple programming tasks',
                'Script generation',
                'Code explanation'
            ],
            'deepseek-math': [
                'Mathematical problem solving',
                'Equation solving',
                'Proof generation',
                'Scientific calculations',
                'Statistical analysis'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'deepseek-v3': '2024-09',
            'deepseek-v2.5': '2024-07',
            'deepseek-coder-v2': '2024-04',
            'deepseek-chat': '2023-10',
            'deepseek-coder': '2023-10',
            'deepseek-math': '2023-12'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_special_features(self, model_id: str) -> List[str]:
        """모델별 특별 기능"""
        features_map = {
            'deepseek-v3': [
                'Multi-token prediction',
                'Mixture of experts architecture',
                'Enhanced reasoning chains',
                'Advanced function calling'
            ],
            'deepseek-v2.5': [
                'Improved coding accuracy',
                'Better instruction following',
                'Enhanced creativity'
            ],
            'deepseek-coder-v2': [
                'Code repository understanding',
                'Multi-language support',
                'Advanced debugging capabilities'
            ],
            'deepseek-math': [
                'Symbolic computation',
                'Step-by-step solutions',
                'Mathematical notation support'
            ]
        }
        
        return features_map.get(model_id, [])
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            details = self.model_info[model_id].copy()
            
            # 성능 벤치마크 정보 추가 (예시 데이터)
            benchmarks = self.get_benchmark_scores(model_id)
            if benchmarks:
                details['benchmarks'] = benchmarks
            
            return details
        return {}
    
    def get_benchmark_scores(self, model_id: str) -> Dict:
        """모델 벤치마크 점수 (공개된 정보 기반)"""
        benchmarks = {
            'deepseek-v3': {
                'humaneval': 85.7,
                'mbpp': 80.1,
                'gsm8k': 92.2,
                'math': 76.8,
                'mmlu': 88.5
            },
            'deepseek-coder-v2': {
                'humaneval': 90.2,
                'mbpp': 85.7,
                'codeforces': 75.2
            },
            'deepseek-math': {
                'gsm8k': 94.1,
                'math': 83.7,
                'aime': 67.8
            }
        }
        
        return benchmarks.get(model_id, {})

if __name__ == "__main__":
    crawler = DeepSeekCrawler()
    crawler.run()