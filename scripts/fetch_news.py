#!/usr/bin/env python3
"""
AI Fintech Weekly - News Fetcher
抓取中英文 AI+金融 相关新闻
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
MAX_NEWS_PER_SOURCE = 10
MAX_TOTAL_NEWS = 20
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "7"))


def _parse_date_yyyy_mm_dd(value: str) -> datetime | None:
    """Parse YYYY-MM-DD into datetime (local time)."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _is_within_lookback(published_dt: datetime, now: datetime) -> bool:
    return published_dt >= (now - timedelta(days=LOOKBACK_DAYS))


def get_google_news(query: str, lang: str = "en", num_results: int = 10) -> list[dict]:
    """从 Google News RSS 获取新闻"""
    encoded_query = quote_plus(query)
    
    if lang == "zh":
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    else:
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        news_items = []
        now = datetime.now()
        cutoff = now - timedelta(days=LOOKBACK_DAYS)
        
        for entry in feed.entries[:num_results]:
            # 解析发布时间
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                pub_dt = datetime(*published[:6])
            else:
                pub_dt = now

            if pub_dt < cutoff:
                continue

            pub_date = pub_dt.strftime("%Y-%m-%d")
            
            # 清理标题中的来源后缀
            title = entry.get("title", "")
            title = re.sub(r'\s*-\s*[^-]+$', '', title)
            
            news_items.append({
                "title": title,
                "link": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "published": pub_date,
                "summary": entry.get("summary", ""),
                "lang": lang,
                "_published_ts": int(pub_dt.timestamp()),
            })
        
        return news_items
    except Exception as e:
        print(f"Error fetching Google News ({lang}): {e}")
        return []


