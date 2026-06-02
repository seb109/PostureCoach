export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
};

export type PostureMetric = {
  id: string;
  captured_at: string;
  score: number;
  classification: string;
  ratio: number | null;
  distance: number | null;
  angle: number | null;
  alert: string | null;
};

export type Session = {
  id: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  average_score: number;
  status: string;
  report_id: string | null;
  metrics: PostureMetric[];
};

export type SessionStats = {
  total_sessions: number;
  total_minutes: number;
  average_score: number;
  good_percentage: number;
  slight_percentage: number;
  bad_percentage: number;
};

export type FrameAnalysis = {
  cal_phase: string;
  cal_progress: number;
  cal_seconds_left: number;
  status: string | null;
  ratio: number | null;
  distance: number | null;
  angle: number | null;
  pose_visible: boolean;
  alert_progress: number;
  alert_seconds_left: number;
  is_flashing: boolean;
  cooldown_seconds: number;
};

export type Report = {
  id: string;
  session_id: string;
  generated_at: string;
  summary: Record<string, unknown>;
  file_path: string | null;
  download_url: string | null;
};
