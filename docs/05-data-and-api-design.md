# 数据结构与接口设计

## 1. 设计目标

这个项目虽然是入门 Demo，也要尽量使用结构化数据。不要让 Dify 返回一大段自然语言后再靠字符串乱切。

核心原则：

- 用户输入结构化。
- Dify Workflow 输出 JSON。
- FastAPI 用 Pydantic 校验。
- 视频任务状态统一。
- FFmpeg 工具输入输出明确。
- 错误信息统一。

## 2. VideoRequirement

表示用户提交的视频生成需求。

```json
{
  "product_name": "AI 编程课",
  "target_audience": "想转行 AI 的程序员",
  "selling_points": [
    "零基础入门 AI Agent",
    "带项目实战",
    "适合 Python 初学者"
  ],
  "style": "科技感、快节奏",
  "duration_seconds": 15,
  "platform": "douyin",
  "aspect_ratio": "9:16",
  "scene_count": 3,
  "material_mode": "uploaded_first"
}
```

字段说明：

- `product_name`: 产品名称。
- `target_audience`: 目标用户。
- `selling_points`: 核心卖点。
- `style`: 视频风格。
- `duration_seconds`: 总时长，单位秒。
- `platform`: 目标平台。
- `aspect_ratio`: 视频比例。
- `scene_count`: 分镜数量。
- `material_mode`: 素材选择策略。

## 3. SceneScript

表示 Dify 输出的一个分镜。

```json
{
  "index": 1,
  "duration_seconds": 5,
  "subtitle": "还在只会写 CRUD？",
  "voiceover": "AI Agent 时代已经来了。",
  "visual_keywords": ["coding", "programmer", "ai"],
  "source_hint": "uploaded_or_library"
}
```

字段说明：

- `index`: 分镜序号。
- `duration_seconds`: 当前分镜时长。
- `subtitle`: 屏幕字幕。
- `voiceover`: 旁白文案。
- `visual_keywords`: 用于素材匹配的关键词。
- `source_hint`: 素材来源建议。

## 4. VideoScript

表示 Dify Workflow 返回的完整脚本。

```json
{
  "title": "AI 编程课 15 秒推广视频",
  "aspect_ratio": "9:16",
  "duration_seconds": 15,
  "scenes": [
    {
      "index": 1,
      "duration_seconds": 5,
      "subtitle": "还在只会写 CRUD？",
      "voiceover": "AI Agent 时代已经来了。",
      "visual_keywords": ["coding", "programmer", "ai"],
      "source_hint": "uploaded_or_library"
    }
  ]
}
```

校验要求：

- `title` 不能为空。
- `scenes` 默认 3 项。
- 每个 scene 必须有字幕、时长和关键词。
- 每个字幕建议不超过 16 个中文字符。
- 分镜时长总和必须等于 `duration_seconds`。

## 5. UploadedMaterial

表示用户上传的素材。

```json
{
  "file_id": "upload-001",
  "original_name": "product-demo.mp4",
  "content_type": "video/mp4",
  "local_path": "storage/uploads/20260608-001/product-demo.mp4",
  "size_bytes": 10485760
}
```

字段说明：

- `file_id`: 后端生成的上传文件 ID。
- `original_name`: 原始文件名。
- `content_type`: 文件类型。
- `local_path`: 本地保存路径。
- `size_bytes`: 文件大小。

## 6. MaterialMatch

表示分镜和素材的匹配结果。

```json
{
  "scene_index": 1,
  "material_path": "assets/videos/coding.mp4",
  "matched_keyword": "coding",
  "source": "library",
  "fallback_used": false
}
```

字段说明：

- `scene_index`: 对应分镜序号。
- `material_path`: 选中的素材路径。
- `matched_keyword`: 命中的关键词。
- `source`: `uploaded`、`library` 或 `fallback`。
- `fallback_used`: 是否使用默认素材。

