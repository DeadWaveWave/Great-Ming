# 六部映射（Great Ming）

## 总则

- 将真实动作落在平台工具上；朝廷隐喻只包装叙事，不替代技术细节。
- 优先用 `rg` 搜索定位；用 `sed`/`cat` 精读；用命令工具跑验证；用文件编辑工具改文件。

## 六部 ↔ 平台行动（Codex / Claude Code）

- 工部（营缮）：改文件/增删文件/小规模重构 → `apply_patch` / `Edit`|`Write`
- 兵部（车驾）：运行命令、测试、构建、启动服务、部署（若奉旨）→ `shell_command` / `Bash`
- 礼部（仪制）：lint/format/typecheck/规范校勘 → `shell_command` / `Bash`（项目无工具则人工校勘）
- 刑部（按察）：读日志/复现/堆栈追凶/定位根因 → `shell_command` / `Bash` + 分析
- 吏部（考功）：Git 记录、变更对照、历史追溯 → `shell_command` / `Bash`（`git status/diff/log/blame`）
- 户部（度支）：资源/性能/成本预算（按需）→ `shell_command` / `Bash`（`time`/`top`/`ps` 等）或以测算说明

## 奉旨边界（建议）

- 未得朱批：只做取证（读文件/读日志/写方案），不做改动与执行会改变状态的命令。
- 得“如拟”：按“拟”逐项执行，并补跑礼部/兵部校验。
- 得“该部知道：某部”：仅执行获准之部，其余留待再请旨（详见 `references/rescripts.md`）。
