#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class PriceMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.current_data_file = self.base_dir / "data/consolidated.json"
        self.history_dir = self.base_dir / "data/history"
        self.changes_file = self.base_dir / "price_changes.txt"
        self.report_file = self.base_dir / "price_changes_report.md"
        
    def get_previous_data(self) -> Dict:
        """이전 데이터 가져오기 (어제 또는 가장 최근 데이터)"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_file = self.history_dir / f"{yesterday}.json"
        
        if yesterday_file.exists():
            with open(yesterday_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 어제 데이터가 없으면 가장 최근 데이터 찾기
        history_files = sorted(self.history_dir.glob("*.json"))
        if history_files:
            with open(history_files[-1], 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return None
    
    def get_current_data(self) -> Dict:
        """현재 데이터 가져오기"""
        if self.current_data_file.exists():
            with open(self.current_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def compare_prices(self, previous: Dict, current: Dict) -> List[Dict]:
        """가격 변경 사항 비교"""
        changes = []
        
        # 이전 데이터를 ID로 인덱싱
        prev_models = {}
        if previous and 'price_snapshot' in previous:
            for model in previous['price_snapshot']:
                prev_models[model['unique_id']] = model
        elif previous and 'models' in previous:
            for model in previous['models']:
                unique_id = model.get('unique_id', f"{model['provider']}/{model['id']}")
                prev_models[unique_id] = {
                    'unique_id': unique_id,
                    'name': model['name'],
                    'provider': model['provider'],
                    'input_price': model.get('pricing', {}).get('input', 0) or model.get('input_price', 0),
                    'output_price': model.get('pricing', {}).get('output', 0) or model.get('output_price', 0)
                }
        
        # 현재 데이터와 비교
        if current and 'models' in current:
            for model in current['models']:
                unique_id = model.get('unique_id', f"{model['provider']}/{model['id']}")
                
                current_input = model.get('pricing', {}).get('input', 0) or model.get('input_price', 0)
                current_output = model.get('pricing', {}).get('output', 0) or model.get('output_price', 0)
                
                if unique_id in prev_models:
                    prev = prev_models[unique_id]
                    prev_input = prev.get('input_price', 0)
                    prev_output = prev.get('output_price', 0)
                    
                    # 가격 변경 확인
                    if (prev_input != current_input or prev_output != current_output) and prev_input > 0:
                        change = {
                            'model_id': model['id'],
                            'name': model['name'],
                            'provider': model['provider'],
                            'input_price': {
                                'old': prev_input,
                                'new': current_input,
                                'change': current_input - prev_input,
                                'change_percent': ((current_input - prev_input) / prev_input * 100) if prev_input > 0 else 0
                            },
                            'output_price': {
                                'old': prev_output,
                                'new': current_output,
                                'change': current_output - prev_output,
                                'change_percent': ((current_output - prev_output) / prev_output * 100) if prev_output > 0 else 0
                            }
                        }
                        changes.append(change)
                else:
                    # 새로운 모델
                    if current_input > 0 or current_output > 0:
                        changes.append({
                            'model_id': model['id'],
                            'name': model['name'],
                            'provider': model['provider'],
                            'type': 'new',
                            'input_price': {'new': current_input},
                            'output_price': {'new': current_output}
                        })
        
        return changes
    
    def generate_report(self, changes: List[Dict]) -> str:
        """변경 사항 리포트 생성"""
        if not changes:
            return "No price changes detected."
        
        report = f"# 🚨 AI Model Price Changes Report\n\n"
        report += f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 새로운 모델
        new_models = [c for c in changes if c.get('type') == 'new']
        if new_models:
            report += "## 🆕 New Models\n\n"
            for model in new_models:
                report += f"### {model['name']} ({model['provider']})\n"
                report += f"- Input: ${model['input_price']['new']}/1M tokens\n"
                report += f"- Output: ${model['output_price']['new']}/1M tokens\n\n"
        
        # 가격 변경
        price_changes = [c for c in changes if c.get('type') != 'new']
        if price_changes:
            report += "## 💰 Price Changes\n\n"
            
            # 인상/인하 분류
            increases = []
            decreases = []
            
            for change in price_changes:
                if change['input_price']['change'] > 0 or change['output_price']['change'] > 0:
                    increases.append(change)
                else:
                    decreases.append(change)
            
            if increases:
                report += "### 📈 Price Increases\n\n"
                for change in increases:
                    report += f"#### {change['name']} ({change['provider']})\n"
                    
                    if change['input_price']['change'] != 0:
                        report += f"- **Input**: ${change['input_price']['old']} → "
                        report += f"${change['input_price']['new']} "
                        report += f"({change['input_price']['change']:+.2f}, "
                        report += f"{change['input_price']['change_percent']:+.1f}%)\n"
                    
                    if change['output_price']['change'] != 0:
                        report += f"- **Output**: ${change['output_price']['old']} → "
                        report += f"${change['output_price']['new']} "
                        report += f"({change['output_price']['change']:+.2f}, "
                        report += f"{change['output_price']['change_percent']:+.1f}%)\n"
                    
                    report += "\n"
            
            if decreases:
                report += "### 📉 Price Decreases\n\n"
                for change in decreases:
                    report += f"#### {change['name']} ({change['provider']})\n"
                    
                    if change['input_price']['change'] != 0:
                        report += f"- **Input**: ${change['input_price']['old']} → "
                        report += f"${change['input_price']['new']} "
                        report += f"({change['input_price']['change']:+.2f}, "
                        report += f"{change['input_price']['change_percent']:+.1f}%)\n"
                    
                    if change['output_price']['change'] != 0:
                        report += f"- **Output**: ${change['output_price']['old']} → "
                        report += f"${change['output_price']['new']} "
                        report += f"({change['output_price']['change']:+.2f}, "
                        report += f"{change['output_price']['change_percent']:+.1f}%)\n"
                    
                    report += "\n"
        
        # 요약
        report += "## 📊 Summary\n\n"
        report += f"- Total changes detected: {len(changes)}\n"
        report += f"- New models: {len(new_models)}\n"
        report += f"- Price changes: {len(price_changes)}\n"
        
        return report
    
    def run(self):
        """가격 모니터링 실행"""
        print("💰 Starting price monitoring...")
        
        # 데이터 로드
        previous = self.get_previous_data()
        current = self.get_current_data()
        
        if not previous:
            print("No previous data found for comparison.")
            with open(self.changes_file, 'w') as f:
                f.write("false")
            return
        
        if not current:
            print("No current data found.")
            with open(self.changes_file, 'w') as f:
                f.write("false")
            return
        
        # 가격 비교
        changes = self.compare_prices(previous, current)
        
        # 결과 저장
        if changes:
            print(f"✅ Found {len(changes)} price changes!")
            
            # 변경 플래그 저장
            with open(self.changes_file, 'w') as f:
                f.write("true")
            
            # 상세 리포트 생성
            report = self.generate_report(changes)
            with open(self.report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # 콘솔 출력
            print("\nPrice changes summary:")
            for change in changes[:5]:  # 상위 5개만 출력
                if change.get('type') == 'new':
                    print(f"  🆕 New: {change['name']} ({change['provider']})")
                else:
                    print(f"  💰 Changed: {change['name']} ({change['provider']})")
        else:
            print("No price changes detected.")
            with open(self.changes_file, 'w') as f:
                f.write("false")

if __name__ == "__main__":
    monitor = PriceMonitor()
    monitor.run()