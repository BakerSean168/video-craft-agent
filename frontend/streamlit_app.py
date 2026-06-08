import streamlit as st
import requests
import time
import os

# Set page layout and title
st.set_page_config(
    page_title="VideoCraft Agent - AI 营销视频一键成片",
    page_icon="🎬",
    layout="wide"
)

# API Base URL configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.title("🎬 VideoCraft Agent")
st.markdown("### V0.1 - V0.4 AI 脚本 + FFmpeg 营销短视频生成系统")
st.write("输入产品信息，由 Dify 生成脚本，本地 FFmpeg 自动混剪、加字幕、加音乐并输出 9:16 短视频。")

st.divider()

# Create layout: Sidebar for configuration, main panel for upload and generation
with st.sidebar:
    st.header("⚙️ 视频参数配置")
    
    product_name = st.text_input("产品名称", value="AI 编程训练营", placeholder="输入您的产品或品牌名")
    target_audience = st.text_input("目标受众", value="想转行 AI 的程序员", placeholder="例如：大学生, 白领, 程序员")
    
    selling_points = st.text_area(
        "核心卖点", 
        value="零基础入门 AI Agent, 带项目实战, 适合 Python 初学者",
        placeholder="输入卖点，多个卖点请用英文或中文逗号分隔"
    )
    
    style = st.selectbox(
        "视频风格",
        options=["科技感、快节奏", "温馨、舒适", "幽默、反转", "高燃、动感", "简约、大气"],
        index=0
    )
    
    platform = st.selectbox(
        "发布平台",
        options=["douyin", "tiktok", "kuaishou", "bilibili"],
        index=0
    )
    
    duration_seconds = st.slider(
        "目标时长 (秒)",
        min_value=5,
        max_value=60,
        value=15,
        step=5
    )

st.subheader("📁 上传素材 (可选)")
uploaded_files = st.file_uploader(
    "上传本地视频片段，系统会根据大模型生成的分镜关键字自动匹配。如果不上传或未匹配到，则会使用默认素材库。",
    type=["mp4", "mov", "avi", "webm"],
    accept_multiple_files=True
)

if st.button("🚀 开始生成短视频", type="primary", use_container_width=True):
    if not product_name or not target_audience or not selling_points:
        st.error("请确保填写了『产品名称』、『目标受众』和『核心卖点』！")
    else:
        st.info("正在将素材及需求提交至 FastAPI 后端...")
        
        # Prepare multipart request
        form_data = {
            "product_name": product_name,
            "target_audience": target_audience,
            "selling_points": selling_points,
            "style": style,
            "platform": platform,
            "duration_seconds": str(duration_seconds)
        }
        
        files_payload = []
        opened_files = []
        try:
            if uploaded_files:
                for uf in uploaded_files:
                    # Read bytes
                    files_payload.append(
                        ("files[]", (uf.name, uf.getvalue(), uf.type))
                    )
            
            # Post request
            response = requests.post(
                f"{API_BASE_URL}/api/video-jobs",
                data=form_data,
                files=files_payload if files_payload else None
            )
            
            if response.status_code != 200:
                st.error(f"创建任务失败 ({response.status_code}): {response.text}")
            else:
                job_data = response.json()
                job_id = job_data["job_id"]
                st.success(f"任务已创建！任务 ID: {job_id}")
                
                # Polling loop
                progress_bar = st.progress(0)
                status_box = st.empty()
                step_box = st.empty()
                
                # Status progression dict for progress bar estimation
                status_progress = {
                    "queued": 10,
                    "calling_dify": 30,
                    "script_ready": 45,
                    "matching_materials": 60,
                    "rendering_video": 80,
                    "succeeded": 100,
                    "failed": 100
                }
                
                with st.spinner("视频正在后台渲染合成中，请稍候..."):
                    while True:
                        # Fetch status
                        status_resp = requests.get(f"{API_BASE_URL}/api/video-jobs/{job_id}")
                        if status_resp.status_code != 200:
                            st.error(f"轮询状态失败: {status_resp.text}")
                            break
                        
                        job_info = status_resp.json()
                        status = job_info["status"]
                        step = job_info["current_step"]
                        
                        # Update progress
                        p_val = status_progress.get(status, 90)
                        progress_bar.progress(p_val / 100.0)
                        status_box.markdown(f"**任务状态**: `{status}`")
                        step_box.info(f"**当前步骤**: {step}")
                        
                        if status == "succeeded":
                            st.balloons()
                            st.success("🎉 视频生成成功！")
                            
                            # Display Dify Response Status
                            dify_success = job_info.get("dify_success")
                            if dify_success is True:
                                st.success("✅ **智能生成**：已成功获取并使用 Dify AI 工作流脚本分镜。")
                            elif dify_success is False:
                                st.warning("⚠️ **模版兜底**：Dify 接口调用或解析失败，已自动启用本地预设模版生成视频。")
                            
                            # Layout results
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("🎥 预览并下载成片")
                                video_download_url = f"{API_BASE_URL}/api/video-jobs/{job_id}/video"
                                # Fetch video stream or use HTML player
                                st.video(video_download_url)
                                st.markdown(f"[📥 点击下载视频]({video_download_url})")
                                
                            with col2:
                                st.subheader("📄 Dify 脚本分镜详情")
                                if job_info.get("script"):
                                    st.json(job_info["script"])
                            break
                            
                        elif status == "failed":
                            st.error(f"❌ 视频生成失败: {job_info.get('error', '未知错误')}")
                            break
                            
                        time.sleep(1.5)
                        
        except Exception as e:
            st.error(f"连接后端服务出错: {e}")
