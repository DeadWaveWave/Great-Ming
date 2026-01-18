#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


STORE_DIRNAME = ".great-ming"
STATE_FILENAME = "state.json"
ARCHIVE_FILENAME = "archives.ndjson"
CASES_DIRNAME = "cases"
TODO_FILENAME = "todo.md"
INSTALLED_SCRIPT_NAME = "mingctl.py"

FORMALITY_VALUES = ("full_ceremonial", "balanced", "pragmatic")
DEPARTMENTS = ("works", "war", "rites", "justice", "personnel", "revenue")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def eprint(*args: Any) -> None:
    print(*args, file=sys.stderr)


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)


def slugify(text: str, *, fallback: str = "case") -> str:
    ascii_text = text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    ascii_text = ascii_text.strip("-")
    return ascii_text or fallback


def find_project_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in [start, *start.parents]:
        if (candidate / STORE_DIRNAME).exists():
            return candidate
        if (candidate / ".git").exists():
            return candidate
    return start


def infer_root_from_script_path() -> Optional[Path]:
    """
    If this script is running from <project>/.great-ming/mingctl.py, prefer <project>
    regardless of current working directory.
    """

    script_path = Path(__file__).resolve()
    if script_path.parent.name == STORE_DIRNAME:
        return script_path.parent.parent
    return None


