// Claude API 클라이언트 — 서버에서만 import (키 노출 방지)
import Anthropic from "@anthropic-ai/sdk";

export const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
});

// AI 큐레이터가 쓰는 모델 (빠르고 저렴한 최신 Haiku)
export const CURATOR_MODEL = "claude-haiku-4-5-20251001";
