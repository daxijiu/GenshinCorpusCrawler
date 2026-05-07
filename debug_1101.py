import asyncio
from story_crawler import StorySpider

class DebugSpider(StorySpider):
    async def fetch_valid_ids(self, id_url):
        return [1101, 1102]

async def main():
    spider = DebugSpider(
        id_url="https://gi.yatta.moe/api/v2/CHS/quest?vh=55F1",
        url_template="https://gi.yatta.moe/api/v2/CHS/quest/{}?vh=55F1",
        output_dir="./data/story"
    )
    await spider.run()

if __name__ == "__main__":
    asyncio.run(main())
