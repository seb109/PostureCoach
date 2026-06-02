"use client";

import axios from "axios";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/store/auth";
import type { FrameAnalysis, Report, Session, SessionStats, TokenPair, User } from "@/types/api";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && getRefreshToken()) {
      original._retry = true;
      const { data } = await axios.post<TokenPair>(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: getRefreshToken() });
      setTokens(data);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return api(original);
    }
    if (error.response?.status === 401) clearTokens();
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (payload: { email: string; full_name: string; password: string }) => api.post<TokenPair>("/auth/register", payload).then((r) => r.data),
  login: (payload: { email: string; password: string }) => api.post<TokenPair>("/auth/login", payload).then((r) => r.data),
  logout: (refresh_token: string) => api.post("/auth/logout", { refresh_token })
};

export const userApi = {
  me: () => api.get<User>("/users/me").then((r) => r.data),
  update: (payload: { full_name?: string }) => api.put<User>("/users/me", payload).then((r) => r.data)
};

export const sessionApi = {
  start: () => api.post<{ session: Session }>("/sessions/start").then((r) => r.data.session),
  stop: (id: string) => api.post<{ session: Session; report_id: string | null }>(`/sessions/${id}/stop`).then((r) => r.data),
  list: () => api.get<Session[]>("/sessions").then((r) => r.data),
  get: (id: string) => api.get<Session>(`/sessions/${id}`).then((r) => r.data),
  stats: () => api.get<SessionStats>("/sessions/stats").then((r) => r.data),
  metric: (payload: { session_id: string; score: number; classification: string; ratio?: number | null; distance?: number | null; angle?: number | null; alert?: string | null }) =>
    api.post("/sessions/metrics", payload).then((r) => r.data)
};

export const postureApi = {
  analyze: (image_base64: string) => api.post<FrameAnalysis>("/posture/analyze", { image_base64 }).then((r) => r.data)
};

export const reportApi = {
  list: () => api.get<Report[]>("/reports").then((r) => r.data),
  get: (id: string) => api.get<Report>(`/reports/${id}`).then((r) => r.data),
  generate: (session_id: string) => api.post<Report>("/reports/generate", { session_id }).then((r) => r.data),
  download: (id: string) => api.get<Blob>(`/reports/${id}/download`, { responseType: "blob" }).then((r) => r.data)
};
