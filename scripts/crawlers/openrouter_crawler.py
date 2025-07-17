#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List
import requests

class OpenRouterCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('openrouter')
        self.api_url = "https://openrouter.ai/api/v1/models"
        
        # OpenRouter에서 주요 모델들만 필터링하기 위한 리스트
        self.featured_models = [
            'openai/gpt-4o',
            'openai/gpt-4o-mini',
            'openai/o1-preview',
            'openai/o1-mini',
            'anthropic/claude-3.5-sonnet',
            'anthropic/claude-3.5-haiku',
            'anthropic/claude-3-opus',
            'google/gemini-2.0-flash-exp:free',
            'google/gemini-1.5-pro',
            'google/gemini-1.5-flash',
            'meta-llama/llama-3.3-70b-instruct',
            'meta-llama/llama-3.2-90b-vision-instruct',
            'mistralai/mistral-large',
            'mistralai/mistral-medium',
            'mistralai/pixtral-large',
            'deepseek/deepseek-chat',
            'deepseek/deepseek-coder',
            'cohere/command-r-plus',
            'x-ai/grok-2',
            'x-ai/grok-2-vision',
            'nvidia/llama-3.1-nemotron-70b-instruct',
            'qwen/qwen-2.5-72b-instruct',
            'perplexity/llama-3.1-sonar-large-128k-online',
            'alibaba/qwq-32b-preview'
        ]
    
    def fetch_models(self) -> List[Dict]:
        """OpenRouter API에서 모델 정보 가져오기"""
        try:
            response = self.session.get(self.api_url)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model in data.get('data', []):
                model_id = model.get('id', '')
                
                # 주요 모델만 필터링
                if not any(model_id.startswith(featured) for featured in self.featured_models):
                    continue
                
                # OpenRouter 형식을 우리 형식으로 변환
                model_data = self.convert_openrouter_format(model)
                models.append(model_data)
            
            return models
            
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
            # 오프라인 데이터 반환
            return self.get_offline_models()
    
    def convert_openrouter_format(self, model: Dict) -> Dict:
        """OpenRouter 형식을 표준 형식으로 변환"""
        model_id = model.get('id', '')
        
        # 가격 정보 추출 (OpenRouter는 $/token 단위)
        pricing = model.get('pricing', {})
        input_price = float(pricing.get('prompt', 0)) * 1000000  # $/token -> $/1M tokens
        output_price = float(pricing.get('completion', 0)) * 1000000
        
        # 제공업체 추출
        provider = model_id.split('/')[0] if '/' in model_id else 'unknown'
        
        # 모델 이름 정리
        name = model.get('name', model_id)
        if ':' in name:
            name = name.split(':')[0]
        
        # 컨텍스트 길이
        context_length = model.get('context_length', 0)
        
        # 기능 추출
        features = []
        if model.get('supports_functions'):
            features.append('function-calling')
        if model.get('supports_vision'):
            features.append('vision')
        if model.get('supports_json_mode'):
            features.append('json-mode')
        
        # 모달리티
        modalities = ['text']
        if model.get('supports_vision'):
            modalities.append('image')
        
        return {
            'id': model_id,
            'name': name,
            'description': model.get('description', ''),
            'input_price': round(input_price, 2),
            'output_price': round(output_price, 2),
            'context_window': context_length,
            'max_output': model.get('max_completion_tokens', 4096),
            'features': features,
            'modalities': modalities,
            'status': 'ga',
            'provider_original': provider,
            'via_openrouter': True
        }
    
    def get_offline_models(self) -> List[Dict]:
        """오프라인 백업 데이터"""
        return [
            {
                'id': 'openai/gpt-4o',
                'name': 'GPT-4o (via OpenRouter)',
                'description': 'Latest GPT-4 model via OpenRouter',
                'input_price': 2.50,
                'output_price': 10.00,
                'context_window': 128000,
                'max_output': 16384,
                'features': ['chat', 'vision', 'function-calling', 'json-mode'],
                'modalities': ['text', 'image'],
                'status': 'ga',
                'provider_original': 'openai',
                'via_openrouter': True
            },
            {
                'id': 'anthropic/claude-3.5-sonnet',
                'name': 'Claude 3.5 Sonnet (via OpenRouter)',
                'description': 'Claude 3.5 Sonnet via OpenRouter',
                'input_price': 3.00,
                'output_price': 15.00,
                'context_window': 200000,
                'max_output': 8192,
                'features': ['chat', 'vision', 'function-calling'],
                'modalities': ['text', 'image'],
                'status': 'ga',
                'provider_original': 'anthropic',
                'via_openrouter': True
            },
            {
                'id': 'google/gemini-1.5-pro',
                'name': 'Gemini 1.5 Pro (via OpenRouter)',
                'description': 'Google Gemini 1.5 Pro via OpenRouter',
                'input_price': 2.50,
                'output_price': 10.00,
                'context_window': 2097152,
                'max_output': 8192,
                'features': ['chat', 'vision', 'function-calling'],
                'modalities': ['text', 'image', 'video'],
                'status': 'ga',
                'provider_original': 'google',
                'via_openrouter': True
            },
            {
                'id': 'meta-llama/llama-3.3-70b-instruct',
                'name': 'Llama 3.3 70B (via OpenRouter)',
                'description': 'Meta Llama 3.3 70B instruction-tuned model',
                'input_price': 0.80,
                'output_price': 0.80,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat'],
                'modalities': ['text'],
                'status': 'ga',
                'provider_original': 'meta',
                'via_openrouter': True
            },
            {
                'id': 'deepseek/deepseek-chat',
                'name': 'DeepSeek Chat (via OpenRouter)',
                'description': 'DeepSeek V3 chat model',
                'input_price': 0.14,
                'output_price': 0.28,
                'context_window': 128000,
                'max_output': 8192,
                'features': ['chat', 'function-calling'],
                'modalities': ['text'],
                'status': 'ga',
                'provider_original': 'deepseek',
                'via_openrouter': True
            },
            {
                'id': 'x-ai/grok-2',
                'name': 'Grok 2 (via OpenRouter)',
                'description': 'xAI Grok 2 model',
                'input_price': 2.00,
                'output_price': 10.00,
                'context_window': 131072,
                'max_output': 4096,
                'features': ['chat'],
                'modalities': ['text'],
                'status': 'beta',
                'provider_original': 'x-ai',
                'via_openrouter': True
            },
            {
                'id': 'mistralai/mistral-large',
                'name': 'Mistral Large (via OpenRouter)',
                'description': 'Mistral AI flagship model',
                'input_price': 2.00,
                'output_price': 6.00,
                'context_window': 128000,
                'max_output': 4096,
                'features': ['chat', 'function-calling'],
                'modalities': ['text'],
                'status': 'ga',
                'provider_original': 'mistral',
                'via_openrouter': True
            },
            {
                'id': 'qwen/qwen-2.5-72b-instruct',
                'name': 'Qwen 2.5 72B (via OpenRouter)',
                'description': 'Alibaba Qwen 2.5 72B model',
                'input_price': 0.40,
                'output_price': 0.40,
                'context_window': 131072,
                'max_output': 8192,
                'features': ['chat'],
                'modalities': ['text'],
                'status': 'ga',
                'provider_original': 'alibaba',
                'via_openrouter': True
            }
        ]
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
        # OpenRouter는 실시간 API 조회가 필요
        try:
            response = self.session.get(f"{self.api_url}/{model_id}")
            if response.status_code == 200:
                return self.convert_openrouter_format(response.json())
        except:
            pass
        return {}

if __name__ == "__main__":
    crawler = OpenRouterCrawler()
    crawler.run()