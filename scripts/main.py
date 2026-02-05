#!/usr/bin/env python3
"""
AI Fintech Weekly - Main Entry Point
完整的工作流：抓取 -> 总结 -> 生成网站
"""

import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from fetch_news import fetch_all_news, save_news
from summarize import load_news, generate_summary, save_summary
from generate_site import generate_site


def main():
    print("=" * 50)
    print("AI Fintech Weekly - Full Pipeline")
    print("=" * 50)
    
    # Step 1: 抓取新闻
    print("\n[1/3] Fetching news...")
    news_data = fetch_all_news()
    save_news(news_data)
    
    # Step 2: 生成 AI 总结
    print("\n[2/3] Generating AI summary...")
    news_data = load_news()
    summary_data = generate_summary(news_data)
    save_summary(summary_data)
    
    # Step 3: 生成静态网站
    print("\n[3/3] Generating static site...")
    generate_site()
    
    print("\n" + "=" * 50)
    print("Pipeline completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
