"""Kiểm tra bộ kit: skill hợp lệ, file vai trò đủ, mẫu báo cáo đã có nội dung chính thức chưa."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLES = ["TL", "BE1", "BE2", "BE3", "FE", "QA"]
errors = 0
warnings = 0


def err(msg: str) -> None:
    global errors
    errors += 1
    print(f"[LỖI] {msg}")


def warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"[CẢNH BÁO] {msg}")


# 1. Skill
skills_dir = ROOT / ".agents" / "skills"
for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
    f = d / "SKILL.md"
    if not f.exists():
        err(f"{d.name}: thiếu SKILL.md")
        continue
    text = f.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        err(f"{d.name}: thiếu frontmatter")
        continue
    meta = {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in m.group(1).splitlines() if ":" in l)}
    if meta.get("name") != d.name:
        err(f"{d.name}: name '{meta.get('name')}' khác tên thư mục")
    if not meta.get("description"):
        err(f"{d.name}: thiếu description")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d.name):
        err(f"{d.name}: tên chỉ gồm chữ thường, số, gạch ngang")
    if text.count("\n") + 1 > 500:
        err(f"{d.name}: SKILL.md quá 500 dòng")
    print(f"[OK]  skill {d.name}")

# 2. Skill được nhắc trong AGENTS.md / role có tồn tại không
names = {p.name for p in skills_dir.iterdir() if p.is_dir()}
for f in [ROOT / "AGENTS.md", *(ROOT / "docs" / "roles").glob("*.md")]:
    for ref in re.findall(r"skill `([a-z0-9-]+)`", f.read_text(encoding="utf-8")):
        if ref not in names:
            err(f"{f.relative_to(ROOT)}: nhắc skill '{ref}' không tồn tại")

# 3. File vai trò
for r in ROLES:
    if not (ROOT / "docs" / "roles" / f"{r}.md").exists():
        err(f"thiếu docs/roles/{r}.md")

# 4. Mẫu báo cáo
for t in ["daily.md", "weekly-mau2.md", "monthly-mau3.md", "handover-8-hang-muc.md"]:
    p = ROOT / "docs" / "templates" / t
    if not p.exists():
        err(f"thiếu docs/templates/{t}")
    elif "⚠ CHƯA CÓ NỘI DUNG CHÍNH THỨC" in p.read_text(encoding="utf-8"):
        warn(f"docs/templates/{t} chưa có nội dung chính thức (TL cần dán mẫu)")

# 5. Quyết định còn chờ
dec = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
pending = len(re.findall(r"\|\s*(ĐỀ XUẤT|CHỜ TL)\s*\|", dec))
if pending:
    warn(f"docs/DECISIONS.md còn {pending} mục chưa chốt")

print(f"\n{errors} lỗi, {warnings} cảnh báo.")
sys.exit(1 if errors else 0)