def get_root(explicit_root: Optional[str]) -> Path:
    env_root = os.environ.get("MING_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()
    inferred = infer_root_from_script_path()
    if inferred:
        return inferred
    return find_project_root(Path.cwd())


def store_dir(root: Path) -> Path:
    return root / STORE_DIRNAME


def state_path(root: Path) -> Path:
    return store_dir(root) / STATE_FILENAME


def archive_path(root: Path) -> Path:
    return store_dir(root) / ARCHIVE_FILENAME


def cases_dir(root: Path) -> Path:
    return store_dir(root) / CASES_DIRNAME


def todo_path(root: Path) -> Path:
    return store_dir(root) / TODO_FILENAME


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(dump_json(data) + "\n", encoding="utf-8")


def append_ndjson(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def ensure_store(root: Path) -> None:
    store_dir(root).mkdir(parents=True, exist_ok=True)
    cases_dir(root).mkdir(parents=True, exist_ok=True)

    if not state_path(root).exists():
        write_json(
            state_path(root),
            {"version": 1, "formality": "balanced", "current_case_id": None},
        )

    archive_path(root).touch(exist_ok=True)

    if not todo_path(root).exists():
        todo_path(root).write_text("# 邸报（Great Ming）\n\n## 在办\n\n", encoding="utf-8")


def load_state(root: Path) -> dict[str, Any]:
    ensure_store(root)
    state = read_json(state_path(root))
    if state.get("version") != 1:
        raise SystemExit(f"Unsupported state version: {state.get('version')}")
    if state.get("formality") not in FORMALITY_VALUES:
        state["formality"] = "balanced"
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    ensure_store(root)
    write_json(state_path(root), state)


def record_event(root: Path, event_type: str, data: dict[str, Any], *, case_id: Optional[str]) -> None:
    ensure_store(root)
    append_ndjson(
        archive_path(root),
        {"ts": now_iso(), "type": event_type, "case": case_id, "data": data},
    )


def load_case(root: Path, case_id: str) -> dict[str, Any]:
    path = cases_dir(root) / f"{case_id}.json"
    if not path.exists():
        raise SystemExit(f"Case not found: {case_id}")
    return read_json(path)


def save_case(root: Path, case: dict[str, Any]) -> None:
    path = cases_dir(root) / f"{case['id']}.json"
    write_json(path, case)


def update_todo(root: Path, *, case_id: str, title: str, done: bool) -> None:
    ensure_store(root)
    line_open = f"- [ ] {case_id} {title}\n"
    line_done = f"- [x] {case_id} {title}\n"
    todo = todo_path(root).read_text(encoding="utf-8").splitlines(keepends=True)
    found = False
    for i, line in enumerate(todo):
        if line.startswith(f"- [ ] {case_id} ") or line.startswith(f"- [x] {case_id} "):
            todo[i] = line_done if done else line_open
            found = True
            break
    if not found and not done:
        todo.append(line_open)
    todo_path(root).write_text("".join(todo), encoding="utf-8")


def new_case_id(title: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = slugify(title)[:32]
    return f"{ts}-{slug}"


def cmd_install(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    ensure_store(root)

    src = Path(__file__).resolve()
    dst = store_dir(root) / INSTALLED_SCRIPT_NAME
    if dst.exists() and not args.force:
        eprint(f"[SKIP] Already installed: {dst}")
    else:
        shutil.copyfile(src, dst)
        eprint(f"[OK] Installed: {dst}")

    record_event(
        root,
        "install",
        {"installed_script": str(dst), "source": str(src)},
        case_id=None,
    )
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    ensure_store(root)
    record_event(root, "init", {"store": str(store_dir(root))}, case_id=None)
    if args.json:
        print(dump_json({"ok": True, "root": str(root), "store": str(store_dir(root))}))
    else:
        print(f"[OK] Initialized {store_dir(root)}")
    return 0


def parse_route(text: str, *, default_formality: str) -> dict[str, Any]:
    lowered = text.lower()

    urgent_keywords = [
        "紧急",
        "加急",
        "生产",
        "线上",
        "全站",
        "宕机",
        "回滚",
        "泄露",
        "数据丢",
        "outage",
        "production",
        "prod",
        "down",
        "rollback",
        "incident",
        "breach",
    ]
    is_urgent = any(k in lowered for k in urgent_keywords)

    ceremonial_keywords = ["全礼", "依礼", "题本", "奏本", "朱批", "票拟"]
    pragmatic_keywords = ["免礼", "简奏", "用人话", "直说"]

    if any(k in text for k in pragmatic_keywords):
        formality = "pragmatic"
    elif any(k in text for k in ceremonial_keywords):
        formality = "full_ceremonial"
    elif is_urgent:
        formality = "pragmatic"
    else:
        formality = default_formality

    doc = "tiben"
    if is_urgent:
        doc = "zoubeng"
    else:
        impeachment_keywords = [
            "review",
            "debug",
            "报错",
            "错误",
            "exception",
            "trace",
            "stack",
            "性能",
            "慢",
            "漏洞",
            "security",
            "xss",
            "sql注入",
            "注入",
            "cve",
        ]
        status_keywords = ["进度", "状态", "结果", "跑完", "done", "status"]
        if any(k in lowered for k in impeachment_keywords) or any(k in text for k in impeachment_keywords):
            doc = "danzhang"
        elif any(k in lowered for k in status_keywords) or any(k in text for k in status_keywords):
            doc = "jietie"

    ministries: set[str] = set()
    if re.search(r"\b(git|commit|push|branch|blame|log)\b", lowered) or any(
        k in text for k in ["提交", "分支", "谁写的", "作者", "责任", "黄册", "吏部"]
    ):
        ministries.add("personnel")

    if re.search(r"\b(test|tests|build|run|start|deploy|ci|docker)\b", lowered) or any(
        k in text for k in ["测试", "运行", "构建", "部署", "上线", "跑一下"]
    ):
        ministries.add("war")

    if re.search(r"\b(lint|format|prettier|eslint|ruff|black|typecheck|mypy|tsc)\b", lowered) or any(
        k in text for k in ["格式化", "规范", "礼部", "校勘"]
    ):
        ministries.add("rites")

    if re.search(r"\b(log|logs|trace|stack|debug)\b", lowered) or any(
        k in text for k in ["日志", "堆栈", "追凶", "复现", "刑部", "报错", "错误"]
    ):
        ministries.add("justice")

    if re.search(r"\b(write|implement|refactor|fix)\b", lowered) or any(
        k in text for k in ["写代码", "实现", "重构", "修复", "修改", "改代码", "新增", "工部"]
    ):
        ministries.add("works")

    if re.search(r"\b(memory|disk|deps|dependency|dependencies|quota|cost)\b", lowered) or any(
        k in text for k in ["内存", "磁盘", "依赖", "占用", "配额", "成本", "户部"]
    ):
        ministries.add("revenue")

    if is_urgent:
        ministries.update({"war", "justice"})

    if not ministries:
        ministries.add("works")

    mutating_keywords = [
        "删除",
        "重写历史",
        "回滚",
        "push",
        "deploy",
        "上线",
        "发布",
        "commit",
        "安装",
        "install",
        "upgrade",
        "rm ",
        "reset",
        "rebase",
    ]
    needs_rescript = any(k in lowered for k in mutating_keywords) or any(k in text for k in mutating_keywords)
    if doc == "jietie":
        needs_rescript = False

    return {
        "input": text,
        "urgency": "urgent" if is_urgent else "normal",
        "document": doc,
        "formality": formality,
        "ministries": sorted(ministries),
        "needs_rescript_for_action": needs_rescript,
    }


def cmd_route(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    decision = parse_route(args.text, default_formality=state["formality"])
    if args.record:
        case_id = args.case or state.get("current_case_id")
        record_event(root, "route", decision, case_id=case_id)

    if args.json:
        print(dump_json(decision))
    else:
        print(f"[ROUTE] document={decision['document']} urgency={decision['urgency']} formality={decision['formality']}")
        print(f"        ministries={', '.join(decision['ministries'])} needs_rescript_for_action={decision['needs_rescript_for_action']}")
    return 0


@dataclass(frozen=True)
class Rescript:
    raw: str
    category: str
    departments: list[str]
    needs_clarification: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "category": self.category,
            "departments": self.departments,
            "needs_clarification": self.needs_clarification,
        }


def parse_departments(raw: str) -> list[str]:
    mapped: dict[str, str] = {
        "工部": "works",
        "兵部": "war",
        "礼部": "rites",
        "刑部": "justice",
        "吏部": "personnel",
        "户部": "revenue",
        "works": "works",
        "war": "war",
        "rites": "rites",
        "justice": "justice",
        "personnel": "personnel",
        "revenue": "revenue",
    }

    # Allow formats:
    # - 该部知道：兵部
    # - 该部知道 工部
    # - 该部知道：工部、礼部
    m = re.search(r"该部知道[:：\s]+(.+)$", raw)
    if not m:
        return []

    tail = m.group(1)
    parts = re.split(r"[，,、\s]+", tail.strip())
    depts: list[str] = []
    for p in parts:
        if not p:
            continue
        key = p.strip()
        key = re.sub(r"[^\w\u4e00-\u9fff-]+", "", key)
        mapped_value = mapped.get(key)
        if mapped_value and mapped_value not in depts:
            depts.append(mapped_value)
    return depts


def parse_rescript(text: str) -> Rescript:
    raw = text.strip()
    lowered = raw.lower()

    if "留中" in raw or any(k in raw for k in ["暂缓", "暂停", "撤回", "不必了"]):
        return Rescript(raw=raw, category="pause", departments=[], needs_clarification=False)

    if any(k in raw for k in ["再议具奏", "重拟", "另拟", "不妥", "不行", "换个办法"]):
        return Rescript(raw=raw, category="rethink", departments=[], needs_clarification=False)

    if any(k in raw for k in ["着九卿议", "九卿", "会同诸部", "会审", "多种方案", "多方案"]):
        return Rescript(raw=raw, category="consensus", departments=[], needs_clarification=False)

    if "该部知道" in raw:
        depts = parse_departments(raw)
        return Rescript(
            raw=raw,
            category="dept_only",
            departments=depts,
            needs_clarification=(len(depts) == 0),
        )

    if "览" in raw or any(k in raw for k in ["知道了", "仅供参考", "先别动", "只看看"]):
        return Rescript(raw=raw, category="view", departments=[], needs_clarification=False)

    if "如拟" in raw or any(k in raw for k in ["准", "可", "依议", "照办", "就这么办", "立刻施行"]):
        return Rescript(raw=raw, category="approve", departments=list(DEPARTMENTS), needs_clarification=False)

    # Fallback: unknown; treat as "rethink" to avoid accidental execution.
    return Rescript(raw=raw, category="unknown", departments=[], needs_clarification=True)


def cmd_rescript(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    case_id = args.case or state.get("current_case_id")

    parsed = parse_rescript(args.text)

    if args.record:
        record_event(root, "rescript", parsed.as_dict(), case_id=case_id)

    if case_id and not args.no_case_update:
        case = load_case(root, case_id)
        case["last_rescript"] = {"ts": now_iso(), **parsed.as_dict()}
        case["updated_at"] = now_iso()
        save_case(root, case)

    if args.json:
        print(dump_json(parsed.as_dict()))
    else:
        print(f"[RESCRIPT] category={parsed.category} departments={','.join(parsed.departments) or '-'} clarification={parsed.needs_clarification}")
    return 0


def cmd_case_open(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)

    case_id = new_case_id(args.title)
    case = {
        "id": case_id,
        "title": args.title,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": "open",
        "last_rescript": None,
    }
    save_case(root, case)
    update_todo(root, case_id=case_id, title=args.title, done=False)
    record_event(root, "case_open", {"title": args.title}, case_id=case_id)

    if args.set_current:
        state["current_case_id"] = case_id
        save_state(root, state)

    if args.json:
        print(dump_json(case))
    else:
        print(f"[OK] Opened case {case_id}: {args.title}")
    return 0


def cmd_case_list(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    load_state(root)  # ensure store
    cases: list[dict[str, Any]] = []
    for p in sorted(cases_dir(root).glob("*.json")):
        try:
            cases.append(read_json(p))
        except Exception:
            continue
    if args.json:
        print(dump_json(cases))
        return 0

    for c in cases:
        last = c.get("last_rescript") or {}
        last_cat = last.get("category")
        suffix = f" (last_rescript={last_cat})" if last_cat else ""
        print(f"- {c.get('id')} [{c.get('status')}] {c.get('title')}{suffix}")
    return 0


def cmd_case_close(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    case = load_case(root, args.case_id)
    case["status"] = "closed"
    case["updated_at"] = now_iso()
    save_case(root, case)
    update_todo(root, case_id=case["id"], title=case["title"], done=True)
    record_event(root, "case_close", {}, case_id=case["id"])

    if state.get("current_case_id") == case["id"]:
        state["current_case_id"] = None
        save_state(root, state)

    if args.json:
        print(dump_json(case))
    else:
        print(f"[OK] Closed case {case['id']}")
    return 0


def cmd_case_set_current(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    load_case(root, args.case_id)  # validate
    state["current_case_id"] = args.case_id
    save_state(root, state)
    record_event(root, "case_set_current", {}, case_id=args.case_id)
    if args.json:
        print(dump_json(state))
    else:
        print(f"[OK] Current case set to {args.case_id}")
    return 0


def cmd_formality(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    if args.value:
        if args.value not in FORMALITY_VALUES:
            raise SystemExit(f"Invalid formality: {args.value} (choose from {', '.join(FORMALITY_VALUES)})")
        state["formality"] = args.value
        save_state(root, state)
        record_event(root, "formality_set", {"value": args.value}, case_id=None)
    if args.json:
        print(dump_json({"formality": state["formality"]}))
    else:
        print(state["formality"])
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    case_id = args.case or state.get("current_case_id")
    payload = {"kind": args.kind, "message": args.message}
    record_event(root, "record", payload, case_id=case_id)
    if args.json:
        print(dump_json({"ok": True, **payload, "case": case_id}))
    else:
        print(f"[OK] Recorded ({args.kind})")
    return 0


def can_execute(case: dict[str, Any], dept: str) -> tuple[bool, str]:
    last = case.get("last_rescript")
    if not last:
        return False, "no rescript recorded for this case"
    category = last.get("category")
    if category == "approve":
        return True, "approved"
    if category == "dept_only":
        allowed = last.get("departments") or []
        if dept in allowed:
            return True, "dept approved"
        return False, f"dept not approved (allowed: {', '.join(allowed) or '-'})"
    if category in {"view", "pause", "rethink", "consensus"}:
        return False, f"rescript category blocks execution: {category}"
    return False, f"unknown rescript category: {category}"


def shlex_join(argv: list[str]) -> str:
    # Python 3.8 compatibility for shlex.join
    import shlex

    return " ".join(shlex.quote(a) for a in argv)


def cmd_exec(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    case_id = args.case or state.get("current_case_id")
    dept = args.dept

    if not args.command:
        raise SystemExit("Missing command (use: mingctl exec -- <command...>)")

    if args.kind == "action" and not args.force:
        if not case_id:
            raise SystemExit("No case selected (use `case open --set-current` or pass --case), or run with --force")
        case = load_case(root, case_id)
        ok, reason = can_execute(case, dept)
        if not ok:
            raise SystemExit(f"Not authorized by rescript: {reason} (use --force to override)")

    started = time.time()
    try:
        if args.capture:
            proc = subprocess.run(
                args.command,
                cwd=root,
                text=True,
                capture_output=True,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            sys.stdout.write(stdout)
            sys.stderr.write(stderr)
            combined = stdout + stderr
            if len(combined) > args.max_capture_bytes:
                combined = combined[: args.max_capture_bytes] + "\n[...truncated...]\n"
            output_snippet = combined
        else:
            proc = subprocess.run(args.command, cwd=root)
            output_snippet = None
    except FileNotFoundError:
        raise SystemExit(f"Command not found: {args.command[0]}")
    finally:
        elapsed_ms = int((time.time() - started) * 1000)

    record_event(
        root,
        "exec",
        {
            "kind": args.kind,
            "dept": dept,
            "command": args.command,
            "command_str": shlex_join(args.command),
            "exit_code": proc.returncode,
            "duration_ms": elapsed_ms,
            "forced": bool(args.force),
            "captured": bool(args.capture),
            "output_snippet": output_snippet,
        },
        case_id=case_id,
    )

    return proc.returncode


def tail_lines(path: Path, n: int) -> list[str]:
    if n <= 0 or not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-n:]


def cmd_prompt_morning(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    current_case_id = state.get("current_case_id")
    case_title = None
    if current_case_id:
        try:
            case_title = load_case(root, current_case_id).get("title")
        except Exception:
            case_title = None

    out: list[str] = []
    out.append("# 早朝议事（Morning Audience）")
    out.append("")
    out.append(f"- 项目：`{root}`")
    out.append(f"- 礼仪：`{state.get('formality')}`")
    out.append(f"- 当前案：`{current_case_id or '-'}`{f' {case_title}' if case_title else ''}")
    out.append("")

    if (root / ".git").exists():
        try:
            status = subprocess.run(
                ["git", "status", "-sb"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            out.append("## 吏部黄册（Git Status）")
            out.append("```")
            out.append((status.stdout or "").rstrip() or "(no output)")
            out.append("```")
            out.append("")
        except Exception:
            pass

    out.append("## 近报（Last Archives）")
    out.append("```jsonl")
    out.extend(tail_lines(archive_path(root), args.tail))
    out.append("```")

    print("\n".join(out))
    return 0


def cmd_prompt_new_emperor(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    state = load_state(root)
    current_case_id = state.get("current_case_id")
    agents_md = root / "AGENTS.md"

    out: list[str] = []
    out.append("# 新帝登基（Onboarding）")
    out.append("")
    out.append(f"- 项目：`{root}`")
    out.append(f"- 礼仪：`{state.get('formality')}`（可用 `python .great-ming/mingctl.py formality pragmatic` 切换简奏）")
    out.append(f"- 当前案：`{current_case_id or '-'}`")
    out.append("")
    out.append("## 一、立司礼监（一次即可）")
    out.append("")
    out.append("- 本项目已存在 `.great-ming/`；建议将其加入目标项目 `.gitignore`：")
    out.append("")
    out.append("```gitignore")
    out.append(".great-ming/")
    out.append("```")
    out.append("")
    out.append("## 二、立祖训（AGENTS.md，推荐）")
    out.append("")
    if agents_md.exists():
        out.append("- 已见 `AGENTS.md`；建议追加 Great Ming“祖训/会典”条目，以固定称谓、文书、朱批边界与记档准则。")
    else:
        out.append("- 建议在仓库根目录创建 `AGENTS.md`，以定国体（固定 Great Ming 风格）。最小模板如下：")
        out.append("")
        out.append("```markdown")
        out.append("# 大明祖训（Great Ming）")
        out.append("- 本仓库默认启用 Great Ming 体例（章奏/朱批/六部）。")
        out.append("- 任何改动/执行前请朱批：如拟 / 该部知道：某部 / 留中。")
        out.append("- 命令优先经 `python .great-ming/mingctl.py exec ...` 记档。")
        out.append("```")
    out.append("- 若陛下允准，agent 可代为创建/更新 `AGENTS.md`。")
    out.append("")
    out.append("## 三、立案（奏章队列）")
    out.append("")
    out.append("- 开一案并设为当前案：")
    out.append("")
    out.append('```bash')
    out.append('python .great-ming/mingctl.py case open "修缮登录法式" --set-current')
    out.append('```')
    out.append("")
    out.append("## 四、三句口令（最小闭环）")
    out.append("")
    out.append("```bash")
    out.append('python .great-ming/mingctl.py route "修复登录报错" --record')
    out.append('python .great-ming/mingctl.py rescript "如拟"')
    out.append('python .great-ming/mingctl.py exec --kind action --dept war -- npm test')
    out.append("```")
    out.append("")
    out.append("## 五、看邸报（早朝议事）")
    out.append("")
    out.append("```bash")
    out.append("python .great-ming/mingctl.py prompt morning-audience --tail 20")
    out.append("```")
    out.append("")
    out.append("## 朱批速记")
    out.append("")
    out.append("- `如拟`：全准（可执行）")
    out.append("- `览`：只阅（不执行）")
    out.append("- `该部知道：兵部/工部/礼部/刑部/吏部/户部`：限部执行")
    out.append("- `再议具奏`：重拟方案")
    out.append("- `着九卿议`：多方案会商")
    out.append("- `留中`：撤回/暂停")
    out.append("")
    out.append("## 提醒")
    out.append("")
    out.append("`mingctl` 只能约束并记档“经由 mingctl 执行的命令”；若绕过直接执行，将失去授权闸门与审计链条。")

    print("\n".join(out))
    return 0


def list_resources(root: Path) -> list[dict[str, Any]]:
    candidates = [
        ("ancestral-instructions", ["README.md", "README", "CONTRIBUTING.md", "CONTRIBUTING", "SECURITY.md", "SECURITY"]),
        ("license", ["LICENSE", "LICENSE.md"]),
    ]
    resources: list[dict[str, Any]] = []
    for name, filenames in candidates:
        for fn in filenames:
            p = root / fn
            if p.exists() and p.is_file():
                resources.append({"name": name, "path": str(p)})
                break
    if (root / ".git").exists():
        resources.append({"name": "yellow-registers", "path": "git://log"})
    return resources


def cmd_resources_list(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    resources = list_resources(root)
    if args.json:
        print(dump_json(resources))
    else:
        for r in resources:
            print(f"- {r['name']}: {r['path']}")
    return 0


def cmd_resources_show(args: argparse.Namespace) -> int:
    root = get_root(args.root)
    resources = {r["name"]: r["path"] for r in list_resources(root)}
    key = args.name
    if key not in resources:
        raise SystemExit(f"Unknown resource: {key}")

    if resources[key].startswith("git://"):
        if key == "yellow-registers":
            proc = subprocess.run(
                ["git", "log", "--oneline", f"-n{args.n}"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            print(proc.stdout.rstrip())
            return proc.returncode

    p = Path(resources[key])
    content = p.read_text(encoding="utf-8", errors="replace")
    if len(content) > args.max_bytes:
        content = content[: args.max_bytes] + "\n[...truncated...]\n"
    print(content.rstrip())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mingctl", add_help=True)
    p.add_argument(
        "--root",
        help="Project root (defaults to MING_ROOT / script location / auto-detect; may appear before or after subcommand)",
    )
    p.add_argument("--json", action="store_true", help="JSON output where applicable")

    sub = p.add_subparsers(dest="cmd", required=True)

    install = sub.add_parser("install", help="Install mingctl into project .great-ming/")
    install.add_argument("--force", action="store_true", help="Overwrite existing installed script")
    install.set_defaults(func=cmd_install)

    init = sub.add_parser("init", help="Initialize .great-ming/ store (no script copy)")
    init.set_defaults(func=cmd_init)

    route = sub.add_parser("route", help="Route an imperial order (通政司路由)")
    route.add_argument("text", help="User request / edict")
    route.add_argument("--record", action="store_true", help="Append to archives.ndjson")
    route.add_argument("--case", help="Case id (defaults to current_case_id)")
    route.set_defaults(func=cmd_route)

    rescript = sub.add_parser("rescript", help="Parse/record a vermilion rescript (朱批)")
    rescript.add_argument("text", help="Rescript text, e.g. 如拟 / 览 / 该部知道：兵部")
    rescript.add_argument("--case", help="Case id (defaults to current_case_id)")
    rescript.add_argument("--no-case-update", action="store_true", help="Do not update case last_rescript")
    rescript.add_argument(
        "--no-record",
        dest="record",
        action="store_false",
        help="Do not append to archives.ndjson",
    )
    rescript.set_defaults(record=True)
    rescript.set_defaults(func=cmd_rescript)

    case = sub.add_parser("case", help="Case (奏章) management")
    case_sub = case.add_subparsers(dest="case_cmd", required=True)

    case_open = case_sub.add_parser("open", help="Open a new case")
    case_open.add_argument("title", help="Case title")
    case_open.add_argument("--set-current", action="store_true", help="Set as current_case_id")
    case_open.set_defaults(func=cmd_case_open)

    case_list = case_sub.add_parser("list", help="List cases")
    case_list.set_defaults(func=cmd_case_list)

    case_close = case_sub.add_parser("close", help="Close a case")
    case_close.add_argument("case_id", help="Case id")
    case_close.set_defaults(func=cmd_case_close)

    case_set = case_sub.add_parser("set-current", help="Set current case")
    case_set.add_argument("case_id", help="Case id")
    case_set.set_defaults(func=cmd_case_set_current)

    formality = sub.add_parser("formality", help="Get/set default formality")
    formality.add_argument("value", nargs="?", help="One of: full_ceremonial, balanced, pragmatic")
    formality.set_defaults(func=cmd_formality)

    record = sub.add_parser("record", help="Append a manual record (for apply_patch etc.)")
    record.add_argument("kind", choices=("note", *DEPARTMENTS), help="Record kind")
    record.add_argument("message", help="Short message")
    record.add_argument("--case", help="Case id (defaults to current_case_id)")
    record.set_defaults(func=cmd_record)

    ex = sub.add_parser("exec", help="Execute a command and archive it (司礼监记档)")
    ex.add_argument("--dept", required=True, choices=DEPARTMENTS, help="Which ministry is executing this command")
    ex.add_argument("--kind", choices=("evidence", "action"), default="evidence", help="evidence=取证, action=奉旨施行")
    ex.add_argument("--case", help="Case id (defaults to current_case_id)")
    ex.add_argument("--force", action="store_true", help="Bypass rescript authorization checks")
    ex.add_argument("--capture", action="store_true", help="Capture output snippet into archives")
    ex.add_argument("--max-capture-bytes", type=int, default=20000, help="Max captured bytes")
    ex.add_argument("command", nargs=argparse.REMAINDER, help="Command after --, e.g. -- git status")
    ex.set_defaults(func=cmd_exec)

    prompt = sub.add_parser("prompt", help="Generate prompt outputs")
    prompt_sub = prompt.add_subparsers(dest="prompt_cmd", required=True)
    morning = prompt_sub.add_parser("morning-audience", help="Morning audience summary")
    morning.add_argument("--tail", type=int, default=10, help="Tail N archive lines")
    morning.set_defaults(func=cmd_prompt_morning)
    new_emperor = prompt_sub.add_parser("new-emperor", help="First-time onboarding guide")
    new_emperor.set_defaults(func=cmd_prompt_new_emperor)

    resources = sub.add_parser("resources", help="List/show resources (祖训/黄册)")
    resources_sub = resources.add_subparsers(dest="res_cmd", required=True)
    res_list = resources_sub.add_parser("list", help="List known resources")
    res_list.set_defaults(func=cmd_resources_list)
    res_show = resources_sub.add_parser("show", help="Show a resource")
    res_show.add_argument("name", help="Resource name, e.g. ancestral-instructions, yellow-registers")
    res_show.add_argument("-n", type=int, default=30, help="For yellow-registers: number of commits")
    res_show.add_argument("--max-bytes", type=int, default=20000, help="Max bytes for file resources")
    res_show.set_defaults(func=cmd_resources_show)

    return p


def extract_global_flags(argv: list[str]) -> tuple[Optional[str], bool, list[str]]:
    """
    Extract --root/--json anywhere before a standalone `--`.

    This keeps CLI ergonomics flexible, e.g.:
      mingctl install --root .
      mingctl --root . install
      mingctl exec --dept war --root . -- npm test
    """

    root: Optional[str] = None
    json_flag = False
    cleaned: list[str] = []

    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--":
            cleaned.extend(argv[i:])
            break

        if token == "--json":
            json_flag = True
            i += 1
            continue

        if token == "--root":
            if i + 1 >= len(argv):
                raise SystemExit("--root requires a value")
            root = argv[i + 1]
            i += 2
            continue

        if token.startswith("--root="):
            root = token.split("=", 1)[1]
            i += 1
            continue

        cleaned.append(token)
        i += 1

    return root, json_flag, cleaned


def main(argv: list[str]) -> int:
    parser = build_parser()
    root, json_flag, cleaned = extract_global_flags(argv)
    args = parser.parse_args(cleaned)
    args.root = root
    args.json = json_flag
    # argparse includes the leading `--` in REMAINDER; strip it.
    if getattr(args, "command", None) and args.command and args.command[0] == "--":
        args.command = args.command[1:]
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
