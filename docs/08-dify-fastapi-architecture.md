# Dify + FastAPI 架构方案

## 1. 方案定位

新版 VideoCraft Agent 采用三层架构：

```text
Python 前端
  -> FastAPI 后端
  -> Dify Workflow
  -> 本地 FFmpeg
  -> 输出视频文件
```

核心思路：

- Dify 负责 AI 能力：脚本、分镜、字幕、关键词。
- FastAPI 负责工程后端：上传文件、调用 Dify、校验 JSON、调 FFmpeg、管理任务状态。
- FFmpeg 负责视频处理：裁剪、转竖屏、拼接、加字幕、加背景音乐、格式转换。
- 前端负责交互：输入产品信息、上传素材、查看进度、预览和下载视频。

这个架构比单独 Streamlit 更清晰，也更适合面试展示“AI 工作流 + 后端服务 + 视频工程”的完整能力。

## 2. 总体架构图

```text
Browser
  |
  | 1. 输入产品信息，上传素材
  v
Python Frontend
  |
  | 2. multipart/form-data
  v
FastAPI Backend
  |
  | 3. 保存上传文件到本地 storage/uploads/{job_id}/
  |
  | 4. 调 Dify Workflow API
  v
Dify Workflow
  |
  | 5. 返回结构化 JSON 脚本
  v
FastAPI Backend
  |
  | 6. Pydantic 校验 JSON
  | 7. 本地素材匹配 / 上传素材选择
  | 8. 调 FFmpeg 渲染视频
  v
storage/outputs/{job_id}/final.mp4
  |
  | 9. 前端轮询状态，预览和下载
  v
Browser
```

## 3. 各层职责

### 3.1 Python 前端

推荐 V0 使用 Streamlit 作为 Python 前端。

页面功能：

- 产品名称输入
- 目标人群输入
- 卖点输入
- 视频风格选择
- 目标平台选择
- 视频时长选择
- 上传视频素材或产品图片
- 点击生成
- 展示任务状态
- 展示 Dify 返回的脚本 JSON
- 预览最终视频
- 下载最终 mp4

说明：

- Streamlit 适合快速做演示。
- 前端不保存 Dify API Key。
- 前端不直接调用 Dify。
- 前端只调用 FastAPI。

如果后续想做得更像正式网站，可以把 Streamlit 换成 FastAPI + Jinja2 模板，或者换成 React / Vue。

### 3.2 FastAPI 后端

FastAPI 是主控层。

它负责：

- 接收上传文件。
- 创建视频生成任务。
- 保存任务输入。
- 调用 Dify Workflow。
- 校验 Dify 输出。
- 调用素材匹配模块。
- 调用 FFmpeg 渲染模块。
- 提供任务状态查询。
- 提供视频预览和下载接口。
- 记录错误日志。

FastAPI 不负责：

- 直接写复杂 Prompt。
- 自己实现大模型能力。
- 替代 Dify 的工作流编排。

### 3.3 Dify Workflow

Dify 负责 AI 生成部分。

建议创建一个 Workflow 应用，而不是 Chatbot 应用。原因是视频生成更像“一次输入，一次结构化输出”的流程，不需要多轮聊天。

Dify 输入：

```json
{
  "product_name": "AI 编程课",
  "target_audience": "零基础转行程序员",
  "selling_points": "项目实战, AI Agent, 求职作品集",
  "style": "科技感, 快节奏",
  "platform": "抖音",
  "duration_seconds": 15,
  "material_mode": "uploaded_first"
}
```

Dify 输出：

```json
{
  "title": "AI 编程课 15 秒推广视频",
  "aspect_ratio": "9:16",
  "duration_seconds": 15,
  "scenes": [
    {
      "index": 1,
      "duration_seconds": 5,
      "subtitle": "AI Agent 时代已经来了",
      "voiceover": "AI Agent 时代已经来了，现在入门还不晚。",
      "visual_keywords": ["ai", "coding", "future"],
      "source_hint": "uploaded_or_library"
    },
    {
      "index": 2,
      "duration_seconds": 5,
      "subtitle": "用项目掌握真实开发流程",
      "voiceover": "从需求到上线，用项目掌握真实开发流程。",
      "visual_keywords": ["project", "programmer", "workflow"],
      "source_hint": "uploaded_or_library"
    },
    {
      "index": 3,
      "duration_seconds": 5,
      "subtitle": "做出能放进简历的作品",
      "voiceover": "完成后，你会拥有一个能放进简历的 AI 项目。",
      "visual_keywords": ["resume", "demo", "success"],
      "source_hint": "uploaded_or_library"
    }
  ]
}
```

Dify 工作流节点建议：

```text
Start
  -> Dify LLM 节点: 生成短视频脚本和分镜
  -> Code: 清洗 JSON，保证字段完整
  -> End: 输出 script_json
```

后续可以增加：

