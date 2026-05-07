import os
import shutil
import re
import difflib

src_dir = r"e:\Projects\GenshinCorpusCrawler\data\story"
dst_dir = r"e:\Projects\GenshinCorpusCrawler\传说任务"

os.makedirs(dst_dir, exist_ok=True)

quests = [
    ("凯亚", "孔雀羽之章 第一幕 海盗秘宝"),
    ("迪卢克", "夜枭之章 第一幕 暗夜英雄的不在场证明"),
    ("安柏", "小兔之章 第一幕 风、勇气和翅膀"),
    ("丽莎", "沙漏之章 第一幕 麻烦的工作"),
    ("雷泽", "小狼之章 第一幕 卢皮卡的意义"),
    ("琴", "幼狮之章 第一幕 骑士团长的一日假期"),
    ("香菱", "长杓之章 第一幕 蒙德食遇之旅"),
    ("行秋", "锦织之章 第一幕 江湖不问出处"),
    ("可莉", "四叶草之章 第一幕 真正的宝物"),
    ("莫娜", "映天之章 第一幕 在此世的星空之外"),
    ("魈", "金翅鹏王之章 第一幕 槐柯胡蝶，傩佑之梦"),
    ("达达利亚", "鲸天之章 第一幕 独眼小宝总动员"),
    ("温迪", "歌仙之章 第一幕 若你困于无风之地"),
    ("钟离", "古闻之章 第一幕 盐花"),
    ("甘雨", "仙麟之章 第一幕 云之海，人之海"),
    ("阿贝多", "白垩之章 第一幕 旅行者观察报告"),
    ("胡桃", "引蝶之章 第一幕 奈何蝶飞去"),
    ("优菈", "浪沫之章 第一幕 浪花不再归海"),
    ("钟离", "古闻之章 第二幕 匪石"),
    ("宵宫", "琉金之章 第一幕 如梦如电的隽永"),
    ("神里绫华", "雪鹤之章 第一幕 鹤与白兔的诉说"),
    ("雷电将军", "天下人之章 第一幕 影照浮世风流"),
    ("珊瑚宫心海", "眠龙之章 第一幕 兵戈梦去，春草如茵"),
    ("八重神子", "仙狐之章 第一幕 鸣神御祓祈愿祭"),
    ("荒泷一斗", "天牛之章 第一幕 赤金魂"),
    ("雷电将军", "天下人之章 第二幕 须臾百梦"),
    ("神里绫人", "神守柏之章 第一幕 梧桐一叶落"),
    ("夜兰", "幽客之章 第一幕 棋生断处"),
    ("提纳里", "郭狐之章 第一幕 没有答案的课题"),
    ("枫原万叶", "枫红之章 第一幕 陌野不识故人"),
    ("赛诺", "金狼之章 第一幕 沉沙归寂"),
    ("妮露", "睡莲之章 第一幕 致智慧者"),
    ("纳西妲", "智慧主之章 第一幕 余温"),
    ("艾尔海森", "天隼之章 第一幕 乌合的虚像"),
    ("迪希雅", "蝎尾鬃狮之章 第一幕 「狮之血」"),
    ("白术", "悬壶之章 第一幕 「医心」"),
    ("宵宫", "琉金之章 第二幕 拾星之旅"),
    ("纳西妲", "智慧主之章 第二幕 归乡"),
    ("林尼", "黑斑猫之章 第一幕 被遗忘的怪盗"),
    ("那维莱特", "潮涌之章 第一幕 往日留痕"),
    ("莱欧斯利", "守狱犬之章 第一幕 于怨嗟之地重生"),
    ("芙宁娜", "司颂之章 第一幕 「水的女儿」"),
    ("娜维娅", "野蔷薇之章 第一幕 共渡潮落"),
    ("闲云", "闲鹤之章 第一幕 千里月明"),
    ("千织", "丝切铗之章 第一幕 当他们谈起今夜"),
    ("阿蕾奇诺", "净炼火之章 第一幕 炉火熄灭之际"),
    ("赛诺", "金狼之章 第二幕 守诺者"),
    ("克洛琳德", "迅捷剑之章 第一幕 夜色无声"),
    ("希格雯", "海精之章 第一幕 谎言的温度"),
    ("艾梅莉埃", "香氛瓶之章 第一幕 花债血偿"),
    ("悬木人", "尤潘基的回火 第一幕 维茨特兰的神秘访客"),
    ("悬木人", "尤潘基的回火 第二幕 英雄的仪式"),
    ("悬木人", "尤潘基的回火 第三幕 基尼奇的交易"),
    ("流泉之众", "流泉所归之处 第一幕 寻找神秘岛的人"),
    ("流泉之众", "流泉所归之处 第二幕 神秘岛的传说"),
    ("流泉之众", "流泉所归之处 第三幕 神秘岛之旅"),
    ("回声之子", "祈祝福愿，倾告嵴锋 第一幕 嵴锋的异响"),
    ("回声之子", "祈祝福愿，倾告嵴锋 第二幕 喑哑的回声"),
    ("回声之子", "祈祝福愿，倾告嵴锋 第三幕 抑扬的吟咏"),
    ("花羽会", "花之归尘，羽之将坠 第一幕 特拉洛坎的失翼者"),
    ("花羽会", "花之归尘，羽之将坠 第二幕 试炼前夜"),
    ("花羽会", "花之归尘，羽之将坠 第三幕 枪与翼"),
    ("烟谜主", "流淌着色彩的回忆 第一幕 来自烟谜主的使命"),
    ("烟谜主", "流淌着色彩的回忆 第二幕 传说中的「色彩」"),
    ("烟谜主", "流淌着色彩的回忆 第三幕 七彩之战的真相"),
    ("玛薇卡", "不败阳焰之章 第一幕 正如那烈日"),
    ("杜林", "赤龙之章 第一幕 名为故事的魔法"),
    ("梦见月", "貘枕之章 第一幕 食梦者的忧郁"),
    ("恰斯卡", "启喻鸟之章 第一幕 飞向归羽声"),
    ("希诺宁", "香糕塔之章 第一幕 珍上至珍")
]

