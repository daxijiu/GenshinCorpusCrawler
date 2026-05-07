# -*- coding:utf-8 -*-
# @FileName  :main.py
# @Time      :2025/3/26 10:32
# @Author    :ZMFY
# Description:
import asyncio
from pathlib import Path

import aiofiles
import aiohttp
from flask import session

from crawler import BaseSpider, CommonSpider
from data_parse import parse_story_data
from utils import sanitize_filename


class StorySpider(CommonSpider):
    def __init__(self, id_url, url_template,
                 concurrency=5, output_dir="./data/Genshin/story",
                 write_workers=4, headers=None, timeout=10):
        super().__init__(id_url, url_template, output_dir, concurrency, write_workers, headers, timeout)

    async def fetch_valid_ids(self, id_url):
        try:
            data = await self.fetch(id_url)
            items = data.get("data", {}).get("items", {})

            # 解析有效ID（过滤chapterNum为null的条目）
            return [int(item["id"]) for item in items.values() if item.get("chapterNum") is not None]
        except Exception as e:
            print(f"🚨 获取有效ID失败: {e}")
            return []

    async def parse_response(self, quest_json):
        """异步解析任务数据， 执行解析，并返回解析结果"""
        result = parse_story_data(quest_json)
        if result is None or result[0] is None:
            return None
            
        chapter_num, chapter_title, parsed_text, quest_type, quest_id = result

        if chapter_num is None:
            chapter_num = ""

        raw_name = f"[{quest_id}] {chapter_num} {chapter_title}".replace('  ', ' ').strip()
        safe_name = await sanitize_filename(raw_name)
        save_data = {
            "save_name": safe_name,
            "content": parsed_text,
            "sub_dir": quest_type,
            "ext": "md"
        }
        return save_data


if __name__ == '__main__':
    quest_url = "https://gi.yatta.moe/api/v2/CHS/quest?vh=55F1"
    url_template = "https://gi.yatta.moe/api/v2/CHS/quest/{}?vh=55F1"
    spider = StorySpider(quest_url, url_template)
    asyncio.run(spider.run())

