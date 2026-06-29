from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from novel_generator.architecture import Novel_architecture_generate
from novel_generator.blueprint import Chapter_blueprint_generate
from novel_generator.chapter import generate_chapter_draft
from novel_generator.finalization import enrich_chapter_text, finalize_chapter
from consistency_checker import check_consistency


GenerationStage = Literal[
    "architecture",
    "directory",
    "draft",
    "finalization",
    "consistency",
    "batch",
    "batchDraft",
    "batchFinalization",
    "batchConsistency",
]
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


def run_generation_job(
    config: dict[str, Any],
    stage: GenerationStage,
    output_path: Path,
    *,
    chapter_number: int | None = None,
    auto_enrich: bool = False,
    minimum_words: int | None = None,
    target_words: int | None = None,
    start_chapter: int | None = None,
    end_chapter: int | None = None,
) -> GenerationExecutionResult:
    log = [f"开始执行真实生成阶段：{stage}"]
    try:
        if stage == "architecture":
            _run_architecture(config, output_path, log)
        elif stage == "directory":
            _run_directory(config, output_path, log)
        elif stage == "draft":
            _run_draft(config, output_path, log, chapter_number)
        elif stage == "finalization":
            _run_finalization(
                config,
                output_path,
                log,
                chapter_number,
                auto_enrich=auto_enrich,
                minimum_words=minimum_words,
                target_words=target_words,
            )
        elif stage == "consistency":
            _run_consistency(config, output_path, log, chapter_number)
        elif stage == "batchDraft":
            return _run_batch_draft(
                config,
                output_path,
                log,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
            )
        elif stage in {"batch", "batchFinalization"}:
            return _run_batch_finalization(
                config,
                output_path,
                log,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                auto_enrich=auto_enrich,
                minimum_words=minimum_words,
                target_words=target_words,
            )
        elif stage == "batchConsistency":
            return _run_batch_consistency(
                config,
                output_path,
                log,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
            )
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


def _run_draft(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    chapter_number: int | None,
) -> None:
    params = _legacy_params(config)
    llm_config = _stage_llm_config(config, "prompt_draft_llm", "生成章节草稿")
    embedding_config = _embedding_config(config)
    output_path.mkdir(parents=True, exist_ok=True)

    novel_number = _chapter_number(chapter_number, params)
    word_number = _positive_int(params.get("word_number"), "每章字数必须大于 0")
    _require_non_empty_file(output_path / DIRECTORY_FILENAME, "请先生成章节目录")

    log.append(f"正在生成第 {novel_number} 章草稿")
    generate_chapter_draft(
        api_key=str(llm_config.get("api_key") or ""),
        base_url=str(llm_config.get("base_url") or ""),
        model_name=str(llm_config.get("model_name") or ""),
        filepath=str(output_path),
        novel_number=novel_number,
        word_number=word_number,
        temperature=float(llm_config.get("temperature") or 0.7),
        user_guidance=str(params.get("user_guidance") or ""),
        characters_involved=str(params.get("characters_involved") or ""),
        key_items=str(params.get("key_items") or ""),
        scene_location=str(params.get("scene_location") or ""),
        time_constraint=str(params.get("time_constraint") or ""),
        embedding_api_key=str(embedding_config.get("api_key") or ""),
        embedding_url=str(embedding_config.get("base_url") or ""),
        embedding_interface_format=str(embedding_config.get("interface_format") or ""),
        embedding_model_name=str(embedding_config.get("model_name") or ""),
        embedding_retrieval_k=int(embedding_config.get("retrieval_k") or 4),
        interface_format=str(llm_config.get("interface_format") or ""),
        max_tokens=int(llm_config.get("max_tokens") or 2048),
        timeout=int(llm_config.get("timeout") or 600),
    )

    legacy_path = _require_non_empty_file(_legacy_chapter_path(output_path, novel_number), "章节草稿生成结果为空")
    _sync_file(legacy_path, _frontend_chapter_path(output_path, novel_number))
    log.append(f"已写入 chapter_{novel_number}.txt，并同步 legacy chapters/ 目录")


