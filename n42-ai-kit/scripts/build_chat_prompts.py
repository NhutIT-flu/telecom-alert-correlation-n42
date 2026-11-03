"""Sinh file dán cho ChatGPT/Gemini/Claude Project từ AGENTS.md + docs/roles/<VAI>.md.

Chạy:  python scripts/build_chat_prompts.py
Kết quả: dist/chat/skill-<VAI>.md  (kèm số ký tự để so với giới hạn của công cụ)
Chỉ sửa AGENTS.md và docs/roles/*.md, đừng sửa file trong dist/.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "chat"
ROLES = ["TL", "BE1", "BE2", "BE3", "FE", "QA"]
LIMIT_PAID = 5000   # ChatGPT Custom Instructions, gói trả phí
LIMIT_FREE = 1500   # ChatGPT Custom Instructions, gói Free/Go


def strip_agent_only(text: str) -> str:
    return re.sub(r"<!-- chat-omit-start -->.*?<!-- chat-omit-end -->\n?", "", text, flags=re.S).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    shared = strip_agent_only((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    shared = shared.replace("# AGENTS.md — Đề tài N4.2 (HKDN UTH × VNPT NET)", "## BỐI CẢNH VÀ QUY ĐỊNH CHUNG — ĐỀ TÀI N4.2 (HKDN UTH × VNPT NET)")
    print(f"{'File':<22}{'Ký tự':>8}   Ghi chú")
    for r in ROLES:
        role = (ROOT / "docs" / "roles" / f"{r}.md").read_text(encoding="utf-8").strip()
        body = (
            f"# CHỈ DỊNH CỐ ĐỊNH CHO AI — TÔI LÀ {r}, ĐỀ TÀI N4.2\n\n"
            f"{shared}\n\n{role}\n\n"
            "Xác nhận đã hiểu, rồi hỏi tôi hôm nay cần làm việc gì.\n"
        )
        path = OUT / f"skill-{r}.md"
        path.write_text(body, encoding="utf-8")
        n = len(body)
        note = "vừa gói trả phí" if n <= LIMIT_PAID else f"VƯỢT {n - LIMIT_PAID} ký tự so với 5.000"
        if n > LIMIT_FREE:
            note += "; vượt 1.500 của gói Free/Go"
        print(f"{path.name:<22}{n:>8}   {note}")


if __name__ == "__main__":
    main()
