#!/usr/bin/env python3
"""
AI Fintech Weekly - AI Summarizer
使用 OpenAI API 生成周报总结
"""

import json
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI

DATA_DIR = Path(__file__).parent.parent / "data"


def load_news(week: str = None) -> dict:
    """加载新闻数据"""
    if week:
        news_file = DATA_DIR / f"news_{week}.json"
    else:
        news_file = DATA_DIR / "latest.json"
    
    if not news_file.exists():
        raise FileNotFoundError(f"News file not found: {news_file}")
    
    with open(news_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_news_for_prompt(news_data: dict) -> str:
    """格式化新闻列表用于 prompt"""
    lines = []
    
    for i, news in enumerate(news_data.get("all_news", []), 1):
        lines.append(f"{i}. [{news.get('lang', 'en').upper()}] {news['title']}")
        lines.append(f"   Source: {news['source']} | Date: {news['published']}")
        if news.get("summary"):
            summary = news["summary"][:200] + "..." if len(news.get("summary", "")) > 200 else news.get("summary", "")
            lines.append(f"   Summary: {summary}")
        lines.append("")
    
    return "\n".join(lines)


def generate_summary(news_data: dict) -> dict:
    """使用 OpenAI 生成周报总结"""
    # 支持代理平台：通过 OPENAI_BASE_URL 环境变量设置自定义 API 地址
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")  # 支持自定义模型
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url  # 如果为 None，则使用默认的 OpenAI 地址
    )
    
    news_text = format_news_for_prompt(news_data)
    week = news_data.get("week", datetime.now().strftime("%Y-W%W"))
    
    prompt = f"""你是一位专业的金融科技分析师。请根据以下本周收集的 AI 在金融领域应用的新闻，撰写一份周报总结。

新闻列表：
{news_text}

请按以下格式输出：

## 本周概要
（用 3-5 句话总结本周 AI 金融领域的整体动态和重要趋势，中文撰写）

## 重点新闻解读
（挑选 3-5 条最重要的新闻，每条用 2-3 句话解读其意义和影响，中文撰写）

## 趋势观察
（基于本周新闻，总结 1-2 个值得关注的发展趋势，中文撰写）

注意：
- 保持客观专业的语调
- 突出实际应用和商业价值
- 如果新闻较少或质量不高，诚实说明
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位资深金融科技分析师，擅长将复杂的技术新闻转化为易于理解的商业洞察。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        summary = response.choices[0].message.content
        
        return {
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "model": model,
            "news_count": len(news_data.get("all_news", []))
        }
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "summary": f"## 本周概要\n\n本周收集了 {len(news_data.get('all_news', []))} 条 AI 金融相关新闻。由于总结生成失败，请直接查看下方新闻列表。\n\n错误信息: {str(e)}",
            "model": "fallback",
            "news_count": len(news_data.get("all_news", [])),
            "error": str(e)
        }


def save_summary(summary_data: dict):
    """保存总结数据"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    week = summary_data["week"]
    output_file = DATA_DIR / f"summary_{week}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    print(f"Summary saved to: {output_file}")
    
    # 保存 latest
    latest_file = DATA_DIR / "latest_summary.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    return output_file


if __name__ == "__main__":
    import sys
    
    week = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"Loading news data{f' for week {week}' if week else ''}...")
    news_data = load_news(week)
    print(f"Found {len(news_data.get('all_news', []))} news items")
    
    print("Generating AI summary...")
    summary = generate_summary(news_data)
    
    save_summary(summary)
    print("Done!")
