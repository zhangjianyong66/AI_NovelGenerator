from pathlib import Path
from datetime import datetime
import json
import os
import re
import shutil
import tempfile
from uuid import uuid4
from typing import Any

import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from chapter_directory_parser import get_chapter_info_from_blueprint


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config.json"
REQUEST_TIMEOUT = (5, 30)
LOCAL_FRONTEND_ORIGIN_REGEX = r"^http://(127\.0\.0\.1|localhost):\d+$"


class NovelParams(BaseModel):
    topic: str = ""
    genre: str = ""
    numChapters: int = Field(default=0, ge=0)
    wordNumber: int = Field(default=0, ge=0)
    chapterNum: str = ""
    userGuidance: str = ""
    charactersInvolved: str = ""
    keyItems: str = ""
    sceneLocation: str = ""
    timeConstraint: str = ""


class ProjectConfig(BaseModel):
    outputPath: str = ""
    novelParams: NovelParams = Field(default_factory=NovelParams)


class ProjectSummary(BaseModel):
    id: str
    title: str
    genre: str
    status: str
    summary: str
    updatedAt: str
    chaptersTotal: int
    chaptersCompleted: int


class LlmConfigItem(BaseModel):
    name: str
    apiKey: str = ""
    hasApiKey: bool = False
    baseUrl: str = ""
    modelName: str = ""
    temperature: float = 0.7
    maxTokens: int = Field(default=4096, ge=0)
    timeout: int = Field(default=600, ge=0)
    interfaceFormat: str = "OpenAI"


class EmbeddingConfigItem(BaseModel):
    name: str
    apiKey: str = ""
    hasApiKey: bool = False
    baseUrl: str = ""
    modelName: str = ""
    retrievalK: int = Field(default=4, ge=0)
    interfaceFormat: str = "OpenAI"


class ProxySetting(BaseModel):
    proxyUrl: str = ""
    proxyPort: str = ""
    enabled: bool = False


class StageModelSelection(BaseModel):
    promptDraft: str = ""
    chapterOutline: str = ""
    architecture: str = ""
    finalChapter: str = ""
    consistencyReview: str = ""


class ModelSettings(BaseModel):
    selectedLlmConfig: str = ""
    selectedEmbeddingConfig: str = ""
    llmConfigs: list[LlmConfigItem] = Field(default_factory=list)
    embeddingConfigs: list[EmbeddingConfigItem] = Field(default_factory=list)
    proxySetting: ProxySetting = Field(default_factory=ProxySetting)
    stageModelSelection: StageModelSelection = Field(default_factory=StageModelSelection)


class ConfigTestRequest(BaseModel):
    configName: str


class ConfigTestResult(BaseModel):
    success: bool
    message: str


class ProjectFile(BaseModel):
    id: str
    label: str
    filename: str
    content: str
    wordCount: int
    exists: bool


class ProjectFileSaveRequest(BaseModel):
    content: str = ""


class Chapter(BaseModel):
    id: str
    projectId: str
    order: int
    title: str
    status: str
    words: int
    synopsis: str
    content: str
    viewpoint: str
    updatedAt: str


class ChapterSaveRequest(BaseModel):
    content: str = ""


class GenerationJob(BaseModel):
    id: str
    projectId: str
    title: str
    stage: str
    status: str
    progress: int
    startedAt: str
    log: list[str]
    error: str | None = None


class GenerationJobCreateRequest(BaseModel):
    projectId: str = "current"
    stage: str
    chapterNumber: int | None = None
    startChapter: int | None = None
    endChapter: int | None = None
    targetWords: int | None = None
    minimumWords: int | None = None
    autoEnrich: bool = False


class OperationResult(BaseModel):
    success: bool
    message: str


class KnowledgeImportRequest(BaseModel):
    filePath: str


class KnowledgeItem(BaseModel):
    id: str
    type: str
    name: str
    description: str
    tags: list[str]
    updatedAt: str


class PlotArcsResponse(BaseModel):
    exists: bool
    content: str
    wordCount: int