def get_36kr_news(num_results: int = 5) -> list[dict]:
    """从 36氪 获取 AI 金融相关新闻"""
    url = "https://36kr.com/api/search-column/mainsite"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        # 搜索 AI 金融相关内容
        params = {
            "per_page": num_results,
            "page": 1,
            "keyword": "AI 金融"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        news_items = []
        now = datetime.now()
        cutoff = now - timedelta(days=LOOKBACK_DAYS)
        for item in data.get("data", {}).get("items", [])[:num_results]:
            widget = item.get("widget_data", {})
            published_at = widget.get("published_at")
            if published_at:
                # e.g. 2026-02-09T12:34:56+08:00
                try:
                    pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except ValueError:
                    pub_dt = _parse_date_yyyy_mm_dd(published_at[:10]) or now
            else:
                pub_dt = now

            if pub_dt < cutoff:
                continue

            news_items.append({
                "title": widget.get("title", ""),
                "link": f"https://36kr.com/p/{widget.get('id', '')}",
                "source": "36氪",
                "published": pub_dt.strftime("%Y-%m-%d"),
                "summary": widget.get("summary", ""),
                "lang": "zh",
                "_published_ts": int(pub_dt.timestamp()),
            })
        
        return news_items
    except Exception as e:
        print(f"Error fetching 36kr: {e}")
        return []


def get_sspai_news(num_results: int = 5) -> list[dict]:
    """从少数派获取 AI 相关新闻"""
    url = "https://sspai.com/api/v1/articles"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        params = {
            "offset": 0,
            "limit": 20,
            "sort": "released_at"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        
        news_items = []
        now = datetime.now()
        cutoff = now - timedelta(days=LOOKBACK_DAYS)
        keywords = ["AI", "人工智能", "GPT", "金融", "fintech", "支付", "银行"]
        
        for item in data.get("data", []):
            title = item.get("title", "")
            summary = item.get("summary", "")
            
            # 只保留与 AI/金融相关的
            if any(kw.lower() in (title + summary).lower() for kw in keywords):
                released_at = item.get("released_at", 0)
                if not released_at:
                    continue

                pub_dt = datetime.fromtimestamp(released_at)
                if pub_dt < cutoff:
                    continue

                pub_date = pub_dt.strftime("%Y-%m-%d")
                
                news_items.append({
                    "title": title,
                    "link": f"https://sspai.com/post/{item.get('id', '')}",
                    "source": "少数派",
                    "published": pub_date,
                    "summary": summary,
                    "lang": "zh",
                    "_published_ts": int(pub_dt.timestamp()),
                })
                
                if len(news_items) >= num_results:
                    break
        
        return news_items
    except Exception as e:
        print(f"Error fetching sspai: {e}")
        return []


def deduplicate_news(news_list: list[dict]) -> list[dict]:
    """去重 - 基于标题相似度"""
    seen_titles = set()
    unique_news = []
    
    for news in news_list:
        # 简单去重：标题前30字符
        title_key = news["title"][:30].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    return unique_news


def filter_recent_news(news_list: list[dict]) -> list[dict]:
    """Filter news to only within LOOKBACK_DAYS."""
    now = datetime.now()
    cutoff = now - timedelta(days=LOOKBACK_DAYS)
    recent = []

    for item in news_list:
        ts = item.get("_published_ts")
        if isinstance(ts, int):
            pub_dt = datetime.fromtimestamp(ts)
        else:
            pub_dt = _parse_date_yyyy_mm_dd(item.get("published", "")) or now
        if pub_dt >= cutoff:
            recent.append(item)

    return recent


def fetch_all_news() -> dict:
    """获取所有来源的新闻"""
    print("Fetching news from all sources...")
    
    all_news = []
    
    # 英文新闻 - Google News
    en_queries = [
        "AI fintech",
        "artificial intelligence finance",
        "AI banking technology",
        "LLM financial services"
    ]
    
    for query in en_queries:
        print(f"  Fetching: {query}")
        news = get_google_news(query, lang="en", num_results=5)
        all_news.extend(news)
    
    # 中文新闻 - Google News
    zh_queries = [
        "AI 金融科技",
        "人工智能 银行",
        "大模型 金融应用"
    ]
    
    for query in zh_queries:
        print(f"  Fetching: {query}")
        news = get_google_news(query, lang="zh", num_results=5)
        all_news.extend(news)
    
    # 国内科技媒体
    print("  Fetching: 36氪")
    all_news.extend(get_36kr_news(5))
    
    print("  Fetching: 少数派")
    all_news.extend(get_sspai_news(5))
    
    # 去重
    all_news = deduplicate_news(all_news)

    # 只保留最近 LOOKBACK_DAYS 天内新闻
    all_news = filter_recent_news(all_news)
    
    # 按日期排序（最新在前）
    all_news.sort(key=lambda x: x.get("_published_ts", 0), reverse=True)
    
    # 限制总数
    all_news = all_news[:MAX_TOTAL_NEWS]
    
    # 分离中英文
    en_news = [n for n in all_news if n.get("lang") == "en"]
    zh_news = [n for n in all_news if n.get("lang") == "zh"]

    # 去掉内部字段
    for n in all_news:
        n.pop("_published_ts", None)
    
    result = {
        "fetch_date": datetime.now().strftime("%Y-%m-%d"),
        "week": datetime.now().strftime("%Y-W%W"),
        "total_count": len(all_news),
        "lookback_days": LOOKBACK_DAYS,
        "en_news": en_news,
        "zh_news": zh_news,
        "all_news": all_news
    }
    
    print(f"Fetched {len(all_news)} unique news items ({len(en_news)} EN, {len(zh_news)} ZH)")
    
    return result


def save_news(news_data: dict):
    """保存新闻数据到 JSON"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    week = news_data["week"]
    output_file = DATA_DIR / f"news_{week}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to: {output_file}")
    
    # 同时保存一份 latest.json
    latest_file = DATA_DIR / "latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to: {latest_file}")
    
    return output_file


if __name__ == "__main__":
    news_data = fetch_all_news()
    save_news(news_data)
