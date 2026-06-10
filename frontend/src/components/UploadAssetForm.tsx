import React, { useState, useRef } from 'react';
import { Upload, X, Film, AlertCircle, RefreshCw } from 'lucide-react';

interface UploadAssetFormProps {
  onUploadSuccess: () => Promise<void>;
  onCancel: () => void;
}

export const UploadAssetForm: React.FC<UploadAssetFormProps> = ({ onUploadSuccess, onCancel }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const validateFiles = (selectedFiles: FileList | null): File[] => {
    if (!selectedFiles) return [];
    const validFiles: File[] = [];
    const allowedExtensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv'];
    const maxSizeBytes = 100 * 1024 * 1024; // 100MB

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!allowedExtensions.includes(extension)) {
        setError(`不支持的文件格式: ${file.name}。仅支持 mp4, mov, avi, webm, mkv。`);
        return [];
      }
      if (file.size > maxSizeBytes) {
        setError(`文件大小超出100MB限制: ${file.name}。`);
        return [];
      }
      validFiles.push(file);
    }
    setError(null);
    return validFiles;
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const valid = validateFiles(e.dataTransfer.files);
    if (valid.length > 0) {
      setFiles((prev) => [...prev, ...valid]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valid = validateFiles(e.target.files);
    if (valid.length > 0) {
      setFiles((prev) => [...prev, ...valid]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      setError('请选择至少一个视频文件进行上传');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // Upload files sequentially or in parallel
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/assets', {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || `上传 ${file.name} 失败`);
        }
      }

      await onUploadSuccess();
    } catch (err: any) {
      setError(err.message || '上传素材失败，请重试');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 h-full overflow-y-auto">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 md:p-8 shadow-xl shadow-slate-100/50 dark:shadow-none">
        
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 rounded-2xl">
            <Upload className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-slate-800 dark:text-slate-100">上传视频至素材库</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">上传后，AI 将在后台自动分析视频场景并提取语义分段</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 text-rose-700 dark:text-rose-400 rounded-2xl flex gap-3 items-start text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex flex-col gap-2">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={triggerFileInput}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
                isDragOver
                  ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20'
                  : 'border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-slate-50/50 dark:hover:bg-slate-850/20'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".mp4,.mov,.avi,.webm,.mkv"
                multiple
                className="hidden"
              />
              <Upload className="w-12 h-12 text-slate-400 dark:text-slate-500 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-350">
                拖拽视频文件到这里，或 <span className="text-indigo-600 dark:text-indigo-400">点击上传</span>
              </p>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                支持格式：mp4, mov, avi, webm, mkv。单个视频大小限制 100MB 以内。
              </p>
            </div>

            {files.length > 0 && (
              <div className="mt-4 space-y-2 max-h-60 overflow-y-auto pr-1">
                {files.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800/80 rounded-xl text-sm"
                  >
                    <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300 truncate">
                      <Film className="w-4 h-4 text-indigo-500 shrink-0" />
                      <span className="truncate font-medium">{file.name}</span>
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(idx);
                      }}
                      className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800/85">
            <button
              type="button"
              onClick={onCancel}
              disabled={isUploading}
              className="py-2.5 px-5 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-850/40 text-slate-650 dark:text-slate-300 font-medium rounded-xl transition-all text-sm"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isUploading || files.length === 0}
              className="flex items-center gap-2 py-2.5 px-6 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-medium rounded-xl shadow-md shadow-indigo-100 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>上传并提取分析中...</span>
                </>
              ) : (
                <span>确认上传</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
