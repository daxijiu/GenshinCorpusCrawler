# -*- coding:utf-8 -*-
# @FileName  :monster_crawler.py
# @Time      :2025/3/27 12:41
# @Author    :ZMFY
# Description:
import asyncio

from crawler import CommonSpider
from data_parse import parse_monster_data
from utils import sanitize_filename


class MonsterSpider(CommonSpider):
    def __init__(self, id_url, url_template, output_dir, concurrency=5,
                 write_workers=4, headers=None, timeout=10):
        super().__init__(id_url, url_template, output_dir, concurrency, write_workers, headers, timeout)

    async def parse_response(self, quest_json) -> dict:
        monster_name, monster_text = parse_monster_data(quest_json)
        if monster_name is None:
            return None

        safe_name = await sanitize_filename(monster_name)
        return {
            "save_name": safe_name,
            "content": monster_text
        }


if __name__ == "__main__":
    monster_id_url = "https://gi.yatta.moe/api/v2/chs/monster?vh=55F2"
    monster_url_template = "https://gi.yatta.moe/api/v2/chs/monster/{}?vh=55F2"
    output_dir = './data/GenShin/monster'
    spider = MonsterSpider(monster_id_url, monster_url_template, output_dir)
    asyncio.run(spider.run())


