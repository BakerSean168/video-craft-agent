import React from 'react';
import { 
  Plus, Moon, Sun, Film, Loader2, CheckCircle2, 
  XCircle, Database, Video, Clock
} from 'lucide-react';
import type { VideoJob, AssetLibraryItem } from '../types';

interface SidebarProps {
  jobs: VideoJob[];
  activeJobId: string | null;
  onSelectJob: (jobId: string) => void;
  
  assets: AssetLibraryItem[];
  activeAssetId: string | null;
  onSelectAsset: (assetId: string) => void;
  
  activeTab: 'jobs' | 'assets';
  onChangeTab: (tab: 'jobs' | 'assets') => void;
  
  onCreateNew: () => void; // Double purpose: New Job or Upload Asset depending on activeTab
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  jobs,
  activeJobId,
  onSelectJob,
  assets,
  activeAssetId,
  onSelectAsset,
  activeTab,
  onChangeTab,
  onCreateNew,
  darkMode,
  onToggleDarkMode,
}) => {
  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'succeeded':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-rose-500" />;
      default:
        return <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />;
    }
  };

  const getJobStatusText = (status: string) => {
    switch (status) {
      case 'queued': return '队列中';
      case 'upload_saved': return '素材已保存';
      case 'analyzing_assets': return '加载素材画像';
      case 'calling_dify': return 'Dify决策中';
      case 'script_ready': return '脚本已生成';
      case 'matching_materials': return '匹配素材中';
      case 'rendering_video': return '视频渲染中';
      case 'succeeded': return '生成成功';
      case 'failed': return '生成失败';
      default: return status;
    }
  };

  const getAssetStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-rose-500" />;
      default:
        return <Loader2 className="w-4 h-4 text-indigo-500 animate-spin" />;
    }
  };

  const getAssetStatusText = (status: string) => {
    switch (status) {
      case 'analyzing': return '分析中';
      case 'completed': return '已完成';
      case 'failed': return '分析失败';
      default: return status;
    }
  };

  return (
    <aside className="w-80 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen overflow-hidden">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-slate-800 dark:text-slate-100 text-lg">
          <Film className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          <span>VideoCraft Studio</span>
        </div>
        <button
          onClick={onToggleDarkMode}
          className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          title={darkMode ? '切换亮色模式' : '切换暗色模式'}
        >
          {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="px-4 pt-3 flex gap-1 border-b border-slate-100 dark:border-slate-800 pb-2">
        <button
          onClick={() => onChangeTab('jobs')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'jobs'
              ? 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-150'
              : 'text-slate-500 hover:text-slate-700 dark:text-slate-450 dark:hover:text-slate-300'
          }`}
        >
          <Film className="w-3.5 h-3.5" />
          <span>剪辑任务</span>
        </button>
        <button
          onClick={() => onChangeTab('assets')}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'assets'
              ? 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-150'
              : 'text-slate-500 hover:text-slate-700 dark:text-slate-450 dark:hover:text-slate-300'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>素材管理</span>
        </button>
      </div>

      {/* Action Button */}
      <div className="p-4">
        {activeTab === 'jobs' ? (
          <button
            onClick={onCreateNew}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl font-medium shadow-md shadow-indigo-100 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>新建视频任务</span>
          </button>
        ) : (
          <button
            onClick={onCreateNew}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl font-medium shadow-md shadow-indigo-100 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm"
          >
            <Plus className="w-4 h-4" />
            <span>上传素材到素材库</span>
          </button>
        )}
      </div>

      {/* Dynamic List */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
        {activeTab === 'jobs' ? (
          <>
            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
              任务历史 ({jobs.length})
            </h3>
            
            {jobs.length === 0 ? (
              <div className="text-center py-8 text-sm text-slate-400 dark:text-slate-500">
                暂无任务记录
              </div>
            ) : (
              jobs.map((job) => {
                const isActive = job.job_id === activeJobId;
                return (
                  <button
                    key={job.job_id}
                    onClick={() => onSelectJob(job.job_id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col gap-1.5 ${
                      isActive
                        ? 'bg-indigo-50/80 border-indigo-200 dark:bg-indigo-950/30 dark:border-indigo-900/60'
                        : 'bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/40 dark:hover:bg-slate-800/80 border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-sm text-slate-800 dark:text-slate-200 line-clamp-1">
                        {job.requirement.product_name || '未命名产品'}
                      </span>
                      {getJobStatusIcon(job.status)}
                    </div>
                    
                    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                      {job.requirement.selling_points.join(' | ')}
                    </p>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                      <span className="font-mono">
                        ID: {job.job_id.substring(0, 8)}...
                      </span>
                      <span className={`px-1.5 py-0.5 rounded-md font-semibold ${
                        job.status === 'succeeded'
                          ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400'
                          : job.status === 'failed'
                          ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/20 dark:text-rose-400'
                          : 'bg-amber-50 text-amber-600 dark:bg-amber-950/20 dark:text-amber-400'
                      }`}>
                        {getJobStatusText(job.status)}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </>
        ) : (
          <>
            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
              素材库列表 ({assets.length})
            </h3>
            
            {assets.length === 0 ? (
              <div className="text-center py-8 text-sm text-slate-400 dark:text-slate-500">
                暂无素材视频，点击上方按钮上传
              </div>
            ) : (
              assets.map((asset) => {
                const isActive = asset.asset_id === activeAssetId;
                return (
                  <button
                    key={asset.asset_id}
                    onClick={() => onSelectAsset(asset.asset_id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex flex-col gap-1.5 ${
                      isActive
                        ? 'bg-indigo-50/80 border-indigo-200 dark:bg-indigo-950/30 dark:border-indigo-900/60'
                        : 'bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/40 dark:hover:bg-slate-800/80 border-transparent'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-semibold text-sm text-slate-800 dark:text-slate-200 line-clamp-1" title={asset.original_name}>
                        {asset.original_name}
                      </span>
                      {getAssetStatusIcon(asset.status)}
                    </div>
                    
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                      <Video className="w-3.5 h-3.5 text-slate-400" />
                      {asset.status === 'completed' && asset.profile ? (
                        <span>{asset.profile.metadata.duration.toFixed(1)}s 时长</span>
                      ) : (
                        <span>视频处理中...</span>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                      <span className="font-mono">
                        ID: {asset.asset_id.substring(0, 8)}...
                      </span>
                      <span className={`px-1.5 py-0.5 rounded-md font-semibold ${
                        asset.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400'
                          : asset.status === 'failed'
                          ? 'bg-rose-50 text-rose-600 dark:bg-rose-950/20 dark:text-rose-400'
                          : 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950/20 dark:text-indigo-400'
                      }`}>
                        {getAssetStatusText(asset.status)}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </>
        )}
      </div>
    </aside>
  );
};
