# 技术设计

## 1. 总体架构

VideoCraft Agent 采用 Dify + FastAPI + FFmpeg 的分层架构。

```text
Python Frontend
  -> FastAPI Backend
  -> Dify Workflow
  -> Material Search
  -> FFmpeg Editor
  -> Local Storage
```

设计原则：

- Dify 负责不确定的 AI 生成：脚本、分镜、字幕、关键词。
- FastAPI 负责服务编排：上传文件、创建任务、调用 Dify、校验结果、更新状态。
- FFmpeg 负责确定性视频处理：裁剪、转竖屏、拼接、字幕、音乐、格式转换。
- Python 前端负责交互：输入、上传、状态展示、预览、下载。

## 2. 推荐技术栈

基础版：

- Python 3.11+
- Dify Workflow
- FastAPI
- Streamlit 或 FastAPI Jinja2 页面
- FFmpeg
- Pydantic
- python-dotenv
- requests 或 httpx

可选增强：

- SQLite：保存任务历史。
- Redis Queue / Celery：处理并发视频任务。
- Chroma / FAISS：素材向量检索。
- Dify Knowledge Base：接入产品资料。
- Dify HTTP Request Node：让 Dify 反向调用渲染接口。

## 3. 项目目录建议

```text
video-craft-agent/
  README.md
  .env.example
  requirements.txt

  frontend/
    streamlit_app.py

  backend/
    main.py
    api/
      __init__.py
      video_jobs.py
    core/
      __init__.py
      config.py
      models.py
      errors.py
    services/
      __init__.py
      dify_client.py
      job_service.py
      video_pipeline.py
    tools/
      __init__.py
      material_search.py
      ffmpeg_editor.py
      format_converter.py

  assets/
    videos/
      coding.mp4
      ai_robot.mp4
      office.mp4
      product.mp4
      default.mp4
    music/
      upbeat.mp3

  storage/
    uploads/
    jobs/
    outputs/

  docs/
```

## 4. 模块职责

### 4.1 frontend/streamlit_app.py

负责快速演示页面：

- 表单输入。
- 文件上传。
- 调用 FastAPI 创建任务。
- 轮询任务状态。
- 展示 Dify 脚本 JSON。
- 预览视频。
- 下载视频。
- 格式转换入口。

前端不直接调用 Dify，也不保存 Dify API Key。

### 4.2 backend/main.py

FastAPI 应用入口：

- 注册路由。
- 配置静态文件或下载接口。
- 初始化配置。
- 提供健康检查。

### 4.3 backend/api/video_jobs.py

视频任务 API：

- `POST /api/video-jobs` 创建生成任务。
- `GET /api/video-jobs/{job_id}` 查询任务状态。
- `GET /api/video-jobs/{job_id}/video` 预览或下载视频。
- `POST /api/video-jobs/{job_id}/convert` 转换格式。

### 4.4 backend/core/config.py

读取环境变量：

- `DIFY_API_BASE`
- `DIFY_API_KEY`
- `DIFY_USER`
- `FFMPEG_PATH`
- `FONT_PATH`
- `STORAGE_DIR`
- `UPLOAD_DIR`
- `OUTPUT_DIR`

### 4.5 backend/core/models.py

定义 Pydantic 数据结构：

- `VideoRequirement`
- `SceneScript`
- `VideoScript`
- `MaterialMatch`
- `RenderResult`
- `VideoJob`
- `VideoJobStatus`

### 4.6 backend/services/dify_client.py

封装 Dify 调用：

- 构造 Workflow 请求。
- 发送 `/workflows/run` 请求。
- 可选上传文件到 Dify。
- 提取 Workflow 输出。
- 处理 Dify 调用失败。

Dify API Key 只允许存在于后端环境变量中。

### 4.7 backend/services/job_service.py

管理任务状态：

- 创建 job_id。
- 保存任务输入。
- 更新任务状态。
- 读取任务结果。
- 保存错误信息。

MVP 可以用内存或本地 JSON 文件保存。后续升级为 SQLite。