class RoleSummary(BaseModel):
    id: str
    category: str
    name: str
    filename: str
    wordCount: int


class RoleCategory(BaseModel):
    name: str
    roles: list[RoleSummary]


class RoleDetail(RoleSummary):
    content: str


class RoleSaveRequest(BaseModel):
    content: str = ""


class RoleImportRequest(BaseModel):
    category: str
    filePath: str


class WebDavConfig(BaseModel):
    webdavUrl: str = ""
    username: str = ""
    password: str = ""
    hasPassword: bool = False


CORE_PROJECT_FILES = {
    "novelSetting": ("小说设定", "Novel_setting.txt"),
    "novelDirectory": ("目录蓝图", "Novel_directory.txt"),
    "characterState": ("角色状态", "character_state.txt"),
    "globalSummary": ("全局摘要", "global_summary.txt"),
}

GENERATION_STAGE_TITLES = {
    "architecture": "生成小说设定",
    "directory": "生成章节目录",
    "draft": "生成章节草稿",
    "finalization": "润色章节定稿",
    "consistency": "一致性审校",
    "batch": "批量生成草稿",
}

CHAPTER_GENERATION_STAGES = {"draft", "finalization", "consistency"}


def _default_config() -> dict[str, Any]:
    return {
        "other_params": {
            "topic": "",
            "genre": "",
            "num_chapters": 0,
            "word_number": 0,
            "filepath": "",
            "chapter_num": "",
            "user_guidance": "",
            "characters_involved": "",
            "key_items": "",
            "scene_location": "",
            "time_constraint": "",
        }
    }


def _default_output_path(config_file: Path) -> Path:
    return config_file.parent / "output"


def _load_config(config_file: Path) -> dict[str, Any]:
    if not config_file.exists():
        config = _default_config()
        default_output_path = _default_output_path(config_file)
        config["other_params"]["filepath"] = str(default_output_path)
        default_output_path.mkdir(parents=True, exist_ok=True)
        _save_config(config_file, config)
        return config

    with config_file.open("r", encoding="utf-8") as file:
        config = json.load(file)

    params = config.setdefault("other_params", {})
    if not str(params.get("filepath") or "").strip():
        default_output_path = _default_output_path(config_file)
        params["filepath"] = str(default_output_path)
        default_output_path.mkdir(parents=True, exist_ok=True)
        _save_config(config_file, config)
    return config


def _save_config(config_file: Path, config: dict[str, Any]) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=".json", dir=str(config_file.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
        os.replace(temp_path, config_file)
    except Exception:
        os.unlink(temp_path)
        raise


def _count_words(content: str) -> int:
    return len("".join(content.split()))


def _active_output_path(config_path: Path) -> Path:
    filepath = (_load_config(config_path).get("other_params") or {}).get("filepath") or ""
    if not str(filepath).strip():
        raise HTTPException(status_code=400, detail="请先设置项目输出路径")
    return Path(filepath)


def _project_summary(config_path: Path) -> ProjectSummary:
    config = _load_config(config_path)
    params = config.get("other_params") or {}
    output_path = _active_output_path(config_path)
    chapter_numbers = _list_chapter_numbers(output_path)
    title = str(params.get("topic") or output_path.name or "当前项目")
    configured_chapters = int(params.get("num_chapters") or 0)
    chapters_total = configured_chapters or len(chapter_numbers)
    return ProjectSummary(
        id="current",
        title=title,
        genre=str(params.get("genre") or ""),
        status="active",
        summary=str(output_path),
        updatedAt="",
        chaptersTotal=chapters_total,
        chaptersCompleted=len(chapter_numbers),
    )


def _project_file_response(file_id: str, output_path: Path) -> ProjectFile:
    if file_id not in CORE_PROJECT_FILES:
        raise HTTPException(status_code=404, detail="未知项目文件")

    label, filename = CORE_PROJECT_FILES[file_id]
    file_path = output_path / filename
    exists = file_path.exists()
    content = file_path.read_text(encoding="utf-8") if exists else ""
    return ProjectFile(
        id=file_id,
        label=label,
        filename=filename,
        content=content,
        wordCount=_count_words(content),
        exists=exists,
    )


def _chapter_file_path(output_path: Path, chapter_number: int) -> Path:
    return output_path / f"chapter_{chapter_number}.txt"


def _chapter_response(
    project_id: str,
    output_path: Path,
    chapter_number: int,
    directory_blueprint: str,
) -> Chapter:
    file_path = _chapter_file_path(output_path, chapter_number)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="章节文件不存在")

    content = file_path.read_text(encoding="utf-8")
    chapter_info = get_chapter_info_from_blueprint(directory_blueprint, chapter_number)
    title = str(chapter_info.get("chapter_title") or f"第{chapter_number}章")
    synopsis = str(chapter_info.get("chapter_summary") or "")
    return Chapter(
        id=f"chapter-{chapter_number}",
        projectId=project_id,
        order=chapter_number,
        title=title,
        status="draft",
        words=_count_words(content),
        synopsis=synopsis,
        content=content,
        viewpoint="",
        updatedAt="",
    )


