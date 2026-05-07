import json
import urllib.request
url = 'https://gi.yatta.moe/api/v2/CHS/quest?vh=55F1'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req).read().decode('utf-8')
data = json.loads(resp)['data']['items']

samples = []
for type_ in ['aq', 'lq', 'eq', 'wq', 'iq']:
    count = 0
    for k, v in data.items():
        if v.get('type') == type_:
            cnum = v.get('chapterNum')
            ctitle = v.get('chapterTitle')
            filename = f'{cnum} {ctitle}' if cnum else str(ctitle)
            samples.append({'type': type_, 'chapterNum': cnum, 'chapterTitle': ctitle, 'filename': filename})
            count += 1
            if count >= 3:
                break
for s in samples:
    print(f"[{s['type']}] chapterNum: '{s['chapterNum']}' | chapterTitle: '{s['chapterTitle']}' -> 预期文件名: '{s['filename']}.txt'")
