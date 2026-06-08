# VideoCraft Agent Backend

本项目后端使用 **FastAPI** 作为主控服务，负责素材保存、任务管理、Dify Workflow 接口调用、Pydantic 数据校验以及 FFmpeg 渲染调度。

## 1. 配置环境

复制 `.env.example` 为 `.env`，填入 Dify Workflow 应用的 API Key 及配置：

```text
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_API_KEY=app-你的key
DIFY_USER=video-craft-demo-user
DIFY_SCRIPT_OUTPUT_KEY=script_json
```

如果是在 Windows 下，FFmpeg 合成字幕需要中文字体，项目默认指向 `C:/Windows/Fonts/msyh.ttc`（微软雅黑）。

## 2. 启动 FastAPI 服务

在 `backend/` 目录下，使用 `uv` 运行：

```powershell
uv run uvicorn main:app --reload
```

启动后可访问 API 文档：`http://127.0.0.1:8000/docs`

## 3. API 接口调用说明 (V0.1 闭环)

### 3.1 创建视频任务

通过 `multipart/form-data` 上传文件和参数：

```bash
curl -X POST "http://127.0.0.1:8000/api/video-jobs" \
  -F "product_name=AI 编程训练营" \
  -F "target_audience=程序员" \
  -F "selling_points=7天变身高手" \
  -F "style=紧张刺激" \
  -F "platform=抖音" \
  -F "duration_seconds=15" \
  -F "files[]=@my_video.mp4"
```

响应：
```json
{
  "job_id": "2d142d1f-823d-4c31-97b7-6bcfc7d5ef0a",
  "status": "queued",
  "message": "任务已创建"
}
```

### 3.2 查询任务状态

轮询查询视频任务的状态：

```bash
curl http://127.0.0.1:8000/api/video-jobs/2d142d1f-823d-4c31-97b7-6bcfc7d5ef0a
```

### 3.3 预览或下载成片

当状态变为 `succeeded` 后，可以通过以下接口直接拉取/播放视频流：

```bash
curl http://127.0.0.1:8000/api/video-jobs/2d142d1f-823d-4c31-97b7-6bcfc7d5ef0a/video --output final.mp4
```

---

## 4. 运行 TDD 测试

我们使用 `pytest` 覆盖了整个链路的自动化测试，包括数据校验、素材检索、FFmpeg 处理和 API 接口。

运行所有测试：

```powershell
uv run python -m pytest
```
