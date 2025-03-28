# -*- coding:utf-8 -*-
# @FileName  :data_parse.py
# @Time      :2025/3/26 11:10
# @Author    :ZMFY
# Description:

import json
import re
import traceback
from typing import List

from utils import number_lowercase_to_uppercase


# def remove_color_tags(text):
#     return re.sub(r'<color=#[0-9A-Fa-f]{6,8}>|</color>', '', text)


def post_precess_text(text):
    # 去除颜色标签
    text = re.sub(r'<color=#[0-9A-Fa-f]{6,8}>|</color>', '', text)
    # 取出 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去掉花括号及其中的内容
    text = re.sub(r'{[^}]*}', '', text)
    # 使用正则表达式去掉特殊字符 #$%&@
    text = re.sub(r'[#$%&@]', '', text)
    # 将被转义的换行符还原
    text = text.replace('\\n', '\n')
    # 去掉可能留下的多余空格
    text = text.strip()

    return text


def contains_hidden_substring(input_string):
    # 定义要搜索的模式
    pattern = r'\$HIDDEN'
    # 使用re.search来查找模式
    match = re.search(pattern, input_string)
    return match is not None


def replace_character_name(text, olds: List[str], news: str):
    """
    将剧情文本中的角色名替换为合适的名字
    :param text: 剧情文本
    :param olds: 剧情文本中的角色名
    :param news: 用于替换的名字
    :return:
    """
    if not olds or not text:
        return text

    # 预处理优化：去重+长度排序+转义
    unique_olds = {old.strip() for old in olds if old.strip()}
    if not unique_olds:
        return text

    # 按长度降序排列（避免短词优先匹配问题）
    sorted_olds = sorted(unique_olds, key=lambda x: -len(x))

    # 预编译正则表达式（关键性能优化）
    pattern = re.compile(
        r'\b(?:{})\b'.format('|'.join(map(re.escape, sorted_olds))),
        flags=re.UNICODE
    )

    return pattern.sub(news, text)


def process_source(data, item_name):
    """
    处理每个 Item 的来源， 适用于有 source 字段的 Item
    :param data:
    :param item_name:
    :return:
    """
    if (source_data := data.get('source', [])) is not None:
        sources = [v["name"] for v in source_data]
        source_text = f"「{item_name}」来源: " + ', '.join(sources) if sources else ""
        return source_text
    else:
        return ""


def parse_story_data(story_json):
    """
    解析 story 的JSON 并生成结构化文本
    :param story_json: json 体
    :return: ChapterNum, ChapterTitle, text
    """

    def process_task_data(task_data):
        """处理单个任务数据块"""
        lines = []
        for task_id, task_item in sorted(task_data.get('items', {}).items(), key=lambda x: x[0]):
            # 提取角色和所有对话文本
            if "player" in task_id:
                # 跳过类似 "3071107-player" 的键值对
                continue
            role = task_item.get('role', '未知角色')
            texts = [t.get('text', '') for t in task_item.get('text', [])]
            for text in texts:
                if text:  # 过滤空文本
                    # # 滤除颜色标签
                    # text = remove_color_tags(text)
                    lines.append(f"{role}: {text}")
        return lines

    def process_scene(scene_data):
        """处理单个场景"""
        output = []
        if scene_data.get('taskData', None) is None:
            # 只有当存在对话剧情时才添加到结果
            return output

        # 场景标题
        scene_title = scene_data.get('title', '未命名场景')

        if scene_title is not None and not contains_hidden_substring(scene_title):
            # 如果标题中带有 $HIDDEN 则跳过该标题
            output.append(f"\n\n{scene_title}")

        # 处理任务数据
        assert len(scene_data.get('tasks', [1])) == 1
        task_lines = process_task_data(scene_data['taskData'][0])
        output.extend(task_lines)
        return output

    def process_act(act_data):
        """处理单个章节"""
        output = []
        # Act信息
        act_info = act_data.get('info', {})
        act_title = act_info.get('title', '未命名章节')
        act_desc = act_info.get('description', '')
        output.append(f"\n\n{act_title}\n{act_desc}")

        # 处理所有场景
        for scene_key in sorted(act_data.get('story', {}).keys(), key=int):
            scene_data = act_data['story'][scene_key]
            output.extend(process_scene(scene_data))
        return output

    try:
        # 基础信息
        base_info = story_json.get('data', {}).get('info', {})
        chapter_num = base_info.get('chapterNum', '未知章节')
        chapter_title = base_info.get('chapterTitle', '未命名章节')

        # 主数据结构
        main_data = story_json.get('data', {})
        story_list = main_data.get('storyList', {})

        # 生成文本
        result = [f"{chapter_num} {chapter_title}"]

        # 按Act顺序处理（排序保证0,1,2...）
        for act_key in sorted(story_list.keys(), key=int):
            act_data = story_list[act_key]
            result.extend(process_act(act_data))

        parsed_text = '\n'.join(result).replace('\n\n', '\n')  # 清理多余空行
        parsed_text = post_precess_text(parsed_text)
        parsed_text = replace_character_name(parsed_text, ['Traveler', "玩家"], news="旅行者(空)")

        return chapter_num, chapter_title, parsed_text

    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        traceback.print_exc()
        return None, None, None


