# -*- coding:utf-8 -*-
# @FileName  :food_crawler.py
# @Time      :2025/3/28 10:38
# @Author    :ZMFY
# Description:
import asyncio

from crawler import CommonSpider
from data_parse import parse_food_data
from utils import sanitize_filename


class FoodSpider(CommonSpider):
    def __init__(self, id_url, url_template,
                 output_dir, concurrency=10,
                 write_workers=8, headers=None, timeout=10):
        super(FoodSpider, self).__init__(id_url, url_template, output_dir,
                                         concurrency, write_workers, headers, timeout)

    async def parse_response(self, quest_json) -> dict | None:
        food_name, text = parse_food_data(quest_json)
        if food_name is None:
            return None
        safe_name = await sanitize_filename(food_name)
        return {
            "save_name": safe_name,
            "content": text
        }


if __name__ == "__main__":
    food_id_url = "https://gi.yatta.moe/api/v2/chs/food?vh=55F3"
    food_url_template = "https://gi.yatta.moe/api/v2/CHS/food/{}?vh=55F3"
    output_dir = './data/GenShin/food'
    spider = FoodSpider(food_id_url, food_url_template, output_dir)
    asyncio.run(spider.run())