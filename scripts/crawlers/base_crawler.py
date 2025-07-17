import json
import os
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
import requests
from typing import Dict, List, Optional

class BaseCrawler(ABC):
    """모든 크롤러의 기본 클래스"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_path = self.base_dir / f"data/models/{provider_name}.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    @abstractmethod
    def fetch_models(self) -> List[Dict]:
        """각 제공업체에서 모델 정보를 가져오는 메서드"""
        pass
    
    @abstractmethod
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보를 가져오는 메서드"""
        pass
    
    def normalize_model_data(self, raw_model: Dict) -> Dict:
        """모델 데이터를 표준 형식으로 정규화"""
        return {
            'id': raw_model.get('id', ''),
            'name': raw_model.get('name', ''),
            'provider': self.provider_name,
            'description': raw_model.get('description', ''),
            'pricing': {
                'input': raw_model.get('input_price', 0),
                'output': raw_model.get('output_price', 0),
                'unit': '1M tokens'
            },
            'context_window': raw_model.get('context_window', 0),
            'max_output': raw_model.get('max_output', 0),
            'release_date': raw_model.get('release_date', ''),
            'status': raw_model.get('status', 'ga'),  # ga, beta, preview, deprecated
            'features': raw_model.get('features', []),
            'modalities': raw_model.get('modalities', ['text']),
            'use_cases': raw_model.get('use_cases', []),
            'training_cutoff': raw_model.get('training_cutoff', ''),
            'last_updated': datetime.now().isoformat()
        }
    
    def save_data(self, models: List[Dict]):
        """JSON 파일로 데이터 저장"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            'provider': self.provider_name,
            'provider_info': self.get_provider_info(),
            'last_updated': datetime.now().isoformat(),
            'models': models
        }
        
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
    def get_provider_info(self) -> Dict:
        """제공업체 정보 반환"""
        provider_info = {
            'openai': {
                'name': 'OpenAI',
                'website': 'https://openai.com',
                'api_endpoint': 'https://api.openai.com/v1'
            },
            'anthropic': {
                'name': 'Anthropic',
                'website': 'https://anthropic.com',
                'api_endpoint': 'https://api.anthropic.com'
            },
            'google': {
                'name': 'Google AI',
                'website': 'https://ai.google.dev',
                'api_endpoint': 'https://generativelanguage.googleapis.com'
            },
            'openrouter': {
                'name': 'OpenRouter',
                'website': 'https://openrouter.ai',
                'api_endpoint': 'https://openrouter.ai/api/v1'
            },
            'mistral': {
                'name': 'Mistral AI',
                'website': 'https://mistral.ai',
                'api_endpoint': 'https://api.mistral.ai'
            },
            'cohere': {
                'name': 'Cohere',
                'website': 'https://cohere.com',
                'api_endpoint': 'https://api.cohere.ai'
            }
        }
        
        return provider_info.get(self.provider_name, {
            'name': self.provider_name.title(),
            'website': '',
            'api_endpoint': ''
        })
    
    def parse_price(self, price_text: str) -> float:
        """가격 텍스트를 숫자로 변환"""
        import re
        # "$2.50 / 1M tokens" -> 2.50
        # "2.50" -> 2.50
        if isinstance(price_text, (int, float)):
            return float(price_text)
            
        match = re.search(r'\$?(\d+\.?\d*)', str(price_text))
        return float(match.group(1)) if match else 0.0
    
    def run(self):
        """크롤러 실행"""
        try:
            print(f"🤖 Starting {self.provider_name} crawler...")
            models = self.fetch_models()
            
            # 모델 데이터 정규화
            normalized_models = []
            for model in models:
                try:
                    normalized = self.normalize_model_data(model)
                    normalized_models.append(normalized)
                except Exception as e:
                    print(f"❌ Error normalizing model {model.get('id', 'unknown')}: {e}")
                    continue
            
            self.save_data(normalized_models)
            print(f"✅ Saved {len(normalized_models)} {self.provider_name} models")
            
        except Exception as e:
            print(f"❌ Error in {self.provider_name} crawler: {e}")
            # 빈 데이터라도 저장하여 전체 프로세스가 중단되지 않도록 함
            self.save_data([])