def parse_weapon_data(weapon_json, exclude_story=False, item_zh_name="武器"):
    """
    解析武器的 Json, 这个函数仅解析武器的描述和故事，即文本内容，不包含词条属性
    :param weapon_json: Json 体
    :param exclude_story: bool, 是否排除武器的故事，星铁的光锥故事意义不大，设置为True
    :param item_zh_name
    :return: weapon_name, text
    """

    def replace_pronoun_with_name(text, type_abbr, name):
        # 构造正则表达式，匹配以这或此开头，后面跟一个可选的中文字符作为量词，然后是类型简称
        pattern = re.compile(r'([这此])([\u4e00-\u9fa5]?)' + re.escape(type_abbr))
        # 替换为指示代词 + 量词（如果有） + 给定的名称
        return pattern.sub(r'\1\2' + name, text)

    try:
        weapon_data = weapon_json.get('data', {})
        weapon_name = weapon_data.get('name', f'未命名{item_zh_name}')
        weapon_type = weapon_data.get("type", "未知类型")
        weapon_description = weapon_data.get('description', '暂无描述')
        weapon_story = weapon_data.get("story", "暂无故事")

        # 将故事中的指代词全部替换为武器的名字，保证指代正确
        if not exclude_story:
            type_abbr = weapon_type[-1]  # 取最后一个字
            weapon_story = replace_pronoun_with_name(weapon_story, type_abbr, weapon_name)

        if not exclude_story:
            output_text = f"{weapon_name} - {weapon_type}\n{weapon_description}\n{weapon_story}\n"
        else:
            output_text = f"{weapon_name} - {weapon_type}\n{weapon_description}\n"
        return weapon_name, post_precess_text(output_text)

    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        return None, None


def parse_monster_data(monster_json):
    """
    解析怪物的 Json， 只解析怪物的文本内容，不包含词条属性
    :param monster_json:
    :return: Monster name, text
    """
    try:
        monster_data = monster_json.get('data', {})
        monster_name = monster_data.get("name", "未知怪物")
        monster_desc = monster_data.get("description", "")
        monster_type = monster_data.get("type", "其它生物")
        tip_data = monster_data.get("tips", {})
        monster_tips = [tip_data[key]["description"] for key in tip_data.keys()] if tip_data is not None else []
        entries = monster_data.get('entries', {})
        rewards = set()

        # 收集击杀奖励
        for key, value in entries.items():
            if isinstance(value, dict) and "reward" in value.keys() and value["reward"] is not None:
                for reward, item in value.get("reward", {}).items():
                    rewards.add(item['name'])
        reward_text = f"击杀「{monster_name}」奖励:" + ', '.join(rewards) if len(rewards) > 0 else ""
        text = f"{monster_name} - {monster_type}\n{monster_desc}\n" + '\n'.join(monster_tips) + '\n' + reward_text

        return monster_name, post_precess_text(text)
    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        return None, None


def parse_material_data(material_json):
    """
    解析材料 JSON， 包含材料的名称、描述、类型、故事（如有）、来源、被需求
    :param material_json:
    :return:
    """

    def process_dropped_by(additional_data, material_name):
        if (dropped_data := additional_data.get('droppedBy', [])) is not None:
            dropped_by = [v['name'] for v in dropped_data]
            dropped_text = f"掉落「{material_name}」的怪物: " + ', '.join(dropped_by) if dropped_by is not None else ""
            return dropped_text
        else:
            return ""

    def process_recipe(material_data, material_name):
        if (recipe_data := material_data.get('recipe', None)) is not None:
            recipe_materials = set()
            for key, val in recipe_data.items():
                txt = ""
                for idx, item in enumerate(val.values()):
                    if idx != 0:
                        txt += " + "
                    txt += f"{item['name']}×{item['count']}"
                recipe_materials.add(txt)

            return f"可通过以下材料换取「{material_name}」: " + ', '.join(
                recipe_materials) if recipe_data is not None else ""
        else:
            return ""

    def process_required_by(additional_data, material_name):
        if (required_data := additional_data.get('requiredBy', {})) is not None:
            required_avatars = set()
            required_weapons = set()
            if "avatar" in required_data.keys():
                required_avatars.update([v['name'] for v in required_data.get('avatar', [])])
            if "weapon" in required_data.keys():
                required_weapons.update([v['name'] for v in required_data.get('weapon', [])])

            required_avatar_text = f"需求「{material_name}」的角色：" + ', '.join(required_avatars) \
                if required_avatars else ""
            required_weapon_text = f"需求「{material_name}」的武器: " + ', '.join(required_weapons) \
                if required_weapons else ""
            return required_avatar_text + '\n' + required_weapon_text
        else:
            return ""

    try:
        material_data = material_json.get('data', {})
        material_name = material_data.get("name", "未知材料")
        material_desc = material_data.get("description", "")
        material_type = material_data.get("type", "未知类型")
        source_text = process_source(material_data, material_name)
        additions_data = material_data.get('additions', {})
        dropped_text = process_dropped_by(additions_data, material_name)
        required_text = process_required_by(additions_data, material_name)
        recipe_text = process_recipe(material_data, material_name)
        output_text = (f"{material_name} - {material_type}\n{material_desc}\n\n{source_text}\n"
                       f"{recipe_text}\n{dropped_text}\n{required_text}")

        return material_name, post_precess_text(output_text)
    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        traceback.print_exc()
        return None, None


