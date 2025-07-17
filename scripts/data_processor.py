#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class DataProcessor:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data/models"
        self.output_file = self.base_dir / "data/consolidated.json"
        self.history_dir = self.base_dir / "data/history"
        
    def consolidate_data(self) -> Dict[str, Any]:
        """모든 제공업체 데이터를 통합"""
        consolidated = {
            'last_updated': datetime.now().isoformat(),
            'providers': {},
            'models': [],
            'statistics': {},
            'metadata': {
                'version': '1.0',
                'data_sources': []
            }
        }
        
        # 각 제공업체 데이터 로드
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    provider_data = json.load(f)
                
                provider_name = provider_data.get('provider', json_file.stem)
                provider_info = provider_data.get('provider_info', {})
                
                # 제공업체 정보 저장
                consolidated['providers'][provider_name] = {
                    'name': provider_info.get('name', provider_name),
                    'website': provider_info.get('website', ''),
                    'api_endpoint': provider_info.get('api_endpoint', ''),
                    'last_updated': provider_data.get('last_updated'),
                    'model_count': len(provider_data.get('models', []))
                }
                
                # 데이터 소스 추가
                consolidated['metadata']['data_sources'].append({
                    'provider': provider_name,
                    'file': json_file.name,
                    'last_updated': provider_data.get('last_updated')
                })
                
                # 모델 데이터 추가
                for model in provider_data.get('models', []):
                    # provider 필드 확인/추가
                    model['provider'] = provider_name
                    
                    # 고유 ID 생성 (provider/model_id 형식)
                    if 'via_openrouter' in model and model.get('via_openrouter'):
                        model['unique_id'] = f"openrouter/{model['id']}"
                    else:
                        model['unique_id'] = f"{provider_name}/{model['id']}"
                    
                    consolidated['models'].append(model)
                    
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                continue
        
        # 모델 중복 제거 (같은 모델이 여러 제공업체에서 제공되는 경우)
        consolidated['models'] = self.deduplicate_models(consolidated['models'])
        
        # 통계 계산
        consolidated['statistics'] = self.calculate_statistics(consolidated['models'])
        
        # 카테고리별 분류
        consolidated['categories'] = self.categorize_models(consolidated['models'])
        
        return consolidated
    
    def deduplicate_models(self, models: List[Dict]) -> List[Dict]:
        """중복 모델 제거 (OpenRouter 등에서 중복 제공되는 모델 처리)"""
        seen = {}
        deduped = []
        
        for model in models:
            # 원본 제공업체가 있는 경우 우선순위 부여
            if 'provider_original' in model:
                key = f"{model['provider_original']}/{model['id'].split('/')[-1]}"
            else:
                key = model['unique_id']
            
            if key not in seen:
                seen[key] = model
                deduped.append(model)
            else:
                # 가격 정보가 더 상세한 모델 유지
                existing = seen[key]
                if (model.get('pricing', {}).get('input', 0) > 0 and 
                    existing.get('pricing', {}).get('input', 0) == 0):
                    seen[key] = model
                    deduped[deduped.index(existing)] = model
        
        return deduped
    
    def calculate_statistics(self, models: List[Dict]) -> Dict[str, Any]:
        """데이터 통계 계산"""
        total_models = len(models)
        
        # 무료/유료 모델 분류
        free_models = len([
            m for m in models 
            if m.get('pricing', {}).get('input', 0) == 0 or 
               m.get('input_price', 0) == 0
        ])
        
        # 제공업체별 통계
        providers = {}
        for model in models:
            provider = model.get('provider')
            if provider not in providers:
                providers[provider] = 0
            providers[provider] += 1
        
        # 가격 범위 계산
        paid_models = [
            m for m in models 
            if (m.get('pricing', {}).get('input', 0) > 0 or 
                m.get('input_price', 0) > 0)
        ]
        
        if paid_models:
            prices = [
                m.get('pricing', {}).get('input', 0) or m.get('input_price', 0) 
                for m in paid_models
            ]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
        else:
            min_price = max_price = avg_price = 0
        
        # 기능별 통계
        features_count = {}
        for model in models:
            for feature in model.get('features', []):
                if feature not in features_count:
                    features_count[feature] = 0
                features_count[feature] += 1
        
        # 모달리티별 통계
        modality_count = {}
        for model in models:
            for modality in model.get('modalities', ['text']):
                if modality not in modality_count:
                    modality_count[modality] = 0
                modality_count[modality] += 1
        
        # 상태별 통계
        status_count = {}
        for model in models:
            status = model.get('status', 'ga')
            if status not in status_count:
                status_count[status] = 0
            status_count[status] += 1
        
        return {
            'total_models': total_models,
            'free_models': free_models,
            'paid_models': total_models - free_models,
            'providers': len(providers),
            'provider_breakdown': providers,
            'price_range': {
                'min': round(min_price, 2),
                'max': round(max_price, 2),
                'average': round(avg_price, 2)
            },
            'features': features_count,
            'modalities': modality_count,
            'status': status_count,
            'context_windows': {
                'min': min((m.get('context_window', 0) for m in models if m.get('context_window', 0) > 0), default=0),
                'max': max((m.get('context_window', 0) for m in models), default=0),
                'over_100k': len([m for m in models if m.get('context_window', 0) > 100000]),
                'over_1m': len([m for m in models if m.get('context_window', 0) > 1000000])
            }
        }
    
    def categorize_models(self, models: List[Dict]) -> Dict[str, List[str]]:
        """모델을 카테고리별로 분류"""
        categories = {
            'vision_models': [],
            'coding_models': [],
            'reasoning_models': [],
            'fast_models': [],
            'large_context': [],
            'multimodal': [],
            'free_models': [],
            'experimental': [],
            'deprecated': []
        }
        
        for model in models:
            unique_id = model.get('unique_id', '')
            
            # Vision 모델
            if 'vision' in model.get('features', []) or 'image' in model.get('modalities', []):
                categories['vision_models'].append(unique_id)
            
            # 코딩 특화 모델
            if any(keyword in model.get('name', '').lower() or keyword in model.get('id', '').lower() 
                   for keyword in ['code', 'coder', 'coding']):
                categories['coding_models'].append(unique_id)
            
            # 추론 모델
            if any(keyword in model.get('name', '').lower() or keyword in model.get('features', [])
                   for keyword in ['reasoning', 'o1-', 'think']):
                categories['reasoning_models'].append(unique_id)
            
            # 빠른 모델
            if any(keyword in model.get('name', '').lower() 
                   for keyword in ['fast', 'flash', 'mini', 'small', '8b']):
                categories['fast_models'].append(unique_id)
            
            # 대용량 컨텍스트
            if model.get('context_window', 0) >= 100000:
                categories['large_context'].append(unique_id)
            
            # 멀티모달
            if len(model.get('modalities', [])) > 1:
                categories['multimodal'].append(unique_id)
            
            # 무료 모델
            if (model.get('pricing', {}).get('input', 0) == 0 or 
                model.get('input_price', 0) == 0):
                categories['free_models'].append(unique_id)
            
            # 실험적 모델
            if model.get('status') in ['experimental', 'preview', 'beta']:
                categories['experimental'].append(unique_id)
            
            # 지원 종료 모델
            if model.get('status') == 'deprecated':
                categories['deprecated'].append(unique_id)
        
        return categories
    
    def save_history_snapshot(self, data: Dict[str, Any]):
        """일별 히스토리 스냅샷 저장"""
        today = datetime.now().strftime("%Y-%m-%d")
        history_file = self.history_dir / f"{today}.json"
        
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 히스토리용 간소화된 데이터
        history_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'statistics': data['statistics'],
            'provider_count': len(data['providers']),
            'model_count': len(data['models']),
            'price_snapshot': [
                {
                    'unique_id': model.get('unique_id'),
                    'id': model['id'],
                    'name': model['name'],
                    'provider': model['provider'],
                    'input_price': model.get('pricing', {}).get('input', 0) or model.get('input_price', 0),
                    'output_price': model.get('pricing', {}).get('output', 0) or model.get('output_price', 0),
                    'context_window': model.get('context_window', 0),
                    'status': model.get('status', 'ga')
                }
                for model in data['models']
            ]
        }
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    
    def run(self):
        """데이터 처리 실행"""
        print("📊 Starting data consolidation...")
        
        # 데이터 통합
        consolidated = self.consolidate_data()
        
        # 통합 데이터 저장
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        
        # 히스토리 스냅샷 저장
        self.save_history_snapshot(consolidated)
        
        # 요약 출력
        stats = consolidated['statistics']
        print(f"✅ Data consolidation complete!")
        print(f"   - Total models: {stats['total_models']}")
        print(f"   - Providers: {stats['providers']}")
        print(f"   - Free models: {stats['free_models']}")
        print(f"   - Paid models: {stats['paid_models']}")
        print(f"   - Price range: ${stats['price_range']['min']} - ${stats['price_range']['max']}")
        print(f"   - Models with >100K context: {stats['context_windows']['over_100k']}")
        print(f"   - Models with >1M context: {stats['context_windows']['over_1m']}")

if __name__ == "__main__":
    processor = DataProcessor()
    processor.run()