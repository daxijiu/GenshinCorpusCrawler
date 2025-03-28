# -*- coding:utf-8 -*-
# @FileName  :character_crawler.py
# @Time      :2025/3/27 18:34
# @Author    :ZMFY
# Description:
import asyncio

from crawler import CommonSpider
from data_parse import parse_character_data
from utils import sanitize_filename


class CharacterSpider(CommonSpider):
    default_weapon_type = {
        "WEAPON_SWORD_ONE_HAND": "单手剑",
        "WEAPON_CATALYST": "法器",
        "WEAPON_CLAYMORE": "双手剑",
        "WEAPON_BOW": "弓",
        "WEAPON_POLE": "长柄武器"
    }

    """爬取角色文本内容的爬虫，不爬取数值信息"""

    def __init__(self, id_url, url_template, story_url_template,
                 output_dir, concurrency=10,
                 write_workers=8, headers=None, timeout=10):
        super().__init__(id_url, url_template, output_dir, concurrency, write_workers, headers, timeout)
        self.story_url_template = story_url_template
        self.weapon_types = None
        self.remove_duplicate_name = True   # 去除重复角色名文件，针对旅行者条目重复

    async def parse_response(self, quest_json) -> dict | None:
        character_name, text = parse_character_data(quest_json, self.weapon_types)
        if character_name is None:
            return None
        safe_name = await sanitize_filename(character_name)
        return {
            "save_name": safe_name,
            "content": text
        }

    async def process_quest(self, quest_id):
        """执行每个 ID 的 URL 请求， 并将响应放入待解析队列。重写函数，添加对角色故事的额外请求并合并响应"""
        try:
            url = self.url_template.format(quest_id)
            story_id = str(quest_id).split('-')[0]  # 重复 ID 共享同一个"故事"页面
            story_url = self.story_url_template.format(story_id)
            data = await self.fetch(url)
            story_data = await self.fetch(story_url)
            if data and story_data:
                data['data']['story'] = story_data.get('data', {}).get('story', {})
                await self.response_queue.put((quest_id, data))
                print(f"⏳ 成功爬取 {self.item_name}: {quest_id}")
        except Exception as e:
            print(f"❌ 爬取 {self.item_name} 失败 [URL: {url}]: {str(e)}")

    async def fetch_valid_ids(self, id_url):
        """获取所有有效任务ID. 重写函数，抓取 ID 的同时获取 Weapon_types 字典"""
        try:
            data = await self.fetch(id_url)
            items = data.get("data", {}).get("items", {})
            self.weapon_types = data.get('data', {}).get("types", self.default_weapon_type)

            # 解析有效ID（过滤chapterNum为null的条目）
            return [item["id"] for item in items.values()]  # ID 不转 int
        except Exception as e:
            print(f"🚨 获取有效ID失败: {e}")
            return []


if __name__ == "__main__":
    avatar_id_url = "https://gi.yatta.moe/api/v2/chs/avatar?vh=55F2"
    avatar_url_template = "https://gi.yatta.moe/api/v2/chs/avatar/{}?vh=55F2"
    avatar_story_url_template = "https://gi.yatta.moe/api/v2/chs/avatarFetter/{}?vh=55F2"
    output_dir = "./data/GenShin/character"
    spider = CharacterSpider(avatar_id_url, avatar_url_template, avatar_story_url_template, output_dir)
    asyncio.run(spider.run())