### 4.8 backend/services/video_pipeline.py

串联完整流程：

```text
save_uploads
  -> call_dify_workflow
  -> validate_script
  -> match_materials
  -> render_video
  -> return_result
```

这是后端主控流程，不把编排责任放在前端，也不把视频处理责任放给 Dify。

### 4.9 backend/tools/material_search.py

素材匹配：

- 优先选择用户上传素材。
- 根据关键词查找本地素材。
- 检查文件是否存在。
- 返回素材路径。
- 未命中时 fallback 到 `default.mp4`。

MVP 使用字典映射。后续可以升级为向量检索。

### 4.10 backend/tools/ffmpeg_editor.py

FFmpeg 视频合成：

- 转竖屏。
- 裁剪片段。
- 拼接片段。
- 添加字幕。
- 添加音乐。
- 输出 mp4。

### 4.11 backend/tools/format_converter.py

FFmpeg 格式转换：

- mp4 -> webm。
- mp4 -> mov。
- mp4 -> gif。

## 5. Dify Workflow 设计

建议创建 Workflow 应用，而不是 Chatbot 应用。

节点建议：

```text
Start
  -> Dify LLM 节点: 生成短视频脚本和分镜
  -> Code: 清洗并修正 JSON
  -> End: 输出 script_json
```

输入字段：

- `product_name`
- `target_audience`
- `selling_points`
- `style`
- `platform`
- `duration_seconds`
- `material_mode`

输出字段：

- `title`
- `aspect_ratio`
- `duration_seconds`
- `scenes`

其中 `scenes` 每项包含：

- `index`
- `duration_seconds`
- `subtitle`
- `voiceover`
- `visual_keywords`
- `source_hint`

## 6. FFmpeg 合成策略

MVP 推荐使用中间文件策略，简单稳定：

1. 每个素材先转成统一规格：

```text
1080x1920, 30fps, h264, aac
```

2. 每段裁剪到固定时长。
3. 为每段加字幕。
4. 生成 concat list。
5. 拼接所有片段。
6. 加背景音乐。
7. 输出 `storage/outputs/{job_id}/final.mp4`。

优点：

- 容易排查问题。
- 每一步都有中间产物。
- 对入门者友好。

缺点：

- 速度不是最快。
- 会产生临时文件。

## 7. 字幕方案

MVP 采用 FFmpeg `drawtext`。

注意点：

- 中文字体路径需要配置。
- Windows 下字体路径可用 `C:/Windows/Fonts/msyh.ttc`。
- 字幕要短，避免溢出。
- 后端可在渲染前对过长字幕做截断或换行。

后续可以升级为 ASS 字幕，支持更丰富样式。

## 8. 配置文件

`.env.example` 建议包含：

```text
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=
DIFY_USER=video-craft-demo-user

FFMPEG_PATH=ffmpeg
FONT_PATH=C:/Windows/Fonts/msyh.ttc

STORAGE_DIR=storage
UPLOAD_DIR=storage/uploads
OUTPUT_DIR=storage/outputs

DEFAULT_VIDEO_DURATION_SECONDS=15
DEFAULT_ASPECT_RATIO=9:16
```

## 9. 日志与错误处理

建议定义统一错误：

- `DifyCallError`
- `ScriptParseError`
- `UploadFileError`
- `MaterialNotFoundError`
- `FFmpegNotFoundError`
- `VideoRenderError`
- `FormatConvertError`

页面展示简短原因，日志记录完整请求、FFmpeg 命令和 stderr。

## 10. 后续扩展

可以逐步扩展：

- 接入 Dify Knowledge Base 读取产品资料。
- 接入 ModelScope Text-to-Video 生成补充素材。
- 接入 AnimateDiff 生成动态片段。
- 接入语音合成生成旁白。
- 接入 Whisper 做字幕校准。
- 接入素材向量检索。
- 加任务历史和重新生成。
- 加任务队列支持批量生成。
- 加模板库，例如课程推广、餐饮探店、电商产品、企业介绍。
