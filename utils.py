# -*- coding:utf-8 -*-
# @FileName  :utils.py
# @Time      :2025/3/26 14:57
# @Author    :ZMFY
# Description:
import asyncio
import re

import unicodedata

if __name__ == "__main__":
    pass


async def sanitize_filename(name: str, max_length=200) -> str:
    """生成合法文件名（异步优化版）"""
    # 异步处理Unicode标准化
    normalized = await asyncio.to_thread(
        unicodedata.normalize, 'NFKC', name
    )

    # 替换非法字符
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', normalized)

    # 智能截断（优先在标点处断开）
    if len(cleaned) > max_length:
        trunc_index = max(
            cleaned.rfind('.', 0, max_length),
            cleaned.rfind('_', 0, max_length),
            max_length
        )
        return cleaned[:trunc_index]
    return cleaned


def number_lowercase_to_uppercase(number) -> str:
    dic = {
        1: "一",
        2: "二",
        3: "三",
        4: "四",
        5: "五",
        6: "六",
        7: "七",
        8: "八",
        9: "九"
    }
    return dic[number]