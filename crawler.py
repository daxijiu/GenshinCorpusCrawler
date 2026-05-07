# -*- coding:utf-8 -*-
# @FileName  :crawler.py
# @Time      :2025/3/26 16:18
# @Author    :ZMFY
# Description:

import os
import asyncio
from pathlib import Path

import aiofiles
import aiohttp
from requests import session


class BaseSpider:
    def __init__(self, output_dir, concurrency=10, write_workers=8, headers=None, timeout=10):
        self.concurrency = concurrency
        self.output_dir = Path(output_dir)
        self.write_workers = write_workers
        self.session_lst = {}
        self.timeout = timeout
        self.headers = headers if headers is not None else {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "fail_details": []  # 存储 (id/name, reason)
        }

    @property
    def item_name(self):
        # 这个 Spider 负责的 Item 的名称
        return self.__class__.__name__[:-6]

    @property
    def set_session(self):
        # reference from https://blog.csdn.net/qq_36274515/article/details/120825513
        try:
            loop = asyncio.get_running_loop()
        except Exception as e:
            loop = asyncio.get_event_loop()
            asyncio.set_event_loop(loop)
        session = aiohttp.ClientSession(loop=loop, headers=self.headers)
        # 利用pid标记不同进程的session
        self.session_lst.update({os.getpid(): session})
        return session

    def get_one_session(self):
        session = None
        if self.session_lst:
            session = self.session_lst.get(os.getpid())
            if session and session.closed:
                self.session_lst.pop(os.getpid())
                session = self.set_session
            elif not session:
                session = self.set_session

        if not session or not session.loop.is_running():
            session = self.set_session

        return session

    async def close_session(self):
        if self.session_lst:
            for session in self.session_lst.values():
                await session.close()

    async def worker(self):
        raise NotImplementedError

    async def fetch_valid_ids(self, id_url):
        """获取所有有效任务ID"""
        try:
            data = await self.fetch(id_url)
            items = data.get("data", {}).get("items", {})

            # 解析有效ID（过滤chapterNum为null的条目）
            return [item["id"] for item in items.values()]  # 不转 int
        except Exception as e:
            print(f"🚨 获取有效ID失败: {e}")
            return []

    async def fetch(self, url, max_retries=3):
        """异步获取单个任务数据"""
        session = self.get_one_session()
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    response.raise_for_status()
            except Exception as e:
                print(f"⚠️ 请求失败（url {url} 第{attempt + 1}次重试）: {str(e)[:50]}...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
        return None

    async def run(self):
        raise NotImplementedError


class CommonSpider(BaseSpider):
    """
    一个通用的 Spider，执行流程为：
    1、基于 id_url 获取有效 ID 列表
    2、根据 ID 列表构造 URL 获取响应
    3、解析响应并保存
    """
    def __init__(self, id_url, url_template,
                 output_dir, concurrency=10,
                 write_workers=8, headers=None, timeout=10):
        super().__init__(output_dir, concurrency, write_workers, headers, timeout)
        self.id_url = id_url
        self.url_template = url_template
        self.id_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        self.save_queue = asyncio.Queue()
        self.remove_duplicate_name = False  # 在保存文件时是否去重(删除同名文件)

    async def parse_response(self, quest_json) -> dict | None:
        """子类根据自己的需求实现解析逻辑，并返回一个 Dict，字典应该包含两个字段 save_name 和 content"""
        raise NotImplementedError

    async def parse_worker(self):
        """异步解析工作协程, 从待解析队列读取响应，执行解析函数并将结果写入到保存队列"""
        while True:
            quest_id, quest_data = await self.response_queue.get()
            try:
                if quest_data:
                    save_data = await self.parse_response(quest_data)
                    if save_data is not None:
                        await self.save_queue.put(save_data)
                        print(f"⏳ 成功解析 {self.item_name}, ID: {quest_id}")
                    else:
                        self.stats["failed"] += 1
                        self.stats["fail_details"].append((quest_id, "解析结果为空 (可能是被过滤了)"))
            except Exception as e:
                self.stats["failed"] += 1
                self.stats["fail_details"].append((quest_id, f"解析异常: {str(e)}"))
                print(f"❌ 解析 {self.item_name} 失败, ID:{quest_id}]: {str(e)}")
            finally:
                self.response_queue.task_done()

    async def save_worker(self):
        """异步保存工作协程， 从保存队列读取数据并写入到磁盘"""
        while True:
            data = await self.save_queue.get()
            try:
                ext_str = f".{data.get('ext')}" if data.get('ext') else ".md"
                if 'sub_dir' in data and data['sub_dir']:
                    target_dir = self.output_dir / data['sub_dir']
                    target_dir.mkdir(parents=True, exist_ok=True)
                    filepath = target_dir / f'{data["save_name"]}{ext_str}'
                else:
                    filepath = self.output_dir / f'{data["save_name"]}{ext_str}'

                if filepath.exists() and self.remove_duplicate_name:
                    print(f"⚠️ 文件 {filepath} 已存在，删除本条目")
                else:
                    # 处理重复文件名
                    counter = 1
                    while filepath.exists():
                        new_name = f"{filepath.stem}_{counter}{filepath.suffix}"
                        filepath = filepath.with_name(new_name)
                        counter += 1
                    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                        await f.write(data["content"])
                        self.stats["success"] += 1
                        print(f"💾 保存 {self.item_name} 成功: {filepath.name}")

            except Exception as e:
                self.stats["failed"] += 1
                self.stats["fail_details"].append((data.get("save_name", "未知"), f"保存异常: {str(e)}"))
                print(f"🚨 保存 {self.item_name} 失败: {str(e)}")
            finally:
                self.save_queue.task_done()

    async def process_quest(self, quest_id):
        """执行每个 ID 的 URL 请求， 并将响应放入待解析队列"""
        url = self.url_template.format(quest_id)
        try:
            data = await self.fetch(url)
            if data:
                await self.response_queue.put((quest_id, data))
                print(f"⏳ 成功爬取 {self.item_name}: {quest_id}")
            else:
                self.stats["failed"] += 1
                self.stats["fail_details"].append((quest_id, "请求返回数据为空"))
        except Exception as e:
            self.stats["failed"] += 1
            self.stats["fail_details"].append((quest_id, f"请求异常: {str(e)}"))
            print(f"❌ 爬取 {self.item_name} 失败 [URL: {url}]: {str(e)}")

    async def worker(self):
        """异步爬取工作协程"""
        while True:
            quest_id = await self.id_queue.get()
            await self.process_quest(quest_id)
            self.id_queue.task_done()

    async def run(self):
        """异步主流程"""
        # 创建输出目录
        await asyncio.to_thread(self.output_dir.mkdir, parents=True, exist_ok=True)

        # 启动保存worker池
        save_workers = [asyncio.create_task(self.save_worker())
                        for _ in range(self.write_workers)]

        # 启动解析worker池
        parse_workers = [asyncio.create_task(self.parse_worker())
                         for _ in range(self.concurrency * 2)]

        # 获取有效任务ID列表
        valid_ids = await self.fetch_valid_ids(self.id_url)
        self.stats["total"] = len(valid_ids)
        if not valid_ids:
            print(f"🛑 条目{self.item_name}未找到有效任务ID")
            await self.close_session()
            return
        print(f"✅ 条目{self.item_name}获取到{len(valid_ids)}个有效 ID")
        for bid in valid_ids:
            self.id_queue.put_nowait(bid)

        # 启动工作线程
        tasks = [asyncio.create_task(self.worker()) for _ in range(self.concurrency)]

        # 等待队列处理完成
        await self.id_queue.join()
        await self.response_queue.join()
        await self.save_queue.join()

        # 关闭worker
        for worker in tasks + parse_workers + save_workers:
            worker.cancel()

        await self.close_session()


if __name__ == "__main__":
    pass
