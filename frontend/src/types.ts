export interface VideoRequirement {
  product_name: string;
  target_audience: string;
  selling_points: string[];
  style: string;
  platform: string;
  duration_seconds: number;
}

export interface EditSceneOperation {
  speed: number;
  crop_mode?: string;
  mute_audio: boolean;
}

export interface EditScene {
  scene_id: number;
  asset_id: string;
  source_start: number;
  source_end: number;
  start_time: number;
  end_time: number;
  subtitle: string;
  voiceover?: string;
  transition?: string;
  operation: EditSceneOperation;
}

export interface EditPlan {
  title: string;
  aspect_ratio: string;
  duration_seconds: number;
  timeline: EditScene[];
  warnings: string[];
}

export interface UploadedMaterial {
  file_id: string;
  original_name: string;
  content_type: string;
  local_path: string;
  size_bytes: number;
}

export interface MaterialMatch {
  scene_index: number;
  material_path: string;
  matched_keyword?: string;
  source: 'uploaded' | 'library' | 'fallback';
  fallback_used: boolean;
}

export interface RenderResult {
  status: 'success' | 'failed';
  output_path?: string;
  duration_seconds: number;
  format: string;
  message: string;
}

export type VideoJobStatus =
  | 'queued'
  | 'upload_saved'
  | 'analyzing_assets'
  | 'calling_dify'
  | 'script_ready'
  | 'matching_materials'
  | 'rendering_video'
  | 'succeeded'
  | 'failed';

export interface VideoMetadata {
  duration: number;
  width: number;
  height: number;
  fps: number;
  has_audio: boolean;
  aspect_ratio: string;
}

export interface AssetSegment {
  segment_id: string;
  start: number;
  end: number;
  summary: string;
  tags: string[];
  marketing_role: string;
  quality_score: number;
}

export interface FrameInfo {
  frame_id: string;
  asset_id: string;
  timestamp: number;
  image_path: string;
}

export interface FrameAnalysis {
  description_cn: string;
  description_en?: string;
  shot_type: string;
  main_subject?: string;
  objects: string[];
  human_presence: string;
  product_visibility: string;
  scene_environment: string;
  action?: string;
  visual_quality: string;
  quality_score: number;
  marketing_role: string;
  editing_suggestion?: string;
  tags: string[];
  people_count: number;
  text_on_screen: string[];
  error?: string;
}

export interface AssetProfile {
  asset_id: string;
  original_name: string;
  local_path: string;
  duration: number;
  content_summary: string;
  tags: string[];
  recommended_usage: string[];
  segments: AssetSegment[];
  metadata: VideoMetadata;
  frames?: FrameInfo[];
  frame_analyses?: FrameAnalysis[];
}


export interface VideoJob {
  job_id: string;
  status: VideoJobStatus;
  current_step: string;
  requirement: VideoRequirement;
  uploads: UploadedMaterial[];
  assets: AssetProfile[];
  edit_plan?: EditPlan;
  materials: MaterialMatch[];
  result?: RenderResult;
  video_url?: string;
  error?: string;
  dify_success?: boolean;
}

export interface AssetLibraryItem {
  asset_id: string;
  status: 'analyzing' | 'completed' | 'failed';
  original_name: string;
  local_path: string;
  profile?: AssetProfile;
  error?: string;
}

export interface CreateVideoJobRequest {
  product_name: string;
  target_audience: string;
  selling_points: string;
  style: string;
  platform: string;
  duration_seconds: number;
  asset_ids: string[];
}

