# -*- coding:utf-8 -*-
# @FileName  :artifact_crawler.py
# @Time      :2025/3/27 15:15
# @Author    :ZMFY
# Description:
import asyncio

import aiofiles

from book_crawler import BookSpider
from data_parse import process_source, post_precess_text
from utils import sanitize_filename, number_lowercase_to_uppercase


class ArtifactSpider(BookSpider):
    def __init__(self, id_url, url_template, readable_url_template, output_dir,
                 concurrency=5, write_workers=4, headers=None, timeout=10):
        super().__init__(id_url, url_template, readable_url_template, output_dir,
                         concurrency, write_workers, headers, timeout)

    async def process_quest(self, quest_id: int):
        """重写函数，处理每个圣遗物套装， "套装" 与 "书" 的词条接近"""
        url = self.url_template.format(quest_id)
        data = await self.fetch(url)
        if not data or not data.get('data'):
            print(f"🛑 未解析到 {self.item_name} {quest_id}")
            return
        data = data['data']

        try:
            if (suit_data := data.get('suit', None)) is not None:
                num_sub_item = len(suit_data.keys())     # 套装子件数量
                level = int(data['levelList'][-1])  # 获取星级
                suit_affix = data['affixList']      # 套装效果
                affix_items = sorted(suit_affix.items(), key=lambda x: x[0])
                if len(affix_items) > 1:
                    affix_text = f"两件套效果: {affix_items[0][1]}\n四件套效果: {affix_items[1][1]}"
                else:
                    affix_text = f"两件套效果: {affix_items[0][1]}"

                async with self.tracker_lock:
                    self.book_tracker[quest_id] = {
                        'total': num_sub_item,
                        'completed': 0,
                        'data': {
                            'name': data['name'],
                            'level': f"{number_lowercase_to_uppercase(level)}星圣遗物",
                            'source': process_source(data, data['name']),
                            "affix": affix_text,
                            'volumes': []  # 待补充字段，类似 Book 的各卷的内容
                        }
                    }

                # 提交子件任务
                for idx, sub in enumerate(suit_data.values()):
                    story_id = int(sub['icon'][-1])     # 获取子件 ID
                    sub['storyId'] = f"{quest_id}_{story_id}"
                    await self.chapter_queue.put((quest_id, sub))
        except Exception as e:
            print(f"❌ 解析 {self.item_name} 异常， ID:  {quest_id}")

    async def save_worker(self):
        """异步文件存储工作协程"""
        while True:
            artifact_data = await self.save_queue.get()
            artifact_name = str(artifact_data['name'])

            try:
                # 生成安全文件名
                safe_name = await sanitize_filename(artifact_name)
                filepath = self.output_dir / f"{safe_name}.md"

                # 异步写入文件
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    # 写入圣遗物/遗器标题
                    await f.write(f"# {artifact_name} - {artifact_data['level']}\n\n")

                    # 写入套装效果
                    await f.write(f"### 套装效果\n{artifact_data['affix']}\n\n")

                    # 写入来源
                    if artifact_data['source']:
                        await f.write(f"### 来源\n{artifact_data['source']}\n\n")

                    # 写入圣遗物的子件内容
                    await f.write(f"## 套装组件\n")
                    for sub_item in artifact_data['volumes']:
                        txt = (f"### {sub_item['name']}\n> {sub_item['description'].replace('\n', '')}\n\n"
                               f"{sub_item.get('content', '暂无内容').replace('\n\n', '\n')}\n")
                        await f.write(txt)

                    print(f"💾 保存成功, 文件名: {safe_name}")

            except Exception as e:
                print(f"🚨 保存失败 {artifact_name}: {str(e)}, book data: {artifact_data}")
            finally:
                self.save_queue.task_done()


if __name__ == "__main__":
    artifact_id_url = "https://gi.yatta.moe/api/v2/chs/reliquary?vh=55F2"
    artifact_url_template = "https://gi.yatta.moe/api/v2/CHS/reliquary/{}?vh=55F2"
    artifact_readable_url = "https://gi.yatta.moe/api/v2/CHS/readable/Relic{}?vh=55F2"  # 填充格式： {artifact_id}_{sub_id}

    output_dir = "./data/GenShin/artifact"
    spider = ArtifactSpider(artifact_id_url, artifact_url_template, artifact_readable_url, output_dir)
    asyncio.run(spider.run())

