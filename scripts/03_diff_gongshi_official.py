# 03_diff_gongshi_official.py — 版本链账目复算(全 PASS 才退出)
# 校验三条硬账:
#   ① 1,636(公示稿) +6 新增 −3 移除 = 1,639(正式版),官方四口径全中
#   ② 正式版 --[3处批次移码+5处批次改名]--> +47批次新增 +1升职 = 1,687(现行库,码集逐一相等)
#   ③ data/gap_gongshi_to_official.csv(人工裁决) 与两侧数据集自洽
import csv, json, re, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

def load(p):
    return {r["careerCode"]: r["careerName"]
            for r in csv.DictReader(open(p, encoding="utf-8-sig"))}

gs = load("data/dadian2022_gongshi_1636.csv")
off = load("data/dadian2022_official_1639.csv")
cur = load("data/dadian2022_current_1687.csv")
batches = list(csv.DictReader(open("data/batches_new_occupations_47.csv", encoding="utf-8-sig")))
gap = list(csv.DictReader(open("data/gap_gongshi_to_official.csv", encoding="utf-8-sig")))

def flag(n):
    s = n.replace(" ", "").replace("、", "")
    m = re.search(r"(L/S|L|S)$", s)
    return m.group(1) if m else ""

def counts(d):
    fl = Counter(flag(n) for n in d.values())
    return (len(d), fl["L"] + fl["L/S"], fl["S"] + fl["L/S"], fl["L/S"])

# ① 公示稿→正式版
assert counts(gs) == (1636, 133, 97, 23), counts(gs)
assert counts(off) == (1639, 134, 97, 23), counts(off)
only_off = set(off) - set(gs)
only_gs = set(gs) - set(off)
print(f"① 公示稿{len(gs)} -> 正式版{len(off)} | 码集差: 正式版独有{len(only_off)}, 公示稿独有{len(only_gs)}, 净差 {len(only_off)-len(only_gs)} (应 3)")
assert len(only_off) - len(only_gs) == 3

# gap CSV 逐行自洽
for r in gap:
    t = r["changeType"]
    if t == "新增":
        assert r["codeAfter"] in off and r["nameAfter"] not in set(gs.values()), r
    elif t == "移除":
        assert r["codeBefore"] in gs and r["nameBefore"] not in set(off.values()), r
    elif t in ("移码", "批次移码", "升职"):
        if r["codeBefore"] and not r["codeBefore"].startswith("6-31"):
            assert r["codeBefore"] in gs, r
        assert r["codeAfter"] in off or r["codeAfter"] in cur, r
    elif t in ("改名", "批次改名"):
        assert r["codeBefore"] in gs and r["codeAfter"] in off, r
print("   gap_gongshi_to_official.csv 逐行与数据集自洽 ✓")

# ② 正式版→现行(正向施加批次变化后码集须逐一相等)
fwd = dict(off)
for old, new in [("2-02-32-00", "2-02-32-01"),   # 制药工程技术人员, 2024批
                 ("4-05-02-00", "4-05-02-01"),   # 证券期货服务师, 2024批
                 ("6-24-04-00", "6-24-04-01")]:  # 电池制造工, 2026批
    fwd[new] = fwd.pop(old)
for c, orig, cur_name in [("2-05-07-02", "口腔医学技师", "口腔修复技师"),
                          ("4-10-05-03", "婚姻家庭咨询师", "婚姻家庭辅导师"),
                          ("4-13-04-04", "研学旅行指导师", "研学旅游指导师"),
                          ("3-01-01-05", "劝募员", "劝募师"),
                          ("6-29-05-00", "古建筑工", "传统建筑工")]:
    fwd[c] = cur_name + fwd[c][len(orig):]
batch_codes = {r["careerCode"] for r in batches}
assert len(batch_codes) == 47, len(batch_codes)
fwd.update({r["careerCode"]: r["careerName"] for r in batches})
fwd["6-03-03-03"] = "烟机设备机械修理工"  # 烟机钳工上升为职业, 2025批, 不计入新增数
assert set(fwd) == set(cur), f"码集不一致: 多={set(fwd)-set(cur)} 少={set(cur)-set(fwd)}"
name_diff = [c for c in fwd if fwd[c] != cur[c]]
print(f"② 正式版+3移码+5改名+47新增+1升职 -> 现行{len(cur)} | 码集逐一相等 ✓ | 名称残留差异 {len(name_diff)} 处(标注空格级)")
assert len(name_diff) == 0 or all(re.sub(r"\s", "", fwd[c]) == re.sub(r"\s", "", cur[c]) for c in name_diff)

print("三条账目全部闭合,复算通过。")
