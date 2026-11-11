import { useEffect, useRef, useState } from "react";
import { ChevronDown, LockKeyhole } from "lucide-react";

import {
  ApiError,
  getAnalysis,
  getGameState,
  playCpuMove,
  playHumanMove,
  resetGame,
  startGame,
} from "@/api/client";
import { AnalysisPanel } from "@/components/game/AnalysisPanel";
import { GameBoard } from "@/components/game/GameBoard";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type {
  AnalysisResult,
  Difficulty,
  GameMode,
  GameState,
  HumanOrder,
  Position,
} from "@/types/game";

const selectClassName =
  "h-10 w-full appearance-none rounded-lg border border-border " +
  "bg-background px-3 pr-10 text-sm font-medium text-foreground " +
  "shadow-sm transition-colors " +
  "hover:border-primary/40 " +
  "focus-visible:outline-none focus-visible:ring-2 " +
  "focus-visible:ring-primary/40 " +
  "disabled:cursor-not-allowed disabled:bg-muted " +
  "disabled:text-muted-foreground disabled:opacity-70";

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "予期しないエラーが発生しました";
}

function getTurnLabel(game: GameState): string {
  if (game.turn === 0) {
    return "対局終了";
  }

  if (game.mode === "pvc") {
    return game.turn === game.cpu_color ? "CPUの手番" : "あなたの手番";
  }

  return game.turn === 1 ? "黒の手番" : "白の手番";
}

