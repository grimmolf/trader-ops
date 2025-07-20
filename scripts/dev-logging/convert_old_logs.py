"""Convert legacy JSON development logs into entries in docs/CLAUDE_DEVELOPMENT_LOG.md

How to run:
    poetry run python scripts/dev-logging/convert_old_logs.py   # or your venv python

The script:
1. Scans docs/development-logs/ for *.json files
2. For each file, extracts key fields and renders a markdown block
3. Appends (oldest first) to docs/CLAUDE_DEVELOPMENT_LOG.md **after** the placeholder line
4. Leaves the original JSON files untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]  # project root
DEV_LOGS_DIR = ROOT / "docs" / "development-logs"
TARGET_MD = ROOT / "docs" / "CLAUDE_DEVELOPMENT_LOG.md"

ENTRY_TEMPLATE = """### [{date} {time}] - [{branch}] - [{title}]
**Context:** {context}
**Changes:** {changes}
**Validation:** _Imported from legacy JSON log_ 

---
"""

def render_entry(data: dict[str, object]) -> str:
    # Support multiple schema variants
    meta = data.get("session_metadata") or data.get("session_info") or {}
    exec_sum = (
        data.get("executive_summary")
        or data.get("implementation_summary")
        or data.get("summary")
        or {}
    )
    # Extract date and time, possibly from ISO timestamp
    date = meta.get("date")
    time = meta.get("time")
    if not date and (ts := meta.get("timestamp")):
        try:
            if "T" in ts:
                date_part, time_part = ts.split("T")
                date = date_part
                time = time_part.split(".")[0]
            elif "_" in ts and len(ts) >= 15:
                # Expect format YYYYMMDD_HHMMSS
                date = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
                time = f"{ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
        except ValueError:
            pass
    date = date or "????-??-??"
    time = time or ""

    branch = meta.get("branch") or meta.get("git_branch") or "unknown-branch"
    commit = (meta.get("commit") or meta.get("commit_hash") or "")[:7]

    title = (
        exec_sum.get("achievement")
        or exec_sum.get("title")
        or meta.get("development_focus")
        or meta.get("type")
        or commit
    )

    context_lines = (
        exec_sum.get("impact")
        or exec_sum.get("description")
        or exec_sum.get("production_readiness")
        or "Imported log"
    )

    raw_achievements = (
        data.get("key_achievements")
        or exec_sum.get("key_achievements")
        or []
    )
    flattened: list[str] = []
    for item in raw_achievements:
        if isinstance(item, str):
            flattened.append(item)
        elif isinstance(item, dict):
            items = item.get("items") or item.get("achievements") or []
            if isinstance(items, list):
                flattened.extend([str(x) for x in items])
    changes = "\n- " + "\n- ".join(flattened) if flattened else "Imported from JSON metrics"

    return ENTRY_TEMPLATE.format(date=date, time=time, branch=branch, title=title, context=context_lines, changes=changes)

def main() -> None:
    if not DEV_LOGS_DIR.exists():
        print("Legacy dev-log directory not found; nothing to convert.")
        return

    json_files = sorted(DEV_LOGS_DIR.glob("*.json"))
    if not json_files:
        print("No JSON dev logs found; nothing to convert.")
        return

    entries = []
    seen_ids: set[str] = set()
    for jf in json_files:
        try:
            data = json.loads(jf.read_text())
            session_id = (data.get("session_metadata") or data.get("session_info") or {}).get("session_id")
            if session_id and session_id in seen_ids:
                continue
            rendered = render_entry(data)
            # Skip if rendered entry lacks title (empty brackets)
            if "- []" in rendered:
                continue
            entries.append(rendered)
            if session_id:
                seen_ids.add(session_id)
        except Exception as e:
            print(f"⚠️  Skipping {jf.name}: {e}")

    # Remove everything after the placeholder line to avoid duplicates
    existing = TARGET_MD.read_text().split("---", 1)[0].rstrip() + "\n---\n"
    TARGET_MD.write_text(existing + "\n".join(entries) + "\n")
    print(f"✅ Imported {len(entries)} legacy logs into {TARGET_MD.relative_to(ROOT)}")

if __name__ == "__main__":
    main() 