def _run_finalization(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    chapter_number: int | None,
    *,
    auto_enrich: bool,
    minimum_words: int | None,
    target_words: int | None,
) -> None:
    params = _legacy_params(config)
    llm_config = _stage_llm_config(config, "final_chapter_llm", "润色章节定稿")
    embedding_config = _embedding_config(config)
    output_path.mkdir(parents=True, exist_ok=True)

    novel_number = _chapter_number(chapter_number, params)
    configured_words = _positive_int(params.get("word_number"), "每章字数必须大于 0")
    word_number = target_words if target_words and target_words > 0 else configured_words
    frontend_path = _require_non_empty_file(
        _frontend_chapter_path(output_path, novel_number),
        "请先生成或保存章节正文",
    )
    legacy_path = _legacy_chapter_path(output_path, novel_number)
    _sync_file(frontend_path, legacy_path)

    chapter_text = legacy_path.read_text(encoding="utf-8")
    if auto_enrich and minimum_words and _count_words(chapter_text) < minimum_words:
        log.append(f"第 {novel_number} 章低于最低字数，正在扩写")
        chapter_text = enrich_chapter_text(
            chapter_text=chapter_text,
            word_number=word_number,
            api_key=str(llm_config.get("api_key") or ""),
            base_url=str(llm_config.get("base_url") or ""),
            model_name=str(llm_config.get("model_name") or ""),
            temperature=float(llm_config.get("temperature") or 0.7),
            interface_format=str(llm_config.get("interface_format") or ""),
            max_tokens=int(llm_config.get("max_tokens") or 2048),
            timeout=int(llm_config.get("timeout") or 600),
        )
        legacy_path.write_text(chapter_text, encoding="utf-8")
        _sync_file(legacy_path, frontend_path)

    log.append(f"正在定稿第 {novel_number} 章")
    finalize_chapter(
        novel_number=novel_number,
        word_number=word_number,
        api_key=str(llm_config.get("api_key") or ""),
        base_url=str(llm_config.get("base_url") or ""),
        model_name=str(llm_config.get("model_name") or ""),
        temperature=float(llm_config.get("temperature") or 0.7),
        filepath=str(output_path),
        embedding_api_key=str(embedding_config.get("api_key") or ""),
        embedding_url=str(embedding_config.get("base_url") or ""),
        embedding_interface_format=str(embedding_config.get("interface_format") or ""),
        embedding_model_name=str(embedding_config.get("model_name") or ""),
        interface_format=str(llm_config.get("interface_format") or ""),
        max_tokens=int(llm_config.get("max_tokens") or 2048),
        timeout=int(llm_config.get("timeout") or 600),
    )
    _sync_file(_require_non_empty_file(legacy_path, "定稿章节正文为空"), frontend_path)
    log.append(f"第 {novel_number} 章定稿完成，已同步章节正文、全局摘要和角色状态")


def _batch_range(start_chapter: int | None, end_chapter: int | None) -> tuple[int, int]:
    start = _positive_int(start_chapter, "批量生成章节范围无效")
    end = _positive_int(end_chapter, "批量生成章节范围无效")
    if end < start:
        raise GenerationExecutionError("批量生成章节范围无效")
    return start, end


