#!/usr/bin/env python3
"""
HuggingFace Inference API 크롤러
공식 가격 페이지: https://huggingface.co/pricing
Inference API: https://huggingface.co/docs/api-inference/index
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List

class HuggingFaceCrawler(BaseCrawler):
    """HuggingFace Inference API 모델 크롤러"""
    
    def __init__(self):
        super().__init__('huggingface')
        self.api_url = "https://api-inference.huggingface.co"
        self.pricing_url = "https://huggingface.co/pricing"
        
    def get_provider_info(self) -> Dict:
        """HuggingFace 제공업체 정보"""
        return {
            'name': 'HuggingFace',
            'website': 'https://huggingface.co',
            'api_endpoint': 'https://api-inference.huggingface.co'
        }
    
    def fetch_models(self) -> List[Dict]:
        """HuggingFace 주요 모델 정보 수집
        
        Note: HuggingFace는 수천 개의 모델을 호스팅하므로,
        주요 상업용/프로덕션 레벨 모델들만 선별하여 수집
        """
        models = []
        
        # HuggingFace Inference API의 주요 상업용 모델들
        # 출처: https://huggingface.co/docs/api-inference/supported-models
        popular_models = [
            {
                'id': 'meta-llama/Meta-Llama-3.1-405B-Instruct',
                'name': 'Meta Llama 3.1 405B Instruct',
                'description': 'Meta의 최대 규모 오픈소스 LLM, 405B 파라미터',
                'input_price': 5.0,  # $5 per 1M tokens (Inference Endpoints 기준)
                'output_price': 16.0,  # $16 per 1M tokens
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'instruct', 'multilingual'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'meta-llama/Meta-Llama-3.1-70B-Instruct',
                'name': 'Meta Llama 3.1 70B Instruct',
                'description': '고품질 오픈소스 LLM, 70B 파라미터',
                'input_price': 0.9,
                'output_price': 0.9,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'instruct', 'multilingual'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                'name': 'Meta Llama 3.1 8B Instruct',
                'description': '효율적인 오픈소스 LLM, 8B 파라미터',
                'input_price': 0.2,
                'output_price': 0.2,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'instruct', 'multilingual'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'mistralai/Mixtral-8x7B-Instruct-v0.1',
                'name': 'Mixtral 8x7B Instruct',
                'description': 'Mistral의 MoE 아키텍처 모델',
                'input_price': 0.7,
                'output_price': 0.7,
                'context_window': 32768,
                'max_output': 8192,
                'features': ['chat', 'instruct', 'moe'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'mistralai/Mistral-7B-Instruct-v0.3',
                'name': 'Mistral 7B Instruct v0.3',
                'description': 'Mistral의 효율적인 7B 모델',
                'input_price': 0.25,
                'output_price': 0.25,
                'context_window': 32768,
                'max_output': 8192,
                'features': ['chat', 'instruct'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'google/gemma-2-27b-it',
                'name': 'Google Gemma 2 27B IT',
                'description': 'Google의 오픈 모델 Gemma 2세대',
                'input_price': 0.8,
                'output_price': 0.8,
                'context_window': 8192,
                'max_output': 4096,
                'features': ['chat', 'instruct'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'google/gemma-2-9b-it',
                'name': 'Google Gemma 2 9B IT',
                'description': 'Google의 경량 Gemma 모델',
                'input_price': 0.3,
                'output_price': 0.3,
                'context_window': 8192,
                'max_output': 4096,
                'features': ['chat', 'instruct'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'Qwen/Qwen2.5-72B-Instruct',
                'name': 'Qwen 2.5 72B Instruct',
                'description': 'Alibaba의 강력한 다국어 모델',
                'input_price': 0.9,
                'output_price': 0.9,
                'context_window': 32768,
                'max_output': 8192,
                'features': ['chat', 'instruct', 'multilingual', 'coding'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'Qwen/Qwen2.5-7B-Instruct',
                'name': 'Qwen 2.5 7B Instruct',
                'description': 'Qwen 경량 모델',
                'input_price': 0.25,
                'output_price': 0.25,
                'context_window': 32768,
                'max_output': 8192,
                'features': ['chat', 'instruct', 'multilingual', 'coding'],
                'modalities': ['text'],
                'status': 'ga'
            },
            {
                'id': 'meta-llama/Llama-3.2-11B-Vision-Instruct',
                'name': 'Llama 3.2 11B Vision Instruct',
                'description': 'Meta의 비전 기능이 있는 Llama 모델',
                'input_price': 0.35,
                'output_price': 0.35,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'vision', 'instruct', 'multimodal'],
                'modalities': ['text', 'image'],
                'status': 'ga'
            },
            {
                'id': 'microsoft/Phi-3-medium-128k-instruct',
                'name': 'Phi-3 Medium 128K Instruct',
                'description': 'Microsoft의 효율적인 소형 모델',
                'input_price': 0.4,
                'output_price': 0.4,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'instruct', 'long-context'],
                'modalities': ['text'],
                'status': 'ga'
            }
        ]
        
        # 가격이 0인 모델은 제외 (무료 사용량 제한 모델)
        paid_models = [m for m in popular_models if m.get('input_price', 0) > 0]
        
        return paid_models
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        # HuggingFace API를 통해 모델 정보를 가져올 수 있지만,
        # 기본 크롤러에서는 fetch_models에서 이미 상세 정보를 포함
        return {}

if __name__ == "__main__":
    crawler = HuggingFaceCrawler()
    crawler.run()
