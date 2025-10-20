#!/usr/bin/env python3
"""Anthropic 모델 데이터를 fallback 정보로 업데이트"""
import json
from pathlib import Path
from datetime import datetime

def main():
    base_dir = Path(__file__).parent.parent
    output_file = base_dir / "data/models/anthropic.json"

    # 최신 Anthropic 모델 정보 (2025년 1월 기준)
    models = [
        {
            'id': 'claude-3-5-sonnet-20241022',
            'name': 'Claude 3.5 Sonnet',
            'description': 'Most intelligent model with advanced reasoning, coding, and vision capabilities',
            'input_price': 3.00,
            'output_price': 15.00,
            'context_window': 200000,
            'max_output': 8192,
            'features': ['chat', 'coding', 'analysis', 'creative-writing', 'vision', 'computer-use', 'reasoning'],
            'modalities': ['text', 'image'],
            'release_date': '2024-10-22',
            'training_cutoff': '2024-04',
            'status': 'ga',
            'use_cases': [
                'Complex reasoning',
                'Creative writing',
                'Code generation',
                'Computer automation',
                'Advanced analysis',
                'Image understanding'
            ]
        },
        {
            'id': 'claude-3-5-haiku-20241022',
            'name': 'Claude 3.5 Haiku',
            'description': 'Fast and affordable model with vision capabilities for everyday tasks',
            'input_price': 1.00,
            'output_price': 5.00,
            'context_window': 200000,
            'max_output': 8192,
            'features': ['chat', 'coding', 'fast', 'vision', 'cost-effective'],
            'modalities': ['text', 'image'],
            'release_date': '2024-11-04',
            'training_cutoff': '2024-07',
            'status': 'ga',
            'use_cases': [
                'Customer support',
                'Content moderation',
                'Quick data extraction',
                'Simple automation',
                'Basic image analysis'
            ]
        },
        {
            'id': 'claude-3-opus-20240229',
            'name': 'Claude 3 Opus',
            'description': 'Most powerful model for complex reasoning and research tasks',
            'input_price': 15.00,
            'output_price': 75.00,
            'context_window': 200000,
            'max_output': 4096,
            'features': ['chat', 'coding', 'analysis', 'research', 'complex-reasoning', 'vision', 'creative-writing'],
            'modalities': ['text', 'image'],
            'release_date': '2024-02-29',
            'training_cutoff': '2023-08',
            'status': 'ga',
            'use_cases': [
                'Research analysis',
                'Complex problem solving',
                'Advanced mathematics',
                'Expert-level tasks'
            ]
        },
        {
            'id': 'claude-3-sonnet-20240229',
            'name': 'Claude 3 Sonnet',
            'description': 'Balanced model for general purpose tasks with good performance',
            'input_price': 3.00,
            'output_price': 15.00,
            'context_window': 200000,
            'max_output': 4096,
            'features': ['chat', 'coding', 'analysis', 'vision', 'general-purpose'],
            'modalities': ['text', 'image'],
            'release_date': '2024-02-29',
            'training_cutoff': '2023-08',
            'status': 'ga',
            'use_cases': [
                'General assistance',
                'Content creation',
                'Data analysis',
                'Code review'
            ]
        },
        {
            'id': 'claude-3-haiku-20240307',
            'name': 'Claude 3 Haiku',
            'description': 'Fastest and most compact model for simple tasks',
            'input_price': 0.25,
            'output_price': 1.25,
            'context_window': 200000,
            'max_output': 4096,
            'features': ['chat', 'fast', 'lightweight', 'vision', 'simple-tasks'],
            'modalities': ['text', 'image'],
            'release_date': '2024-03-07',
            'training_cutoff': '2023-08',
            'status': 'ga',
            'use_cases': [
                'Quick responses',
                'Simple queries',
                'Basic tasks',
                'High-volume processing'
            ]
        }
    ]

    # 정규화된 형식으로 변환
    normalized_models = []
    for model in models:
        normalized = {
            'id': model['id'],
            'name': model['name'],
            'provider': 'anthropic',
            'description': model['description'],
            'pricing': {
                'input': model['input_price'],
                'output': model['output_price'],
                'unit': '1M tokens'
            },
            'context_window': model['context_window'],
            'max_output': model['max_output'],
            'release_date': model['release_date'],
            'status': model['status'],
            'features': model['features'],
            'modalities': model['modalities'],
            'use_cases': model['use_cases'],
            'training_cutoff': model['training_cutoff'],
            'last_updated': datetime.now().isoformat()
        }
        normalized_models.append(normalized)

    # 파일로 저장
    output_data = {
        'provider': 'anthropic',
        'provider_info': {
            'name': 'Anthropic',
            'website': 'https://anthropic.com',
            'api_endpoint': 'https://api.anthropic.com'
        },
        'last_updated': datetime.now().isoformat(),
        'models': normalized_models
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(normalized_models)} Anthropic models to {output_file}")

if __name__ == "__main__":
    main()