def _list_chapter_numbers(output_path: Path) -> list[int]:
    chapter_numbers: list[int] = []
    for file_path in output_path.glob("chapter_*.txt"):
        match = re.fullmatch(r"chapter_(\d+)\.txt", file_path.name)
        if match:
            chapter_numbers.append(int(match.group(1)))
    return sorted(chapter_numbers)


def _validate_library_name(name: str) -> str:
    clean_name = name.strip()
    if not clean_name or clean_name in {".", ".."} or "/" in clean_name or "\\" in clean_name:
        raise HTTPException(status_code=400, detail="角色库名称无效")
    return clean_name


def _role_library_path(output_path: Path) -> Path:
    return output_path / "角色库"


def _role_file_path(output_path: Path, category: str, role_name: str) -> Path:
    category = _validate_library_name(category)
    role_name = _validate_library_name(role_name)
    return _role_library_path(output_path) / category / f"{role_name}.txt"


def _role_summary(category: str, file_path: Path) -> RoleSummary:
    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
    role_name = file_path.stem
    return RoleSummary(
        id=f"{category}/{role_name}",
        category=category,
        name=role_name,
        filename=file_path.name,
        wordCount=_count_words(content),
    )


def _knowledge_items(output_path: Path) -> list[KnowledgeItem]:
    items: list[KnowledgeItem] = []
    import_dir = output_path / "vectorstore" / "imported"
    if import_dir.exists():
        for file_path in sorted(path for path in import_dir.iterdir() if path.is_file()):
            items.append(
                KnowledgeItem(
                    id=f"file/{file_path.name}",
                    type="file",
                    name=file_path.name,
                    description=str(file_path.relative_to(output_path)),
                    tags=["导入文件"],
                    updatedAt="",
                )
            )

    library_path = _role_library_path(output_path)
    if library_path.exists():
        for category_path in sorted(path for path in library_path.iterdir() if path.is_dir()):
            for role_path in sorted(category_path.glob("*.txt")):
                role_name = role_path.stem
                items.append(
                    KnowledgeItem(
                        id=f"role/{category_path.name}/{role_name}",
                        type="role",
                        name=role_name,
                        description=str(role_path.relative_to(library_path)),
                        tags=["角色库", category_path.name],
                        updatedAt="",
                    )
                )
    return items


def _project_config_from_legacy(config: dict[str, Any]) -> ProjectConfig:
    params = config.get("other_params") or {}
    return ProjectConfig(
        outputPath=str(params.get("filepath") or ""),
        novelParams=NovelParams(
            topic=str(params.get("topic") or ""),
            genre=str(params.get("genre") or ""),
            numChapters=int(params.get("num_chapters") or 0),
            wordNumber=int(params.get("word_number") or 0),
            chapterNum=str(params.get("chapter_num") or ""),
            userGuidance=str(params.get("user_guidance") or ""),
            charactersInvolved=str(params.get("characters_involved") or ""),
            keyItems=str(params.get("key_items") or ""),
            sceneLocation=str(params.get("scene_location") or ""),
            timeConstraint=str(params.get("time_constraint") or ""),
        ),
    )


