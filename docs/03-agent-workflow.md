# Agent 工作流设计

## 1. 设计原则

这个项目的 Agent 不追求复杂框架，而是追求任务边界清楚。

一个好的入门 Agent 项目应该能回答：

- 用户输入是什么？
- 哪些决策交给 Dify AI 工作流？
- 哪些步骤由 FastAPI 编排？
- 哪些步骤由确定性的工具完成？
- 每一步失败后如何处理？

VideoCraft Agent 的核心思想是：Dify 负责创意和结构化脚本，FastAPI 负责流程控制，FFmpeg 负责确定性视频执行。

## 2. 总工作流

```text
用户输入产品信息和上传素材
  -> FastAPI 创建视频任务
  -> Dify Workflow 生成分镜脚本
  -> FastAPI 校验脚本 JSON
  -> 素材检索 Tool
  -> FFmpeg 视频合成 Tool
  -> FFmpeg 格式转换 Tool
  -> 前端预览和下载
```

## 3. 节点 1: FastAPI 任务创建

### 职责

接收前端输入，保存上传文件，并创建一个可查询状态的视频任务。

### 输入

```json
{
  "product_name": "AI 编程课",
  "target_audience": "想转行 AI 的程序员",
  "selling_points": ["零基础入门", "项目实战", "适合 Python 初学者"],
  "style": "科技感、快节奏",
  "duration_seconds": 15,
  "platform": "douyin",
  "uploaded_files": ["intro.mp4", "product.jpg"]
}
```

### 输出

```json
{
  "job_id": "20260608-001",
  "status": "upload_saved",
  "upload_dir": "storage/uploads/20260608-001"
}
```

### 规则

- 抖音、小红书、视频号默认 9:16。
- 15 秒默认拆成 3 段，每段 5 秒。
- 上传视频优先用于素材匹配。
- Dify API Key 只保存在后端。

## 4. 节点 2: Dify Workflow 脚本生成

### 职责

把结构化需求变成短视频分镜脚本。

### 输入

```json
{
  "product_name": "AI 编程课",
  "target_audience": "想转行 AI 的程序员",
  "selling_points": "零基础入门, 项目实战, 适合 Python 初学者",
  "style": "科技感、快节奏",
  "duration_seconds": 15,
  "platform": "douyin",
  "material_mode": "uploaded_first"
}
```

### 输出

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

### Dify 节点建议

```text
Start
  -> Dify LLM 节点: 生成短视频脚本和分镜
  -> Code: 清洗 JSON，补齐必要字段
  -> End: 输出 script_json
```

### 输出约束

- 只输出结构化 JSON。
- `scenes` 默认 3 项。
- 每段字幕不超过 16 个中文字符。
- 每段 `visual_keywords` 用英文小写关键词。
- `duration_seconds` 总和必须等于用户输入的视频时长。

### 失败兜底

如果 Dify 调用失败或 JSON 解析失败：

- FastAPI 使用内置模板脚本。
- 任务状态记录 `dify_failed_fallback_used`。
- 页面提示“Dify 脚本生成失败，已使用默认模板继续合成”。

这样可以保证项目 Demo 不会因为模型失败而完全中断。

## 5. 节点 3: 脚本校验

### 职责

FastAPI 用 Pydantic 校验 Dify 返回的脚本。

### 校验规则

- 必须有 `title`。
- 必须有 `scenes`。
- 每个 scene 必须有字幕、时长和关键词。
- 分镜总时长必须等于目标时长。
- 字幕过长时可以截断或换行。
- 关键词为空时补充默认关键词 `product`。

### 失败处理

- 可修复问题：后端自动修复并记录 warning。
- 不可修复问题：使用备用脚本或标记任务失败。

## 6. 节点 4: 素材检索 Tool

### 职责

根据分镜关键词选择视频素材。

### MVP 策略

优先级：

```text
上传视频素材
  -> 本地关键词素材库
  -> default.mp4
```

本地关键词映射：

```json
{
  "coding": "assets/videos/coding.mp4",
  "programmer": "assets/videos/coding.mp4",
  "ai": "assets/videos/ai_robot.mp4",
  "automation": "assets/videos/ai_robot.mp4",
  "office": "assets/videos/office.mp4",
  "course": "assets/videos/product.mp4",
  "product": "assets/videos/product.mp4"
}
```

### 输出

```json
[
  {
    "scene_index": 1,
    "material_path": "assets/videos/coding.mp4",
    "matched_keyword": "coding",
    "source": "library",
    "fallback_used": false
  }
]
```

### 失败兜底

- 找不到关键词匹配：使用 `default.mp4`。
- 文件不存在：提示用户补充素材，停止合成。

## 7. 节点 5: 视频合成 Tool

### 职责

调用 FFmpeg 生成最终视频。

### 输入

- `VideoScript`
- `MaterialMatch` 列表
- 背景音乐路径
- 输出目录
- 字体路径

### 输出

```json
{
  "output_path": "storage/outputs/20260608-001/final.mp4",
  "duration_seconds": 15,
  "format": "mp4",
  "status": "success"
}
```

### 执行步骤

1. 为每个 scene 生成临时片段。
2. 把素材转为 1080x1920。
3. 裁剪到 scene duration。
4. 添加字幕。
5. 拼接片段。
6. 混入背景音乐。
7. 输出 `final.mp4`。

## 8. 节点 6: 格式转换 Tool

### 职责

把已有视频转换成目标格式。

### 输入

```json
{
  "input_path": "storage/outputs/20260608-001/final.mp4",
  "target_format": "webm"
}
```

### 输出

```json
{
  "output_path": "storage/outputs/20260608-001/final.webm",
  "status": "success"
}
```

## 9. 状态机

前端可以用这些状态驱动展示：

```text
idle
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

状态由 FastAPI 维护，前端只负责轮询和展示。

## 10. Dify 与 FastAPI 的边界

MVP 推荐：

```text
FastAPI 调 Dify
```

原因：

- Dify API Key 不暴露给前端。
- FastAPI 能访问本地上传文件和 FFmpeg。
- 任务状态可以统一由后端管理。
- Dify 专注生成结构化脚本。

后续可选：

```text
Dify HTTP Request Node 调 FastAPI 渲染接口
```

这个方向需要 FastAPI 服务可被 Dify 访问，适合部署后再做。