function App() {
  const [game, setGame] = useState<GameState | null>(null);

  const [mode, setMode] = useState<GameMode>("pvp");
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [humanOrder, setHumanOrder] = useState<HumanOrder>("first");
  const [hasStarted, setHasStarted] = useState(false);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const busyRef = useRef(false);

  function applyGameState(state: GameState): void {
    setGame(state);
    setMode(state.mode);
    setDifficulty(state.difficulty);
    setHumanOrder(state.human_color === 2 ? "second" : "first");
    setHasStarted(state.started);
    setAnalysis(null);
    setStatus(getTurnLabel(state));
  }

  useEffect(() => {
    let active = true;

    async function loadGame(): Promise<void> {
      try {
        const state = await getGameState();

        if (!active) return;

        setGame(state);
        setMode(state.mode);
        setDifficulty(state.difficulty);
        setHumanOrder(state.human_color === 2 ? "second" : "first");
        setHasStarted(state.started);

        setStatus(getTurnLabel(state));
      } catch (cause: unknown) {
        if (active) {
          setError(getErrorMessage(cause));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadGame();

    return () => {
      active = false;
    };
  }, []);

  async function runAction(action: () => Promise<void>): Promise<void> {
    if (busyRef.current || loading) return;

    busyRef.current = true;
    setBusy(true);
    setError(null);

    try {
      await action();
    } catch (cause: unknown) {
      if (cause instanceof ApiError && cause.status === 409) {
        setAnalysis(null);
        try {
          const latest = await getGameState();
          applyGameState(latest);
          setError(
            "別の操作によって対局状態が変わりました。最新の盤面を読み込みました。",
          );
        } catch (refreshError: unknown) {
          setGame(null);
          setStatus("対局状態を取得できませんでした。");
          setError(`状態の再取得に失敗しました: ${getErrorMessage(refreshError)}`);
        }
      } else {
        setStatus("操作に失敗しました。");
        setError(getErrorMessage(cause));
      }
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  async function executeCpuTurn(): Promise<void> {
    setStatus("CPUが解析しています...");
    setAnalysis(null);

    const result = await getAnalysis();

    setStatus("CPUが着手しています...");

    const next = await playCpuMove(result.analysis_token ?? undefined);

    applyGameState(next);
    setAnalysis(result);
  }

  async function handleStart(): Promise<void> {
    // 追加：対局開始後の再開始は禁止
    if (hasStarted) return;

    await runAction(async () => {
      setStatus("対局を開始しています...");

      const next = await startGame({
        mode,
        difficulty,
        human_order: mode === "pvp" ? "first" : humanOrder,
      });

      applyGameState(next);
    });
  }

  async function handleMove([y, x]: Position): Promise<void> {
    if (!game || game.turn === 0) return;

    if (game.mode === "pvc" && game.turn !== game.human_color) {
      return;
    }

    await runAction(async () => {
      setStatus("着手しています...");

      const afterHuman = await playHumanMove({ y, x });
      applyGameState(afterHuman);

      if (
        afterHuman.mode === "pvc" &&
        afterHuman.turn !== 0 &&
        afterHuman.turn === afterHuman.cpu_color
      ) {
        await executeCpuTurn();
      }
    });
  }

  async function handleCpuMove(): Promise<void> {
    if (
      !game ||
      game.mode !== "pvc" ||
      game.turn === 0 ||
      game.turn !== game.cpu_color
    ) {
      return;
    }

    await runAction(async () => {
      await executeCpuTurn();
    });
  }

  async function handleReset(): Promise<void> {
    await runAction(async () => {
      setStatus("リセットしています...");

      const next = await resetGame();

      applyGameState(next);
      setStatus("リセットしました。設定を変更できます。");
    });
  }

  async function handleRetryLoad(): Promise<void> {
    await runAction(async () => {
      const latest = await getGameState();
      applyGameState(latest);
    });
  }

  const settingsLocked = loading || busy || hasStarted;

  const canPlay =
    game !== null &&
    !loading &&
    !busy &&
    game.turn !== 0 &&
    (game.mode === "pvp" || game.turn === game.human_color);

  const cpuPending =
    game !== null &&
    game.mode === "pvc" &&
    game.turn !== 0 &&
    game.turn === game.cpu_color;

  return (
    <AppLayout>
      <div className="w-full space-y-6">
        <div className="border-b border-border pb-4">
          <h1 className="text-xl font-semibold tracking-tight">オセロ</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            対局とコンピュータの思考解析
          </p>
        </div>

        <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
          <Card className="min-w-0">
            <CardHeader className="text-center">
              <CardTitle>盤面</CardTitle>
              <CardDescription>
                {game ? getTurnLabel(game) : "読み込み中"}
              </CardDescription>
            </CardHeader>

            <CardContent className="flex flex-col items-center gap-5">
              {game ? (
                <>
                  <GameBoard
                    board={game.board}
                    validMoves={game.valid_moves}
                    onSelectMove={(move) => void handleMove(move)}
                    disabled={!canPlay}
                  />

                  {game.mode === "pvc" && (
                    <p className="text-sm text-muted-foreground">
                      あなた：
                      {game.human_color === 1 ? "黒" : "白"}
                      {" / "}
                      CPU：
                      {game.cpu_color === 1 ? "黒" : "白"}
                    </p>
                  )}

                  {cpuPending && !busy && (
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => void handleCpuMove()}
                    >
                      CPUの着手を実行
                    </Button>
                  )}
                </>
              ) : (
                <p className="py-12 text-sm text-muted-foreground">
                  {loading ? "盤面を読み込んでいます..." : "盤面を取得できませんでした"}
                </p>
              )}

              <p
                role="status"
                aria-live="polite"
                className="text-sm text-muted-foreground"
              >
                {status || (game ? getTurnLabel(game) : "読み込み中")}
              </p>

              {error && (
                <div className="space-y-2 text-center">
                  <p role="alert" className="text-sm text-destructive">
                    {error}
                  </p>
                  {!game && !loading && (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={busy}
                      onClick={() => void handleRetryLoad()}
                    >
                      再度読み込み
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
          <div className="min-w-0 space-y-5">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle>対局設定</CardTitle>
                  {hasStarted && (
                    <span
                      role="status"
                      className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                    >
                      <LockKeyhole className="size-3.5" />
                      対局中・設定固定
                    </span>
                  )}
                </div>
                <CardDescription>
                  {hasStarted
                    ? "設定を変更するにはリセットしてください。"
                    : "モード・難易度・先攻後攻を選択してください。"}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* 変更：PCでは設定項目を横一列にする */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <label htmlFor="game-mode" className="block text-sm font-medium">
                      対戦モード
                    </label>

                    <div className="relative">
                      <select
                        id="game-mode"
                        value={mode}
                        disabled={settingsLocked}
                        onChange={(event) => setMode(event.target.value as GameMode)}
                        className={selectClassName}
                      >
                        <option value="pvp">二人で遊ぶ</option>
                        <option value="pvc">一人で遊ぶ（CPU戦）</option>
                      </select>
                      <ChevronDown
                        aria-hidden="true"
                        className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground"
                      />
                    </div>
                  </div>

                  {mode === "pvc" && (
                    <>
                      <div className="space-y-2">
                        <label
                          htmlFor="difficulty"
                          className="block text-sm font-medium"
                        >
                          CPUの難易度
                        </label>

                        <div className="relative">
                          <select
                            id="difficulty"
                            value={difficulty}
                            disabled={settingsLocked}
                            onChange={(event) =>
                              setDifficulty(event.target.value as Difficulty)
                            }
                            className={selectClassName}
                          >
                            <option value="easy">Easy</option>
                            <option value="normal">Normal</option>
                            <option value="hard">Hard</option>
                          </select>
                          <ChevronDown
                            aria-hidden="true"
                            className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label
                          htmlFor="human-order"
                          className="block text-sm font-medium"
                        >
                          自分の手番
                        </label>

                        <div className="relative">
                          <select
                            id="human-order"
                            value={humanOrder}
                            disabled={settingsLocked}
                            onChange={(event) =>
                              setHumanOrder(event.target.value as HumanOrder)
                            }
                            className={selectClassName}
                          >
                            <option value="first">先攻（黒）</option>
                            <option value="second">後攻（白）</option>
                            <option value="random">ランダム</option>
                          </select>
                          <ChevronDown
                            aria-hidden="true"
                            className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground"
                          />
                        </div>
                      </div>
                    </>
                  )}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    disabled={settingsLocked}
                    onClick={() => void handleStart()}
                  >
                    対局を開始する
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    disabled={loading || busy || !game}
                    onClick={() => void handleReset()}
                  >
                    リセット
                  </Button>
                </div>
              </CardContent>
            </Card>

            {analysis && game?.mode === "pvc" ? (
              <AnalysisPanel analysis={analysis} />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>CPUの思考解析</CardTitle>
                  <CardDescription>AIが選んだ手の根拠を確認できます。</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
                    CPUが着手すると、ここに解析結果を表示します。
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default App;
