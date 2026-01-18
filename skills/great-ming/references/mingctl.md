# 司礼监记档（`mingctl`）

`mingctl` 是本 Skill 的"司礼监"脚本：不依赖 MCP，在项目根目录生成并维护 `.great-ming/`，用于：

- 记录朱批（授权边界）与执行（审计日志，NDJSON）
- 保存在办奏章（cases/todo）与默认礼仪严格度（state）
- 生成"早朝议事"摘要（prompt）
- 提供"祖训/黄册"资源入口（resources）

## 1) 安装到项目根目录（一次即可）

目标：让项目内始终可用 `python .great-ming/mingctl.py ...`

**Codex 环境：**
- `python "$CODEX_HOME/skills/great-ming/scripts/mingctl.py" install --root .`
- 若 `CODEX_HOME` 未设：`python ~/.codex/skills/great-ming/scripts/mingctl.py install --root .`

**Claude Code 环境：**
- `python ~/.claude/skills/great-ming/scripts/mingctl.py install --root .`

安装后会生成：

- `.great-ming/mingctl.py`
- `.great-ming/state.json`
- `.great-ming/archives.ndjson`
- `.great-ming/cases/`
- `.great-ming/todo.md`

## 2) 常用流程（建议在 Skill 内强制采用）

- 开一案并设为当前案：`python .great-ming/mingctl.py case open "修缮登录法式" --set-current`
- 通政司路由（可记档）：`python .great-ming/mingctl.py route "修复登录报错" --record`
- 记录朱批：`python .great-ming/mingctl.py rescript "如拟"`
- 取证命令（不需要"如拟"）：`python .great-ming/mingctl.py exec --kind evidence --dept justice -- rg \"error\" -n`
- 奉旨施行（会检查最近朱批是否允许）：`python .great-ming/mingctl.py exec --kind action --dept war -- npm test`
- 工部已用文件编辑工具（`apply_patch` / `Edit`|`Write`）修缮后，补一条记档：`python .great-ming/mingctl.py record works "apply_patch/Edit: updated src/..."`（可选但推荐）
- 结案：`python .great-ming/mingctl.py case close <case-id>`

## 3) 早朝议事 / 资源

- 新帝登基（引导）：`python .great-ming/mingctl.py prompt new-emperor`
- 早朝议事：`python .great-ming/mingctl.py prompt morning-audience --tail 10`
- 祖训/黄册列表：`python .great-ming/mingctl.py resources list`
- 祖训（README/CONTRIBUTING）：`python .great-ming/mingctl.py resources show ancestral-instructions`
- 黄册（git log）：`python .great-ming/mingctl.py resources show yellow-registers -n 30`

## 4) 注意（边界与安全）

- `mingctl` 只能"约束与记档"你通过它执行的命令；模型仍可绕过直接用命令执行工具（`shell_command` / `Bash`），所以应在本 Skill 的流程里要求"所有命令经由 `mingctl exec`"。
- 若命令含密钥/Token，建议不用 `--capture`（避免写入 `archives.ndjson`），或先将敏感值放进环境变量再执行。