def _merge_project_config(config: dict[str, Any], project_config: ProjectConfig) -> dict[str, Any]:
    params = config.setdefault("other_params", {})
    params.update(
        {
            "filepath": project_config.outputPath,
            "topic": project_config.novelParams.topic,
            "genre": project_config.novelParams.genre,
            "num_chapters": project_config.novelParams.numChapters,
            "word_number": project_config.novelParams.wordNumber,
            "chapter_num": project_config.novelParams.chapterNum,
            "user_guidance": project_config.novelParams.userGuidance,
            "characters_involved": project_config.novelParams.charactersInvolved,
            "key_items": project_config.novelParams.keyItems,
            "scene_location": project_config.novelParams.sceneLocation,
            "time_constraint": project_config.novelParams.timeConstraint,
        }
    )
    return config


def _model_settings_from_legacy(config: dict[str, Any]) -> ModelSettings:
    llm_configs = config.get("llm_configs") or {}
    embedding_configs = config.get("embedding_configs") or {}
    choose_configs = config.get("choose_configs") or {}
    proxy_setting = config.get("proxy_setting") or {}
    first_llm_name = next(iter(llm_configs), "")

    return ModelSettings(
        selectedLlmConfig=str(choose_configs.get("prompt_draft_llm") or first_llm_name),
        selectedEmbeddingConfig=str(
            config.get("last_embedding_interface_format") or next(iter(embedding_configs), "")
        ),
        llmConfigs=[
            LlmConfigItem(
                name=name,
                apiKey="",
                hasApiKey=bool(item.get("api_key")),
                baseUrl=str(item.get("base_url") or ""),
                modelName=str(item.get("model_name") or ""),
                temperature=float(item.get("temperature") or 0.7),
                maxTokens=int(item.get("max_tokens") or 0),
                timeout=int(item.get("timeout") or 0),
                interfaceFormat=str(item.get("interface_format") or ""),
            )
            for name, item in llm_configs.items()
        ],
        embeddingConfigs=[
            EmbeddingConfigItem(
                name=name,
                apiKey="",
                hasApiKey=bool(item.get("api_key")),
                baseUrl=str(item.get("base_url") or ""),
                modelName=str(item.get("model_name") or ""),
                retrievalK=int(item.get("retrieval_k") or 0),
                interfaceFormat=str(item.get("interface_format") or ""),
            )
            for name, item in embedding_configs.items()
        ],
        proxySetting=ProxySetting(
            proxyUrl=str(proxy_setting.get("proxy_url") or ""),
            proxyPort=str(proxy_setting.get("proxy_port") or ""),
            enabled=bool(proxy_setting.get("enabled")),
        ),
        stageModelSelection=StageModelSelection(
            promptDraft=str(choose_configs.get("prompt_draft_llm") or ""),
            chapterOutline=str(choose_configs.get("chapter_outline_llm") or ""),
            architecture=str(choose_configs.get("architecture_llm") or ""),
            finalChapter=str(choose_configs.get("final_chapter_llm") or ""),
            consistencyReview=str(choose_configs.get("consistency_review_llm") or ""),
        ),
    )


