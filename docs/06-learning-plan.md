# 学习路线

## 1. 学习目标

这个项目不只是为了展示，而是为了让你真正学会把 AI 能力落到一个可运行的视频工具里。

完成后你应该能掌握：

- 如何用 Dify Workflow 生成结构化 AI 结果。
- 如何用 FastAPI 做后端服务和任务编排。
- 如何用 Python 管理上传文件、本地素材和输出文件。
- 如何用 FFmpeg 完成视频处理。
- 如何用 Python 前端快速做上传、状态展示、预览和下载。
- 如何解释一个 AI 项目的工程价值。

## 2. 学习顺序

建议按这个顺序学：

```text
Dify Workflow 基础
  -> JSON 输出与 Pydantic 校验
  -> FastAPI 接口和文件上传
  -> Python 文件和路径管理
  -> FFmpeg 基础
  -> FastAPI 调 FFmpeg
  -> Python 前端调用 FastAPI
  -> 项目包装和复盘
```

不要一开始就学习复杂 Agent 框架。这个项目先用 Dify 承担 AI 工作流，用 FastAPI 承担工程编排，边界更清楚。

## 3. 第 1 阶段: Dify Workflow

要学会：

- Workflow 应用和 Chatbot 应用的区别。
- Start、Dify LLM、Code、End 节点的基本用法。
- 如何设计输入字段。
- 如何约束 AI 输出 JSON。
- 如何在 Dify 控制台测试工作流。

练习任务：

- 创建一个 Workflow。
- 输入产品名称、目标人群、卖点、风格、平台、时长。
- 输出 3 段短视频分镜 JSON。

验收问题：

- 为什么这个项目更适合用 Workflow，而不是 Chatbot？
- 为什么 Dify 输出必须是 JSON？

## 4. 第 2 阶段: FastAPI 基础

要学会：

- 路由定义。
- 请求参数。
- multipart 文件上传。
- JSON 响应。
- 环境变量读取。
- 错误返回。

练习任务：

- 创建 `backend/main.py`。
- 创建 `POST /api/video-jobs`。
- 创建 `GET /api/video-jobs/{job_id}`。
- 创建 `GET /health`。

验收问题：

- 为什么 Dify API Key 只能放在后端？
- 为什么前端不应该直接调用 Dify？

## 5. 第 3 阶段: Dify API 调用

要学会：

- API Key 配置。
- 后端调用 Dify Workflow API。
- 构造 inputs。
- 解析 Workflow 输出。
- 失败重试和兜底。

练习任务：

- 实现 `dify_client.run_workflow()`。
- 把用户输入转成 Dify inputs。
- 用 Pydantic 校验 Dify 返回的脚本。

验收问题：

- Dify 调用失败时系统应该怎么处理？
- JSON 解析失败时系统应该怎么处理？

## 6. 第 4 阶段: FFmpeg 基础

要学会：

- 视频容器和编码的区别。
- mp4、mov、webm、gif 的区别。
- 分辨率和比例。
- 裁剪、缩放、拼接、加字幕。

先掌握这些命令类型：

```text
查看视频信息
裁剪视频
调整尺寸
拼接视频
添加字幕
添加音乐
转换格式
```

验收问题：

- 为什么抖音视频通常要处理成 9:16？
- FFmpeg 在项目里负责哪些确定性任务？

## 7. 第 5 阶段: 视频流水线

要学会：

- Python 调用外部命令。
- 文件路径和临时文件管理。
- 上传素材和本地素材的优先级。
- 中间文件策略。
- FFmpeg stderr 日志记录。

本项目中的视频流水线：

```text
Dify 脚本
  -> 素材匹配
  -> 转竖屏
  -> 裁剪片段
  -> 添加字幕
  -> 拼接片段
  -> 添加音乐
  -> 输出视频
```

验收问题：

- 哪些步骤必须用 AI？
- 哪些步骤不应该用 AI？
- 为什么视频合成应该交给 FFmpeg？

## 8. 第 6 阶段: Python 前端

要学会：

- 表单输入。
- 文件上传。
- 按钮触发。
- 调用 FastAPI。
- 状态展示。
- 视频预览。
- 下载按钮。

页面不要做复杂。目标是让面试官能一眼看到：

- 输入了什么。
- 上传了什么素材。
- Dify 生成了什么脚本。
- 输出了什么视频。

验收问题：

- 非技术用户能不能不用命令行完成一次生成？

## 9. 第 7 阶段: 工程化

要学会：

- 错误提示。
- 日志。
- README。
- 示例输入。
- 项目截图。
- 复盘文档。

这个阶段决定项目像不像真实项目。

验收问题：

- FFmpeg 没装时，用户看到的是什么？
- 素材缺失时，页面怎么提示？
- Dify 挂了时，项目还能不能演示？
- 视频生成很慢时，页面如何展示状态？

## 10. 进阶学习

MVP 完成后再学：

- Dify Knowledge Base。
- Dify HTTP Request Node。
- FastAPI 后台任务。
- SQLite 任务历史。
- Redis Queue / Celery。
- 向量检索素材库。
- ModelScope Text-to-Video。
- AnimateDiff。
- TTS 配音。
- Whisper 字幕对齐。

## 11. 面试前自测问题

你应该能回答：

- 这个项目解决了什么业务问题？
- 为什么选择 Dify + FastAPI + FFmpeg？
- 为什么选择先做素材合成，而不是直接做文生视频模型？
- Dify 在项目里负责什么？
- FastAPI 在项目里负责什么？
- FFmpeg 在项目里负责什么？
- 如何处理 Dify 调用失败？
- 如何处理视频生成失败？
- 后续如何接入开源文生视频模型？
- 如果业务要批量生成 100 条视频，你会怎么改？
