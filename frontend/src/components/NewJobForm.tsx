import React, { useState } from 'react';
import { Sparkles, AlertCircle, Database, Film, Clock, Check } from 'lucide-react';
import type { AssetLibraryItem, CreateVideoJobRequest } from '../types';

interface NewJobFormProps {
  assets: AssetLibraryItem[];
  onSubmit: (request: CreateVideoJobRequest) => Promise<void>;
  onCancel: () => void;
}

export const NewJobForm: React.FC<NewJobFormProps> = ({ assets, onSubmit, onCancel }) => {
  const [productName, setProductName] = useState('AI 编程训练营');
  const [targetAudience, setTargetAudience] = useState('想转行 AI 的程序员');
  const [sellingPoints, setSellingPoints] = useState('零基础入门 AI Agent, 带项目实战, 适合 Python 初学者');
  const [style, setStyle] = useState('科技感、快节奏');
  const [platform, setPlatform] = useState('douyin');
  const [durationSeconds, setDurationSeconds] = useState(15);
  
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Only selectable if completed
  const completedAssets = assets.filter(a => a.status === 'completed' && a.profile);

  const filteredAssets = completedAssets.filter(a => 
    a.original_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.profile?.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const toggleSelectAsset = (assetId: string) => {
    setSelectedAssetIds((prev) => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId) 
        : [...prev, assetId]
    );
  };

  const getSelectedTotalDuration = () => {
    return selectedAssetIds.reduce((sum, id) => {
      const asset = completedAssets.find(a => a.asset_id === id);
      return sum + (asset?.profile?.metadata.duration || 0);
    }, 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) {
      setError('请输入产品名称');
      return;
    }
    if (selectedAssetIds.length === 0) {
      setError('请选择至少一个视频素材');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const request: CreateVideoJobRequest = {
        product_name: productName,
        target_audience: targetAudience,
        selling_points: sellingPoints,
        style: style,
        platform: platform,
        duration_seconds: durationSeconds,
        asset_ids: selectedAssetIds
      };

      await onSubmit(request);
    } catch (err: any) {
      setError(err.message || '创建任务失败，请检查后端服务');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 h-full overflow-y-auto">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-100/50 dark:shadow-none">
        
        {/* Title */}
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 rounded-2xl">
            <Sparkles className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-slate-800 dark:text-slate-100">新建智能剪辑任务</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">选择素材库中已分析的视频，AI 将进行精准编排并渲染短视频</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-rose-700 dark:text-rose-450 rounded-2xl flex gap-3 items-start text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Grid Layout for Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Product Name */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">产品名称</label>
              <input
                type="text"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="例如：AI 编程训练营"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all text-sm"
              />
            </div>

            {/* Target Audience */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">目标受众</label>
              <input
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="例如：想转行 AI 的程序员"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all text-sm"
              />
            </div>

            {/* Style */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">剪辑风格</label>
              <input
                type="text"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                placeholder="例如：科技感、快节奏"
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all text-sm"
              />
            </div>

            {/* Platform Selection */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">投放平台</label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all text-sm"
              >
                <option value="douyin">抖音 (9:16)</option>
                <option value="wechat_channels">微信视频号 (9:16)</option>
                <option value="kuaishou">快手 (9:16)</option>
                <option value="xiaohongshu">小红书 (3:4)</option>
              </select>
            </div>
          </div>

          {/* Selling Points */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">核心卖点 (以逗号分隔)</label>
            <textarea
              rows={2}
              value={sellingPoints}
              onChange={(e) => setSellingPoints(e.target.value)}
              placeholder="零基础入门 AI Agent, 带项目实战, 适合 Python 初学者"
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-800 dark:text-slate-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none transition-all text-sm resize-none"
            />
          </div>

          {/* Duration Slider */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-semibold text-slate-700 dark:text-slate-350">期望视频时长</label>
              <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400">{durationSeconds} 秒</span>
            </div>
            <input
              type="range"
              min="5"
              max="60"
              step="5"
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(parseInt(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600 dark:accent-indigo-400 focus:outline-none"
            />
            <div className="flex justify-between text-[10px] text-slate-400 dark:text-slate-500">
              <span>5 秒</span>
              <span>15 秒 (推荐)</span>
              <span>30 秒</span>
              <span>60 秒</span>
            </div>
          </div>

          {/* Decoupled Asset Library Card Selector */}
          <div className="space-y-3 pt-2">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-350 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-indigo-550" />
                  <span>选择素材库视频 (多选)</span>
                </label>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  已选择 <span className="font-bold text-indigo-600 dark:text-indigo-400">{selectedAssetIds.length}</span> 个视频，已勾选总时长: <span className="font-semibold">{getSelectedTotalDuration().toFixed(1)} 秒</span>
                </p>
              </div>

              {/* Search filter */}
              <input
                type="text"
                placeholder="搜索素材名或标签..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs"
              />
            </div>

            {completedAssets.length === 0 ? (
              <div className="border border-slate-200 dark:border-slate-800 p-8 rounded-2xl text-center text-slate-500 dark:text-slate-400 bg-slate-50/20">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                <p className="text-sm font-semibold">素材库内暂无已分析的视频</p>
                <p className="text-xs mt-1">请先切至“素材管理”页签上传并等待 AI 提取分析完毕后再创建任务。</p>
              </div>
            ) : filteredAssets.length === 0 ? (
              <div className="text-center py-6 text-xs text-slate-400 dark:text-slate-500">
                无匹配搜索关键词的已分析素材。
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[300px] overflow-y-auto pr-1">
                {filteredAssets.map((asset) => {
                  const isSelected = selectedAssetIds.includes(asset.asset_id);
                  return (
                    <div
                      key={asset.asset_id}
                      onClick={() => toggleSelectAsset(asset.asset_id)}
                      className={`border p-3.5 rounded-2xl cursor-pointer transition-all flex flex-col justify-between space-y-3 relative overflow-hidden select-none ${
                        isSelected
                          ? 'bg-indigo-50/50 dark:bg-indigo-950/20 border-indigo-500 dark:border-indigo-400 shadow-md ring-1 ring-indigo-500 dark:ring-indigo-400'
                          : 'bg-white hover:bg-slate-50 dark:bg-slate-900 dark:hover:bg-slate-850/60 border-slate-200 dark:border-slate-800'
                      }`}
                    >
                      {/* Check badge */}
                      {isSelected && (
                        <div className="absolute top-0 right-0 bg-indigo-500 dark:bg-indigo-400 text-white p-1 rounded-bl-xl">
                          <Check className="w-3.5 h-3.5 stroke-[3]" />
                        </div>
                      )}

                      <div className="space-y-1 pr-4">
                        <h4 className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate" title={asset.original_name}>
                          {asset.original_name}
                        </h4>
                        <p className="text-[10px] text-slate-550 dark:text-slate-400 line-clamp-1 leading-relaxed">
                          {asset.profile?.content_summary}
                        </p>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-400 dark:text-slate-500">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-indigo-500 shrink-0" />
                          <span className="font-semibold">{asset.profile?.metadata.duration.toFixed(1)}s 时长</span>
                          <span>({asset.profile?.metadata.width}x{asset.profile?.metadata.height})</span>
                        </div>
                        <span className="font-mono text-[9px] uppercase bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded">
                          {asset.asset_id.substring(0, 6)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800/80">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="py-2.5 px-5 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-650 dark:text-slate-350 font-medium rounded-xl transition-all text-sm"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isSubmitting || selectedAssetIds.length === 0}
              className="flex items-center gap-2 py-2.5 px-6 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-medium rounded-xl shadow-md shadow-indigo-100 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>任务创建并轮询中...</span>
                </>
              ) : (
                <span>生成剪辑视频</span>
              )}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