def _merge_model_settings(config: dict[str, Any], settings: ModelSettings) -> dict[str, Any]:
    old_llm_configs = config.get("llm_configs") or {}
    old_embedding_configs = config.get("embedding_configs") or {}

    selected_llm = next(
        (item for item in settings.llmConfigs if item.name == settings.selectedLlmConfig),
        settings.llmConfigs[0] if settings.llmConfigs else None,
    )
    config["last_interface_format"] = selected_llm.interfaceFormat if selected_llm else ""
    config["last_embedding_interface_format"] = settings.selectedEmbeddingConfig
    config["llm_configs"] = {
        item.name: {
            "api_key": item.apiKey or (old_llm_configs.get(item.name) or {}).get("api_key", ""),
            "base_url": item.baseUrl,
            "model_name": item.modelName,
            "temperature": item.temperature,
            "max_tokens": item.maxTokens,
            "timeout": item.timeout,
            "interface_format": item.interfaceFormat,
        }
        for item in settings.llmConfigs
    }
    config["embedding_configs"] = {
        item.name: {
            "api_key": item.apiKey or (old_embedding_configs.get(item.name) or {}).get("api_key", ""),
            "base_url": item.baseUrl,
            "model_name": item.modelName,
            "retrieval_k": item.retrievalK,
            "interface_format": item.interfaceFormat,
        }
        for item in settings.embeddingConfigs
    }
    config["proxy_setting"] = {
        "proxy_url": settings.proxySetting.proxyUrl,
        "proxy_port": settings.proxySetting.proxyPort,
        "enabled": settings.proxySetting.enabled,
    }
    config["choose_configs"] = {
        "prompt_draft_llm": settings.stageModelSelection.promptDraft,
        "chapter_outline_llm": settings.stageModelSelection.chapterOutline,
        "architecture_llm": settings.stageModelSelection.architecture,
        "final_chapter_llm": settings.stageModelSelection.finalChapter,
        "consistency_review_llm": settings.stageModelSelection.consistencyReview,
    }
    return config


def _webdav_config_from_legacy(config: dict[str, Any]) -> WebDavConfig:
    webdav_config = config.get("webdav_config") or {}
    password = str(webdav_config.get("webdav_password") or "")
    return WebDavConfig(
        webdavUrl=str(webdav_config.get("webdav_url") or ""),
        username=str(webdav_config.get("webdav_username") or ""),
        password="",
        hasPassword=bool(password),
    )


def _merge_webdav_config(config: dict[str, Any], webdav_config: WebDavConfig) -> dict[str, Any]:
    old_config = config.get("webdav_config") or {}
    config["webdav_config"] = {
        "webdav_url": webdav_config.webdavUrl,
        "webdav_username": webdav_config.username,
        "webdav_password": webdav_config.password or old_config.get("webdav_password", ""),
    }
    return config


def _webdav_runtime_config(config: dict[str, Any]) -> dict[str, str]:
    webdav_config = config.get("webdav_config") or {}
    return {
        "url": str(webdav_config.get("webdav_url") or "").rstrip("/"),
        "username": str(webdav_config.get("webdav_username") or ""),
        "password": str(webdav_config.get("webdav_password") or ""),
    }


def _webdav_remote_config_url(config: dict[str, Any]) -> str:
    runtime_config = _webdav_runtime_config(config)
    if not runtime_config["url"]:
        raise HTTPException(status_code=400, detail="WebDAV URL 不能为空")
    return f"{runtime_config['url']}/AI_Novel_Generator/config.json"


def _backup_local_config(config_path: Path) -> Path | None:
    if not config_path.exists():
        return None
    backup_dir = config_path.parent / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_dir / f"{config_path.stem}_{timestamp}_bak{config_path.suffix}"
    shutil.copy2(config_path, backup_path)
    return backup_path


