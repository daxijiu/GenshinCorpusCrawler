# Genshin Corpus Crawler 🏮

《原神》全语料异步爬虫 - 高效采集剧情/书籍/角色/武器等游戏内文本数据

## 项目介绍

### 数据来源
本项目通过逆向分析抓取自非官方《原神》资料站 [gi.yatta.moe](https://gi.yatta.moe)，该站以结构化形式整理了游戏内各类文本资源。所有数据仅限用于非商业的学术研究或个人学习。

### 支持采集的语料类型
| 类别       | 包含内容示例   | 数据量预估  |
|------------|----------|--------|
| 剧情任务   | 主线/支线任务对话等 | 12000+ |
| 书籍文献   | 《清泉之心》《野猪公主》等 | 400+   |
| 角色资料   | 角色描述/角色故事等 | 90+    |
| 武器图鉴   | 武器背景故事/属性描述等 | 200+   |
| 圣遗物     | 套装故事/单件描述等 | 50+    |
| 材料       | 突破材料/天赋书等| 600+   |
| 生物       | 怪物图鉴/属性说明等 | 200+   |
| 食物       | 食谱/料理效果描述等| 300+   |

## 环境要求

### Python版本
- Python 3.8+

### 依赖库
```bash
# 核心依赖
pip install aiohttp==3.11.14
pip install aiofiles==24.1.0
```

## 快速开始

### 全量采集
```bash
python main.py -o ./data
```

### 选择性采集
```bash
# 仅采集角色和武器数据
python main.py -o ./data \
  --book false \
  --artifact false \
  --monster false \
  --material false \
  --food false \
  --story false \
  --character true \
  --weapon true

```