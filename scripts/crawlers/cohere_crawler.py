#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class CohereCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('cohere')
        
        # Cohere 모델 정보 (2025년 1월 기준)
        self.model_info = {
            'command-r-plus': {
                'name': 'Command R+',
                'description': 'Advanced conversational AI optimized for complex reasoning and RAG',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'reasoning', 'rag', 'function-calling', 'multilingual'],
                'modalities': ['text'],
                'release_date': '2024-04-04',
                'status': 'ga',
                'input_price': 3.00,
                'output_price': 15.00
            },
            'command-r': {
                'name': 'Command R',
                'description': 'Balanced model for retrieval-augmented generation and conversation',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'reasoning', 'rag', 'function-calling', 'multilingual'],
                'modalities': ['text'],
                'release_date': '2024-03-11',
                'status': 'ga',
                'input_price': 0.50,
                'output_price': 1.50
            },
            'command': {
                'name': 'Command',
                'description': 'General-purpose conversational AI model',
                'context_window': 4096,
                'max_output': 4096,
                'features': ['chat', 'reasoning'],
                'modalities': ['text'],
                'release_date': '2023-06-01',
                'status': 'ga',
                'input_price': 1.00,
                'output_price': 2.00
            },
            'command-light': {
                'name': 'Command Light',
                'description': 'Faster, lighter version for simple tasks',
                'context_window': 4096,
                'max_output': 4096,
                'features': ['chat', 'fast-inference'],
                'modalities': ['text'],
                'release_date': '2023-06-01',
                'status': 'ga',
                'input_price': 0.30,
                'output_price': 0.60
            },
            'command-nightly': {
                'name': 'Command Nightly',
                'description': 'Experimental model with latest features',
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'reasoning', 'experimental'],
                'modalities': ['text'],
                'release_date': '2024-01-01',
                'status': 'experimental',
                'input_price': 15.00,
                'output_price': 15.00
            },
            'embed-english-v3.0': {
                'name': 'Embed English v3.0',
                'description': 'State-of-the-art English text embeddings',
                'context_window': 512,
                'max_output': 1024,
                'features': ['embeddings', 'semantic-search', 'clustering'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 0.10,
                'output_price': 0.00
            },
            'embed-multilingual-v3.0': {
                'name': 'Embed Multilingual v3.0',
                'description': 'Multilingual text embeddings supporting 100+ languages',
                'context_window': 512,
                'max_output': 1024,
                'features': ['embeddings', 'multilingual', 'semantic-search'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 0.10,
                'output_price': 0.00
            },
            'embed-english-light-v3.0': {
                'name': 'Embed English Light v3.0',
                'description': 'Lightweight English embeddings for high-throughput applications',
                'context_window': 512,
                'max_output': 1024,
                'features': ['embeddings', 'fast-inference', 'lightweight'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 0.10,
                'output_price': 0.00
            },
            'embed-multilingual-light-v3.0': {
                'name': 'Embed Multilingual Light v3.0',
                'description': 'Lightweight multilingual embeddings',
                'context_window': 512,
                'max_output': 1024,
                'features': ['embeddings', 'multilingual', 'lightweight'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 0.10,
                'output_price': 0.00
            },
            'rerank-english-v3.0': {
                'name': 'Rerank English v3.0',
                'description': 'Advanced reranking model for search relevance',
                'context_window': 4096,
                'max_output': 1,
                'features': ['reranking', 'search-optimization', 'relevance-scoring'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 0.00
            },
            'rerank-multilingual-v3.0': {
                'name': 'Rerank Multilingual v3.0',
                'description': 'Multilingual reranking for global search applications',
                'context_window': 4096,
                'max_output': 1,
                'features': ['reranking', 'multilingual', 'search-optimization'],
                'modalities': ['text'],
                'release_date': '2023-11-02',
                'status': 'ga',
                'input_price': 2.00,
                'output_price': 0.00
            }
        }
        
        # Cohere의 특별한 기능들
        self.special_capabilities = {
            'rag_optimized': {
                'models': ['command-r-plus', 'command-r'],
                'description': 'Optimized for Retrieval-Augmented Generation'
            },
            'multilingual_support': {
                'models': ['command-r-plus', 'command-r', 'embed-multilingual-v3.0', 'embed-multilingual-light-v3.0', 'rerank-multilingual-v3.0'],
                'description': 'Native support for 10+ languages'
            },
            'enterprise_features': {
                'models': ['command-r-plus', 'command-r'],
                'description': 'Enterprise-grade security and compliance'
            }
        }
    
    def fetch_models(self) -> List[Dict]:
        """Cohere 모델 정보 수집"""
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
            
            # Cohere만의 특별 기능 추가
            model_data['cohere_features'] = self.get_cohere_features(model_id)
            
            # 모델 타입 분류
            model_data['model_type'] = self.get_model_type(model_id)
            
            models.append(model_data)
        
        return models
    
    def get_use_cases(self, model_id: str) -> List[str]:
        """모델별 사용 사례"""
        use_cases_map = {
            'command-r-plus': [
                'Complex reasoning tasks',
                'RAG applications',
                'Enterprise chatbots',
                'Document analysis',
                'Knowledge base queries',
                'Multi-step workflows'
            ],
            'command-r': [
                'Retrieval-augmented generation',
                'Information synthesis',
                'Customer support',
                'Content generation',
                'Question answering'
            ],
            'command': [
                'General conversations',
                'Content creation',
                'Text summarization',
                'Simple Q&A'
            ],
            'command-light': [
                'High-throughput applications',
                'Real-time chat',
                'Simple text generation',
                'Cost-sensitive deployments'
            ],
            'command-nightly': [
                'Experimental features testing',
                'Cutting-edge capabilities',
                'Research applications'
            ],
            'embed-english-v3.0': [
                'Semantic search',
                'Text similarity',
                'Document clustering',
                'Recommendation systems',
                'Content classification'
            ],
            'embed-multilingual-v3.0': [
                'Cross-lingual search',
                'Multilingual clustering',
                'Global content analysis',
                'International applications'
            ],
            'embed-english-light-v3.0': [
                'High-volume embeddings',
                'Real-time similarity',
                'Edge deployments'
            ],
            'embed-multilingual-light-v3.0': [
                'Lightweight multilingual search',
                'Fast cross-lingual matching'
            ],
            'rerank-english-v3.0': [
                'Search result optimization',
                'Relevance scoring',
                'Information retrieval',
                'Query optimization'
            ],
            'rerank-multilingual-v3.0': [
                'Global search systems',
                'Multilingual relevance',
                'Cross-language retrieval'
            ]
        }
        
        return use_cases_map.get(model_id, [])
    
    def get_training_cutoff(self, model_id: str) -> str:
        """모델별 훈련 데이터 컷오프 날짜"""
        cutoff_dates = {
            'command-r-plus': '2024-01',
            'command-r': '2024-01',
            'command': '2023-03',
            'command-light': '2023-03',
            'command-nightly': '2024-01',
            'embed-english-v3.0': '2023-09',
            'embed-multilingual-v3.0': '2023-09',
            'embed-english-light-v3.0': '2023-09',
            'embed-multilingual-light-v3.0': '2023-09',
            'rerank-english-v3.0': '2023-09',
            'rerank-multilingual-v3.0': '2023-09'
        }
        
        return cutoff_dates.get(model_id, '')
    
    def get_cohere_features(self, model_id: str) -> List[str]:
        """Cohere만의 특별한 기능들"""
        features_map = {
            'command-r-plus': [
                'Advanced RAG capabilities',
                'Citation generation',
                'Multi-hop reasoning',
                'Enterprise security',
                'Tool use integration'
            ],
            'command-r': [
                'RAG optimization',
                'Source attribution',
                'Efficient retrieval',
                'Tool integration'
            ],
            'embed-english-v3.0': [
                'High-dimensional vectors',
                'Semantic understanding',
                'Fine-tuning capability'
            ],
            'embed-multilingual-v3.0': [
                '100+ language support',
                'Cross-lingual alignment',
                'Cultural context awareness'
            ],
            'rerank-english-v3.0': [
                'Relevance optimization',
                'Query understanding',
                'Result prioritization'
            ]
        }
        
        return features_map.get(model_id, [])
    
    def get_model_type(self, model_id: str) -> str:
        """모델 타입 분류"""
        if 'embed' in model_id:
            return 'embeddings'
        elif 'rerank' in model_id:
            return 'reranking'
        else:
            return 'generative'
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        if model_id in self.model_info:
            details = self.model_info[model_id].copy()
            
            # 성능 벤치마크 추가
            benchmarks = self.get_benchmark_scores(model_id)
            if benchmarks:
                details['benchmarks'] = benchmarks
            
            # 지원 언어 정보
            details['supported_languages'] = self.get_supported_languages(model_id)
            
            return details
        return {}
    
    def get_benchmark_scores(self, model_id: str) -> Dict:
        """모델 벤치마크 점수"""
        benchmarks = {
            'command-r-plus': {
                'mmlu': 75.0,
                'hellaswag': 82.0,
                'arc_challenge': 79.0,
                'gsm8k': 75.7
            },
            'command-r': {
                'mmlu': 68.0,
                'hellaswag': 78.0,
                'arc_challenge': 74.0,
                'gsm8k': 67.3
            }
        }
        
        return benchmarks.get(model_id, {})
    
    def get_supported_languages(self, model_id: str) -> List[str]:
        """모델이 지원하는 언어들"""
        multilingual_models = [
            'command-r-plus', 'command-r', 
            'embed-multilingual-v3.0', 'embed-multilingual-light-v3.0',
            'rerank-multilingual-v3.0'
        ]
        
        if model_id in multilingual_models:
            return [
                'English', 'French', 'Spanish', 'Italian', 'German', 
                'Portuguese', 'Japanese', 'Korean', 'Chinese', 'Arabic',
                'Hindi', 'Russian', 'Dutch', 'Polish', 'Swedish'
            ]
        else:
            return ['English']

if __name__ == "__main__":
    crawler = CohereCrawler()
    crawler.run()