def _run_batch_draft(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    *,
    start_chapter: int | None,
    end_chapter: int | None,
) -> GenerationExecutionResult:
    start, end = _batch_range(start_chapter, end_chapter)

    succeeded: list[int] = []
    skipped: list[int] = []
    failed: list[tuple[int, str]] = []
    log.append(f"开始批量生成草稿第 {start}-{end} 章")
    for novel_number in range(start, end + 1):
        if _frontend_chapter_path(output_path, novel_number).exists():
            skipped.append(novel_number)
            log.append(f"第 {novel_number} 章已有正文，跳过草稿生成")
            continue
        log.append(f"开始生成第 {novel_number} 章草稿")
        try:
            _run_draft(config, output_path, log, novel_number)
        except GenerationExecutionError as exc:
            message = str(exc)
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章草稿失败：{message}")
        except Exception as exc:
            message = f"生成执行失败：{exc}"
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章草稿失败：{message}")
        else:
            succeeded.append(novel_number)
            log.append(f"第 {novel_number} 章草稿成功")

    log.append(f"批量草稿完成：成功 {len(succeeded)} 章，跳过 {len(skipped)} 章，失败 {len(failed)} 章")
    if failed:
        success_label = _format_chapter_numbers(succeeded) or "无"
        failed_label = _format_chapter_numbers([chapter_number for chapter_number, _ in failed])
        error = f"批量草稿部分失败：成功章节 {success_label}；失败章节 {failed_label}"
        return GenerationExecutionResult(
            status="failed",
            progress=100,
            log=log,
            error=error,
        )

    return GenerationExecutionResult(
        status="done",
        progress=100,
        log=[*log, "真实生成执行完成"],
    )


def _run_batch_finalization(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    *,
    start_chapter: int | None,
    end_chapter: int | None,
    auto_enrich: bool,
    minimum_words: int | None,
    target_words: int | None,
) -> GenerationExecutionResult:
    start, end = _batch_range(start_chapter, end_chapter)

    succeeded: list[int] = []
    failed: list[tuple[int, str]] = []
    log.append(f"开始批量定稿第 {start}-{end} 章")
    for novel_number in range(start, end + 1):
        log.append(f"开始定稿第 {novel_number} 章")
        try:
            _run_finalization(
                config,
                output_path,
                log,
                novel_number,
                auto_enrich=auto_enrich,
                minimum_words=minimum_words,
                target_words=target_words,
            )
        except GenerationExecutionError as exc:
            message = str(exc)
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章定稿失败：{message}")
        except Exception as exc:
            message = f"生成执行失败：{exc}"
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章定稿失败：{message}")
        else:
            succeeded.append(novel_number)
            log.append(f"第 {novel_number} 章定稿成功")

    log.append(f"批量定稿完成：成功 {len(succeeded)} 章，失败 {len(failed)} 章")
    if failed:
        success_label = _format_chapter_numbers(succeeded) or "无"
        failed_label = _format_chapter_numbers([chapter_number for chapter_number, _ in failed])
        error = f"批量定稿部分失败：成功章节 {success_label}；失败章节 {failed_label}"
        return GenerationExecutionResult(
            status="failed",
            progress=100,
            log=log,
            error=error,
        )

    return GenerationExecutionResult(
        status="done",
        progress=100,
        log=[*log, "真实生成执行完成"],
    )


def _run_batch_consistency(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    *,
    start_chapter: int | None,
    end_chapter: int | None,
) -> GenerationExecutionResult:
    start, end = _batch_range(start_chapter, end_chapter)

    succeeded: list[int] = []
    failed: list[tuple[int, str]] = []
    log.append(f"开始批量审校第 {start}-{end} 章")
    for novel_number in range(start, end + 1):
        log.append(f"开始审校第 {novel_number} 章")
        try:
            _run_consistency(config, output_path, log, novel_number)
        except GenerationExecutionError as exc:
            message = str(exc)
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章审校失败：{message}")
        except Exception as exc:
            message = f"生成执行失败：{exc}"
            failed.append((novel_number, message))
            log.append(f"第 {novel_number} 章审校失败：{message}")
        else:
            succeeded.append(novel_number)
            log.append(f"第 {novel_number} 章审校成功")

    log.append(f"批量审校完成：成功 {len(succeeded)} 章，失败 {len(failed)} 章")
    if failed:
        success_label = _format_chapter_numbers(succeeded) or "无"
        failed_label = _format_chapter_numbers([chapter_number for chapter_number, _ in failed])
        error = f"批量审校部分失败：成功章节 {success_label}；失败章节 {failed_label}"
        return GenerationExecutionResult(
            status="failed",
            progress=100,
            log=log,
            error=error,
        )

    return GenerationExecutionResult(
        status="done",
        progress=100,
        log=[*log, "真实生成执行完成"],
    )


