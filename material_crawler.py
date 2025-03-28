# -*- coding:utf-8 -*-
# @FileName  :material_crawler.py
# @Time      :2025/3/27 13:55
# @Author    :ZMFY
# Description:
import asyncio

from crawler import CommonSpider
from data_parse import parse_material_data
from utils import sanitize_filename


class MaterialSpider(CommonSpider):
    def __init__(self, id_url, url_template,
                 output_dir, concurrency=10,
                 write_workers=8, headers=None, timeout=10):
        super(MaterialSpider, self).__init__(id_url, url_template, output_dir,
                                             concurrency, write_workers, headers, timeout)

    @property
    def item_name(self):
        return "Material"

    async def parse_response(self, quest_json) -> dict | None:
        material_name, text = parse_material_data(quest_json)
        if material_name is None:
            return None

        safe_name = await sanitize_filename(material_name)
        return {
            "save_name": safe_name,
            "content": text
        }


if __name__ == "__main__":
    material_id_url = "https://gi.yatta.moe/api/v2/chs/material?vh=55F2"
    material_url_template = "https://gi.yatta.moe/api/v2/CHS/material/{}?vh=55F2"
    output_dir = "./data/GenShin/material"
    spider= MaterialSpider(material_id_url, material_url_template, output_dir)
    asyncio.run(spider.run())

