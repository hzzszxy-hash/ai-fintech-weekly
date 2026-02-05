#!/usr/bin/env python3
"""
AI Fintech Weekly - Static Site Generator
生成静态网站和存档页面
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
DOCS_DIR = PROJECT_ROOT / "docs"
ARCHIVES_DIR = DOCS_DIR / "archives"


def load_json(filepath: Path) -> dict:
    """加载 JSON 文件"""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_weeks() -> list[str]:
    """获取所有已有的周报周次"""
    weeks = []
    for f in DATA_DIR.glob("news_*.json"):
        week = f.stem.replace("news_", "")
        weeks.append(week)
    weeks.sort(reverse=True)
    return weeks


def generate_index_page(env: Environment, news_data: dict, summary_data: dict, all_weeks: list[str]):
    """生成首页"""
    template = env.get_template("index.html")
    
    html = template.render(
        news=news_data,
        summary=summary_data,
        all_weeks=all_weeks,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        current_week=news_data.get("week", "")
    )
    
    output_file = DOCS_DIR / "index.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Generated: {output_file}")


def generate_archive_page(env: Environment, week: str):
    """生成单个周的存档页面"""
    news_file = DATA_DIR / f"news_{week}.json"
    summary_file = DATA_DIR / f"summary_{week}.json"
    
    news_data = load_json(news_file)
    summary_data = load_json(summary_file)
    
    if not news_data:
        print(f"Skipping {week}: no news data")
        return
    
    template = env.get_template("archive.html")
    
    html = template.render(
        news=news_data,
        summary=summary_data,
        week=week,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    
    output_file = ARCHIVES_DIR / f"{week}.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Generated: {output_file}")


def generate_archives_index(env: Environment, all_weeks: list[str]):
    """生成存档索引页"""
    template = env.get_template("archives_index.html")
    
    # 加载每周的基本信息
    weeks_info = []
    for week in all_weeks:
        news_file = DATA_DIR / f"news_{week}.json"
        news_data = load_json(news_file)
        if news_data:
            weeks_info.append({
                "week": week,
                "fetch_date": news_data.get("fetch_date", ""),
                "total_count": news_data.get("total_count", 0)
            })
    
    html = template.render(
        weeks=weeks_info,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    
    output_file = DOCS_DIR / "archives.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Generated: {output_file}")


def copy_static_assets():
    """复制静态资源"""
    static_src = TEMPLATES_DIR / "static"
    static_dst = DOCS_DIR / "static"
    
    if static_src.exists():
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"Copied static assets to {static_dst}")


def generate_site():
    """生成完整网站"""
    print("Generating static site...")
    
    # 确保目录存在
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
    
    # 设置 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True
    )
    
    # 加载最新数据
    news_data = load_json(DATA_DIR / "latest.json")
    summary_data = load_json(DATA_DIR / "latest_summary.json")
    
    # 获取所有周次
    all_weeks = get_all_weeks()
    
    if not news_data:
        print("No news data found. Run fetch_news.py first.")
        return
    
    # 生成首页
    generate_index_page(env, news_data, summary_data, all_weeks)
    
    # 生成每周的存档页
    for week in all_weeks:
        generate_archive_page(env, week)
    
    # 生成存档索引
    generate_archives_index(env, all_weeks)
    
    # 复制静态资源
    copy_static_assets()
    
    print(f"\nSite generated successfully!")
    print(f"  - Index: {DOCS_DIR / 'index.html'}")
    print(f"  - Archives: {ARCHIVES_DIR}")


if __name__ == "__main__":
    generate_site()
