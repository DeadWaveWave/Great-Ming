# Great Ming：登基加冕，成为AI的皇帝

![Imperial Edict](https://img.shields.io/badge/Imperial_Edict-天子诰命-blue)
![Court Officials](https://img.shields.io/github/stars/DeadWaveWave/Great-Ming?style=social&label=Court%20Officials)
![Version](https://img.shields.io/badge/Version-Yongle_3.1.4-green)

Great Ming is a Codex Skill (not MCP) that turns coding work into a Ming-dynasty "morning audience" workflow: you draft proposals as **memorials** (题本/奏本/弹章), wait for the Emperor's **vermilion rescript** (朱批), then execute via the "Six Ministries" metaphor—with real actions backed by `apply_patch` / `shell_command`.

This repo also ships `mingctl`, a small Python script that creates a project-local **`.great-ming/`** archive to record rescripts, executions, and case state (司礼监记档).

## What’s Included

- Codex Skill: `skills/great-ming/` (trigger phrases: Great Ming/大明/朱批/题本/票拟…)
- Script: `skills/great-ming/scripts/mingctl.py` (install into a target repo’s `.great-ming/`)
- Packaged artifact: `dist/great-ming.skill` (zip-format `.skill`)
- Design article (journal-style): `docs/principles-and-historical-mapping.zh-CN.md`

## Install

### Option 1: Let the Agent Install (Easiest)

Simply tell your Agent in a conversation:

```
Please install this Skill for me:
https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill
```

The Agent will automatically download and install it to the appropriate skills directory (`~/.codex/skills/` or `~/.claude/skills/`), then restart to load it.

### Option 2: Manual Installation (Local Development)

#### Codex Environment

Copy/symlink the folder into your Codex skills directory:

- `cp -R skills/great-ming ~/.codex/skills/great-ming`

Or use the packaged file:

- `curl -L -o /tmp/great-ming.skill https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill`
- `unzip /tmp/great-ming.skill -d ~/.codex/skills`

Restart Codex to pick up the new skill.

#### Claude Code Environment

Copy/symlink the folder into your Claude Code skills directory:

- `cp -R skills/great-ming ~/.claude/skills/great-ming`

Or use the packaged file:

- `curl -L -o /tmp/great-ming.skill https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill`
- `unzip /tmp/great-ming.skill -d ~/.claude/skills`

Restart Claude Code (or start a new conversation) to load the skill.

## Packaging (Build `dist/great-ming.skill`)

A `.skill` file is just a zip archive. It should contain a top-level `great-ming/` folder (i.e. `great-ming/SKILL.md` exists inside the archive).

One-command build:

- `./scripts/release.sh build`

(Optional) one-command publish (requires `gh` auth):

- `./scripts/release.sh publish 3.1.5`

From the repo root:

- `mkdir -p dist`
- `rm -f dist/great-ming.skill`
- `mkdir -p dist && (cd skills && zip -r ../dist/great-ming.skill great-ming -x '**/.DS_Store' -x '**/__pycache__/*')`

(Optional) verify:

- `unzip -l dist/great-ming.skill | head`

## Use (in a Project)

### “New Emperor” Onboarding (60 seconds)

In a Codex chat, say one word: `登基`.

The agent will auto-bootstrap first-time setup (create/install `.great-ming/`, update `.gitignore`, and print the onboarding guide), and will also recommend adding a repo-level `AGENTS.md` “canon/constitution” to lock the Great Ming style, then ask for your first case/task.

Manual mode (optional):

1) Install the project-local archive (creates `.great-ming/`):

- `python ~/.codex/skills/great-ming/scripts/mingctl.py install --root .`

2) Print the onboarding guide anytime:

- `python .great-ming/mingctl.py prompt new-emperor`

3) Add `.great-ming/` to your target project’s `.gitignore`:

```gitignore
.great-ming/
```

### Lock The Style (Recommended: `AGENTS.md`)

This skill is **opt-in by default** (it should only trigger when the user explicitly says “Great Ming” or “登基”). If you want Great Ming to be the default style for a specific repo, add an `AGENTS.md` at that repo root and treat it as a project “constitution/canon” (祖训/会典).

- Template (Chinese): `docs/AGENTS-template.zh-CN.md`

1) Install the “司礼监” archive into your project root:

- `python ~/.codex/skills/great-ming/scripts/mingctl.py install --root .`

2) Open a case (奏章) and set it as current:

- `python .great-ming/mingctl.py case open "修缮登录法式" --set-current`

3) Route the edict (通政司) and record it:

- `python .great-ming/mingctl.py route "修复登录报错" --record`

4) Record the rescript (朱批) before “奉旨施行”:

- `python .great-ming/mingctl.py rescript "如拟"`
- or: `python .great-ming/mingctl.py rescript "该部知道：兵部"`

5) Run evidence vs action commands with automatic auditing:

- Evidence (取证): `python .great-ming/mingctl.py exec --kind evidence --dept justice -- rg "error" -n`
- Action (施行): `python .great-ming/mingctl.py exec --kind action --dept war -- npm test`

6) After `apply_patch` edits (工部修缮), optionally append a manual record:

- `python .great-ming/mingctl.py record works "apply_patch: updated src/auth/login.ts"`

7) Morning-audience summary:

- `python .great-ming/mingctl.py prompt morning-audience --tail 20`

## `.great-ming/` Files (Project-Local State)

`mingctl` creates:

- `.great-ming/state.json` (default formality + current case id)
- `.great-ming/archives.ndjson` (append-only audit log)
- `.great-ming/cases/*.json` (case records)
- `.great-ming/todo.md` (human-readable bulletin)

Add this to your target project’s `.gitignore`:

```gitignore
.great-ming/
```

## Security Notes

`archives.ndjson` is an audit log. Avoid putting secrets into commands or captured output. Prefer running sensitive commands without `--capture`.

## Imperial Edict (License)

This repository is released under the **Imperial Edict** (based on MIT License), see `LICENSE` file for details.

## Dynasty Chronicle

[![Dynasty Chronicle](https://api.star-history.com/svg?repos=DeadWaveWave/Great-Ming&type=Date)](https://star-history.com/#DeadWaveWave/Great-Ming&Date)
