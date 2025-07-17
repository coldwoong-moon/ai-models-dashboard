#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import time

def run_crawler(script_name: str) -> bool:
    """개별 크롤러 실행"""
    try:
        print(f"\n🔄 Running {script_name}...")
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {script_name} completed in {elapsed_time:.2f}s")
            return True
        else:
            print(f"❌ {script_name} failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    """모든 크롤러 실행"""
    print("🚀 Starting all crawlers...")
    
    crawlers = [
        "crawlers/openai_crawler.py",
        "crawlers/anthropic_crawler.py",
        "crawlers/google_crawler.py",
        "crawlers/openrouter_crawler.py"
    ]
    
    success_count = 0
    failed_crawlers = []
    
    for crawler in crawlers:
        if run_crawler(crawler):
            success_count += 1
        else:
            failed_crawlers.append(crawler)
    
    print(f"\n📊 Crawler Summary:")
    print(f"   - Successful: {success_count}/{len(crawlers)}")
    if failed_crawlers:
        print(f"   - Failed: {', '.join(failed_crawlers)}")
    
    # 데이터 통합 프로세서 실행
    print("\n🔄 Running data processor...")
    if run_crawler("data_processor.py"):
        print("✅ Data consolidation complete!")
    else:
        print("❌ Data consolidation failed!")
        return 1
    
    # 가격 모니터링 실행
    print("\n🔄 Running price monitor...")
    if run_crawler("price_monitor.py"):
        print("✅ Price monitoring complete!")
    else:
        print("❌ Price monitoring failed!")
    
    print("\n🎉 All tasks completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())