## 7. RenderResult

表示视频生成结果。

```json
{
  "status": "success",
  "output_path": "storage/outputs/20260608-001/final.mp4",
  "duration_seconds": 15,
  "format": "mp4",
  "message": "视频生成成功"
}
```

失败示例：

```json
{
  "status": "failed",
  "output_path": null,
  "duration_seconds": 0,
  "format": "mp4",
  "message": "FFmpeg 合成失败：未找到素材 assets/videos/coding.mp4"
}
```

## 8. VideoJob

表示一次视频生成任务。

```json
{
  "job_id": "20260608-001",
  "status": "rendering_video",
  "current_step": "正在调用 FFmpeg 合成视频",
  "requirement": {},
  "uploads": [],
  "script": {},
  "materials": [],
  "result": null,
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
converting_format
succeeded
failed
```

## 9. FastAPI 接口

### 9.1 健康检查

```http
GET /health
```

响应：

```json
{
  "status": "ok"
}
```

### 9.2 创建视频任务

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

### 9.3 查询任务状态

```http
GET /api/video-jobs/{job_id}
```

响应：

```json
{
  "job_id": "20260608-001",
  "status": "succeeded",
  "current_step": "视频生成完成",
  "script": {},
  "materials": [],
  "video_url": "/api/video-jobs/20260608-001/video",
  "error": null
}
```

### 9.4 预览或下载视频

```http
GET /api/video-jobs/{job_id}/video
```

返回：

```text
video/mp4
```

### 9.5 格式转换

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

## 10. Dify Workflow 输出约束

Workflow End 节点建议输出 `script_json` 字段。

约束：

```text
输出必须是 JSON，不要输出 Markdown。
scenes 默认 3 项。
每个 subtitle 不超过 16 个中文字符。
visual_keywords 必须使用英文小写关键词。
duration_seconds 总和必须等于用户输入的视频时长。
```

原因：

- 方便 FastAPI 解析。
- 降低 AI 输出不稳定性。
- 让素材匹配更简单。
- 让 FFmpeg 渲染流程可预测。

## 11. 后端核心服务接口

### 11.1 run_workflow

```python
def run_workflow(requirement: VideoRequirement) -> VideoScript:
    ...
```

职责：

- 构造 Dify inputs。
- 调用 Dify Workflow API。
- 提取 `script_json`。
- 返回 `VideoScript`。

### 11.2 create_job

```python
def create_job(requirement: VideoRequirement, uploads: list[UploadedMaterial]) -> VideoJob:
    ...
```

职责：

- 创建 job_id。
- 保存用户输入。
- 保存上传文件信息。
- 初始化任务状态。

### 11.3 match_materials

```python
def match_materials(script: VideoScript, uploads: list[UploadedMaterial]) -> list[MaterialMatch]:
    ...
```

职责：

- 遍历每个分镜。
- 优先选择上传素材。
- 根据关键词匹配本地素材。
- 检查文件存在。
- 返回匹配列表。

### 11.4 render_video

```python
def render_video(
    job_id: str,
    script: VideoScript,
    materials: list[MaterialMatch],
    output_path: str
) -> RenderResult:
    ...
```

职责：

- 调用 FFmpeg。
- 生成最终视频。
- 返回输出路径。

### 11.5 convert_format

```python
def convert_format(input_path: str, target_format: str) -> RenderResult:
    ...
```

职责：

- 校验输入文件。
- 调用 FFmpeg 转换格式。
- 返回转换后文件路径。

## 12. 错误码建议

```text
DIFY_CALL_FAILED
SCRIPT_PARSE_FAILED
UPLOAD_FILE_INVALID
MATERIAL_NOT_FOUND
FFMPEG_NOT_FOUND
VIDEO_RENDER_FAILED
FORMAT_CONVERT_FAILED
UNKNOWN_ERROR
```

页面展示中文提示，日志记录错误码和详细异常。
