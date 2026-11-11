# 02_rebuild_official.py — 从现行库快照回滚重构《大典(2022年版)》正式版底库
# 输入: data/dadian2022_current_1687.csv (官方发布的现行职业数据整理快照)
#       sources/attachment_202*.pdf (三批官方附件,提供新增职业名单)
# 输出: data/dadian2022_official_1639.csv
# 验版: 1,639 职业 / 绿色L 134 / 数字S 97 / 双标 23 (官方四口径,2026-11-11 全中)
import csv, json, re, sys

sys.stdout.reconfigure(encoding="utf-8")
import pymupdf

BATCH_PDFS = [
    ("sources/attachment_2024_rensheTingFa2024-36.pdf",),
    ("sources/attachment_2025_rensheTingFa2025-26.pdf",),
    ("sources/attachment_2026_rensheTingFa2026-35.pdf",),
]

occ = {r["careerCode"]: r["careerName"]
       for r in csv.DictReader(open("data/dadian2022_current_1687.csv", encoding="utf-8-sig"))}

# 1) 扣除三批"新增职业"(47 个)
batch_new = {}
for (f,) in BATCH_PDFS:
    doc = pymupdf.open(f)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    seg = re.split(r"新增职业信息", text)[1]
    seg = re.split(r"新增工种信息", seg)[0]
    for m in re.finditer(r"（[一二三四五六七八九十]+）\s*(\d-\d{2}-\d{2}-\d{2})\s*\n?([^\n（]+)", seg):
        batch_new[m.group(1)] = m.group(2).strip()
for c in batch_new:
    occ.pop(c, None)
print("三批新增职业:", len(batch_new))

# 2) 扣除烟机钳工"上升为职业"(人社厅发〔2025〕26号,不计入新增职业数)
occ.pop("6-03-03-03", None)

# 3) 回退批次编码变更(附件调整变更原文:2024 批制药/证券期货,2026 批电池)
for old, new in [("2-02-32-00", "2-02-32-01"),
                 ("4-05-02-00", "4-05-02-01"),
                 ("6-24-04-00", "6-24-04-01")]:
    occ[old] = occ.pop(new)

# 4) 回退批次改名(附件调整变更原文),保留 L/S 标注后缀
RENAMES = {
    "2-05-07-02": ("口腔修复技师", "口腔医学技师"),
    "4-10-05-03": ("婚姻家庭辅导师", "婚姻家庭咨询师"),
    "4-13-04-04": ("研学旅游指导师", "研学旅行指导师"),
    "3-01-01-05": ("劝募师", "劝募员"),
    "6-29-05-00": ("传统建筑工", "古建筑工"),
}
for c, (cur, orig) in RENAMES.items():
    assert occ[c].rstrip("LS") == cur, (c, occ[c])
    occ[c] = orig + occ[c][len(cur):]

# 5) 验版:官方四口径
def flag(n):
    s = n.replace(" ", "").replace("、", "")
    m = re.search(r"(L/S|L|S)$", s)
    return m.group(1) if m else ""

from collections import Counter
fl = Counter(flag(n) for n in occ.values())
L, S, both = fl["L"] + fl["L/S"], fl["S"] + fl["L/S"], fl["L/S"]
print(f"重构结果: {len(occ)} 职业 | 绿色L {L} (官方134) | 数字S {S} (官方97) | 双标 {both} (官方23)")
assert len(occ) == 1639 and L == 134 and S == 97 and both == 23, "验版未通过,勿使用!"

with open("data/dadian2022_official_1639.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["careerCode", "careerName"])
    w.writerows(sorted(occ.items()))
json.dump(dict(sorted(occ.items())), open("data/dadian2022_official_1639.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("已写出 data/dadian2022_official_1639.csv / .json")
