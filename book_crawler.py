# -*- coding:utf-8 -*-
# @FileName  :book_crawler.py
# @Time      :2025/3/26 14:56
# @Author    :ZMFY
# Description:


import asyncio

import aiofiles

from crawler import BaseSpider
from data_parse import post_precess_text
from utils import sanitize_filename


class BookSpider(BaseSpider):
    def __init__(self, id_url, url_template, readable_url_template, output_dir,
                 concurrency=5, write_workers=4, headers=None, timeout=10):
        super().__init__(output_dir, concurrency, write_workers, headers, timeout)
        self.url_template = url_template
        self.readable_url_template = readable_url_template
        self.id_url = id_url
        self.book_queue = asyncio.Queue()
        self.chapter_queue = asyncio.Queue()
        self.save_queue = asyncio.Queue()
        self.book_tracker = {}  # {quest_id: (total_vols, completed_vols, data)}
        self.tracker_lock = asyncio.Lock()

    async def process_quest(self, quest_id: int):
        """处理单本书籍, quest_id 即 book_id"""
        url = self.url_template.format(quest_id)
        data = await self.fetch(url)
        if not data or not data.get('data'):
            print(f"🛑 未解析到 {self.item_name} {quest_id}")
            return
        data = data['data']

        async with self.tracker_lock:
            self.book_tracker[quest_id] = {
                'total': len(data['volume']),
                'completed': 0,
                'data': {
                    'name': data['name'],
                    'volumes': []
                }
            }

        # 提交章节任务
        for vol in data['volume']:
            await self.chapter_queue.put((quest_id, vol))

    async def save_worker(self):
        """异步文件存储工作协程"""
        while True:
            book_data = await self.save_queue.get()
            book_name = str(book_data['name'])

            try:
                if book_name.isdigit():
                    # 跳过数字命名的文本
                    continue

                # 生成安全文件名
                safe_name = await sanitize_filename(book_name)
                filepath = self.output_dir / f"{safe_name}.txt"

                # 异步写入文件
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    # 写入书籍标题
                    await f.write(f"{book_name}\n\n")

                    # 顺序写入各卷
                    for vol in book_data['volumes']:
                        txt = f"{vol['name']}\n{vol['description']}\n\n{vol.get('content', '暂无内容')}\n\n"
                        txt = post_precess_text(txt)
                        await f.write(txt)

                print(f"💾 保存 {self.item_name} 成功, 文件名: {safe_name}")

            except Exception as e:
                print(f"🚨 保存 {self.item_name} 失败 {book_name}: {str(e)}, book data: {book_data}")
            finally:
                self.save_queue.task_done()

    async def process_chapter(self):
        """处理单个章节"""
        while True:
            book_id, vol = await self.chapter_queue.get()

            # 获取章节内容
            url = self.readable_url_template.format(vol['storyId'])
            content = await self.fetch(url)
            content = content['data']

            async with self.tracker_lock:
                tracker = self.book_tracker.get(book_id)
                if not tracker:
                    continue

                # 更新数据
                tracker['data']['volumes'].append({
                    **vol,
                    'content': content
                })
                tracker['completed'] += 1

                # 检查是否完成
                if tracker['completed'] == tracker['total']:
                    # 提交保存任务
                    print(f"⏳ 已成功获取 {self.item_name} {tracker['data']['name']} 的全部内容")
                    await self.save_queue.put(tracker['data'])
                    del self.book_tracker[book_id]  # 释放内存

            self.chapter_queue.task_done()

    async def worker(self):
        """书籍处理工作线程"""
        while True:
            book_id = await self.book_queue.get()
            await self.process_quest(book_id)
            self.book_queue.task_done()

    async def run(self):
        """启动爬虫"""
        # 创建存储目录
        await asyncio.to_thread(self.output_dir.mkdir, parents=True, exist_ok=True)

        # 启动存储worker
        save_workers = [
            asyncio.create_task(self.save_worker())
            for _ in range(self.write_workers)
        ]
        chapter_workers = [
            asyncio.create_task(self.process_chapter())
            for _ in range(self.concurrency * 2)
        ]

        # 初始化书籍ID队列
        valid_ids = await self.fetch_valid_ids(self.id_url)
        if not valid_ids:
            print(f"🛑 条目{self.item_name}未找到有效任务ID")
            await self.close_session()
            return
        print(f"✅ 条目{self.item_name}获取到{len(valid_ids)}个有效 ID")
        for bid in valid_ids:
            self.book_queue.put_nowait(bid)

        # 启动工作协程
        workers = [
            asyncio.create_task(self.worker())
            for _ in range(self.concurrency)
        ]

        # 等待任务完成
        await self.book_queue.join()
        await self.chapter_queue.join()
        await self.save_queue.join()

        # 清理工作线程
        for w in workers + chapter_workers + save_workers:
            w.cancel()

        await self.close_session()


if __name__ == '__main__':
    id_api_base = "https://gi.yatta.moe/api/v2/chs/book?vh=55F1"
    bool_base = "https://gi.yatta.moe/api/v2/CHS/book/{}?vh=55F1"
    readable_base = "https://gi.yatta.moe/api/v2/CHS/readable/Book{}?vh=55F1"
    output_dir = "./data/Genshin/books"
    spider = BookSpider(id_api_base, bool_base, readable_base, output_dir)
    asyncio.run(spider.run())

