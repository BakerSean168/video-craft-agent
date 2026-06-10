import React, { useState } from 'react';
import { 
  Loader2, Download, AlertTriangle, HelpCircle, 
  Layers, Video, RefreshCw, CheckCircle, Clock, VolumeX, Eye
} from 'lucide-react';
import type { VideoJob } from '../types';

interface JobDetailsProps {
  job: VideoJob;
}

export const JobDetails: React.FC<JobDetailsProps> = ({ job }) => {
  const [activeTab, setActiveTab] = useState<'video' | 'assets'>('video');
  const [conversionFormat, setConversionFormat] = useState<'mp4' | 'webm' | 'mov' | 'gif'>('mp4');
  const [isConverting, setIsConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [convertedUrls, setConvertedUrls] = useState<Record<string, string>>({
    mp4: `/api/video-jobs/${job.job_id}/video`,
  });

  const getProgressPercentage = (status: string) => {
    switch (status) {
      case 'queued': return 10;
      case 'upload_saved': return 20;
      case 'analyzing_assets': return 40;
      case 'calling_dify': return 65;
      case 'script_ready': return 75;
      case 'matching_materials': return 80;
      case 'rendering_video': return 90;
      case 'succeeded': return 100;
      case 'failed': return 100;
      default: return 0;
    }
  };


  const triggerConversion = async (format: 'mp4' | 'webm' | 'mov' | 'gif') => {
    if (format === 'mp4') {
      setConversionFormat('mp4');
      return;
    }
    
    setIsConverting(true);
    setConversionFormat(format);
    setConversionError(null);

    try {
      const response = await fetch(`/api/video-jobs/${job.job_id}/convert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ target_format: format }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '转换失败');
      }

      const data = await response.json();
      setConvertedUrls((prev) => ({
        ...prev,
        [format]: data.download_url,
      }));
    } catch (err: any) {
      setConversionError(err.message || '转换出错，请重试');
    } finally {
      setIsConverting(false);
    }
  };

  // Helper colors for different marketing roles
  const getMarketingRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'hook': return 'bg-rose-500/10 border-rose-500/35 text-rose-600 dark:text-rose-400';
      case 'pain_point': return 'bg-amber-500/10 border-amber-500/35 text-amber-600 dark:text-amber-400';
      case 'product_intro': return 'bg-indigo-500/10 border-indigo-500/35 text-indigo-600 dark:text-indigo-400';
      case 'cta': return 'bg-emerald-500/10 border-emerald-500/35 text-emerald-600 dark:text-emerald-400';
      default: return 'bg-slate-500/10 border-slate-500/35 text-slate-600 dark:text-slate-400';
    }
  };

  const isProcessing = job.status !== 'succeeded' && job.status !== 'failed';

  return (
    <div className="flex-1 overflow-y-auto h-full px-6 py-6 space-y-6">
      
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">
              {job.requirement.product_name || '未命名剪辑任务'}
            </h1>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
              job.status === 'succeeded'
                ? 'bg-emerald-550/10 text-emerald-600 dark:text-emerald-400'
                : job.status === 'failed'
                ? 'bg-rose-550/10 text-rose-600 dark:text-rose-400'
                : 'bg-indigo-550/10 text-indigo-600 dark:text-indigo-400 animate-pulse'
            }`}>
              {job.status === 'succeeded' ? '已完成' : job.status === 'failed' ? '已失败' : '处理中'}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            任务ID: <span className="font-mono text-slate-600 dark:text-slate-350">{job.job_id}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-500 dark:text-slate-400">
          <div>目标：<span className="font-semibold text-slate-700 dark:text-slate-300">{job.requirement.target_audience}</span></div>
          <div className="w-px h-3 bg-slate-200 dark:bg-slate-800 hidden md:block"></div>
          <div>风格：<span className="font-semibold text-slate-700 dark:text-slate-300">{job.requirement.style}</span></div>
          <div className="w-px h-3 bg-slate-200 dark:bg-slate-800 hidden md:block"></div>
          <div>时长：<span className="font-semibold text-slate-700 dark:text-slate-300">{job.requirement.duration_seconds}秒</span></div>
        </div>
      </div>

      {/* 1. Processing State Progress Bar */}
      {isProcessing && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 rounded-3xl space-y-6 shadow-sm">
          <div className="flex justify-between items-center text-sm">
            <span className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              正在生成智能短视频...
            </span>
            <span className="font-bold text-slate-700 dark:text-slate-300">
              {getProgressPercentage(job.status)}%
            </span>
          </div>

          {/* Progress Bar Container */}
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
            <div 
              className="bg-indigo-600 dark:bg-indigo-500 h-full rounded-full transition-all duration-550 ease-out"
              style={{ width: `${getProgressPercentage(job.status)}%` }}
            />
          </div>

          {/* Steps Detail */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 border-t border-slate-100 dark:border-slate-800/60 text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
              <div className="text-slate-700 dark:text-slate-300">素材已上传</div>
            </div>
            <div className="flex items-center gap-2">
              {['analyzing_assets', 'calling_dify', 'script_ready', 'rendering_video', 'succeeded'].includes(job.status) ? (
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
              ) : job.status === 'upload_saved' ? (
                <Loader2 className="w-4 h-4 text-indigo-500 animate-spin shrink-0" />
              ) : (
                <Clock className="w-4 h-4 text-slate-350 dark:text-slate-600 shrink-0" />
              )}
              <div className="text-slate-700 dark:text-slate-300">智能分析关键帧</div>
            </div>
            <div className="flex items-center gap-2">
              {['calling_dify', 'script_ready', 'rendering_video', 'succeeded'].includes(job.status) ? (
                job.status === 'calling_dify' ? (
                  <Loader2 className="w-4 h-4 text-indigo-500 animate-spin shrink-0" />
                ) : (
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                )
              ) : (
                <Clock className="w-4 h-4 text-slate-350 dark:text-slate-600 shrink-0" />
              )}
              <div className="text-slate-700 dark:text-slate-300">Dify 剪辑编排</div>
            </div>
            <div className="flex items-center gap-2">
              {job.status === 'rendering_video' ? (
                <Loader2 className="w-4 h-4 text-indigo-500 animate-spin shrink-0" />
              ) : job.status === 'succeeded' ? (
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
              ) : (
                <Clock className="w-4 h-4 text-slate-350 dark:text-slate-600 shrink-0" />
              )}
              <div className="text-slate-700 dark:text-slate-300">FFmpeg 渲染导出</div>
            </div>
          </div>

          <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800 rounded-xl text-center">
            <span className="text-xs text-slate-400 dark:text-slate-500 mr-2">当前步骤:</span>
            <span className="text-sm font-medium text-slate-750 dark:text-slate-350">{job.current_step}</span>
          </div>
        </div>
      )}

      {/* 2. Failure State */}
      {job.status === 'failed' && (
        <div className="bg-rose-50 dark:bg-rose-950/15 border border-rose-200 dark:border-rose-900/40 p-6 rounded-3xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-100 dark:bg-rose-900/35 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-rose-600 dark:text-rose-450" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-rose-900 dark:text-rose-400">视频生成失败</h2>
              <p className="text-xs text-rose-700/80 dark:text-rose-400/85">在执行流水线时发生了错误</p>
            </div>
          </div>
          <div className="p-4 bg-white dark:bg-slate-950 border border-rose-100 dark:border-rose-900/20 rounded-xl">
            <pre className="text-xs text-rose-700 dark:text-rose-400 whitespace-pre-wrap font-mono">
              {job.error || '未知错误详情。'}
            </pre>
          </div>
        </div>
      )}

      {/* 3. Succeeded State */}
      {job.status === 'succeeded' && (
        <div className="space-y-6">
          
          {/* Main Visual Content Tabs */}
          <div className="flex border-b border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setActiveTab('video')}
              className={`py-3 px-6 text-sm font-semibold border-b-2 -mb-px transition-all flex items-center gap-2 ${
                activeTab === 'video'
                  ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-450 dark:hover:text-slate-200'
              }`}
            >
              <Video className="w-4 h-4" />
              <span>生成视频与时间轴</span>
            </button>
            <button
              onClick={() => setActiveTab('assets')}
              className={`py-3 px-6 text-sm font-semibold border-b-2 -mb-px transition-all flex items-center gap-2 ${
                activeTab === 'assets'
                  ? 'border-indigo-600 text-indigo-600 dark:border-indigo-400 dark:text-indigo-400'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-450 dark:hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>素材深度分析 ({job.assets?.length || 0})</span>
            </button>
          </div>

          {activeTab === 'video' && (
            <div className="space-y-6">
              {/* Video Player and Format Selector Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Video Player Container */}
                <div className="lg:col-span-2 bg-slate-900 rounded-3xl overflow-hidden border border-slate-800 relative aspect-video flex items-center justify-center group">
                  <video
                    src={convertedUrls[conversionFormat] || `/api/video-jobs/${job.job_id}/video`}
                    controls
                    className="w-full h-full object-contain max-h-[500px]"
                    poster=""
                  />
                </div>

                {/* Format Converter Panel */}
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-3">
                    <h3 className="font-bold text-slate-800 dark:text-slate-100 text-base">一键格式转换</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      该视频为智能算法生成，支持在前端转换并导出为其他格式：
                    </p>

                    <div className="grid grid-cols-2 gap-2">
                      {(['mp4', 'webm', 'mov', 'gif'] as const).map((fmt) => (
                        <button
                          key={fmt}
                          onClick={() => triggerConversion(fmt)}
                          disabled={isConverting}
                          className={`py-2 px-3 border rounded-xl text-xs font-semibold uppercase transition-all flex items-center justify-center gap-1.5 ${
                            conversionFormat === fmt
                              ? 'bg-indigo-600 border-indigo-600 text-white shadow-md shadow-indigo-100 dark:shadow-none'
                              : 'bg-white hover:bg-slate-50 dark:bg-slate-950 dark:hover:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          <span className="uppercase">{fmt}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {conversionError && (
                    <div className="p-3 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/35 rounded-xl text-xs text-rose-600 dark:text-rose-450 flex gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>{conversionError}</span>
                    </div>
                  )}

                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80">
                    {isConverting ? (
                      <div className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-50 dark:bg-indigo-950/20 text-indigo-600 dark:text-indigo-400 rounded-xl text-sm font-semibold">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>正在生成 {conversionFormat.toUpperCase()} 格式...</span>
                      </div>
                    ) : (
                      <a
                        href={convertedUrls[conversionFormat] || `/api/video-jobs/${job.job_id}/video?format=${conversionFormat}`}
                        download={`final_${job.job_id}.${conversionFormat}`}
                        className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-100 dark:shadow-none transition-all"
                      >
                        <Download className="w-4.5 h-4.5" />
                        <span>下载 {conversionFormat.toUpperCase()} 格式</span>
                      </a>
                    )}
                  </div>
                </div>

              </div>

              {/* EditPlan High Fidelity Timeline */}
              {job.edit_plan && (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 md:p-6 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-850 pb-3">
                    <div className="space-y-0.5">
                      <h3 className="font-bold text-slate-850 dark:text-slate-100 text-base">
                        剪辑决策时间轴 (Edit Plan)
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        脚本标题: <span className="font-semibold text-slate-700 dark:text-slate-300">{job.edit_plan.title}</span> ({job.edit_plan.aspect_ratio})
                      </p>
                    </div>
                    {job.edit_plan.warnings?.length > 0 && (
                      <div className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 px-2.5 py-1 rounded-lg">
                        <AlertTriangle className="w-4 h-4 shrink-0" />
                        <span>{job.edit_plan.warnings.length} 个调整警告</span>
                      </div>
                    )}
                  </div>

                  {/* Horizontal Timeline Track */}
                  <div className="relative pt-2">
                    <div className="flex gap-2.5 overflow-x-auto pb-4 pt-1">
                      {job.edit_plan.timeline?.map((scene) => {
                        const duration = scene.end_time - scene.start_time;
                        // Calculate width percentage relative to total duration
                        const totalDur = job.edit_plan?.duration_seconds || 15;
                        const widthPct = Math.max(12, (duration / totalDur) * 100);

                        return (
                          <div
                            key={scene.scene_id}
                            style={{ minWidth: `${widthPct}%` }}
                            className="flex-1 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 dark:from-indigo-950/30 dark:to-violet-950/30 border border-indigo-250 dark:border-indigo-900/60 rounded-2xl p-3.5 space-y-2 flex flex-col justify-between"
                          >
                            <div className="flex items-start justify-between">
                              <span className="px-2 py-0.5 bg-indigo-600 text-white rounded text-[10px] font-bold">
                                Scene {scene.scene_id}
                              </span>
                              <div className="flex items-center gap-1 text-[10px] text-slate-500 dark:text-slate-400 font-semibold bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-100 dark:border-slate-750">
                                <Clock className="w-3 h-3 text-indigo-500" />
                                <span>{duration.toFixed(1)}s</span>
                              </div>
                            </div>

                            <p className="text-xs text-slate-800 dark:text-slate-200 font-medium line-clamp-2 leading-relaxed italic">
                              "{scene.subtitle}"
                            </p>

                            <div className="border-t border-indigo-100/50 dark:border-indigo-900/30 pt-2 flex flex-wrap items-center justify-between gap-1 text-[10px] text-slate-400 dark:text-slate-500">
                              <span className="truncate max-w-[80px]" title={`素材: ${scene.asset_id}`}>
                                {scene.asset_id}
                              </span>
                              <div className="flex items-center gap-1.5">
                                {scene.operation.speed !== 1.0 && (
                                  <span className="bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 px-1 rounded font-bold">
                                    {scene.operation.speed}x速
                                  </span>
                                )}
                                {scene.operation.mute_audio && (
                                  <VolumeX className="w-3 h-3 text-slate-400" />
                                )}
                                {scene.transition && (
                                  <span className="bg-slate-50 dark:bg-slate-800 px-1 rounded text-slate-500 dark:text-slate-455">
                                    {scene.transition}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Scene Table list for screen readers / details */}
                  <div className="border border-slate-100 dark:border-slate-800/80 rounded-2xl overflow-hidden mt-4">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/40 text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-100 dark:border-slate-800">
                          <th className="py-2.5 px-4 w-12 text-center">镜号</th>
                          <th className="py-2.5 px-4 w-24">使用素材</th>
                          <th className="py-2.5 px-4 w-28">素材剪辑区间</th>
                          <th className="py-2.5 px-4 w-28">输出开始-结束</th>
                          <th className="py-2.5 px-4">屏幕字幕 / 旁白文案</th>
                          <th className="py-2.5 px-4 w-28 text-right">变速/音量/转场</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-350">
                        {job.edit_plan.timeline?.map((scene) => (
                          <tr key={scene.scene_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-colors">
                            <td className="py-3 px-4 font-bold text-center">{scene.scene_id}</td>
                            <td className="py-3 px-4 font-mono text-slate-500 dark:text-slate-400">{scene.asset_id}</td>
                            <td className="py-3 px-4">{scene.source_start.toFixed(1)}s - {scene.source_end.toFixed(1)}s</td>
                            <td className="py-3 px-4 font-semibold text-slate-900 dark:text-slate-200">
                              {scene.start_time.toFixed(1)}s - {scene.end_time.toFixed(1)}s
                            </td>
                            <td className="py-3 px-4 space-y-0.5">
                              <div className="font-medium">字幕: {scene.subtitle}</div>
                              {scene.voiceover && (
                                <div className="text-slate-400 dark:text-slate-500 text-[10px]">
                                  旁白: {scene.voiceover}
                                </div>
                              )}
                            </td>
                            <td className="py-3 px-4 text-right space-y-0.5">
                              <div>{scene.operation.speed !== 1.0 ? `变速: ${scene.operation.speed}x` : '常速 1.0x'}</div>
                              <div className="text-[10px] text-slate-400 dark:text-slate-500">
                                {scene.operation.mute_audio ? '已静音' : '含音频'} 
                                {scene.transition ? ` | 转场: ${scene.transition}` : ''}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                </div>
              )}
            </div>
          )}

          {activeTab === 'assets' && (
            <div className="space-y-6">
              
              {job.assets && job.assets.length > 0 ? (
                job.assets.map((asset) => (
                  <div 
                    key={asset.asset_id} 
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 md:p-6 space-y-5 shadow-sm"
                  >
                    {/* Header */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-805 pb-4">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <Video className="w-5 h-5 text-indigo-600 dark:text-indigo-400 shrink-0" />
                          <h3 className="font-bold text-slate-850 dark:text-slate-100 text-base">
                            {asset.original_name}
                          </h3>
                        </div>
                        <p className="text-[11px] text-slate-400 dark:text-slate-500">
                          素材ID: <span className="font-mono text-slate-500 dark:text-slate-400">{asset.asset_id}</span>
                        </p>
                      </div>

                      {/* Video Resolution and metadata badge list */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-xs font-semibold">
                          {asset.metadata.width} x {asset.metadata.height} ({asset.metadata.aspect_ratio})
                        </span>
                        <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-xs font-semibold">
                          {asset.metadata.fps} FPS
                        </span>
                        <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-xs font-semibold">
                          {asset.metadata.duration.toFixed(1)}s 时长
                        </span>
                        <span className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-xs font-semibold">
                          {asset.metadata.has_audio ? '含音频流' : '无音频'}
                        </span>
                      </div>
                    </div>

                    {/* Content Summary Card */}
                    <div className="bg-slate-50 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800/80 p-4 rounded-2xl space-y-2">
                      <h4 className="text-xs font-bold text-indigo-650 dark:text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Eye className="w-3.5 h-3.5" />
                        <span>多帧特征二次聚合总结</span>
                      </h4>
                      <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                        {asset.content_summary}
                      </p>
                    </div>

                    {/* Usage & Tags */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">推荐用途</span>
                        <div className="flex flex-wrap gap-1.5">
                          {asset.recommended_usage?.map((use, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 bg-indigo-50 border border-indigo-100/50 text-indigo-655 dark:bg-indigo-950/15 dark:border-indigo-900/40 dark:text-indigo-400 rounded-lg text-xs font-semibold uppercase"
                            >
                              {use === 'hook' ? '🔥 黄金开头 Hook' : use === 'pain_point' ? '📌 痛点呈现 Pain Point' : use === 'product_intro' ? '💻 产品演示 Intro' : use === 'cta' ? '🎯 呼吁转化 CTA' : use}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">视觉标签</span>
                        <div className="flex flex-wrap gap-1.5">
                          {asset.tags?.map((tag, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 bg-slate-100 border border-slate-200 text-slate-600 dark:bg-slate-800/60 dark:border-slate-750 dark:text-slate-350 rounded-lg text-xs"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Semantic Video Segments Timeline Visual */}
                    {asset.segments && asset.segments.length > 0 && (
                      <div className="space-y-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
                        <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5" />
                          <span>视觉语义分段时间轴 (Semantic Segments)</span>
                        </span>

                        {/* Interactive Visual Segments bar */}
                        <div className="w-full bg-slate-100 dark:bg-slate-800/60 h-10 rounded-2xl overflow-hidden flex border border-slate-200 dark:border-slate-750 p-1 gap-1">
                          {asset.segments.map((seg) => {
                            const segDuration = seg.end - seg.start;
                            const totalDuration = asset.duration || 1;
                            const widthPercent = (segDuration / totalDuration) * 100;

                            return (
                              <div
                                key={seg.segment_id}
                                style={{ width: `${widthPercent}%` }}
                                className={`h-full border rounded-xl flex flex-col justify-center px-2 group relative cursor-pointer hover:opacity-90 transition-all ${getMarketingRoleColor(seg.marketing_role)}`}
                              >
                                <div className="text-[10px] font-bold truncate">
                                  {seg.marketing_role.toUpperCase()}
                                </div>
                                <div className="text-[9px] opacity-75 font-mono truncate">
                                  {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                                </div>

                                {/* Floating Tooltip details on Hover */}
                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-slate-900 text-white p-3 rounded-xl shadow-xl border border-slate-800 text-xs hidden group-hover:block z-25 pointer-events-none space-y-1">
                                  <div className="flex justify-between font-bold text-indigo-400 border-b border-slate-800 pb-1 mb-1">
                                    <span>分段: {seg.marketing_role.toUpperCase()}</span>
                                    <span>画质: {(seg.quality_score * 100).toFixed(0)}分</span>
                                  </div>
                                  <p className="leading-relaxed font-medium text-slate-200">
                                    {seg.summary}
                                  </p>
                                  <div className="flex flex-wrap gap-1 pt-1 text-[9px]">
                                    {seg.tags.map((t, i) => (
                                      <span key={i} className="bg-slate-800 px-1 py-0.5 rounded text-slate-400">#{t}</span>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Detailed segment items listing */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 mt-2.5">
                          {asset.segments.map((seg) => (
                            <div
                              key={seg.segment_id}
                              className={`p-3.5 border rounded-2xl space-y-2 flex flex-col justify-between ${getMarketingRoleColor(seg.marketing_role)}`}
                            >
                              <div className="flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-1.5">
                                <span className="text-xs font-bold uppercase tracking-wider">
                                  {seg.marketing_role === 'hook' ? '🔥 Hook 段' : seg.marketing_role === 'pain_point' ? '📌 痛点呈现' : seg.marketing_role === 'product_intro' ? '💻 产品演示' : seg.marketing_role === 'cta' ? '🎯 CTA 转化' : seg.marketing_role}
                                </span>
                                <div className="flex gap-2 text-[10px] font-semibold bg-white/40 dark:bg-black/20 px-2 py-0.5 rounded-md">
                                  <span>{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s</span>
                                  <span>画质评分: {seg.quality_score.toFixed(2)}</span>
                                </div>
                              </div>
                              <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed font-medium">
                                {seg.summary}
                              </p>
                              <div className="flex flex-wrap gap-1 text-[10px]">
                                {seg.tags.map((t, idx) => (
                                  <span key={idx} className="opacity-80 bg-white/30 dark:bg-black/15 px-1.5 py-0.5 rounded">
                                    #{t}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 text-center text-slate-500 dark:text-slate-400 flex flex-col items-center justify-center space-y-2">
                  <HelpCircle className="w-10 h-10 text-slate-400" />
                  <p className="font-semibold text-sm">暂无素材画像</p>
                  <p className="text-xs">该剪辑任务暂未关联或提取到视频素材特征分析结果。</p>
                </div>
              )}

            </div>
          )}

        </div>
      )}

    </div>
  );
};
