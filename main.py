# -*- coding:utf-8 -*-
# @FileName  :main.py
# @Time      :2025/3/26 12:57
# @Author    :ZMFY
# Description:

import asyncio
import argparse
import time

from book_crawler import BookSpider
from food_crawler import FoodSpider
from character_crawler import CharacterSpider
from story_crawler import StorySpider
from weapon_crawler import WeaponSpider
from material_crawler import MaterialSpider
from monster_crawler import MonsterSpider
from artifact_crawler import ArtifactSpider

task_dic = {
    "story": {
        "id_url": "https://gi.yatta.moe/api/v2/CHS/quest?vh=55F1",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/quest/{}?vh=55F1",
    },
    "book": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/book?vh=55F1",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/book/{}?vh=55F1",
        "readable_url_template": "https://gi.yatta.moe/api/v2/CHS/readable/Book{}?vh=55F1",
    },
    "food": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/food?vh=55F3",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/food/{}?vh=55F3",
    },
    "character": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/avatar?vh=55F2",
        "url_template": "https://gi.yatta.moe/api/v2/chs/avatar/{}?vh=55F2",
        "story_url_template": "https://gi.yatta.moe/api/v2/chs/avatarFetter/{}?vh=55F2",
    },
    "artifact": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/reliquary?vh=55F2",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/reliquary/{}?vh=55F2",
        "readable_url_template": "https://gi.yatta.moe/api/v2/CHS/readable/Relic{}?vh=55F2",
    },
    "monster": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/monster?vh=55F2",
        "url_template": "https://gi.yatta.moe/api/v2/chs/monster/{}?vh=55F2"
    },
    "material": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/material?vh=55F2",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/material/{}?vh=55F2",
    },
    "weapon": {
        "id_url": "https://gi.yatta.moe/api/v2/chs/weapon?vh=55F1",
        "url_template": "https://gi.yatta.moe/api/v2/CHS/weapon/{}?vh=55F1",
        "story_url_template": "https://gi.yatta.moe/api/v2/CHS/readable/Weapon{}?vh=55F1",
    }
}

parser = argparse.ArgumentParser(description="arguments for crawlers of GenShin corpus")
parser.add_argument("--output_dir", '-o', type=str, default="./data/")
parser.add_argument("--book", type=str, default="true", choices=["true", "false"],
                    help="whether crawl book corpus")
parser.add_argument("--artifact", type=str, default="true", choices=["true", "false"],
                    help="whether crawl artifact corpus")
parser.add_argument("--monster", default="true", type=str, choices=["true", "false"],
                    help="whether crawl monster corpus")
parser.add_argument("--material", default="true", type=str, choices=["true", "false"],
                    help="whether crawl material corpus")
parser.add_argument("--weapon", default='true', type=str, choices=["true", "false"],
                    help="whether crawl weapon corpus")
parser.add_argument("--food", default='true', type=str, choices=["true", "false"],
                    help="whether crawl food corpus")
parser.add_argument("--character", default='true', type=str, choices=["true", "false"],
                    help="whether crawl character corpus")
parser.add_argument("--story", default='true', type=str, choices=["true", "false"],
                    help="whether crawl story corpus")
parser.add_argument("--timeout", type=int, default=10, help="request timeout of network")
parser.add_argument("--write_workers", default=5, type=int, help="number of workers to save data for per spider")
parser.add_argument("--concurrency", default=5, type=int, help="number of workers to crawl url for per spider")
args = parser.parse_args()


async def main():
    tasks = []
    if args.artifact == "true":
        spider = ArtifactSpider(
            **task_dic["artifact"], output_dir=f"{args.output_dir}/artifact",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.material == "true":
        spider = MaterialSpider(
            **task_dic["material"], output_dir=f"{args.output_dir}/material",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.monster == "true":
        spider = MonsterSpider(
            **task_dic["monster"], output_dir=f"{args.output_dir}/monster",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.character == "true":
        spider = CharacterSpider(
            **task_dic["character"], output_dir=f"{args.output_dir}/character",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.story == "true":
        spider = StorySpider(
            **task_dic["story"], output_dir=f"{args.output_dir}/story",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.book == "true":
        spider = BookSpider(
            **task_dic['book'], output_dir=f"{args.output_dir}/book",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.weapon == 'true':
        spider = WeaponSpider(
            **task_dic['weapon'], output_dir=f"{args.output_dir}/weapon",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    if args.food == 'true':
        spider = FoodSpider(
            **task_dic['food'], output_dir=f"{args.output_dir}/food",
            concurrency=args.concurrency, timeout=args.timeout, write_workers=args.write_workers
        )
        tasks.append(spider.run())
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    print(f"🚀 启动爬虫程序")
    st = time.perf_counter()
    asyncio.run(main())
    print(f"✅ 爬虫结束，总耗时{time.perf_counter() - st:.4f} 秒")
