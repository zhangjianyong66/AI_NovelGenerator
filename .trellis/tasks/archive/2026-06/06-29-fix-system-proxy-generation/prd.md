# 修复系统代理污染生成执行

## Goal

当项目代理配置未启用时，生成执行不应因为进程继承了系统代理环境变量而在构造 OpenAI 兼容 LLM 客户端时失败。用户仍可在项目配置中显式启用代理；本次修复只处理未启用项目代理时被系统 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 等环境变量污染的问题。

当前用户遇到的错误是 `ChatOpenAI` 校验代理 URL 失败：系统环境里存在 `socks://127.0.0.1:10808`，但底层客户端不接受 `socks://` scheme，导致任务还没开始请求模型就失败。

## Confirmed Facts

- 生成执行服务通过 `app/services/generation_executor.py` 调用旧生成函数，旧生成函数最终通过 `llm_adapters.py` 创建 LLM adapter。
- `llm_adapters.py` 中 DeepSeek、OpenAI、Ollama、ML Studio 等 OpenAI 兼容适配器直接构造 `langchain_openai.ChatOpenAI(...)`，当前没有显式控制系统代理环境。
- 旧 GUI 的 `ui/main_window.py` 和 `ui/config_tab.py` 只设置或清理 `HTTP_PROXY` / `HTTPS_PROXY`，本地 API 路径不会在每次生成前按项目 `proxy_setting.enabled` 清理系统环境代理。
- `config.json.proxy_setting.enabled=false` 的语义应表示项目未启用代理；这种情况下不应隐式使用系统代理导致生成失败。
- `config.json` 是本地私有配置，不能提交；测试必须使用临时配置或直接测试适配器边界。

## Requirements

- 未启用项目代理时，OpenAI 兼容 LLM 客户端构造不得读取系统代理环境变量。
- 修复应集中在 LLM adapter 边界，避免在每个生成阶段复制环境变量处理。
- 不改变现有 `base_url` 规范化、API Key、模型名、温度、超时等 LLM 参数行为。
- 不记录 API Key、私有 Base URL、完整配置或小说正文。
- 需要新增测试覆盖 `ALL_PROXY=socks://...` 等系统环境存在时，构造 OpenAI 兼容 adapter 不再抛出代理 scheme 校验错误。
- 显式项目代理能力暂不扩展；如果未来需要支持项目代理，应另行设计如何把 `proxy_setting` 传入 adapter，而不是依赖系统环境变量。

## Acceptance Criteria

- [ ] 在 `ALL_PROXY=socks://127.0.0.1:10808` 等系统代理环境存在时，创建 OpenAI 兼容 LLM adapter 不再因 `Unknown scheme for proxy URL` 失败。
- [ ] 生成任务后台执行继续使用同一个 LLM adapter 工厂，不需要在各阶段添加重复代理清理逻辑。
- [ ] 相关自动化测试通过，至少覆盖本次代理污染回归。
- [ ] 不提交或修改真实 `config.json`、API Key、私有 Base URL 或小说输出。

## Notes

- 本任务是轻量 bugfix，PRD-only 足够；实现前仍需用户确认设计。
