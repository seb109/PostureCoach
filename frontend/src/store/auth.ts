"use client";

import type { TokenPair } from "@/types/api";

const ACCESS = "posturecoach.access";
const REFRESH = "posturecoach.refresh";

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS);
}

export function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH);
}

export function setTokens(tokens: TokenPair) {
  localStorage.setItem(ACCESS, tokens.access_token);
  localStorage.setItem(REFRESH, tokens.refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS);
  localStorage.removeItem(REFRESH);
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}
