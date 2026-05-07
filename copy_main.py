import os
import shutil
import re
import difflib

md_path = r"e:\Projects\GenshinCorpusCrawler\目录.md"
src_dir = r"e:\Projects\GenshinCorpusCrawler\data\story"
dst_dir = r"e:\Projects\GenshinCorpusCrawler\主线"

os.makedirs(dst_dir, exist_ok=True)

with open(md_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

chapters = []
for line in lines:
    line = line.strip()
    match = re.match(r"^(\d{2})\s+(.+)$", line)
    if match:
        chapters.append((match.group(1), match.group(2)))

files_in_src = os.listdir(src_dir)

def normalize(text):
    return re.sub(r'[\s，,·\._\-]', '', text)

not_found = []

for num, title in chapters:
    norm_title = normalize(title)
    
    matched_file = None
    
    # 1. Exact normalize match
    for f_name in files_in_src:
        if not f_name.endswith(".txt"): continue
        if normalize(f_name[:-4]) == norm_title:
            matched_file = f_name
            break
            
    # 2. Contains match if not found exactly
    if not matched_file:
        for f_name in files_in_src:
            if not f_name.endswith(".txt"): continue
            if norm_title in normalize(f_name[:-4]):
                matched_file = f_name
                break
                
    # 3. Fuzzy match for typos (e.g. 凄灭 vs 湮灭)
    if not matched_file:
        best_ratio = 0
        best_file = None
        for f_name in files_in_src:
            if not f_name.endswith(".txt"): continue
            ratio = difflib.SequenceMatcher(None, norm_title, normalize(f_name[:-4])).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_file = f_name
        if best_ratio > 0.8:
            matched_file = best_file

    if matched_file:
        src_path = os.path.join(src_dir, matched_file)
        # title might contain some invalid characters for Windows paths if we are not careful, but looks ok
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
        dst_path = os.path.join(dst_dir, f"{num} {safe_title}.txt")
        shutil.copy2(src_path, dst_path)
        print(f"[{num}] Copied: {safe_title}  <--  {matched_file.strip()}")
    else:
        print(f"[{num}] Not found: {title}")
        not_found.append(title)

print("\n--- Summary ---")
print(f"Total matched: {len(chapters) - len(not_found)} / {len(chapters)}")
if not_found:
    print("Failed to find:")
    for nf in not_found:
        print("  " + nf)
