import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { NewJobForm } from './components/NewJobForm';
import { JobDetails } from './components/JobDetails';
import { UploadAssetForm } from './components/UploadAssetForm';
import { AssetDetails } from './components/AssetDetails';
import type { VideoJob, AssetLibraryItem, CreateVideoJobRequest } from './types';
import { Film, Sparkles, AlertCircle, Database, Upload } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'jobs' | 'assets'>('jobs');
  const [jobs, setJobs] = useState<VideoJob[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  
  const [assets, setAssets] = useState<AssetLibraryItem[]>([]);
  const [activeAssetId, setActiveAssetId] = useState<string | null>(null);

  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(false);

  // 1. Fetch initial jobs and assets
  const fetchJobs = async () => {
    try {
      const res = await fetch('/api/video-jobs');
      if (!res.ok) throw new Error('无法连接后端 API');
      const data = await res.json();
      setJobs(data);
    } catch (err: any) {
      console.error('Error fetching jobs:', err);
      setError('获取任务列表失败，请确保 Python 后端已启动并正常工作');
    }
  };

  const fetchAssets = async () => {
    try {
      const res = await fetch('/api/assets');
      if (!res.ok) throw new Error('无法拉取素材库数据');
      const data = await res.json();
      setAssets(data);
    } catch (err: any) {
      console.error('Error fetching assets:', err);
      setError('获取素材库失败，请确保 Python 后端已启动并正常工作');
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchJobs(), fetchAssets()]);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  // 2. Setup theme preference
  useEffect(() => {
    const isDark = localStorage.getItem('theme') === 'dark' || 
      (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    
    setDarkMode(isDark);
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const handleToggleDarkMode = () => {
    const nextDark = !darkMode;
    setDarkMode(nextDark);
    if (nextDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  // 3. Polling active job details if it's processing
  useEffect(() => {
    if (!activeJobId) return;

    const activeJob = jobs.find(j => j.job_id === activeJobId);
    if (!activeJob || (activeJob.status === 'succeeded' || activeJob.status === 'failed')) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/video-jobs/${activeJobId}`);
        if (!res.ok) return;
        const updatedJob: VideoJob = await res.json();
        
        setJobs(prevJobs => 
          prevJobs.map(job => (job.job_id === activeJobId ? updatedJob : job))
        );
      } catch (err) {
        console.error('Polling job error:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [activeJobId, jobs]);

  // 4. Polling assets if any are in 'analyzing' state
  useEffect(() => {
    const hasAnalyzing = assets.some(a => a.status === 'analyzing');
    if (!hasAnalyzing) return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/assets');
        if (!res.ok) return;
        const data: AssetLibraryItem[] = await res.json();
        setAssets(data);

        // If the currently viewed asset is analyzing, update its state
        if (activeAssetId) {
          const current = data.find(a => a.asset_id === activeAssetId);
          if (current && current.status !== 'analyzing') {
            // Keep activeAssetId selected, state will update automatically in render
          }
        }
      } catch (err) {
        console.error('Polling assets error:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [assets, activeAssetId]);

  // 5. Handlers
  const handleCreateJob = async (request: CreateVideoJobRequest) => {
    const res = await fetch('/api/video-jobs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '提交任务失败');
    }

    const result = await res.json();
    
    // Refresh jobs list
    await fetchJobs();
    
    // Select the new job
    setActiveJobId(result.job_id);
    setIsCreating(false);
    setActiveTab('jobs');
  };

  const handleUploadAssetSuccess = async () => {
    await fetchAssets();
    setIsCreating(false);
    
    // Auto-select the first asset (usually newest)
    const list = await (await fetch('/api/assets')).json();
    if (list.length > 0) {
      setActiveAssetId(list[0].asset_id);
    }
  };

  const handleDeleteAsset = async (assetId: string) => {
    const res = await fetch(`/api/assets/${assetId}`, {
      method: 'DELETE',
    });

    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '删除素材失败');
    }

    // Refresh assets
    await fetchAssets();
    
    if (activeAssetId === assetId) {
      setActiveAssetId(null);
    }
  };

  const activeJob = jobs.find((j) => j.job_id === activeJobId);
  const activeAsset = assets.find((a) => a.asset_id === activeAssetId);

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors overflow-hidden">
      
      {/* Sidebar Navigation */}
      <Sidebar
        jobs={jobs}
        activeJobId={activeJobId}
        onSelectJob={(id) => {
          setActiveJobId(id);
          setIsCreating(false);
        }}
        assets={assets}
        activeAssetId={activeAssetId}
        onSelectAsset={(id) => {
          setActiveAssetId(id);
          setIsCreating(false);
        }}
        activeTab={activeTab}
        onChangeTab={(tab) => {
          setActiveTab(tab);
          setIsCreating(false);
        }}
        onCreateNew={() => {
          setIsCreating(true);
        }}
        darkMode={darkMode}
        onToggleDarkMode={handleToggleDarkMode}
      />

      {/* Main Panel */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-3">
            <LoaderComponent />
            <p className="text-sm text-slate-500 dark:text-slate-400">正在载入 Studio 画板...</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 p-6 rounded-3xl max-w-md text-center space-y-4 shadow-lg">
              <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
              <div className="space-y-1">
                <h3 className="font-bold text-rose-800 dark:text-rose-450">连接服务异常</h3>
                <p className="text-xs text-rose-700 dark:text-rose-400">{error}</p>
              </div>
              <button 
                onClick={() => { setError(null); loadData(); }}
                className="py-2 px-5 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-semibold transition-all shadow-md shadow-rose-100 dark:shadow-none"
              >
                重试连接
              </button>
            </div>
          </div>
        ) : isCreating ? (
          /* Create forms depending on active tab */
          activeTab === 'jobs' ? (
            <NewJobForm
              assets={assets}
              onSubmit={handleCreateJob}
              onCancel={() => {
                setIsCreating(false);
                if (jobs.length > 0 && !activeJobId) {
                  setActiveJobId(jobs[0].job_id);
                }
              }}
            />
          ) : (
            <UploadAssetForm
              onUploadSuccess={handleUploadAssetSuccess}
              onCancel={() => {
                setIsCreating(false);
                if (assets.length > 0 && !activeAssetId) {
                  setActiveAssetId(assets[0].asset_id);
                }
              }}
            />
          )
        ) : activeTab === 'jobs' ? (
          activeJob ? (
            <JobDetails job={activeJob} />
          ) : (
            /* Welcome Jobs */
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-6">
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-3xl blur opacity-30 group-hover:opacity-40 transition duration-1000"></div>
                <div className="relative p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl flex items-center justify-center">
                  <Film className="w-12 h-12 text-indigo-650 dark:text-indigo-400" />
                </div>
              </div>

              <div className="max-w-md space-y-2">
                <h2 className="text-xl md:text-2xl font-bold text-slate-850 dark:text-slate-100">欢迎来到 VideoCraft 剪辑室</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  选择侧边栏的任务，或立即点击新建，从已分析的素材库中选取素材生成您的智能短视频。
                </p>
              </div>

              <button
                onClick={() => setIsCreating(true)}
                className="flex items-center gap-2 py-3 px-6 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl font-medium shadow-md shadow-indigo-150 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm"
              >
                <Sparkles className="w-4 h-4" />
                <span>立即新建剪辑任务</span>
              </button>
            </div>
          )
        ) : activeAsset ? (
          <AssetDetails item={activeAsset} onDelete={handleDeleteAsset} />
        ) : (
          /* Welcome Assets */
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-6">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-3xl blur opacity-30 group-hover:opacity-40 transition duration-1000"></div>
              <div className="relative p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl flex items-center justify-center">
                <Database className="w-12 h-12 text-indigo-650 dark:text-indigo-400" />
              </div>
            </div>

            <div className="max-w-md space-y-2">
              <h2 className="text-xl md:text-2xl font-bold text-slate-850 dark:text-slate-100">视频素材库 (Asset Library)</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                上传您的视频素材。系统会在后台提取关键帧并使用 Vision 大模型进行全局内容分析、推荐营销用途和语义分段，完成后即可供剪辑使用。
              </p>
            </div>

            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 py-3 px-6 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-xl font-medium shadow-md shadow-indigo-150 dark:shadow-none hover:shadow-indigo-200 transition-all text-sm"
            >
              <Upload className="w-4.5 h-4.5" />
              <span>立即上传视频素材</span>
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

const LoaderComponent = () => (
  <div className="relative w-10 h-10">
    <div className="absolute inset-0 rounded-full border-4 border-slate-250 dark:border-slate-800" />
    <div className="absolute inset-0 rounded-full border-4 border-indigo-600 dark:border-indigo-400 border-t-transparent animate-spin" />
  </div>
);

export default App;
