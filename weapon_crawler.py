# -*- coding:utf-8 -*-
# @FileName  :weapon_crawler.py
# @Time      :2025/3/26 18:45
# @Author    :ZMFY
# Description:
import asyncio

import aiohttp

from crawler import CommonSpider
from story_crawler import StorySpider
from data_parse import parse_weapon_data
from utils import sanitize_filename


class WeaponSpider(CommonSpider):
    """
    爬取武器文本内容的爬虫，包括武器名、类型、描述和故事（可选）
    web 请求流程与 StorySpider 类似， 解析不同
    因此仅改写 process_quest 和 parse_response 函数 以及解析逻辑
    """

    def __init__(self, id_url, url_template,
                 story_url_template, exclude_story=False, item_name="武器",
                 concurrency=5, output_dir="./data/Genshin/weapon",
                 write_workers=4, headers=None, timeout=10):
        super().__init__(id_url, url_template,
                         output_dir, concurrency,
                         write_workers, headers, timeout)
        self.exclude_story = exclude_story
        self.story_url_template = story_url_template        # 武器故事 URL 模板
        self.item_zh_name = item_name  # Item 的中文名，原神为武器，星铁为光锥

    async def parse_response(self, quest_json):
        """异步解析任务数据"""
        weapon_name, text = parse_weapon_data(quest_json, self.exclude_story, self.item_zh_name)
        if weapon_name is None:
            return None

        safe_name = await sanitize_filename(f"{weapon_name}")
        save_data = {
            "save_name": safe_name,
            "content": text,
        }
        return save_data

    async def process_quest(self, quest_id):
        url = self.url_template.format(quest_id)
        affix_text_url = self.story_url_template.format(quest_id)
        try:
            data = await self.fetch(url)
            story = await self.fetch(affix_text_url)
            if data and data.get('data', None):
                data['data']["story"] = story['data']
                await self.response_queue.put((quest_id, data))
                print(f"⏳ 成功爬取: {quest_id}")
        except Exception as e:
            print(f"❌ 爬取失败 [URL: {url}]: {str(e)}")


if __name__ == "__main__":
    weapon_id_url = "https://gi.yatta.moe/api/v2/chs/weapon?vh=55F1"
    weapon_url_template = "https://gi.yatta.moe/api/v2/CHS/weapon/{}?vh=55F1"
    weapon_story_url_template = "https://gi.yatta.moe/api/v2/CHS/readable/Weapon{}?vh=55F1"
    weapon_glossary_url = "https://gi.yatta.moe/api/v2/CHS/manualWeapon?vh=55F1"
    output_dir = "./data/GenShin/weapon"
    exclude_story = False
    spider = WeaponSpider(weapon_id_url, weapon_url_template, weapon_story_url_template,
                          output_dir=output_dir, exclude_story=exclude_story)
    asyncio.run(spider.run())
