from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from novel_generator.architecture import Novel_architecture_generate
from novel_generator.blueprint import Chapter_blueprint_generate


GenerationStage = Literal["architecture", "directory"]
GenerationStatus = Literal["done", "failed"]

ARCHITECTURE_FILENAME = "Novel_architecture.txt"
FRONTEND_SETTING_FILENAME = "Novel_setting.txt"
DIRECTORY_FILENAME = "Novel_directory.txt"


@dataclass
class GenerationExecutionResult:
    status: GenerationStatus
    progress: int
    log: list[str] = field(default_factory=list)
    error: str | None = None


class GenerationExecutionError(Exception):
    """User-facing generation precondition or execution failure."""


def run_generation_job(config: dict[str, Any], stage: GenerationStage, output_path: Path) -> GenerationExecutionResult:
    log = [f"开始执行真实生成阶段：{stage}"]
    try:
        if stage == "architecture":
            _run_architecture(config, output_path, log)
        elif stage == "directory":
            _run_directory(config, output_path, log)
        else:
            raise GenerationExecutionError("该生成阶段尚未接入真实执行器")
    except GenerationExecutionError as exc:
        message = str(exc)
        return GenerationExecutionResult(
            status="failed",
            progress=0,
            log=[*log, f"执行失败：{message}"],
            error=message,
        )
    except Exception as exc:
        message = f"生成执行失败：{exc}"
        return GenerationExecutionResult(
            status="failed",
            progress=0,
            log=[*log, message],
            error=message,
        )

    return GenerationExecutionResult(
        status="done",
        progress=100,
        log=[*log, "真实生成执行完成"],
    )


def _run_architecture(config: dict[str, Any], output_path: Path, log: list[str]) -> None:
    params = _legacy_params(config)
    llm_config = _stage_llm_config(config, "architecture_llm", "生成小说设定")
    output_path.mkdir(parents=True, exist_ok=True)

    topic = _required_text(params, "topic", "题材不能为空")
    genre = _required_text(params, "genre", "类型不能为空")
    number_of_chapters = _positive_int(params.get("num_chapters"), "章节数必须大于 0")
    word_number = _positive_int(params.get("word_number"), "每章字数必须大于 0")

    log.append("正在调用小说设定生成器")
    Novel_architecture_generate(
        interface_format=str(llm_config.get("interface_format") or ""),
        api_key=str(llm_config.get("api_key") or ""),
        base_url=str(llm_config.get("base_url") or ""),
        llm_model=str(llm_config.get("model_name") or ""),
        topic=topic,
        genre=genre,
        number_of_chapters=number_of_chapters,
        word_number=word_number,
        filepath=str(output_path),
        user_guidance=str(params.get("user_guidance") or ""),
        temperature=float(llm_config.get("temperature") or 0.7),
        max_tokens=int(llm_config.get("max_tokens") or 2048),
        timeout=int(llm_config.get("timeout") or 600),
    )

    architecture_path = _require_non_empty_file(output_path / ARCHITECTURE_FILENAME, "小说设定生成结果为空")
    frontend_setting_path = output_path / FRONTEND_SETTING_FILENAME
    frontend_setting_path.write_text(architecture_path.read_text(encoding="utf-8"), encoding="utf-8")
    log.append(f"已写入 {ARCHITECTURE_FILENAME} 和 {FRONTEND_SETTING_FILENAME}")


def _run_directory(config: dict[str, Any], output_path: Path, log: list[str]) -> None:
    params = _legacy_params(config)
    llm_config = _stage_llm_config(config, "chapter_outline_llm", "生成章节目录")
    output_path.mkdir(parents=True, exist_ok=True)
    number_of_chapters = _positive_int(params.get("num_chapters"), "章节数必须大于 0")

    architecture_path = output_path / ARCHITECTURE_FILENAME
    frontend_setting_path = output_path / FRONTEND_SETTING_FILENAME
    if not architecture_path.exists() and frontend_setting_path.exists():
        architecture_path.write_text(frontend_setting_path.read_text(encoding="utf-8"), encoding="utf-8")

    _require_non_empty_file(architecture_path, "请先生成小说设定")

    log.append("正在调用章节目录生成器")
    Chapter_blueprint_generate(
        interface_format=str(llm_config.get("interface_format") or ""),
        api_key=str(llm_config.get("api_key") or ""),
        base_url=str(llm_config.get("base_url") or ""),
        llm_model=str(llm_config.get("model_name") or ""),
        filepath=str(output_path),
        number_of_chapters=number_of_chapters,
        user_guidance=str(params.get("user_guidance") or ""),
        temperature=float(llm_config.get("temperature") or 0.7),
        max_tokens=int(llm_config.get("max_tokens") or 4096),
        timeout=int(llm_config.get("timeout") or 600),
    )

    _require_non_empty_file(output_path / DIRECTORY_FILENAME, "章节目录生成结果为空")
    log.append(f"已写入 {DIRECTORY_FILENAME}")


def _legacy_params(config: dict[str, Any]) -> dict[str, Any]:
    params = config.get("other_params") or {}
    if not isinstance(params, dict):
        raise GenerationExecutionError("项目参数格式无效")
    return params


def _stage_llm_config(config: dict[str, Any], choose_key: str, stage_label: str) -> dict[str, Any]:
    choose_configs = config.get("choose_configs") or {}
    llm_configs = config.get("llm_configs") or {}
    if not isinstance(choose_configs, dict) or not isinstance(llm_configs, dict):
        raise GenerationExecutionError("模型配置格式无效")

    config_name = str(choose_configs.get(choose_key) or "").strip()
    if not config_name:
        raise GenerationExecutionError(f"{stage_label}未选择 LLM 配置")

    llm_config = llm_configs.get(config_name)
    if not isinstance(llm_config, dict):
        raise GenerationExecutionError(f"LLM 配置不存在：{config_name}")

    if not str(llm_config.get("api_key") or "").strip():
        raise GenerationExecutionError(f"LLM 配置缺少 API Key：{config_name}")
    if not str(llm_config.get("model_name") or "").strip():
        raise GenerationExecutionError(f"LLM 配置缺少模型名称：{config_name}")
    if not str(llm_config.get("interface_format") or "").strip():
        raise GenerationExecutionError(f"LLM 配置缺少接口格式：{config_name}")

    return llm_config


def _required_text(params: dict[str, Any], key: str, message: str) -> str:
    value = str(params.get(key) or "").strip()
    if not value:
        raise GenerationExecutionError(message)
    return value


def _positive_int(value: Any, message: str) -> int:
    try:
        number = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise GenerationExecutionError(message) from exc
    if number <= 0:
        raise GenerationExecutionError(message)
    return number


def _require_non_empty_file(path: Path, message: str) -> Path:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        raise GenerationExecutionError(message)
    return path
