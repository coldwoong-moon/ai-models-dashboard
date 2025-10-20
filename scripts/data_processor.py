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
        
        # 각 제공업체 데이터 로드 (OpenRouter 제외)
        excluded_providers = ['openrouter']
        for json_file in self.data_dir.glob("*.json"):
            # OpenRouter 파일 스킵
            if json_file.stem in excluded_providers:
                continue
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
                    
                    # 무료 모델 (사용량 제한) 제외
                    # 입력/출력 가격이 모두 0인 모델은 제외
                    pricing = model.get('pricing', {})
                    input_price = pricing.get('input', 0) or model.get('input_price', 0)
                    output_price = pricing.get('output', 0) or model.get('output_price', 0)
                    
                    if input_price == 0 and output_price == 0:
                        continue  # 무료 모델 제외
                    
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

        # Provider 비교 정보 추가
        consolidated['provider_comparison'] = self.create_provider_comparison(consolidated['models'])

        # 가격대별 분류
        consolidated['price_tiers'] = self.classify_by_price_tiers(consolidated['models'])

        return consolidated
    
    def deduplicate_models(self, models: List[Dict]) -> List[Dict]:
        """중복 모델 제거 및 다중 제공업체 추적"""
        # 모델 이름과 주요 파라미터로 그룹화
        model_groups = {}
        
        for model in models:
            # 모델 이름에서 제공업체 프리픽스 제거하고 기본 이름 추출
            model_name = model.get('name', '').lower()
            model_id = model.get('id', '').split('/')[-1].lower()
            
            # 그룹화 키 생성 (모델 이름 기반)
            # 예: "Llama 3.1 70B", "GPT-4o" 등
            group_key = None
            
            # Llama 모델 그룹화
            if 'llama' in model_name or 'llama' in model_id:
                if '405b' in model_name or '405b' in model_id:
                    group_key = 'llama-3.1-405b'
                elif '70b' in model_name or '70b' in model_id:
                    group_key = 'llama-3.1-70b'
                elif '8b' in model_name or '8b' in model_id:
                    group_key = 'llama-3.1-8b'
            
            # Mistral 모델 그룹화
            elif 'mistral' in model_name or 'mistral' in model_id:
                if '7b' in model_name or '7b' in model_id:
                    group_key = 'mistral-7b'
                elif 'mixtral' in model_name or 'mixtral' in model_id:
                    group_key = 'mixtral-8x7b'
            
            # Gemma 모델 그룹화
            elif 'gemma' in model_name or 'gemma' in model_id:
                if '27b' in model_name or '27b' in model_id:
                    group_key = 'gemma-2-27b'
                elif '9b' in model_name or '9b' in model_id:
                    group_key = 'gemma-2-9b'
            
            # Qwen 모델 그룹화
            elif 'qwen' in model_name or 'qwen' in model_id:
                if '72b' in model_name or '72b' in model_id:
                    group_key = 'qwen-2.5-72b'
                elif '7b' in model_name or '7b' in model_id:
                    group_key = 'qwen-2.5-7b'
            
            # 그룹이 없으면 unique_id 사용
            if not group_key:
                group_key = model['unique_id']
            
            # 그룹에 추가
            if group_key not in model_groups:
                model_groups[group_key] = []
            model_groups[group_key].append(model)
        
        # 각 그룹에서 대표 모델 선택 및 다중 제공업체 추적
        deduped = []
        for group_key, group_models in model_groups.items():
            if len(group_models) == 1:
                # 단일 제공업체
                deduped.append(group_models[0])
            else:
                # 다중 제공업체 - 가장 상세한 정보를 가진 모델을 선택하고
                # 다른 제공업체 정보를 추가
                primary_model = max(group_models, 
                                   key=lambda m: (
                                       m.get('pricing', {}).get('input', 0),
                                       len(m.get('description', '')),
                                       len(m.get('features', []))
                                   ))
                
                # 다른 제공업체 정보 수집
                available_providers = [m['provider'] for m in group_models]
                primary_model['available_providers'] = list(set(available_providers))
                
                # 제공업체별 가격 정보 저장 (가격이 다를 경우)
                provider_pricing = {}
                for m in group_models:
                    provider = m['provider']
                    pricing = m.get('pricing', {})
                    if pricing.get('input', 0) > 0:
                        provider_pricing[provider] = {
                            'input': pricing.get('input', 0),
                            'output': pricing.get('output', 0)
                        }
                
                if len(provider_pricing) > 1:
                    primary_model['provider_pricing'] = provider_pricing
                
                deduped.append(primary_model)
        
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

    def create_provider_comparison(self, models: List[Dict]) -> Dict[str, Any]:
        """Provider별 모델 비교 정보 생성"""
        comparison = {
            'by_use_case': {},
            'by_capability': {},
            'pricing_comparison': {}
        }

        # 사용 사례별 모델 그룹화
        use_cases = {
            'general_chat': {
                'keywords': ['chat', 'conversation', 'general'],
                'models': []
            },
            'advanced_reasoning': {
                'keywords': ['reasoning', 'complex', 'advanced', 'opus', 'o1'],
                'models': []
            },
            'fast_affordable': {
                'keywords': ['fast', 'mini', 'flash', 'haiku', 'small'],
                'models': []
            },
            'vision': {
                'keywords': ['vision', 'image', 'multimodal'],
                'models': []
            },
            'coding': {
                'keywords': ['code', 'coder', 'coding', 'programming'],
                'models': []
            },
            'large_context': {
                'keywords': ['long', 'context', 'large'],
                'min_context': 100000,
                'models': []
            }
        }

        for model in models:
            model_info = {
                'id': model.get('id'),
                'name': model.get('name'),
                'provider': model.get('provider'),
                'input_price': model.get('pricing', {}).get('input', 0) or model.get('input_price', 0),
                'output_price': model.get('pricing', {}).get('output', 0) or model.get('output_price', 0),
                'context_window': model.get('context_window', 0),
                'features': model.get('features', []),
                'unique_id': model.get('unique_id', '')
            }

            # 각 사용 사례별로 분류
            for use_case, config in use_cases.items():
                should_include = False

                # 키워드 기반 매칭
                if 'keywords' in config:
                    model_text = ' '.join([
                        model.get('name', '').lower(),
                        model.get('id', '').lower(),
                        ' '.join(model.get('features', []))
                    ])

                    if any(keyword in model_text for keyword in config['keywords']):
                        should_include = True

                # 컨텍스트 윈도우 기준
                if 'min_context' in config:
                    if model.get('context_window', 0) >= config['min_context']:
                        should_include = True

                if should_include:
                    config['models'].append(model_info)

        # 사용 사례별로 정리하고 가격순 정렬
        for use_case, config in use_cases.items():
            sorted_models = sorted(config['models'],
                                 key=lambda m: m['input_price'])
            comparison['by_use_case'][use_case] = sorted_models

        # 기능별 비교 (vision, coding 등)
        capabilities = ['vision', 'coding', 'reasoning', 'fast']
        for cap in capabilities:
            cap_models = []
            for model in models:
                if cap in model.get('features', []) or cap in model.get('name', '').lower():
                    cap_models.append({
                        'id': model.get('id'),
                        'name': model.get('name'),
                        'provider': model.get('provider'),
                        'input_price': model.get('pricing', {}).get('input', 0) or model.get('input_price', 0),
                        'output_price': model.get('pricing', {}).get('output', 0) or model.get('output_price', 0),
                        'unique_id': model.get('unique_id', '')
                    })

            comparison['by_capability'][cap] = sorted(cap_models,
                                                     key=lambda m: m['input_price'])

        # Provider별 가격 비교 (동일 작업에 대한 비용)
        # 예시: 100K input + 10K output 토큰
        sample_workload = {
            'input_tokens': 100000,
            'output_tokens': 10000
        }

        provider_costs = {}
        for model in models:
            provider = model.get('provider')
            input_price = model.get('pricing', {}).get('input', 0) or model.get('input_price', 0)
            output_price = model.get('pricing', {}).get('output', 0) or model.get('output_price', 0)

            if input_price > 0:
                # 1M tokens 기준 가격을 실제 사용량으로 계산
                cost = (input_price * sample_workload['input_tokens'] / 1000000 +
                       output_price * sample_workload['output_tokens'] / 1000000)

                if provider not in provider_costs:
                    provider_costs[provider] = []

                provider_costs[provider].append({
                    'model': model.get('name'),
                    'model_id': model.get('id'),
                    'cost_for_sample': round(cost, 4),
                    'input_price': input_price,
                    'output_price': output_price,
                    'unique_id': model.get('unique_id', '')
                })

        # Provider별로 정렬
        for provider in provider_costs:
            provider_costs[provider] = sorted(provider_costs[provider],
                                            key=lambda m: m['cost_for_sample'])

        comparison['pricing_comparison'] = {
            'sample_workload': sample_workload,
            'by_provider': provider_costs
        }

        return comparison

    def classify_by_price_tiers(self, models: List[Dict]) -> Dict[str, List[Dict]]:
        """가격대별로 모델 분류"""
        tiers = {
            'budget': {'max': 1.0, 'models': []},      # < $1/M tokens
            'standard': {'min': 1.0, 'max': 5.0, 'models': []},  # $1-5/M tokens
            'premium': {'min': 5.0, 'max': 15.0, 'models': []},  # $5-15/M tokens
            'enterprise': {'min': 15.0, 'models': []}  # > $15/M tokens
        }

        for model in models:
            input_price = model.get('pricing', {}).get('input', 0) or model.get('input_price', 0)

            if input_price == 0:
                continue

            model_info = {
                'id': model.get('id'),
                'name': model.get('name'),
                'provider': model.get('provider'),
                'input_price': input_price,
                'output_price': model.get('pricing', {}).get('output', 0) or model.get('output_price', 0),
                'context_window': model.get('context_window', 0),
                'features': model.get('features', []),
                'unique_id': model.get('unique_id', '')
            }

            # 가격대 분류
            if input_price < 1.0:
                tiers['budget']['models'].append(model_info)
            elif 1.0 <= input_price < 5.0:
                tiers['standard']['models'].append(model_info)
            elif 5.0 <= input_price < 15.0:
                tiers['premium']['models'].append(model_info)
            else:
                tiers['enterprise']['models'].append(model_info)

        # 각 티어별로 가격순 정렬
        for tier in tiers.values():
            tier['models'] = sorted(tier['models'],
                                  key=lambda m: m['input_price'])

        return tiers

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