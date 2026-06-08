# VideoCraft Agent

AI 营销短视频生成 Agent 学习项目。

本项目目标是用一个轻量但完整的 Demo，练习 Dify AI 工作流、FastAPI 后端服务、素材检索、FFmpeg 视频合成和业务需求拆解能力。它不是先追求复杂文生视频模型，而是先完成一个更适合入门和面试展示的业务闭环：

```text
文本需求 / 上传素材 -> Dify 生成脚本 -> FastAPI 校验和编排 -> FFmpeg 视频合成 -> 前端预览和下载
```

## 项目定位

面向全栈开发工程师 / AI 视频方向 JD，构建一个可以快速演示的 AI 视频生产工具：

- 用户输入产品、卖点、目标人群、平台和风格
- Dify Workflow 生成 3 段式营销短视频脚本
- FastAPI 校验脚本并匹配上传素材或本地素材库
- 调用 FFmpeg 自动裁剪、拼接、加字幕、加音乐
- 输出 9:16 竖屏营销短视频
- 提供视频格式转换工具

## 文档目录

当前主方案以 [Dify + FastAPI 架构方案](docs/08-dify-fastapi-architecture.md) 为准；其余文档已按该架构统一。

- [PRD](docs/01-prd.md)
- [技术设计](docs/02-technical-design.md)
- [Agent 工作流](docs/03-agent-workflow.md)
- [MVP 开发计划](docs/04-mvp-roadmap.md)
- [数据结构与接口设计](docs/05-data-and-api-design.md)
- [学习路线](docs/06-learning-plan.md)
- [面试与简历包装](docs/07-interview-packaging.md)
- [Dify + FastAPI 架构方案](docs/08-dify-fastapi-architecture.md)

## 推荐 MVP 技术栈

- AI 工作流: Dify Workflow
- 前端: Streamlit 或简单 Python Web 页面
- 后端: FastAPI
- 语言: Python
- 视频处理: FFmpeg
- HTTP 客户端: requests 或 httpx
- 数据校验: Pydantic
- 配置: python-dotenv

## 建议开发顺序

1. 在 Dify 创建 Workflow，让 AI 输出结构化脚本 JSON。
2. 搭建 FastAPI 后端，接收产品信息和上传素材。
3. FastAPI 调用 Dify Workflow，并用 Pydantic 校验返回结果。
4. 调用 FFmpeg 根据脚本和素材生成 9:16 mp4。
5. 做 Python 前端，完成输入、上传、状态展示、视频预览和下载。
6. 加格式转换、错误处理、日志、样例素材和 README 演示说明。

## 项目边界

MVP 不做这些复杂功能：

- 不训练视频生成模型
- 不做真实素材平台爬取
- 不做多人协作后台
- 不做复杂剪辑时间线
- 不做商用级版权管理

后续增强可以接入 ModelScope Text-to-Video、AnimateDiff、Stable Video Diffusion 或云端视频生成 API。
