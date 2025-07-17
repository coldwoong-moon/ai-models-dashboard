#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawlers.base_crawler import BaseCrawler
from typing import Dict, List
import requests
import re

class OpenRouterCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('openrouter')
        self.api_url = "https://openrouter.ai/api/v1/models"
        
    def fetch_models(self) -> List[Dict]:
        """OpenRouter API에서 모델 정보 가져오기"""
        try:
            response = self.session.get(self.api_url)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model in data.get('data', []):
                # Deprecated 모델 제외
                if self.is_deprecated(model):
                    continue
                
                # OpenRouter 형식을 우리 형식으로 변환
                model_data = self.convert_openrouter_format(model)
                if model_data:
                    models.append(model_data)
            
            return models
            
        except Exception as e:
            print(f"Error fetching OpenRouter models: {e}")
            # 오프라인 데이터는 사용하지 않음
            return []
    
    def is_deprecated(self, model: Dict) -> bool:
        """모델이 deprecated인지 확인"""
        model_id = model.get('id', '').lower()
        name = model.get('name', '').lower()
        
        # Deprecated 패턴들
        deprecated_patterns = [
            'deprecated',
            'old',
            'legacy',
            'v1',  # 더 새로운 버전이 있는 경우
            'preview'  # 정식 버전이 나온 preview 모델들
        ]
        
        # ID나 이름에 deprecated 패턴이 있는지 확인
        for pattern in deprecated_patterns:
            if pattern in model_id or pattern in name:
                # 예외: preview가 최신 모델인 경우는 유지
                if pattern == 'preview' and self.is_latest_preview(model_id):
                    continue
                return True
        
        # 오래된 날짜 패턴 (2023년 이전 모델들)
        old_date_pattern = r'(2022|2021|2020)'
        if re.search(old_date_pattern, model_id):
            return True
            
        return False
    
    def is_latest_preview(self, model_id: str) -> bool:
        """preview 모델이 최신 버전인지 확인"""
        latest_previews = [
            'openai/o1-preview',
            'anthropic/claude-3-opus-preview',
            'alibaba/qwq-32b-preview'
        ]
        return model_id in latest_previews
    
    def convert_openrouter_format(self, model: Dict) -> Dict:
        """OpenRouter 형식을 표준 형식으로 변환"""
        model_id = model.get('id', '')
        
        # 모델명 정리
        clean_name = self.clean_model_name(model_id, model.get('name', ''))
        if not clean_name:
            return None
        
        # 가격 정보 추출 (OpenRouter는 $/token 단위)
        pricing = model.get('pricing', {})
        input_price = float(pricing.get('prompt', 0)) * 1000000  # $/token -> $/1M tokens
        output_price = float(pricing.get('completion', 0)) * 1000000
        
        # 제공업체 추출
        provider = model_id.split('/')[0] if '/' in model_id else 'unknown'
        
        # 컨텍스트 길이
        context_length = model.get('context_length', 0)
        
        # 태그/기능 추출
        features = self.extract_features(model, model_id)
        
        # 모달리티 추출
        modalities = self.extract_modalities(model, model_id, features)
        
        # 상태 결정
        status = self.determine_status(model_id, clean_name)
        
        return {
            'id': model_id,
            'name': clean_name,
            'description': model.get('description', ''),
            'input_price': round(input_price, 4),
            'output_price': round(output_price, 4),
            'context_window': context_length,
            'max_output': model.get('max_completion_tokens', 4096),
            'features': features,
            'modalities': modalities,
            'status': status,
            'provider_original': provider,
            'via_openrouter': True,
            'architecture': model.get('architecture', {}).get('model_type', 'transformer')
        }
    
    def clean_model_name(self, model_id: str, raw_name: str) -> str:
        """모델명 정리 - Provider 이름이 아닌 실제 모델명 추출"""
        # 이미 깔끔한 이름인 경우
        if raw_name and not raw_name.lower() in ['google', 'mistral', 'meta', 'anthropic', 'openai']:
            return raw_name
        
        # model_id에서 모델명 추출
        parts = model_id.split('/')
        if len(parts) >= 2:
            model_part = parts[1]
            
            # 날짜나 버전 정보 제거
            model_part = re.sub(r':\d{4}-\d{2}-\d{2}', '', model_part)
            model_part = re.sub(r'-\d{4}\d{2}\d{2}', '', model_part)
            
            # 특별한 경우 처리
            name_mappings = {
                'gpt-4o': 'GPT-4o',
                'gpt-4o-mini': 'GPT-4o Mini',
                'gpt-4-turbo': 'GPT-4 Turbo',
                'gpt-3.5-turbo': 'GPT-3.5 Turbo',
                'claude-3.5-sonnet': 'Claude 3.5 Sonnet',
                'claude-3.5-haiku': 'Claude 3.5 Haiku',
                'claude-3-opus': 'Claude 3 Opus',
                'claude-3-sonnet': 'Claude 3 Sonnet',
                'claude-3-haiku': 'Claude 3 Haiku',
                'gemini-pro': 'Gemini Pro',
                'gemini-pro-vision': 'Gemini Pro Vision',
                'gemini-1.5-pro': 'Gemini 1.5 Pro',
                'gemini-1.5-flash': 'Gemini 1.5 Flash',
                'llama-3.3-70b-instruct': 'Llama 3.3 70B Instruct',
                'llama-3.2-90b-vision-instruct': 'Llama 3.2 90B Vision',
                'llama-3.1-405b-instruct': 'Llama 3.1 405B Instruct',
                'mixtral-8x22b-instruct': 'Mixtral 8x22B Instruct',
                'mixtral-8x7b-instruct': 'Mixtral 8x7B Instruct',
                'mistral-large': 'Mistral Large',
                'mistral-medium': 'Mistral Medium',
                'mistral-small': 'Mistral Small',
                'mistral-7b-instruct': 'Mistral 7B Instruct',
                'deepseek-chat': 'DeepSeek Chat',
                'deepseek-coder': 'DeepSeek Coder',
                'qwen-2.5-72b-instruct': 'Qwen 2.5 72B',
                'qwen-2-72b-instruct': 'Qwen 2 72B',
                'command-r-plus': 'Command R+',
                'command-r': 'Command R',
                'grok-2': 'Grok 2',
                'grok-2-vision': 'Grok 2 Vision',
                'dbrx-instruct': 'DBRX Instruct',
                'phi-3-medium': 'Phi-3 Medium',
                'phi-3-mini': 'Phi-3 Mini',
                'solar-10.7b-instruct': 'Solar 10.7B',
                'dolphin-mixtral-8x22b': 'Dolphin Mixtral 8x22B',
                'wizardlm-2-8x22b': 'WizardLM 2 8x22B'
            }
            
            # 매핑에서 찾기
            for key, value in name_mappings.items():
                if key in model_part.lower():
                    return value
            
            # 기본 변환 (하이픈을 공백으로, 첫 글자 대문자)
            clean_name = model_part.replace('-', ' ').title()
            
            # 숫자와 문자 사이에 공백 추가
            clean_name = re.sub(r'(\d)([A-Za-z])', r'\1 \2', clean_name)
            clean_name = re.sub(r'([A-Za-z])(\d)', r'\1 \2', clean_name)
            
            return clean_name
        
        return raw_name or model_id
    
    def extract_features(self, model: Dict, model_id: str) -> List[str]:
        """모델에서 기능/태그 추출"""
        features = []
        model_id_lower = model_id.lower()
        
        # 기본 기능 체크
        if model.get('supports_functions', False):
            features.append('function-calling')
        if model.get('supports_system_messages', False):
            features.append('system-messages')
        if model.get('supports_json_mode', False):
            features.append('json-mode')
        if model.get('supports_vision', False):
            features.append('vision')
        
        # 모델 이름에서 기능 추출
        feature_patterns = {
            'chat': ['chat', 'instruct', 'conversation'],
            'coding': ['code', 'coder', 'codestral'],
            'reasoning': ['reasoning', 'think', 'o1', 'reflection'],
            'math': ['math', 'mathematical'],
            'multilingual': ['multilingual', 'multi-lang'],
            'embeddings': ['embed', 'embedding'],
            'fast': ['fast', 'mini', 'small', 'light', 'flash'],
            'long-context': ['128k', '200k', '256k', '1m', 'long'],
            'multimodal': ['vision', 'image', 'multimodal', 'mm'],
            'instruction': ['instruct', 'instruction'],
            'creative': ['creative', 'story', 'roleplay'],
            'uncensored': ['uncensored', 'unfiltered'],
            'tool-use': ['tool', 'function', 'agent'],
            'online': ['online', 'internet', 'search']
        }
        
        for feature, patterns in feature_patterns.items():
            if any(pattern in model_id_lower for pattern in patterns):
                if feature not in features:
                    features.append(feature)
        
        # 컨텍스트 윈도우에 따른 태그
        context = model.get('context_length', 0)
        if context >= 128000:
            features.append('large-context')
        if context >= 1000000:
            features.append('mega-context')
        
        # 아키텍처에 따른 태그
        architecture = model.get('architecture', {})
        if architecture.get('model_type') == 'moe':
            features.append('mixture-of-experts')
        
        return sorted(list(set(features)))
    
    def extract_modalities(self, model: Dict, model_id: str, features: List[str]) -> List[str]:
        """모델이 지원하는 모달리티 추출"""
        modalities = ['text']  # 기본값
        
        if 'vision' in features or model.get('supports_vision', False):
            modalities.append('image')
        
        # 모델 이름에서 추가 모달리티 확인
        model_id_lower = model_id.lower()
        if 'audio' in model_id_lower:
            modalities.append('audio')
        if 'video' in model_id_lower:
            modalities.append('video')
        
        return sorted(list(set(modalities)))
    
    def determine_status(self, model_id: str, model_name: str) -> str:
        """모델 상태 결정"""
        model_id_lower = model_id.lower()
        model_name_lower = model_name.lower()
        
        if 'beta' in model_id_lower or 'beta' in model_name_lower:
            return 'beta'
        elif 'preview' in model_id_lower or 'preview' in model_name_lower:
            return 'preview'
        elif 'experimental' in model_id_lower or 'experimental' in model_name_lower:
            return 'experimental'
        else:
            return 'ga'
    
    def get_model_details(self, model_id: str) -> Dict:
        """특정 모델의 상세 정보"""
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