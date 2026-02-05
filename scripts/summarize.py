#!/usr/bin/env python3
"""
AI Fintech Weekly - AI Summarizer
使用 OpenAI API 生成周报总结、新闻翻译和摘要
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from openai import OpenAI

DATA_DIR = Path(__file__).parent.parent / "data"


def get_client():
    """获取 OpenAI 客户端"""
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key, base_url=base_url)


def get_model():
    """获取模型名称"""
    return os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


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


def save_news(news_data: dict, week: str = None):
    """保存更新后的新闻数据"""
    if week:
        news_file = DATA_DIR / f"news_{week}.json"
    else:
        news_file = DATA_DIR / "latest.json"
    
    with open(news_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)


def markdown_to_html(text: str) -> str:
    """简单的 Markdown 转 HTML"""
    # 处理标题
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # 处理粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # 处理列表项
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', text, flags=re.MULTILINE)
    
    # 将连续的 <li> 包裹在 <ul> 中
    text = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', text)
    
    # 处理段落（非标签开头的行）
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('<'):
            result.append(f'<p>{line}</p>')
        elif line:
            result.append(line)
    
    return '\n'.join(result)


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


def generate_weekly_summary(client, model: str, news_data: dict) -> str:
    """生成周报总结"""
    news_text = format_news_for_prompt(news_data)
    
    prompt = f"""你是一位专业的金融科技分析师。请根据以下本周收集的 AI 在金融领域应用的新闻，撰写一份周报总结。

新闻列表：
{news_text}

请按以下格式输出（使用 Markdown 格式）：

## 本周概要

用 3-5 句话总结本周 AI 金融领域的整体动态和重要趋势。每句话单独一行，便于阅读。

## 重点新闻解读

挑选 3-5 条最重要的新闻，每条用 2-3 句话解读其意义和影响：

- **新闻标题1**：解读内容...
- **新闻标题2**：解读内容...

## 趋势观察

基于本周新闻，总结 1-2 个值得关注的发展趋势。

注意：
- 保持客观专业的语调
- 突出实际应用和商业价值
- 段落之间要有空行，便于阅读
- 如果新闻较少或质量不高，诚实说明
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一位资深金融科技分析师，擅长将复杂的技术新闻转化为易于理解的商业洞察。请确保输出格式清晰，段落分明。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def generate_news_enhancements(client, model: str, news_list: list) -> list:
    """为新闻生成翻译和摘要"""
    
    # 构建批量处理的 prompt
    news_items = []
    for i, news in enumerate(news_list):
        news_items.append({
            "index": i,
            "title": news["title"],
            "lang": news.get("lang", "en"),
            "source": news.get("source", ""),
            "original_summary": news.get("summary", "")[:300] if news.get("summary") else ""
        })
    
    prompt = f"""请为以下新闻列表生成翻译和摘要。

新闻列表（JSON格式）：
{json.dumps(news_items, ensure_ascii=False, indent=2)}

请按以下 JSON 格式输出，不要输出其他内容：
{{
  "results": [
    {{
      "index": 0,
      "title_zh": "中文标题（如果原标题是英文则翻译，如果是中文则保持原样）",
      "ai_summary": "50-100字的中文摘要，简要概括新闻核心内容和意义"
    }},
    ...
  ]
}}

要求：
1. 英文标题必须翻译成通顺的中文
2. 中文标题保持原样
3. 摘要要精炼，突出新闻的核心价值和影响
4. 严格输出 JSON 格式
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一位专业的金融科技新闻编辑，擅长翻译和摘要。请严格按照 JSON 格式输出。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    # 解析 JSON 响应
    response_text = response.choices[0].message.content
    
    # 尝试提取 JSON
    try:
        # 尝试直接解析
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # 尝试从 markdown 代码块中提取
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            result = json.loads(json_match.group(1))
        else:
            # 尝试找到 { 开始的部分
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                result = json.loads(response_text[start:end])
            else:
                raise ValueError("无法解析 AI 响应")
    
    return result.get("results", [])


def enhance_news_data(news_data: dict) -> dict:
    """增强新闻数据：添加翻译和摘要"""
    client = get_client()
    model = get_model()
    
    all_news = news_data.get("all_news", [])
    
    if not all_news:
        return news_data
    
    print(f"Generating translations and summaries for {len(all_news)} news items...")
    
    try:
        enhancements = generate_news_enhancements(client, model, all_news)
        
        # 应用增强数据
        for item in enhancements:
            idx = item.get("index")
            if idx is not None and idx < len(all_news):
                all_news[idx]["title_zh"] = item.get("title_zh", all_news[idx]["title"])
                all_news[idx]["ai_summary"] = item.get("ai_summary", "")
        
        # 同步更新 en_news 和 zh_news
        for news in all_news:
            if news.get("lang") == "en":
                for en_news in news_data.get("en_news", []):
                    if en_news.get("title") == news.get("title"):
                        en_news["title_zh"] = news.get("title_zh", "")
                        en_news["ai_summary"] = news.get("ai_summary", "")
            else:
                for zh_news in news_data.get("zh_news", []):
                    if zh_news.get("title") == news.get("title"):
                        zh_news["title_zh"] = news.get("title_zh", "")
                        zh_news["ai_summary"] = news.get("ai_summary", "")
        
        print("News enhancements applied successfully")
        
    except Exception as e:
        print(f"Error enhancing news: {e}")
        # 失败时使用默认值
        for news in all_news:
            if "title_zh" not in news:
                news["title_zh"] = news["title"]
            if "ai_summary" not in news:
                news["ai_summary"] = news.get("summary", "")[:100] if news.get("summary") else ""
    
    return news_data


def generate_summary(news_data: dict) -> dict:
    """生成完整的周报数据"""
    client = get_client()
    model = get_model()
    week = news_data.get("week", datetime.now().strftime("%Y-W%W"))
    
    try:
        print("Generating weekly summary...")
        summary_text = generate_weekly_summary(client, model, news_data)
        summary_html = markdown_to_html(summary_text)
        
        return {
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "summary": summary_html,
            "summary_raw": summary_text,
            "model": model,
            "news_count": len(news_data.get("all_news", []))
        }
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return {
            "week": week,
            "generated_at": datetime.now().isoformat(),
            "summary": f"<h2>本周概要</h2><p>本周收集了 {len(news_data.get('all_news', []))} 条 AI 金融相关新闻。由于总结生成失败，请直接查看下方新闻列表。</p><p>错误信息: {str(e)}</p>",
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
    
    # 增强新闻数据（翻译 + 摘要）
    print("\nEnhancing news with translations and summaries...")
    news_data = enhance_news_data(news_data)
    save_news(news_data, week)
    
    # 生成周报总结
    print("\nGenerating AI summary...")
    summary = generate_summary(news_data)
    save_summary(summary)
    
    print("\nDone!")
