import { analysisResultSchema, gameStateSchema } from "./schemas";

import type {
  AnalysisResult,
  GameState,
  MoveRequest,
  StartGameRequest,
} from "@/types/game";

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getErrorMessage(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }
  if ("error" in payload && typeof payload.error === "string") {
    return payload.error;
  }
  if ("detail" in payload && typeof payload.detail === "string") {
    return payload.detail;
  }
  return null;
}

async function request(
  path: string,
  method: "GET" | "POST",
  body?: unknown,
): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError("サーバーに接続できませんでした", 0);
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError("サーバーから不正な応答が返されました", response.status);
  }
  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(payload) ?? "APIリクエストに失敗しました",
      response.status,
    );
  }
  return payload;
}

function parseGameState(payload: unknown): GameState {
  const result = gameStateSchema.safeParse(payload);
  if (!result.success) {
    throw new ApiError("ゲーム状態の形式が不正です", 0);
  }
  return result.data;
}

function parseAnalysisResult(payload: unknown): AnalysisResult {
  const result = analysisResultSchema.safeParse(payload);
  if (!result.success) {
    throw new ApiError("解析結果の形式が不正です", 0);
  }
  return result.data;
}

export async function getGameState(): Promise<GameState> {
  return parseGameState(await request("/state", "GET"));
}

export async function startGame(settings: StartGameRequest): Promise<GameState> {
  return parseGameState(await request("/games/start", "POST", settings));
}

export async function playHumanMove(move: MoveRequest): Promise<GameState> {
  return parseGameState(await request("/moves/player", "POST", move));
}

export async function playCpuMove(analysisToken?: string): Promise<GameState> {
  const body = analysisToken === undefined ? {} : { analysis_token: analysisToken };
  return parseGameState(await request("/moves/cpu", "POST", body));
}

export async function resetGame(): Promise<GameState> {
  return parseGameState(await request("/reset", "POST"));
}

export async function getAnalysis(depth?: number): Promise<AnalysisResult> {
  const path = depth === undefined ? "/analysis" : `/analysis?depth=${depth}`;
  return parseAnalysisResult(await request(path, "GET"));
}
