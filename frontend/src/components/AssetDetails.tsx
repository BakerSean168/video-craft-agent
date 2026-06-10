import React, { useState } from 'react';
import { 
  Loader2, Trash2, AlertTriangle, Eye, Video, 
  Layers
} from 'lucide-react';
import type { AssetLibraryItem } from '../types';

interface AssetDetailsProps {
  item: AssetLibraryItem;
  onDelete: (assetId: string) => Promise<void>;
}

export const AssetDetails: React.FC<AssetDetailsProps> = ({ item, onDelete }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!window.confirm('您确定要将该视频从素材库中彻底物理删除吗？此操作无法撤销。')) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await onDelete(item.asset_id);
    } catch (err: any) {
      setDeleteError(err.message || '删除素材失败，请重试');
      setIsDeleting(false);
    }
  };

  const getMarketingRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'hook': return 'bg-rose-500/10 border-rose-500/35 text-rose-600 dark:text-rose-400';
      case 'pain_point': return 'bg-amber-500/10 border-amber-500/35 text-amber-600 dark:text-amber-400';
      case 'product_intro': return 'bg-indigo-500/10 border-indigo-500/35 text-indigo-600 dark:text-indigo-400';
      case 'cta': return 'bg-emerald-500/10 border-emerald-500/35 text-emerald-600 dark:text-emerald-400';
      default: return 'bg-slate-500/10 border-slate-500/35 text-slate-600 dark:text-slate-400';
    }
  };

  const getMarketingRoleLabel = (role: string) => {
    switch (role?.toLowerCase()) {
      case 'hook': return '🔥 Hook 黄金开头';
      case 'pain_point': return '📌 痛点呈现';
      case 'product_intro': return '💻 产品演示';
      case 'cta': return '🎯 CTA 转化';
      default: return role;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto h-full px-6 py-6 space-y-6">
      
      {/* Header Info */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-lg font-bold text-slate-800 dark:text-slate-100 truncate max-w-md">
              {item.original_name}
            </h1>
            <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
              item.status === 'completed'
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                : item.status === 'failed'
                ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                : 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 animate-pulse'
            }`}>
              {item.status === 'completed' ? '已分析' : item.status === 'failed' ? '分析失败' : '正在分析'}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            素材ID: <span className="font-mono text-slate-600 dark:text-slate-350">{item.asset_id}</span>
          </p>
        </div>

        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="flex items-center gap-1.5 py-2 px-4 bg-rose-50 hover:bg-rose-100 active:bg-rose-200 dark:bg-rose-950/20 dark:hover:bg-rose-950/40 text-rose-600 dark:text-rose-450 border border-rose-100 dark:border-rose-900/30 font-medium rounded-xl text-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isDeleting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Trash2 className="w-3.5 h-3.5" />
          )}
          <span>删除素材</span>
        </button>
      </div>

      {deleteError && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-rose-700 dark:text-rose-400 rounded-2xl text-sm flex gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{deleteError}</span>
        </div>
      )}

      {/* 1. Analyzing State */}
      {item.status === 'analyzing' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-8 rounded-3xl text-center flex flex-col items-center justify-center space-y-4">
          <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border-4 border-slate-100 dark:border-slate-800" />
            <div className="absolute inset-0 rounded-full border-4 border-indigo-600 dark:border-indigo-400 border-t-transparent animate-spin" />
          </div>
          <div className="space-y-1 max-w-sm">
            <h3 className="font-bold text-slate-800 dark:text-slate-100 text-sm">正在分析视频素材...</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              后端正在使用 FFmpeg 提取关键帧，并调用 Vision LLM 模型进行镜头级智能感知与二次全局总结。请稍等片刻，无需刷新页面。
            </p>
          </div>
        </div>
      )}

      {/* 2. Failed State */}
      {item.status === 'failed' && (
        <div className="bg-rose-50 dark:bg-rose-950/15 border border-rose-200 dark:border-rose-900/40 p-6 rounded-3xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-rose-100 dark:bg-rose-900/35 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-rose-600 dark:text-rose-450" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-rose-900 dark:text-rose-400">视觉分析失败</h2>
              <p className="text-xs text-rose-700/80 dark:text-rose-400/85">素材抽取或接口调用异常</p>
            </div>
          </div>
          <div className="p-4 bg-white dark:bg-slate-950 border border-rose-100 dark:border-rose-900/20 rounded-xl">
            <pre className="text-xs text-rose-700 dark:text-rose-400 whitespace-pre-wrap font-mono">
              {item.error || '未知错误详情。'}
            </pre>
          </div>
        </div>
      )}

      {/* 3. Completed Detail State */}
      {item.status === 'completed' && item.profile && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Video Player Area */}
            <div className="lg:col-span-2 bg-slate-900 rounded-3xl overflow-hidden border border-slate-800 relative aspect-video flex items-center justify-center">
              <video
                src={`/api/assets/${item.asset_id}/video`}
                controls
                className="w-full h-full object-contain max-h-[500px]"
              />
            </div>

            {/* Video Metadata Panel */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 space-y-4">
              <h3 className="font-bold text-slate-850 dark:text-slate-100 text-sm flex items-center gap-1.5 border-b border-slate-100 dark:border-slate-800/80 pb-2">
                <Video className="w-4 h-4 text-indigo-650" />
                <span>视频元数据</span>
              </h3>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400 dark:text-slate-500">分辨率:</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-350">
                    {item.profile.metadata.width} x {item.profile.metadata.height} ({item.profile.metadata.aspect_ratio})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 dark:text-slate-500">时长:</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-350">
                    {item.profile.metadata.duration.toFixed(2)} 秒
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 dark:text-slate-500">帧率 (FPS):</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-350">
                    {item.profile.metadata.fps.toFixed(1)} FPS
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 dark:text-slate-500">含音频流:</span>
                  <span className="font-semibold text-slate-700 dark:text-slate-350">
                    {item.profile.metadata.has_audio ? '是' : '否'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 dark:text-slate-500">存储路径:</span>
                  <span className="font-mono text-[10px] text-slate-500 dark:text-slate-400 max-w-[150px] truncate" title={item.local_path}>
                    {item.local_path}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Keyframes Process Section */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 md:p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800/80 pb-3">
              <div className="space-y-1">
                <h3 className="font-bold text-slate-855 dark:text-slate-100 text-sm flex items-center gap-1.5">
                  <Eye className="w-4.5 h-4.5 text-indigo-650" />
                  <span>智能视觉帧流 (Frame-Level Perception Process)</span>
                </h3>
                <p className="text-[11px] text-slate-400 dark:text-slate-500">
                  视频分析的中间过程：提取关键帧图像，使用视觉大模型识别并返回独立帧结果
                </p>
              </div>
              <span className="shrink-0 text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-550 dark:text-slate-400">
                共提取 {item.profile.frames?.length || 0} 帧
              </span>
            </div>

            {(!item.profile.frames || item.profile.frames.length === 0) ? (
              <div className="text-center py-6 text-xs text-slate-400 dark:text-slate-500 italic">
                未保留该素材的提取帧或旧版素材无帧记录。
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {item.profile.frames.map((frame, idx) => {
                  const analysis = item.profile?.frame_analyses?.[idx];
                  const hasError = !!analysis?.error;
                  return (
                    <div 
                      key={frame.frame_id} 
                      className={`border rounded-2xl overflow-hidden flex flex-col justify-between transition-all bg-slate-50/50 dark:bg-slate-950/20 ${
                        hasError 
                          ? 'border-rose-250 dark:border-rose-900/40 hover:shadow-rose-50/30' 
                          : 'border-slate-200 dark:border-slate-800 hover:shadow-md hover:shadow-slate-100 dark:hover:shadow-none'
                      }`}
                    >
                      {/* Image container */}
                      <div className="relative aspect-video bg-black overflow-hidden group">
                        <img
                          src={`/api/assets/${item.asset_id}/frames/${frame.frame_id}`}
                          alt={`Frame at ${frame.timestamp}s`}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        {/* Timestamp badge */}
                        <span className="absolute bottom-2 left-2 px-1.5 py-0.5 bg-black/60 backdrop-blur-xs text-white rounded text-[10px] font-mono font-semibold">
                          {frame.timestamp.toFixed(1)}s
                        </span>
                        {/* Frame Number badge */}
                        <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-indigo-650/90 text-white rounded text-[9px] font-bold uppercase tracking-wider">
                          #{(idx + 1).toString().padStart(2, '0')}
                        </span>
                      </div>

                      {/* Content details */}
                      <div className="p-3 space-y-2 flex-1 flex flex-col justify-between">
                        <div className="space-y-1.5">
                          {hasError ? (
                            <div className="text-[11px] text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 border border-rose-100/50 dark:border-rose-900/30 p-2.5 rounded-xl flex gap-1.5 items-start">
                              <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-500" />
                              <div className="space-y-0.5">
                                <span className="font-bold text-xs">分析异常:</span>
                                <p className="leading-tight break-all text-[10px] font-mono opacity-90">{analysis.error}</p>
                              </div>
                            </div>
                          ) : (
                            <>
                              <p className="text-xs text-slate-700 dark:text-slate-300 font-medium leading-relaxed line-clamp-3" title={analysis?.description_cn}>
                                {analysis?.description_cn || '未能识别画面内容'}
                              </p>
                              
                              {/* Small details if successful */}
                              {analysis && (
                                <div className="space-y-1 pt-1.5 border-t border-slate-100 dark:border-slate-800/80">
                                  {analysis.scene_environment && analysis.scene_environment !== 'other' && (
                                    <div className="flex justify-between text-[10px]">
                                      <span className="text-slate-400">环境:</span>
                                      <span className="font-semibold text-slate-600 dark:text-slate-400">{analysis.scene_environment}</span>
                                    </div>
                                  )}
                                  {analysis.shot_type && analysis.shot_type !== 'other' && (
                                    <div className="flex justify-between text-[10px]">
                                      <span className="text-slate-400">镜头:</span>
                                      <span className="font-semibold text-slate-600 dark:text-slate-400">{analysis.shot_type}</span>
                                    </div>
                                  )}
                                  {analysis.marketing_role && analysis.marketing_role !== 'filler' && (
                                    <div className="flex justify-between text-[10px]">
                                      <span className="text-slate-400">角色:</span>
                                      <span className="font-semibold text-indigo-600 dark:text-indigo-400">{analysis.marketing_role.toUpperCase()}</span>
                                    </div>
                                  )}
                                </div>
                              )}
                            </>
                          )}
                        </div>

                        {/* Tags list */}
                        {analysis?.tags && analysis.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1.5 border-t border-slate-100 dark:border-slate-800/80">
                            {analysis.tags.slice(0, 3).map((tag, tIdx) => (
                              <span key={tIdx} className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded text-[9px]">
                                #{tag}
                              </span>
                            ))}
                            {analysis.tags.length > 3 && (
                              <span className="text-[9px] text-slate-400 self-center">
                                +{analysis.tags.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Aggregated content summary */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 md:p-6 space-y-4">
            <h3 className="font-bold text-slate-850 dark:text-slate-100 text-sm flex items-center gap-1.5">
              <Eye className="w-4.5 h-4.5 text-indigo-650" />
              <span>多帧图像全局聚合摘要</span>
            </h3>
            <p className="text-xs md:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
              {item.profile.content_summary}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-3 border-t border-slate-100 dark:border-slate-800/80">
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">推荐营销用途</span>
                <div className="flex flex-wrap gap-1.5">
                  {item.profile.recommended_usage?.map((use, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 bg-indigo-50 border border-indigo-100/50 text-indigo-655 dark:bg-indigo-950/20 dark:border-indigo-900/40 dark:text-indigo-400 rounded-lg text-xs font-semibold"
                    >
                      {getMarketingRoleLabel(use)}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">视觉特征标签</span>
                <div className="flex flex-wrap gap-1.5">
                  {item.profile.tags?.map((tag, idx) => (
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
          </div>

          {/* Semantic Segments Timeline */}
          {item.profile.segments && item.profile.segments.length > 0 && (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 md:p-6 space-y-4">
              <h3 className="font-bold text-slate-850 dark:text-slate-100 text-sm flex items-center gap-1.5">
                <Layers className="w-4.5 h-4.5 text-indigo-655" />
                <span>智能语义分段 (Semantic Segments)</span>
              </h3>

              {/* Graphical Relative Segment Timeline */}
              <div className="relative w-full bg-slate-100 dark:bg-slate-800/60 h-12 rounded-2xl overflow-hidden flex border border-slate-250 dark:border-slate-750 p-1 gap-1">
                {item.profile.segments.map((seg) => {
                  const segDuration = seg.end - seg.start;
                  const totalDuration = item.profile?.duration || 1;
                  const widthPercent = (segDuration / totalDuration) * 100;

                  return (
                    <div
                      key={seg.segment_id}
                      style={{ width: `${widthPercent}%` }}
                      className={`h-full border rounded-xl flex flex-col justify-center px-3 group relative cursor-pointer hover:opacity-90 transition-all ${getMarketingRoleColor(seg.marketing_role)}`}
                    >
                      <div className="text-[10px] font-bold truncate">
                        {seg.marketing_role.toUpperCase()}
                      </div>
                      <div className="text-[9px] opacity-75 font-mono truncate">
                        {seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s
                      </div>

                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-slate-900 text-white p-3 rounded-xl shadow-xl border border-slate-800 text-xs hidden group-hover:block z-20 pointer-events-none space-y-1">
                        <div className="flex justify-between font-bold text-indigo-400 border-b border-slate-850 pb-1 mb-1">
                          <span>{getMarketingRoleLabel(seg.marketing_role)}</span>
                          <span>评分: {(seg.quality_score * 100).toFixed(0)}</span>
                        </div>
                        <p className="leading-relaxed font-medium text-slate-200">{seg.summary}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Grid detail card segments */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                {item.profile.segments.map((seg) => (
                  <div
                    key={seg.segment_id}
                    className={`p-4 border rounded-2xl space-y-2.5 flex flex-col justify-between ${getMarketingRoleColor(seg.marketing_role)}`}
                  >
                    <div className="flex items-center justify-between border-b border-black/5 dark:border-white/5 pb-1.5">
                      <span className="text-xs font-bold uppercase tracking-wider">
                        {getMarketingRoleLabel(seg.marketing_role)}
                      </span>
                      <div className="flex gap-2 text-[10px] font-semibold bg-white/40 dark:bg-black/25 px-2 py-0.5 rounded-md">
                        <span>{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s</span>
                        <span>画质: {seg.quality_score.toFixed(2)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed font-medium">
                      {seg.summary}
                    </p>
                    <div className="flex flex-wrap gap-1 text-[10px]">
                      {seg.tags?.map((t, i) => (
                        <span key={i} className="opacity-80 bg-white/30 dark:bg-black/20 px-1.5 py-0.5 rounded">
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
      )}
    </div>
  );
};
