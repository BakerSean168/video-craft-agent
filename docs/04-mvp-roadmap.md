# MVP 开发计划

## 1. 总体节奏

推荐用 5 天完成一个可演示版本。主线是先跑通 Dify AI 脚本和 FFmpeg 成片闭环，再补前端体验和稳定性。

```text
Day 1: Dify Workflow + FastAPI 项目骨架
Day 2: FastAPI 调 Dify，拿到结构化脚本 JSON
Day 3: 上传素材 + FFmpeg 合成 mp4
Day 4: Python 前端 + 状态展示 + 视频预览
Day 5: 格式转换 + 错误处理 + 面试材料
```

如果时间更紧，可以压缩为 3 天：

```text
Day 1: Dify Workflow + FastAPI 调用闭环
Day 2: FFmpeg 根据脚本合成视频
Day 3: 前端上传、预览、下载和文档包装
```

## 2. 第 0 阶段: 环境准备

目标：确保本机能跑 Python、FastAPI、FFmpeg，并且 Dify Workflow 可以被 API 调用。

任务：

- 安装 Python 3.11+。
- 安装 FFmpeg。
- 确认命令行可执行 `ffmpeg -version`。
- 准备 Dify 账号和 Workflow 应用。
- 获取 Dify API Key。
- 准备 4 到 5 个测试视频素材。
- 准备 1 个背景音乐文件。

验收：

- 能看到 FFmpeg 版本。
- Dify Workflow 能在 Dify 网站内运行。
- `assets/videos/` 下有可用 mp4 文件。

## 3. 第 1 阶段: Dify Workflow

目标：让 Dify 能根据产品信息输出稳定的分镜脚本 JSON。

任务：

- 创建 Dify Workflow 应用。
- 设置输入字段：产品名称、目标人群、卖点、风格、平台、时长。
- 添加 Dify LLM 节点生成短视频脚本。
- 添加 Code 节点清洗 JSON。
- End 节点输出 `script_json`。
- 在 Dify 控制台测试多组输入。

验收：

- 输入产品信息后，输出 3 段脚本。
- 每段有字幕、旁白、时长和 `visual_keywords`。
- 输出格式可以被后端 JSON 解析。

## 4. 第 2 阶段: FastAPI 项目骨架

目标：建立清晰后端目录和基础接口。

任务：

- 创建 `requirements.txt`。
- 创建 `.env.example`。
- 创建 `backend/main.py`。
- 创建 `backend/api/video_jobs.py`。
- 创建 `backend/core/config.py`。
- 创建 `backend/core/models.py`。
- 创建 `backend/services/dify_client.py`。
- 创建 `backend/services/job_service.py`。
- 创建 `backend/services/video_pipeline.py`。
- 创建 `backend/tools/ffmpeg_editor.py`。
- 创建 `backend/tools/material_search.py`。

验收：

- FastAPI 可以启动。
- `GET /health` 返回正常。
- Python 文件可以正常 import。

## 5. 第 3 阶段: FastAPI 调 Dify

目标：后端能够调用 Dify Workflow 并校验脚本。

任务：

- 在 `.env` 配置 `DIFY_API_BASE` 和 `DIFY_API_KEY`。
- 实现 `run_workflow()`。
- 实现 `POST /api/video-jobs`。
- 把用户输入转换为 Dify inputs。
- 用 Pydantic 校验 Dify 返回脚本。
- 增加 Dify 失败兜底脚本。

验收：

- 调用 `POST /api/video-jobs` 后能拿到 job_id。
- 后端能获得 Dify 生成的脚本。
- Dify 失败时不会导致服务崩溃。

## 6. 第 4 阶段: 上传素材和素材匹配

目标：让用户上传素材，并让系统为每个分镜选择素材。

任务：

- 支持 multipart 文件上传。
- 保存上传文件到 `storage/uploads/{job_id}/`。
- 定义关键词映射表。
- 实现 `match_materials(script, uploads)`。
- 上传素材优先，本地素材库兜底。
- 缺失文件给出明确错误。

验收：

- 可以上传视频素材。
- 每个 scene 都能匹配到一个素材。
- 未命中关键词时使用 `default.mp4`。

## 7. 第 5 阶段: FFmpeg 合成闭环

目标：根据 Dify 生成的脚本合成视频。

任务：

- 编写 `normalize_clip`。
- 编写 `trim_clip`。
- 编写 `add_subtitle`。
- 编写 `concat_clips`。
- 编写 `add_background_music`。
- 输出 `storage/outputs/{job_id}/final.mp4`。

验收：

- 输入 3 个素材和 Dify 脚本。
- 输出 1 个 15 秒左右竖屏 mp4。
- 视频能正常播放。
- 字幕能显示。

## 8. 第 6 阶段: Python 前端

目标：做出可演示界面。

页面模块：

- 产品信息输入区。
- 风格和平台选择。
- 文件上传。
- 生成按钮。
- 状态展示。
- 脚本预览。
- 视频预览。
- 下载按钮。
- 格式转换入口。

验收：

- 不需要命令行操作即可生成视频。
- 页面能展示当前进度。
- 生成后能预览和下载。

## 9. 第 7 阶段: 格式转换

目标：补齐 JD 中的视频工具集成能力。

任务：

- 上传视频或选择输出视频。
- 选择目标格式。
- 调用 FFmpeg 转换。
- 提供下载。

验收：

- mp4 能转换为 webm。
- mp4 能转换为 gif。
- 失败时展示错误原因。

## 10. 第 8 阶段: 错误处理和项目包装

目标：从“能跑”变成“像一个工程项目”。

任务：

- 增加日志。
- 捕获常见异常。
- 整理 README。
- 增加截图或录屏。
- 写项目复盘。
- 准备简历描述。

验收：

- 常见错误有明确提示。
- README 能指导别人运行。
- 面试时能 3 分钟讲清项目价值。

## 11. 优先级

P0 必须完成：

- Dify 生成脚本。
- FastAPI 调用 Dify。
- 上传素材或使用本地素材。
- FFmpeg 合成 mp4。
- 前端演示。

P1 尽量完成：

- 字幕样式。
- 背景音乐。
- 格式转换。
- 错误处理。
- 任务状态轮询。

P2 后续增强：

- Dify Knowledge Base。
- Dify HTTP Request Node。
- 文生视频模型。
- 语音合成。
- 向量检索素材。
- 任务队列。
- 模板库。

## 12. 每日学习重点

Day 1 学会：

- Dify Workflow 基础。
- FastAPI 项目结构。
- 环境变量配置。

Day 2 学会：

- 后端调用 Dify API。
- JSON 输出与 Pydantic 校验。
- AI 失败兜底。

Day 3 学会：

- Python 调用 FFmpeg。
- 文件路径和临时文件管理。
- 视频比例、编码、容器格式。

Day 4 学会：

- 前端上传文件。
- 前端调用 FastAPI。
- 任务状态展示。

Day 5 学会：

- 项目包装。
- 面试表达。
- 后续架构升级思路。