- Knowledge Retrieval：读取品牌资料、产品资料。
- Conditional Branch：不同平台选择不同文案风格。
- HTTP Request：调用外部素材库 API。
- Dify LLM 节点二次审核：检查字幕是否过长、是否适合短视频。

### 3.4 FFmpeg 视频执行层

FFmpeg 只做确定性视频处理。

处理步骤：

```text
选择素材
  -> 转成 9:16
  -> 裁剪每段时长
  -> 添加字幕
  -> 拼接片段
  -> 添加背景音乐
  -> 输出 final.mp4
```

MVP 推荐先使用中间文件策略：

```text
storage/jobs/{job_id}/clips/scene_1.mp4
storage/jobs/{job_id}/clips/scene_2.mp4
storage/jobs/{job_id}/clips/scene_3.mp4
storage/outputs/{job_id}/final.mp4
```

这样速度不是最快，但最容易排查问题。

## 4. 文件上传策略

用户上传的文件先进入 FastAPI，不建议前端直接上传到 Dify。

原因：

- 视频合成需要本地 FFmpeg 读取文件。
- Dify Cloud 默认不能访问你的本地路径。
- Dify API Key 不能暴露在前端。
- 大视频直接交给 Dify 处理没有必要。

推荐规则：

- 视频素材：保存在 FastAPI 本地，由 FFmpeg 使用。
- 产品图片：可以只保存在本地，也可以由 FastAPI 上传到 Dify 做视觉理解。
- 文档资料：可以由 FastAPI 上传到 Dify，作为脚本生成上下文。
- 最终视频：由 FastAPI 提供下载，不上传到 Dify。

如果需要把图片或文档传给 Dify，流程是：

```text
前端上传文件
  -> FastAPI 保存文件
  -> FastAPI 调 Dify Upload File API
  -> 获取 upload_file_id
  -> FastAPI 调 Dify Workflow API，并在 inputs 中引用 upload_file_id
```

MVP 可以先不把上传文件传给 Dify，只把用户填写的文字信息传给 Dify。

## 5. FastAPI 接口设计

### 5.1 创建生成任务

```http
POST /api/video-jobs
Content-Type: multipart/form-data
```

表单字段：

```text
product_name
target_audience
selling_points
style
platform
duration_seconds
files[]
```

响应：

```json
{
  "job_id": "20260608-001",
  "status": "queued",
  "message": "任务已创建"
}
```

### 5.2 查询任务状态

```http
GET /api/video-jobs/{job_id}
```

响应：

```json
{
  "job_id": "20260608-001",
  "status": "rendering_video",
  "current_step": "正在调用 FFmpeg 合成视频",
  "script": {
    "title": "AI 编程课 15 秒推广视频",
    "scenes": []
  },
  "video_url": null,
  "error": null
}
```

状态枚举：

```text
queued
upload_saved
calling_dify
script_ready
matching_materials
rendering_video
succeeded
failed
```

### 5.3 预览或下载视频

```http
GET /api/video-jobs/{job_id}/video
```

返回：

```text
video/mp4
```

### 5.4 格式转换

```http
POST /api/video-jobs/{job_id}/convert
```

请求：

```json
{
  "target_format": "webm"
}
```

响应：

```json
{
  "job_id": "20260608-001",
  "target_format": "webm",
  "download_url": "/api/video-jobs/20260608-001/video?format=webm"
}
```

## 6. 后端模块设计

推荐目录：

```text
video-craft-agent/
  frontend/
    streamlit_app.py

  backend/
    main.py
    api/
      video_jobs.py
    core/
      config.py
      models.py
      errors.py
    services/
      dify_client.py
      job_service.py
      video_pipeline.py
    tools/
      material_search.py
      ffmpeg_editor.py
      format_converter.py

  storage/
    uploads/
    jobs/
    outputs/

  assets/
    videos/
    music/

  docs/
```

核心模块：

```text
dify_client.py
  - run_workflow()
  - upload_file_to_dify()

job_service.py
  - create_job()
  - update_job_status()
  - get_job()

video_pipeline.py
  - generate_script_with_dify()
  - match_materials()
  - render_video()

ffmpeg_editor.py
  - normalize_clip()
  - trim_clip()
  - add_subtitle()
  - concat_clips()
  - add_background_music()
```

## 7. 配置项

`.env.example`：

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

## 8. 开发版本规划

### V0.1: AI 脚本 + FFmpeg 成片闭环

目标：第一版就接入 Dify AI。

任务：

- 在 Dify 创建 Workflow 应用。
- Workflow 输出固定 JSON。
- FastAPI 实现 `POST /api/video-jobs`。
- FastAPI 调 Dify Workflow API。
- Pydantic 校验 Dify 返回结果。
- 使用上传素材或默认素材。
- FFmpeg 输出一个 9:16 mp4。

验收：

- 用户输入产品信息后，Dify 能生成 3 段脚本。
- 后端能把脚本转成字幕。
- 最终输出 `final.mp4`。