def create_app(config_file: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="AI Novel Generator Local API")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=LOCAL_FRONTEND_ORIGIN_REGEX,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    config_path = Path(config_file) if config_file is not None else DEFAULT_CONFIG_FILE
    generation_jobs: dict[str, GenerationJob] = {}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": "backend",
            "service": "AI_NovelGenerator",
        }

    @app.get("/api/project-config", response_model=ProjectConfig)
    def get_project_config() -> ProjectConfig:
        return _project_config_from_legacy(_load_config(config_path))

    @app.put("/api/project-config", response_model=ProjectConfig)
    def save_project_config(project_config: ProjectConfig) -> ProjectConfig:
        config = _merge_project_config(_load_config(config_path), project_config)
        _save_config(config_path, config)
        return _project_config_from_legacy(config)

    @app.get("/api/model-settings", response_model=ModelSettings)
    def get_model_settings() -> ModelSettings:
        return _model_settings_from_legacy(_load_config(config_path))

    @app.put("/api/model-settings", response_model=ModelSettings)
    def save_model_settings(settings: ModelSettings) -> ModelSettings:
        config = _merge_model_settings(_load_config(config_path), settings)
        _save_config(config_path, config)
        return _model_settings_from_legacy(config)

    @app.get("/api/webdav-config", response_model=WebDavConfig)
    def get_webdav_config() -> WebDavConfig:
        return _webdav_config_from_legacy(_load_config(config_path))

    @app.put("/api/webdav-config", response_model=WebDavConfig)
    def save_webdav_config(webdav_config: WebDavConfig) -> WebDavConfig:
        config = _merge_webdav_config(_load_config(config_path), webdav_config)
        _save_config(config_path, config)
        return _webdav_config_from_legacy(config)

    @app.post("/api/webdav/test", response_model=OperationResult)
    def test_webdav_connection(webdav_config: WebDavConfig) -> OperationResult:
        config = _merge_webdav_config(_load_config(config_path), webdav_config)
        runtime_config = _webdav_runtime_config(config)
        if not runtime_config["url"]:
            raise HTTPException(status_code=400, detail="WebDAV URL 不能为空")
        response = requests.request(
            "PROPFIND",
            runtime_config["url"],
            headers={"Depth": "1", "User-Agent": "Python WebDAV Client", "Accept": "*/*"},
            auth=HTTPBasicAuth(runtime_config["username"], runtime_config["password"]),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        _save_config(config_path, config)
        return OperationResult(success=True, message="WebDAV 连接成功")

    @app.post("/api/webdav/backup", response_model=OperationResult)
    def backup_webdav_config() -> OperationResult:
        config = _load_config(config_path)
        runtime_config = _webdav_runtime_config(config)
        remote_url = _webdav_remote_config_url(config)
        with config_path.open("rb") as file:
            response = requests.put(
                remote_url,
                data=file,
                auth=HTTPBasicAuth(runtime_config["username"], runtime_config["password"]),
                headers={"User-Agent": "Python WebDAV Client", "Accept": "*/*"},
                timeout=REQUEST_TIMEOUT,
            )
        response.raise_for_status()
        return OperationResult(success=True, message="配置备份成功")

    @app.post("/api/webdav/restore", response_model=OperationResult)
    def restore_webdav_config() -> OperationResult:
        config = _load_config(config_path)
        runtime_config = _webdav_runtime_config(config)
        remote_url = _webdav_remote_config_url(config)
        response = requests.get(
            remote_url,
            auth=HTTPBasicAuth(runtime_config["username"], runtime_config["password"]),
            headers={"User-Agent": "Python WebDAV Client", "Accept": "*/*"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        restored_config = json.loads(response.content.decode("utf-8"))
        required_keys = {"llm_configs", "embedding_configs", "other_params", "choose_configs"}
        if not isinstance(restored_config, dict) or not required_keys.issubset(restored_config):
            raise HTTPException(status_code=400, detail="下载的配置文件格式不完整")
        _backup_local_config(config_path)
        _save_config(config_path, restored_config)
        return OperationResult(success=True, message="配置恢复成功")

    @app.post("/api/model-settings/test-llm", response_model=ConfigTestResult)
    def test_llm_config(request: ConfigTestRequest) -> ConfigTestResult:
        config = _load_config(config_path)
        llm_config = (config.get("llm_configs") or {}).get(request.configName)
        if not llm_config:
            return ConfigTestResult(success=False, message="LLM 配置不存在")
        if not llm_config.get("api_key"):
            return ConfigTestResult(success=False, message="LLM 配置缺少 API Key")
        return ConfigTestResult(success=True, message="LLM 配置已具备测试所需字段")

    @app.get("/api/projects", response_model=list[ProjectSummary])
    def list_projects() -> list[ProjectSummary]:
        return [_project_summary(config_path)]

    @app.get("/api/project-files", response_model=list[ProjectFile])
    def list_project_files() -> list[ProjectFile]:
        output_path = _active_output_path(config_path)
        return [_project_file_response(file_id, output_path) for file_id in CORE_PROJECT_FILES]

    @app.put("/api/project-files/{file_id}", response_model=ProjectFile)
    def save_project_file(file_id: str, request: ProjectFileSaveRequest) -> ProjectFile:
        if file_id not in CORE_PROJECT_FILES:
            raise HTTPException(status_code=404, detail="未知项目文件")
        output_path = _active_output_path(config_path)
        output_path.mkdir(parents=True, exist_ok=True)
        _, filename = CORE_PROJECT_FILES[file_id]
        (output_path / filename).write_text(request.content, encoding="utf-8")
        return _project_file_response(file_id, output_path)

    @app.get("/api/projects/{project_id}/chapters", response_model=list[Chapter])
    def list_chapters(project_id: str) -> list[Chapter]:
        output_path = _active_output_path(config_path)
        directory_path = output_path / "Novel_directory.txt"
        directory_blueprint = directory_path.read_text(encoding="utf-8") if directory_path.exists() else ""
        return [
            _chapter_response(project_id, output_path, chapter_number, directory_blueprint)
            for chapter_number in _list_chapter_numbers(output_path)
        ]

    @app.put("/api/chapters/{chapter_number}", response_model=Chapter)
    def save_chapter(chapter_number: int, request: ChapterSaveRequest) -> Chapter:
        output_path = _active_output_path(config_path)
        file_path = _chapter_file_path(output_path, chapter_number)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="章节文件不存在")
        file_path.write_text(request.content, encoding="utf-8")
        directory_path = output_path / "Novel_directory.txt"
        directory_blueprint = directory_path.read_text(encoding="utf-8") if directory_path.exists() else ""
        return _chapter_response("current", output_path, chapter_number, directory_blueprint)

    @app.post("/api/generation-jobs", response_model=GenerationJob)
    def create_generation_job(request: GenerationJobCreateRequest) -> GenerationJob:
        if request.stage not in GENERATION_STAGE_TITLES:
            raise HTTPException(status_code=422, detail="不支持的生成阶段")

        output_path = _active_output_path(config_path)
        extra_log: list[str] = []
        if request.stage in CHAPTER_GENERATION_STAGES:
            chapter_number = request.chapterNumber or int(
                (_load_config(config_path).get("other_params") or {}).get("chapter_num") or 0
            )
            if chapter_number <= 0 or not _chapter_file_path(output_path, chapter_number).exists():
                raise HTTPException(status_code=400, detail="章节文件不存在")
        if request.stage == "batch":
            start_chapter = request.startChapter or 0
            end_chapter = request.endChapter or 0
            if start_chapter <= 0 or end_chapter < start_chapter:
                raise HTTPException(status_code=400, detail="批量生成章节范围无效")
            missing_chapters = [
                chapter_number
                for chapter_number in range(start_chapter, end_chapter + 1)
                if not _chapter_file_path(output_path, chapter_number).exists()
            ]
            if missing_chapters:
                raise HTTPException(status_code=400, detail=f"章节文件不存在：{missing_chapters[0]}")
            extra_log.extend(
                [
                    f"章节范围：{start_chapter}-{end_chapter}",
                    (
                        f"目标字数：{request.targetWords or 0}，最低字数：{request.minimumWords or 0}，"
                        f"自动扩写：{'是' if request.autoEnrich else '否'}"
                    ),
                ]
            )

        job_id = f"job-{uuid4().hex[:12]}"
        job = GenerationJob(
            id=job_id,
            projectId=request.projectId,
            title=GENERATION_STAGE_TITLES[request.stage],
            stage=request.stage,
            status="queued",
            progress=0,
            startedAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            log=[
                f"已接收 {GENERATION_STAGE_TITLES[request.stage]} 请求",
                f"输出路径：{output_path}",
                *extra_log,
                "任务已创建，等待执行器接入",
            ],
        )
        generation_jobs[job.id] = job
        return job

    @app.get("/api/projects/{project_id}/jobs", response_model=list[GenerationJob])
    def list_generation_jobs(project_id: str) -> list[GenerationJob]:
        return [job for job in generation_jobs.values() if job.projectId == project_id]

    @app.get("/api/generation-jobs/{job_id}", response_model=GenerationJob)
    def get_generation_job(job_id: str) -> GenerationJob:
        if job_id not in generation_jobs:
            raise HTTPException(status_code=404, detail="任务不存在")
        return generation_jobs[job_id]

    @app.get("/api/knowledge", response_model=list[KnowledgeItem])
    def list_knowledge() -> list[KnowledgeItem]:
        output_path = _active_output_path(config_path)
        return _knowledge_items(output_path)

    @app.post("/api/knowledge/import", response_model=OperationResult)
    def import_knowledge_file(request: KnowledgeImportRequest) -> OperationResult:
        output_path = _active_output_path(config_path)
        source_path = Path(request.filePath)
        if not source_path.is_file():
            raise HTTPException(status_code=400, detail="知识文件不存在")

        import_dir = output_path / "vectorstore" / "imported"
        import_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, import_dir / source_path.name)
        return OperationResult(success=True, message=f"已导入 {source_path.name}")

    @app.post("/api/knowledge/clear-vectorstore", response_model=OperationResult)
    def clear_vectorstore() -> OperationResult:
        output_path = _active_output_path(config_path)
        vectorstore_path = output_path / "vectorstore"
        if vectorstore_path.exists():
            shutil.rmtree(vectorstore_path)
        return OperationResult(success=True, message="向量库已清理")

    @app.get("/api/knowledge/plot-arcs", response_model=PlotArcsResponse)
    def get_plot_arcs() -> PlotArcsResponse:
        output_path = _active_output_path(config_path)
        plot_arcs_path = output_path / "plot_arcs.txt"
        if not plot_arcs_path.exists():
            return PlotArcsResponse(exists=False, content="", wordCount=0)
        content = plot_arcs_path.read_text(encoding="utf-8")
        return PlotArcsResponse(exists=True, content=content, wordCount=_count_words(content))

    @app.get("/api/roles", response_model=list[RoleCategory])
    def list_roles() -> list[RoleCategory]:
        output_path = _active_output_path(config_path)
        library_path = _role_library_path(output_path)
        if not library_path.exists():
            return []

        categories: list[RoleCategory] = []
        for category_path in sorted(path for path in library_path.iterdir() if path.is_dir()):
            roles = [
                _role_summary(category_path.name, role_path)
                for role_path in sorted(category_path.glob("*.txt"))
            ]
            categories.append(RoleCategory(name=category_path.name, roles=roles))
        return categories

    @app.post("/api/roles/import", response_model=RoleSummary)
    def import_role(request: RoleImportRequest) -> RoleSummary:
        output_path = _active_output_path(config_path)
        category = _validate_library_name(request.category)
        source_path = Path(request.filePath)
        if not source_path.is_file() or source_path.suffix != ".txt":
            raise HTTPException(status_code=400, detail="角色文件不存在")
        role_name = _validate_library_name(source_path.stem)
        target_path = _role_file_path(output_path, category, role_name)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        return _role_summary(category, target_path)

    @app.get("/api/roles/{category}/{role_name}", response_model=RoleDetail)
    def get_role(category: str, role_name: str) -> RoleDetail:
        output_path = _active_output_path(config_path)
        role_path = _role_file_path(output_path, category, role_name)
        if not role_path.exists():
            raise HTTPException(status_code=404, detail="角色文件不存在")
        summary = _role_summary(category, role_path)
        return RoleDetail(**summary.model_dump(), content=role_path.read_text(encoding="utf-8"))

    @app.put("/api/roles/{category}/{role_name}", response_model=RoleDetail)
    def save_role(category: str, role_name: str, request: RoleSaveRequest) -> RoleDetail:
        output_path = _active_output_path(config_path)
        role_path = _role_file_path(output_path, category, role_name)
        role_path.parent.mkdir(parents=True, exist_ok=True)
        role_path.write_text(request.content, encoding="utf-8")
        summary = _role_summary(category, role_path)
        return RoleDetail(**summary.model_dump(), content=request.content)

    return app


app = create_app()
