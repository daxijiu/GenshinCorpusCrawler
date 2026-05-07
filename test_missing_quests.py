import json
import urllib.request
from data_parse import parse_story_data

def test_quest(quest_id):
    url = f'https://gi.yatta.moe/api/v2/CHS/quest/{quest_id}?vh=55F1'
    print(f"Testing Quest {quest_id}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req).read().decode('utf-8')
        quest_json = json.loads(resp)
        result = parse_story_data(quest_json)
        print(f"Result: {result[:2]} (Text length: {len(result[2]) if result[2] else 'None'})")
    except Exception as e:
        print(f"Error: {e}")

test_quest(1101)
test_quest(1102)