### V0.2: 上传页面 + 状态展示

目标：用户不用命令行也能操作。

任务：

- Streamlit 表单。
- 上传视频素材。
- 调 FastAPI 创建任务。
- 轮询任务状态。
- 展示脚本 JSON。
- 预览和下载视频。

验收：

- 页面可输入、上传、生成、预览、下载。

### V0.3: 稳定性和兜底

目标：从能跑变成稳定可演示。

任务：

- Dify 调用失败时使用备用脚本。
- Dify JSON 不合法时自动修复或报错。
- 上传文件类型校验。
- FFmpeg stderr 记录到日志。
- 字幕过长时自动截断或换行。

验收：

- 常见错误不会让服务直接崩溃。
- 页面能显示明确错误原因。

### V0.4: 格式转换和模板化

目标：增强视频工具属性。

任务：

- mp4 转 webm / mov / gif。
- 支持不同平台模板。
- 支持不同视频风格模板。
- 支持背景音乐选择。

验收：

- 能展示“视频工具集成能力”，不只是 Dify 文案生成。

### V0.5: 可选升级

可选方向：

- Dify Knowledge Base：上传产品资料后生成更贴近品牌的脚本。
- Dify HTTP Request 节点：让 Dify 反向调用 FastAPI 渲染接口。
- 素材向量检索：用 CLIP / embedding 匹配素材。
- 任务队列：用 Redis Queue / Celery 支持并发。
- 历史记录：用 SQLite 保存任务。

## 9. 关键技术决策

### 9.1 为什么 FastAPI 调 Dify，而不是 Dify 调 FastAPI

MVP 推荐 FastAPI 调 Dify。

原因：

- Dify API Key 放在服务端更安全。
- FastAPI 能直接访问本地上传文件和 FFmpeg。
- 后端能统一管理任务状态。
- Dify 只负责生成结构化脚本，边界更清楚。

后期如果想展示 Dify 的工具调用能力，可以使用 Dify HTTP Request 节点调用 FastAPI：

```text
Dify Workflow
  -> HTTP Request: POST /api/internal/render-video
  -> FastAPI 渲染视频
  -> Dify 返回视频下载链接
```

但这需要 FastAPI 服务能被 Dify 访问，例如部署到公网服务器，或者开发时用 ngrok 暴露本地地址。

### 9.2 为什么上传视频不直接交给 Dify

视频剪辑不是 Dify 的核心能力。

上传视频主要是给 FFmpeg 使用：

- 裁剪
- 拼接
- 转码
- 加字幕
- 加音乐

Dify 更适合根据文字、图片或资料生成“要怎么剪”的结构化指令，而不是直接完成本地剪辑。

### 9.3 为什么 Dify 输出必须是 JSON

FastAPI 和 FFmpeg 需要确定的数据结构。

如果 Dify 只输出自然语言，后端很难稳定知道：

- 有几段分镜。
- 每段多长。
- 字幕是什么。
- 应该匹配什么素材。
- 最终视频比例是什么。

所以 Dify 输出必须是严格 JSON，并由 Pydantic 校验。

## 10. 主要风险和处理

| 风险 | 表现 | 处理 |
| --- | --- | --- |
| Dify 输出不是合法 JSON | 后端解析失败 | Prompt 强约束 + Dify Code 节点清洗 + Pydantic 校验 |
| Dify 调用超时 | 生成任务卡住 | 脚本生成用 blocking，长任务改 streaming 或轮询 |
| FFmpeg 字体问题 | 中文字幕不显示 | 配置 `FONT_PATH`，默认使用微软雅黑 |
| 上传素材太短 | 某段无法裁剪够时长 | 循环素材或 fallback 到默认素材 |
| 上传素材比例不对 | 画面拉伸或黑边 | FFmpeg 统一裁剪为 1080x1920 |
| 视频生成时间长 | 页面无响应 | 前端轮询任务状态，后端异步执行 |
| API Key 泄露 | 用户看到密钥 | Dify API Key 只存在 `.env` 和后端 |

## 11. 面试表达

可以这样介绍：

> 这个项目采用 Dify + FastAPI + FFmpeg 的架构。Dify 负责 AI 工作流，生成营销短视频的结构化分镜脚本；FastAPI 负责接收上传素材、调用 Dify、校验脚本、管理任务状态；FFmpeg 负责实际的视频裁剪、转竖屏、拼接、加字幕和导出。这样设计的原因是把不确定的 AI 生成和确定性的视频工程分开，既能利用 Dify 的低代码 AI 编排能力，也能体现后端服务和本地视频处理能力。

## 12. 参考文档

- Dify Run Workflow API: https://docs.dify.ai/api-reference/workflows/run-workflow
- Dify Upload File API: https://docs.dify.ai/api-reference/files/upload-file
- Dify HTTP Request Node: https://docs.dify.ai/en/use-dify/nodes/http-request
