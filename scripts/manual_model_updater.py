#!/usr/bin/env python3
"""
수동 큐레이션 모델 통합기
manual_models.json의 최신 모델 정보를 기존 데이터와 통합합니다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class ManualModelUpdater:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.models_dir = self.data_dir / "models"
        self.manual_file = self.data_dir / "manual_models.json"
        
    def load_manual_models(self) -> Dict[str, Any]:
        """수동 큐레이션 모델 데이터 로드"""
        if not self.manual_file.exists():
            print(f"❌ Manual models file not found: {self.manual_file}")
            return {}
            
        with open(self.manual_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_existing_provider_data(self, provider: str) -> Dict[str, Any]:
        """기존 공급업체 데이터 로드"""
        provider_file = self.models_dir / f"{provider}.json"
        
        if not provider_file.exists():
            # 새 공급업체인 경우 기본 구조 생성
            return {
                'provider': provider,
                'provider_info': {
                    'name': provider.title(),
                    'website': f'https://{provider}.com',
                    'api_endpoint': f'https://api.{provider}.com'
                },
                'last_updated': datetime.now().isoformat(),
                'models': []
            }
        
        with open(provider_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def merge_models(self, existing_models: List[Dict], manual_models: List[Dict]) -> List[Dict]:
        """기존 모델과 수동 큐레이션 모델 병합"""
        # 기존 모델을 ID로 인덱싱
        existing_by_id = {model['id']: model for model in existing_models}
        
        # 수동 모델들을 추가하거나 업데이트
        for manual_model in manual_models:
            model_id = manual_model['id']
            
            # 표준 형식으로 변환
            standardized_model = self.standardize_model(manual_model)
            
            # 기존 모델이 있으면 업데이트, 없으면 추가
            existing_by_id[model_id] = standardized_model
            
            print(f"  ✅ {model_id}: {'updated' if model_id in existing_by_id else 'added'}")
        
        # 업데이트된 모델 목록 반환
        return list(existing_by_id.values())
    
    def standardize_model(self, manual_model: Dict[str, Any]) -> Dict[str, Any]:
        """수동 모델을 표준 형식으로 변환"""
        return {
            'id': manual_model['id'],
            'name': manual_model['name'], 
            'provider': manual_model.get('provider', ''),
            'description': manual_model['description'],
            'pricing': manual_model.get('pricing', {}),
            'input_price': manual_model.get('pricing', {}).get('input', 0),
            'output_price': manual_model.get('pricing', {}).get('output', 0),
            'context_window': manual_model.get('context_window', 4096),
            'max_output': manual_model.get('max_output', 4096),
            'release_date': manual_model.get('release_date', ''),
            'status': manual_model.get('status', 'ga'),
            'features': manual_model.get('features', []),
            'modalities': manual_model.get('modalities', ['text']),
            'use_cases': manual_model.get('use_cases', []),
            'training_cutoff': manual_model.get('training_cutoff', ''),
            'last_updated': datetime.now().isoformat(),
            'notes': manual_model.get('notes', ''),
            'source': 'manual_curation'
        }
    
    def save_provider_data(self, provider: str, data: Dict[str, Any]):
        """공급업체 데이터 저장"""
        provider_file = self.models_dir / f"{provider}.json"
        
        # 디렉토리 생성
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 업데이트 시간 갱신
        data['last_updated'] = datetime.now().isoformat()
        
        with open(provider_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 {provider}: {len(data['models'])} models saved")
    
    def update_all_providers(self):
        """모든 공급업체의 수동 큐레이션 모델 업데이트"""
        print("🔄 Starting manual model integration...")
        
        # 수동 모델 데이터 로드
        manual_data = self.load_manual_models()
        if not manual_data:
            print("❌ No manual models data found")
            return
        
        providers_updated = 0
        total_models_added = 0
        
        # 각 공급업체별로 처리
        for provider, provider_manual in manual_data.get('providers', {}).items():
            print(f"\n📦 Processing {provider}...")
            
            # 기존 데이터 로드
            existing_data = self.load_existing_provider_data(provider)
            
            # 모델 병합
            manual_models = provider_manual.get('latest_models', [])
            if not manual_models:
                print(f"  ⚠️ No manual models for {provider}")
                continue
            
            # 각 수동 모델에 provider 정보 추가
            for model in manual_models:
                model['provider'] = provider
            
            # 모델 병합
            before_count = len(existing_data['models'])
            existing_data['models'] = self.merge_models(existing_data['models'], manual_models)
            after_count = len(existing_data['models'])
            
            # 데이터 저장
            self.save_provider_data(provider, existing_data)
            
            providers_updated += 1
            models_added = after_count - before_count
            total_models_added += models_added
            
            print(f"  📊 Models: {before_count} → {after_count} (+{models_added})")
        
        print(f"\n✅ Manual model integration completed!")
        print(f"   - Providers updated: {providers_updated}")
        print(f"   - Total models added/updated: {total_models_added}")
        
        # 통합 데이터 재생성 권장
        print(f"\n💡 Run 'python scripts/data_processor.py' to regenerate consolidated data")

if __name__ == "__main__":
    updater = ManualModelUpdater()
    updater.update_all_providers()