def _run_consistency(
    config: dict[str, Any],
    output_path: Path,
    log: list[str],
    chapter_number: int | None,
) -> None:
    params = _legacy_params(config)
    llm_config = _stage_llm_config(config, "consistency_review_llm", "一致性审校")

    novel_number = _chapter_number(chapter_number, params)
    novel_setting = _read_first_non_empty_file(
        [
            output_path / FRONTEND_SETTING_FILENAME,
            output_path / ARCHITECTURE_FILENAME,
        ],
        "请先准备小说设定",
    )
    chapter_text = _read_required_file(
        _frontend_chapter_path(output_path, novel_number),
        "请先生成或保存章节正文",
    )
    character_state = _read_optional_file(output_path / "character_state.txt")
    global_summary = _read_optional_file(output_path / "global_summary.txt")
    plot_arcs = _read_optional_file(output_path / "plot_arcs.txt")

    log.append(f"正在审校第 {novel_number} 章")
    log.append("已读取小说设定、角色状态、全局摘要、剧情要点和章节正文")
    result = check_consistency(
        novel_setting=novel_setting,
        character_state=character_state,
        global_summary=global_summary,
        chapter_text=chapter_text,
        api_key=str(llm_config.get("api_key") or ""),
        base_url=str(llm_config.get("base_url") or ""),
        model_name=str(llm_config.get("model_name") or ""),
        temperature=float(llm_config.get("temperature") or 0.3),
        plot_arcs=plot_arcs,
        interface_format=str(llm_config.get("interface_format") or ""),
        max_tokens=int(llm_config.get("max_tokens") or 2048),
        timeout=int(llm_config.get("timeout") or 600),
    )
    result = result.strip()
    if not result:
        raise GenerationExecutionError("一致性审校结果为空")
    log.append("一致性审校结果：")
    log.append(result)


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


def _embedding_config(config: dict[str, Any]) -> dict[str, Any]:
    embedding_configs = config.get("embedding_configs") or {}
    if not isinstance(embedding_configs, dict) or not embedding_configs:
        return {}

    selected_name = str(config.get("last_embedding_interface_format") or "").strip()
    if selected_name and isinstance(embedding_configs.get(selected_name), dict):
        return embedding_configs[selected_name]

    first_config = next((item for item in embedding_configs.values() if isinstance(item, dict)), None)
    return first_config or {}


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


def _read_required_file(path: Path, message: str) -> str:
    _require_non_empty_file(path, message)
    return path.read_text(encoding="utf-8").strip()


def _read_first_non_empty_file(paths: list[Path], message: str) -> str:
    for path in paths:
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                return content
    raise GenerationExecutionError(message)


def _read_optional_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _chapter_number(chapter_number: int | None, params: dict[str, Any]) -> int:
    value = chapter_number if chapter_number is not None else params.get("chapter_num")
    return _positive_int(value, "章节号必须大于 0")


def _frontend_chapter_path(output_path: Path, chapter_number: int) -> Path:
    return output_path / f"chapter_{chapter_number}.txt"


def _legacy_chapter_path(output_path: Path, chapter_number: int) -> Path:
    return output_path / "chapters" / f"chapter_{chapter_number}.txt"


def _sync_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _count_words(content: str) -> int:
    return len("".join(content.split()))


def _format_chapter_numbers(chapter_numbers: list[int]) -> str:
    return "、".join(str(chapter_number) for chapter_number in chapter_numbers)
