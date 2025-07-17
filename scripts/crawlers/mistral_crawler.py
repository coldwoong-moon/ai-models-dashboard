#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class MistralCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('mistral')
        
        # Mistral AI 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'mistral-large-2411': {
                'name': 'Mistral Large 2411',
                'description': 'Latest flagship model with enhanced reasoning and multilingual capabilities',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'function-calling', 'json-mode', 'multilingual'],
                'modalities': ['text'],
                'release_date': '2024-11-15',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 6.00
            },
            'mistral-large-2407': {
                'name': 'Mistral Large 2407',
                'description': 'Previous version of the flagship model',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'function-calling', 'json-mode', 'multilingual'],
                'modalities': ['text'],
                'release_date': '2024-07-24',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 6.00
            },
            'mistral-medium': {
                'name': 'Mistral Medium',
                'description': 'Balanced model for general-purpose tasks',
                'context_window': 32000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'multilingual'],
                'modalities': ['text'],
                'release_date': '2023-12-11',
                'status': 'ga',
                'input_price': 2.70,
                'output_price': 8.10
            },
            'mistral-small-2409': {
                'name': 'Mistral Small 2409',
                'description': 'Cost-effective model for simple tasks',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'function-calling', 'json-mode'],
                'modalities': ['text'],
                'release_date': '2024-09-18',
                'status': 'ga',
                'input_price': 0.20,
                'output_price': 0.60
            },
            'mistral-nemo': {
                'name': 'Mistral Nemo',
                'description': '12B parameter model built in partnership with NVIDIA',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'multilingual', 'apache-license'],
                'modalities': ['text'],
                'release_date': '2024-07-18',
                'status': 'ga',
                'input_price': 0.15,
                'output_price': 0.15
            },
            'pixtral-large-2411': {
                'name': 'Pixtral Large 2411',
                'description': 'Latest multimodal model with vision capabilities',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'reasoning', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'release_date': '2024-11-21',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 6.00
            },
            'pixtral-12b': {
                'name': 'Pixtral 12B',
                'description': 'Open-source multimodal model with vision',
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'reasoning', 'apache-license'],
                'modalities': ['text', 'image'],
                'release_date': '2024-09-11',
                'status': 'ga',
                'input_price': 0.15,
                'output_price': 0.15
            },
            'codestral-2405': {
                'name': 'Codestral 2405',
                'description': 'Code generation model trained on 80+ programming languages',
                'context_window': 32000,
                'max_output': 8192,
                'features': ['coding', 'code-completion', 'function-calling'],
                'modalities': ['text'],
                'release_date': '2024-05-29',
                'status': 'ga',
                'input_price': 0.20,
                'output_price': 0.60
            },
            'codestral-mamba-2407': {
                'name': 'Codestral Mamba 2407',
                'description': 'Code generation model with Mamba architecture for faster inference',
                'context_window': 256000,
                'max_output': 8192,
                'features': ['coding', 'code-completion', 'long-context', 'fast-inference'],
                'modalities': ['text'],
                'release_date': '2024-07-16',
                'status': 'ga',
                'input_price': 0.25,
                'output_price': 0.25
            },
            'mistral-7b': {
                'name': 'Mistral 7B',
                'description': 'Original open-source model with Apache 2.0 license',
                'context_window': 32000,
                'max_output': 8192,
                'features': ['chat', 'reasoning', 'apache-license', 'open-source'],
                'modalities': ['text'],
                'release_date': '2023-09-27',
                'status': 'ga',
                'input_price': 0.25,
                'output_price': 0.25
            }
        }
        
        # 특별 기능들
        self.special_features = {
            'multilingual': {
                'models': ['mistral-large-2411', 'mistral-large-2407', 'mistral-medium', 'mistral-nemo'],
                'description': 'Excellent support for multiple languages',
                'languages': ['English', 'French', 'German', 'Spanish', 'Italian', 'Portuguese', 'Russian', 'Chinese', 'Japanese', 'Korean']
            },
            'apache_license': {
                'models': ['mistral-nemo', 'pixtral-12b', 'mistral-7b'],
                'description': 'Available under Apache 2.0 license for commercial use'
            },
            'long_context': {
                'models': ['codestral-mamba-2407'],
                'description': 'Optimized for very long context processing'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """Mistral AI 모델 정보 수집"""
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
            model_data['mistral_features'] = self.get_mistral_features(model_id)
            
            # 라이선스 정보
            model_data['license_info'] = self.get_license_info(model_id)
            
            models.append(model_data)
        
        return models
    
    def get_use_cases(self, model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'mistral-large-2411': [
                'Complex reasoning tasks',
                'Multilingual applications',
                'Enterprise chatbots',
                'Content generation',
                'Function calling applications',
                'JSON structured outputs'
            ],
            'mistral-large-2407': [
                'General-purpose AI applications',
                'Customer support',
                'Content creation',
                'Research assistance'
            ],
            'mistral-medium': [
                'Balanced performance tasks',
                'Educational applications',
                'Content moderation',
                'Translation services'
            ],
            'mistral-small-2409': [
                'Simple Q&A',
                'Basic text generation',
                'Cost-sensitive applications',
                'High-volume processing'
            ],
            'mistral-nemo': [
                'On-device deployment',
                'Privacy-sensitive applications',
                'Custom fine-tuning',
                'Edge computing'
            ],
            'pixtral-large-2411': [
                'Visual content analysis',
                'Multimodal applications',
                'Document understanding',
                'Image captioning',
                'Visual Q&A'
            ],
            'pixtral-12b': [
                'Open-source vision projects',
                'Research applications',
                'Custom multimodal solutions'
            ],
            'codestral-2405': [
                'Code generation',
                'Programming assistance',
                'Code completion',
                'Software development',
                'Algorithm implementation'
            ],
            'codestral-mamba-2407': [
                'Large codebase analysis',
                'Long code generation',
                'Fast inference coding tasks',
                'Real-time code completion'
            ],
            'mistral-7b': [
                'Open-source projects',
                'Research and experimentation',
                'Custom fine-tuning',
                'Educational purposes'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'mistral-large-2411': '2024-09',
            'mistral-large-2407': '2024-05',
            'mistral-medium': '2023-10',
            'mistral-small-2409': '2024-07',
            'mistral-nemo': '2024-06',
            'pixtral-large-2411': '2024-09',
            'pixtral-12b': '2024-07',
            'codestral-2405': '2024-03',
            'codestral-mamba-2407': '2024-05',
            'mistral-7b': '2023-07'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_mistral_features(self, model_id: str) -> List[str]:
        """Mistral만의 특별한 기능들"""
        features_map = {
            'mistral-large-2411': [
                'Advanced function calling',
                'Excellent multilingual support',
                'JSON mode for structured outputs',
                'Enhanced reasoning capabilities'
            ],
            'mistral-nemo': [
                'NVIDIA partnership optimizations',
                'Apache 2.0 license',
                'Efficient 12B parameters',
                'Commercial-friendly'
            ],
            'pixtral-large-2411': [
                'State-of-the-art vision understanding',
                'Multimodal reasoning',
                'High-resolution image processing'
            ],
            'codestral-2405': [
                '80+ programming languages',
                'Fill-in-the-middle capability',
                'Code explanation and documentation'
            ],
            'codestral-mamba-2407': [
                'Mamba architecture for speed',
                'Very long context (256K)',
                'Faster inference than transformers'
            ]
        }
        
        return features_map.get(model_id, [])
    
    def get_license_info(self, model_id: str) -> Dict:
        """모델 라이선스 정보"""
        apache_models = ['mistral-nemo', 'pixtral-12b', 'mistral-7b']
        
        if model_id in apache_models:
            return {
                'type': 'Apache 2.0',
                'commercial_use': True,
                'modification_allowed': True,
                'distribution_allowed': True,
                'source_available': True
            }
        else:
            return {
                'type': 'Mistral AI Commercial',
                'commercial_use': True,
                'modification_allowed': False,
                'distribution_allowed': False,
                'source_available': False
            }
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            details = self.model_info[model_id].copy()
            
            # 성능 벤치마크 추가
            benchmarks = self.get_benchmark_scores(model_id)
            if benchmarks:
                details['benchmarks'] = benchmarks
            
            return details
        return {}
    
    def get_benchmark_scores(self, model_id: str) -> Dict:
        """모델 벤치마크 점수"""
        benchmarks = {
            'mistral-large-2411': {
                'mmlu': 84.0,
                'gsm8k': 93.0,
                'humaneval': 85.0,
                'math': 74.0,
                'ifeval': 88.0
            },
            'mistral-nemo': {
                'mmlu': 68.0,
                'gsm8k': 74.0,
                'humaneval': 62.0,
                'hellaswag': 83.5
            },
            'codestral-2405': {
                'humaneval': 81.1,
                'mbpp': 70.6,
                'eval_plus': 75.8
            }
        }
        
        return benchmarks.get(model_id, {})

if __name__ == "__main__":
    # 웹 스크래핑 버전 사용
    from mistral_web_scraper import MistralCrawlerV2
    crawler = MistralCrawlerV2()
    crawler.run()