#!/usr/bin/env python3
"""
모든 크롤러 실행 스크립트 (Playwright 불필요)
각 Provider의 simple 크롤러를 순차적으로 실행
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

def run_all_crawlers():
    """모든 크롤러 실행"""
    print("=" * 60)
    print("🚀 Starting all crawlers...")
    print("=" * 60)

    results = []

    # 1. OpenAI
    print("\n📌 Running OpenAI crawler...")
    try:
        from crawlers.openai_simple_crawler import OpenAISimpleCrawler
        crawler = OpenAISimpleCrawler()
        crawler.run()
        results.append(("OpenAI", "✅ Success"))
    except Exception as e:
        print(f"❌ OpenAI crawler failed: {e}")
        results.append(("OpenAI", f"❌ Failed: {e}"))

    # 2. Anthropic
    print("\n📌 Running Anthropic crawler...")
    try:
        from update_anthropic_fallback import main as update_anthropic
        update_anthropic()
        results.append(("Anthropic", "✅ Success"))
    except Exception as e:
        print(f"❌ Anthropic crawler failed: {e}")
        results.append(("Anthropic", f"❌ Failed: {e}"))

    # 3. Google AI
    print("\n📌 Running Google AI crawler...")
    try:
        from crawlers.google_simple_crawler import GoogleSimpleCrawler
        crawler = GoogleSimpleCrawler()
        crawler.run()
        results.append(("Google AI", "✅ Success"))
    except Exception as e:
        print(f"❌ Google AI crawler failed: {e}")
        results.append(("Google AI", f"❌ Failed: {e}"))

    # 4. DeepSeek
    print("\n📌 Running DeepSeek crawler...")
    try:
        from crawlers.deepseek_crawler import DeepSeekCrawler
        crawler = DeepSeekCrawler()
        crawler.run()
        results.append(("DeepSeek", "✅ Success"))
    except Exception as e:
        print(f"❌ DeepSeek crawler failed: {e}")
        results.append(("DeepSeek", f"❌ Failed: {e}"))

    # 5. xAI
    print("\n📌 Running xAI crawler...")
    try:
        from crawlers.xai_crawler import XAICrawler
        crawler = XAICrawler()
        crawler.run()
        results.append(("xAI", "✅ Success"))
    except Exception as e:
        print(f"❌ xAI crawler failed: {e}")
        results.append(("xAI", f"❌ Failed: {e}"))

    # 6. Mistral
    print("\n📌 Running Mistral crawler...")
    try:
        from crawlers.mistral_crawler import MistralCrawler
        crawler = MistralCrawler()
        crawler.run()
        results.append(("Mistral", "✅ Success"))
    except Exception as e:
        print(f"❌ Mistral crawler failed: {e}")
        results.append(("Mistral", f"❌ Failed: {e}"))

    # 7. Cohere
    print("\n📌 Running Cohere crawler...")
    try:
        from crawlers.cohere_crawler import CohereCrawler
        crawler = CohereCrawler()
        crawler.run()
        results.append(("Cohere", "✅ Success"))
    except Exception as e:
        print(f"❌ Cohere crawler failed: {e}")
        results.append(("Cohere", f"❌ Failed: {e}"))

    # 8. HuggingFace
    print("\n📌 Running HuggingFace crawler...")
    try:
        from crawlers.huggingface_crawler import HuggingFaceCrawler
        crawler = HuggingFaceCrawler()
        crawler.run()
        results.append(("HuggingFace", "✅ Success"))
    except Exception as e:
        print(f"❌ HuggingFace crawler failed: {e}")
        results.append(("HuggingFace", f"❌ Failed: {e}"))

    # 요약 출력
    print("\n" + "=" * 60)
    print("📊 Crawling Summary:")
    print("=" * 60)

    for provider, status in results:
        print(f"{provider:20s} {status}")

    successful = sum(1 for _, status in results if "Success" in status)
    total = len(results)

    print(f"\n✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {total - successful}/{total}")

    print("\n" + "=" * 60)
    print("✨ All crawlers finished!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_crawlers()
