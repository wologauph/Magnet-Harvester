import os
import glob
import re
import shutil
import ctypes

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
archive_dir = os.path.join(desktop, "已合并磁力归档")

output_filename = "汇总的所有磁力链接.txt"
output_path = os.path.join(desktop, output_filename)

ed2k_pattern = re.compile(r"ed2k://\|file\|.+?\|\d+\|[a-fA-F0-9]{32}\|.*?(?:\|/|/|\||$)", re.IGNORECASE)
magnet_pattern = re.compile(r"magnet:\?xt=urn:[a-zA-Z0-9:]+.*?(?=[\s\u4e00-\u9fa5\"'\r\n]|$)", re.IGNORECASE)

# 1. 绝不跳过任何文件：同时扫描【桌面上所有txt（包括现有汇总文本）】与【归档里的历史txt】
scan_files = []

# (A) 归档目录里的所有文本
if os.path.exists(archive_dir):
    scan_files.extend(glob.glob(os.path.join(archive_dir, "*.txt")))

# (B) 桌面上的所有文本（包括旧汇总文件《汇总的所有磁力链接.txt》）
scan_files.extend(glob.glob(os.path.join(desktop, "*.txt")))

seen_links = set()
all_blocks = []

for file_path in scan_files:
    basename = os.path.basename(file_path)
    # 避开错误报告文件，其余所有 txt（包括现有的汇总文本）全部深度读取！
    if basename == "格式异常的链接报告.txt":
        continue

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        continue

    current_title = ""

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        lower = line_str.lower()
        if 'ed2k' not in lower and 'magnet' not in lower:
            # 记录可能的标题/描述（跳过分隔线和汇总头）
            if not line_str.startswith("===") and not line_str.startswith("【银月"):
                if line_str.startswith("#") or line_str.startswith("【") or line_str.startswith("---") or len(line_str) < 200:
                    current_title = line_str
        else:
            found_ed2k = ed2k_pattern.findall(line_str)
            found_mag = magnet_pattern.findall(line_str)
            found_links = found_ed2k + found_mag

            if found_links:
                for lk in found_links:
                    lk_clean = lk.strip()
                    if lk_clean not in seen_links:
                        seen_links.add(lk_clean)
                        all_blocks.append((current_title, lk_clean))
                        current_title = ""

# 2. 安全覆盖写入最新的全量汇总文件
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(f"【银月磁力全量汇总库】全量重置更新 (共收录 {len(all_blocks)} 条无损去重资源)\n")
    f.write("=" * 60 + "\n\n")

    for title, link in all_blocks:
        if title:
            f.write(f"{title}\n")
        f.write(f"{link}\n\n")

# 3. 将桌面上的新 txt 移动至归档文件夹（跳过汇总文件自身）
desktop_txts = glob.glob(os.path.join(desktop, "*.txt"))
os.makedirs(archive_dir, exist_ok=True)
archived_count = 0

for file_path in desktop_txts:
    basename = os.path.basename(file_path)
    if basename == output_filename or basename.startswith("汇总的所有磁力链接") or basename == "格式异常的链接报告.txt":
        continue
    try:
        dest = os.path.join(archive_dir, basename)
        shutil.move(file_path, dest)
        archived_count += 1
    except Exception:
        pass

# 4. 刷新桌面通知
try:
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
except Exception:
    pass

msg = f"全量无损重置更新完成！\n\n- 包含【已有汇总 + 桌面新文本 + 历史归档】\n- 当前全量去重资源库：{len(all_blocks)} 条\n- 已安全写入：《{output_filename}》\n- 归档桌面新文本：{archived_count} 个"
ctypes.windll.user32.MessageBoxW(0, msg, "银月磁力神器", 0x40 | 0x0)