files_in_src = os.listdir(src_dir)

def normalize(text):
    return re.sub(r'[\s，,·\._\-「」]', '', text)

not_found = []

for idx, (char_name, title) in enumerate(quests, start=1):
    num_str = f"{idx:03d}"
    norm_title = normalize(title)
    
    matched_file = None
    
    # 1. Exact normalize match
    for f_name in files_in_src:
        if not f_name.endswith(".txt"): continue
        if normalize(f_name[:-4]) == norm_title:
            matched_file = f_name
            break
            
    # 2. Contains match
    if not matched_file:
        for f_name in files_in_src:
            if not f_name.endswith(".txt"): continue
            if norm_title in normalize(f_name[:-4]):
                matched_file = f_name
                break
                
    # 3. Fuzzy match
    if not matched_file:
        best_ratio = 0
        best_file = None
        for f_name in files_in_src:
            if not f_name.endswith(".txt"): continue
            ratio = difflib.SequenceMatcher(None, norm_title, normalize(f_name[:-4])).ratio()
            if ratio > 0.8 and ratio > best_ratio:
                best_ratio = ratio
                best_file = f_name
        if best_file:
            matched_file = best_file

    if matched_file:
        src_path = os.path.join(src_dir, matched_file)
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        dst_path = os.path.join(dst_dir, f"{num_str} {char_name} {safe_title}.txt")
        shutil.copy2(src_path, dst_path)
        print(f"[{num_str}] Copied: {char_name} {safe_title}")
    else:
        print(f"[{num_str}] Not found: {char_name} {title}")
        not_found.append(f"{char_name} {title}")

print(f"\nCompleted: {len(quests) - len(not_found)}/{len(quests)}")
if not_found:
    print("Missed:", not_found)
