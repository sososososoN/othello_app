import { useEffect, useState, useRef } from "react";

import {
  getGameState,
  playCpuMove,
  playHumanMove,
  resetGame,
  startGame,
} from "@/api/client";
import { AppLayout } from "@/components/layout/AppLayout";
import { GameBoard } from "@/components/game/GameBoard";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import type {
  Difficulty,
  GameMode,
  GameState,
  HumanOrder,
  Position,
} from "@/types/game";

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
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const busyRef = useRef(false);
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
    if (busyRef.current || loading) {
      return;
    }
    busyRef.current = true;
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (cause: unknown) {
      setError(getErrorMessage(cause));
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }
  async function handleStart(): Promise<void> {
    await runAction(async () => {
      setStatus("対局を開始しています...");
      const next = await startGame({
        mode,
        difficulty,
        human_order: mode === "pvp" ? "first" : humanOrder,
      });
      setGame(next);
      setStatus(getTurnLabel(next));
    });
  }
  async function handleMove([y, x]: Position): Promise<void> {
    if (!game || game.turn === 0) {
      return;
    }
    if (game.mode === "pvc" && game.turn !== game.human_color) {
      return;
    }
    await runAction(async () => {
      setStatus("着手しています...");
      const afterHuman = await playHumanMove({ y, x });
      setGame(afterHuman);
      if (
        afterHuman.mode === "pvc" &&
        afterHuman.turn !== 0 &&
        afterHuman.turn === afterHuman.cpu_color
      ) {
        setStatus("CPUが考えています");
        const afterCpu = await playCpuMove();
        setGame(afterCpu);
        setStatus(getTurnLabel(afterCpu));
      } else {
        setStatus(getTurnLabel(afterHuman));
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
      setStatus("CPUが考えています...");
      const next = await playCpuMove();
      setGame(next);
      setStatus(getTurnLabel(next));
    });
  }
  async function handleReset(): Promise<void> {
    await runAction(async () => {
      setStatus("リセットしています...");
      const next = await resetGame();
      setGame(next);
      setMode(next.mode);
      setDifficulty(next.difficulty);
      setHumanOrder("first");
      setStatus("リセットしました");
    });
  }
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
      <div className="mx-auto w-full max-w-2xl space-y-6">
        <section className="text-center">
          <p className="text-sm font-medium text-primary">PLAY AGAINST AI</p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            オセロをプレイ
          </h1>

          <p className="mt-3 text-muted-foreground">
            AIの思考を可視化しながら、オセロを楽しもう。
          </p>
        </section>

        <Card>
          <CardHeader>
            <CardTitle>対局設定</CardTitle>
            <CardDescription>
              モード・難易度・先攻後攻をせんたくしてください。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="game-mode" className="block text-sm font-medium">
                対戦モード
              </label>
              <select
                id="game-mode"
                value={mode}
                disabled={loading || busy}
                onChange={(event) => setMode(event.target.value as GameMode)}
                className="p2 w-full rounded-md border border-border bg-background"
              >
                <option value="pvp">二人で遊ぶ</option>
                <option value="pvc">一人で遊ぶ(CPU戦)</option>
              </select>
            </div>
            {mode === "pvc" && (
              <>
                <div className="space-y-2">
                  <label htmlFor="difficulty" className="block text-sm font-medium">
                    CPUの難易度
                  </label>
                  <select
                    id="difficulty"
                    value={difficulty}
                    disabled={loading || busy}
                    onChange={(event) =>
                      setDifficulty(event.target.value as Difficulty)
                    }
                    className="w-full rounded-md border border-border bg-background p-2"
                  >
                    <option value="easy">Easy</option>
                    <option value="normal">Normal</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label htmlFor="human-order" className="block text-sm font-medium">
                    自分の手番
                  </label>
                  <select
                    id="human-order"
                    value={humanOrder}
                    disabled={loading || busy}
                    onChange={(event) =>
                      setHumanOrder(event.target.value as HumanOrder)
                    }
                    className="p2 w-full rounded-md border border-border bg-background"
                  >
                    <option value="first">先攻（黒）</option>
                    <option value="second">後攻（白）</option>
                    <option value="random">ランダム</option>
                  </select>
                </div>
              </>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                disabled={loading || busy}
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
        <Card>
          <CardHeader className="text-center">
            <CardTitle>Game Board</CardTitle>

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
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}

export default App;
