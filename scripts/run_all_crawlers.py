#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import time
import concurrent.futures
from typing import Tuple

def run_crawler(script_name: str) -> Tuple[bool, str]:
    """개별 크롤러 실행"""
    output_lines = []
    try:
        output_lines.append(f"🔄 Running {script_name}...")
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            output_lines.append(f"✅ {script_name} completed in {elapsed_time:.2f}s")
            return True, "\n".join(output_lines)
        else:
            output_lines.append(f"❌ {script_name} failed: {result.stderr}")
            return False, "\n".join(output_lines)
            
    except Exception as e:
        output_lines.append(f"❌ Error running {script_name}: {e}")
        return False, "\n".join(output_lines)

def main():
    """모든 크롤러 실행"""
    print("🚀 Starting all crawlers...")
    
    crawlers = [
        "crawlers/openai_crawler.py",
        "crawlers/anthropic_crawler.py",
        "crawlers/google_crawler.py",
        "crawlers/deepseek_crawler.py",
        "crawlers/xai_crawler.py",
        "crawlers/mistral_crawler.py",
        "crawlers/cohere_crawler.py",
        "crawlers/huggingface_crawler.py"
    ]
    
    success_count = 0
    failed_crawlers = []
    
    # 병렬 실행 (max_workers=4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_crawler = {executor.submit(run_crawler, crawler): crawler for crawler in crawlers}

        for future in concurrent.futures.as_completed(future_to_crawler):
            crawler = future_to_crawler[future]
            try:
                success, output = future.result()
                print(output)

                if success:
                    success_count += 1
                else:
                    failed_crawlers.append(crawler)
            except Exception as e:
                print(f"❌ Exception executing {crawler}: {e}")
                failed_crawlers.append(crawler)
    
    print(f"\n📊 Crawler Summary:")
    print(f"   - Successful: {success_count}/{len(crawlers)}")
    if failed_crawlers:
        print(f"   - Failed: {', '.join(failed_crawlers)}")
    
    # 데이터 통합 프로세서 실행
    print("\n🔄 Running data processor...")
    success, output = run_crawler("data_processor.py")
    print(output)

    if success:
        print("✅ Data consolidation complete!")
    else:
        print("❌ Data consolidation failed!")
        return 1
    
    # 가격 모니터링 실행
    print("\n🔄 Running price monitor...")
    success, output = run_crawler("price_monitor.py")
    print(output)

    if success:
        print("✅ Price monitoring complete!")
    else:
        print("❌ Price monitoring failed!")
    
    print("\n🎉 All tasks completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