def parse_character_data(character_json, weapon_types: dict):
    """解析角色的文本内容"""

    def process_fetter(fetter_data):
        character_title = fetter_data.get('title', '')
        character_detail = fetter_data.get('detail', '')
        character_constellation = fetter_data.get('constellation', '')
        character_native = fetter_data.get('native', '')
        cvs = fetter_data.get('cv', {})
        character_zh_cv = cvs.get('CHS', '未知中文CV')
        character_en_cv = cvs.get('EN', "未知英文CV")

        title_text = f"称号: {character_title}\n" if character_title is not None else ""
        constellation_text = f"命之座: {character_constellation}\n" if character_constellation is not None else ""
        native_text = f"所属: {character_native}\n" if character_native is not None else ""
        detail_text = f"描述: {character_detail}\n" if character_detail is not None else ""
        zh_cv_text = f"中文CV: {character_zh_cv}\n" if character_zh_cv is not None else ""
        en_cv_text = f"英文CV: {character_en_cv}\n" if character_en_cv is not None else ""
        fetter_text = title_text + constellation_text + native_text + detail_text + zh_cv_text + en_cv_text
        return fetter_text

    def process_birthday(birthday_data):
        if not birthday_data:
            return ""
        month, day = birthday_data
        return f"生日: {month}月{day}日\n"

    def process_story(story_data: dict):
        story = ""
        for k, v in story_data.items():
            if v['text'] != '暂未开放':
                story += f"{v['title']}:\n {v['text']}\n\n"
        return story

    try:
        character_data = character_json.get('data', {})
        character_name = character_data.get('name', '')
        character_rank = character_data.get('rank', '')  # 星级
        weapon_type = character_data.get("weaponType", "WEAPON_SWORD_ONE_HAND")
        character_weapon = weapon_types[weapon_type]
        character_desc_text = f"{number_lowercase_to_uppercase(character_rank)}星{character_weapon}角色"

        # character_route = character_data.get('route', '')   # 英文名
        # character_sex = character_data.get("bodyType", "BOY")
        fetter_text = process_fetter(character_data.get('fetter', {}))
        birthday_text = process_birthday(character_data.get('birthday', None))

        character_story = process_story(character_data.get('story', {}))

        output_text = f"{character_name} - {character_desc_text}\n{birthday_text}\n{fetter_text}\n\n{character_story}"
        return character_name, post_precess_text(output_text)
    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        traceback.print_exc()
        return None, None


def parse_food_data(food_json):
    def process_effect(effect_data, name):
        if not effect_data:
            return ""
        effect_text = f"「{name}」效果: "
        for k, v in effect_data.items():
            effect_text += v
        return effect_text + '\n'

    def process_input_materials(input_data, name):
        if not input_data:
            return ""
        text = f"「{name}」制作所需材料: "
        materials = [f"{v['name']}×{v['count']}" for v in input_data.values()]
        return text + " + ".join(materials) + '\n' if materials else ""
    try:
        food_data = food_json.get('data', {})
        food_name = food_data.get("name", "")
        food_rank = food_data.get("rank", "")
        food_desc = food_data.get("description", "")
        food_type = food_data.get("type", "")
        rank_text = f"{number_lowercase_to_uppercase(food_rank)}星{food_type}"

        recipe_data = food_data.get("recipe", None)
        if recipe_data:
            effect_text = process_effect(recipe_data.get('effect', None), food_name)
            material_text = process_input_materials(recipe_data.get('input', None), food_name)
        else:
            effect_text, material_text = "", ""
        source_text = process_source(food_data, food_name)

        output_text = (f"{food_name} - {rank_text}\n"
                       f"{food_desc}\n{source_text}\n{effect_text}{material_text}")
        return food_name, post_precess_text(output_text)

    except Exception as e:
        print(f"❌ 解析异常: {str(e)}")
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    weapon_types = {
        "WEAPON_SWORD_ONE_HAND": "单手剑",
        "WEAPON_CATALYST": "法器",
        "WEAPON_CLAYMORE": "双手剑",
        "WEAPON_BOW": "弓",
        "WEAPON_POLE": "长柄武器"
    }
    with open('data/test_food.json', 'r', encoding='utf-8') as f:
        sample_json = json.load(f)
    # 生成文本
    name, text = parse_food_data(sample_json)
    print("✅ 生成结果：\n" + text)
