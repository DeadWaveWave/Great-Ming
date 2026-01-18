# Great Ming：登基加冕，成为AI的皇帝

![诏书](https://img.shields.io/badge/诏书-天子诰命-blue)
![朝臣](https://img.shields.io/github/stars/DeadWaveWave/Great-Ming?style=social&label=朝臣)
![版本](https://img.shields.io/badge/版本-永乐_3.1.4-green)

Great Ming 是一个同时支持 **Codex** 和 **Claude Code** 的 Skill，用于把日常开发工作改写为"大明早朝"式的工程闭环：先以 **章奏文书**（题本/奏本/弹章）起草"票拟"，等待陛下 **朱批** 后再奉旨施行；实际动作仍由对应平台的工具落地执行。

本仓库同时提供 `mingctl`（Python 脚本），用于在项目根目录创建 **`.great-ming/`**，记录朱批、执行与在办奏章状态（司礼监记档）。

## 平台兼容性

本 Skill 同时支持：
- **Codex**：使用 `apply_patch` 和 `shell_command`
- **Claude Code**：使用 `Edit`/`Write` 和 `Bash`

AI 会自动根据当前环境选择可用的工具，无需手动切换。

## 内容一览

- Skill 主文件：`skills/great-ming/SKILL.md`（触发词：Great Ming/大明/朱批/题本/票拟…；兼容 Codex & Claude Code）
- 参考文档：`skills/great-ming/references/*.md`（路由、模板、六部映射等）
- 司礼监脚本：`skills/great-ming/scripts/mingctl.py`（安装到目标项目的 `.great-ming/`）
- 打包产物：`dist/great-ming.skill`（zip 格式的 `.skill`）
- 原理与历史对应（期刊式文章）：`docs/principles-and-historical-mapping.zh-CN.md`

## 安装

### 方式一：请 Agent 代为安装（最便捷）

直接在对话中对 Agent 说：

```
帮我安装这个 Skill：
https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill
```

Agent 会自动下载并安装到对应的 skills 目录（`~/.codex/skills/` 或 `~/.claude/skills/`），然后重启即可。

### 方式二：手动安装（本地开发）

#### Codex 环境

把文件夹复制/链接到 Codex skills 目录：

- `cp -R skills/great-ming ~/.codex/skills/great-ming`

或使用打包文件：

- `curl -L -o /tmp/great-ming.skill https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill`
- `unzip /tmp/great-ming.skill -d ~/.codex/skills`

重启 Codex 以加载新 Skill。

#### Claude Code 环境

把文件夹复制/链接到 Claude Code skills 目录：

- `cp -R skills/great-ming ~/.claude/skills/great-ming`

或使用打包文件：

- `curl -L -o /tmp/great-ming.skill https://raw.githubusercontent.com/DeadWaveWave/Great-Ming/main/dist/great-ming.skill`
- `unzip /tmp/great-ming.skill -d ~/.claude/skills`

重启 Claude Code（或新建对话）以加载新 Skill。

## 打包（生成 `dist/great-ming.skill`）

`.skill` 本质是 zip 包，内部应包含顶层目录 `great-ming/`（即存在 `great-ming/SKILL.md`）。

一键打包：

- `./scripts/release.sh build`

（可选）一键发版（需要已安装并登录 `gh`）：

- `./scripts/release.sh publish 3.1.5`

在仓库根目录执行：

- `mkdir -p dist`
- `rm -f dist/great-ming.skill`
- `mkdir -p dist && (cd skills && zip -r ../dist/great-ming.skill great-ming -x '**/.DS_Store' -x '**/__pycache__/*')`

校验（可选）：

- `unzip -l dist/great-ming.skill | head`

## 使用（在项目中）

### 新帝登基（首次上手 60 秒）

在对话中对 agent 说一句：`登基`。

agent 会自动完成首次启用（创建/安装 `.great-ming/`、补齐 `.gitignore`、输出引导与例子），并建议（可代立）将 Great Ming 体例写入 `AGENTS.md`“祖训”，随后引导你口谕第一案。

手动方式（可选，便于自测/脚本化）：

1) 在项目根目录安装"司礼监记档"（会创建 `.great-ming/`）：

**Codex 环境：**
- `python ~/.codex/skills/great-ming/scripts/mingctl.py install --root .`

**Claude Code 环境：**
- `python ~/.claude/skills/great-ming/scripts/mingctl.py install --root .`

2) 打印引导（可随时再跑）：

- `python .great-ming/mingctl.py prompt new-emperor`

3) 将 `.great-ming/` 加入目标项目 `.gitignore`：

```gitignore
.great-ming/
```

### 固定风格（推荐：写入 `AGENTS.md`）

本 Skill 默认是 **opt-in**（只有用户显式说 “Great Ming” 或 “登基” 才触发）。若你希望在某个仓库内“固定国体”，建议在该仓库根目录添加 `AGENTS.md`，把 Great Ming 体例写成项目宪章（推荐命名为“祖训”/“会典”）。

- 模板：`docs/AGENTS-template.zh-CN.md`

1) 安装"司礼监记档"到项目根目录：

**Codex 环境：**
- `python ~/.codex/skills/great-ming/scripts/mingctl.py install --root .`

**Claude Code 环境：**
- `python ~/.claude/skills/great-ming/scripts/mingctl.py install --root .`

2) 开一案（奏章）并设为当前案：

- `python .great-ming/mingctl.py case open "修缮登录法式" --set-current`

3) 通政司路由并记档：

- `python .great-ming/mingctl.py route "修复登录报错" --record`

4) 奉旨施行前先记录朱批：

- `python .great-ming/mingctl.py rescript "如拟"`
- 或：`python .great-ming/mingctl.py rescript "该部知道：兵部"`

5) 取证 / 施行命令（自动审计落盘）：

- 取证：`python .great-ming/mingctl.py exec --kind evidence --dept justice -- rg "error" -n`
- 施行：`python .great-ming/mingctl.py exec --kind action --dept war -- npm test`

6) 工部以 `apply_patch` 修缮后，可补一条手工记档（推荐）：

- `python .great-ming/mingctl.py record works "apply_patch: updated src/auth/login.ts"`

7) 早朝议事摘要：

- `python .great-ming/mingctl.py prompt morning-audience --tail 20`

## `.great-ming/`（项目内状态）

`mingctl` 会生成：

- `.great-ming/state.json`（默认礼仪严格度 + 当前案）
- `.great-ming/archives.ndjson`（追加写审计日志）
- `.great-ming/cases/*.json`（案件记录）
- `.great-ming/todo.md`（人类可读的“邸报”）

建议在目标项目 `.gitignore` 中加入：

```gitignore
.great-ming/
```

## 安全提示

`archives.ndjson` 属于审计日志。避免在命令或捕获输出中出现密钥；敏感命令尽量不要开启 `--capture`。

## 诏书（许可证）

本仓库遵循《天子诰命》（基于 MIT 许可）开放源代码，详见 `LICENSE` 文件。

## 龙庭编年

[![龙庭编年](https://api.star-history.com/svg?repos=DeadWaveWave/Great-Ming&type=Date)](https://star-history.com/#DeadWaveWave/Great-Ming&Date)
