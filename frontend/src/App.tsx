
import { AppLayout } from "@/components/layout/AppLayout";
import { GameBoard } from "@/components/game/GameBoard";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Board, Position } from "@/types/game";

// バックエンドのcreate_board()と同じ初期盤面。
// 0=空き、1=黒、2=白
const initialBoard: Board = [
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 2, 1, 0, 0, 0],
  [0, 0, 0, 1, 2, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
  [0, 0, 0, 0, 0, 0, 0, 0],
];

// Python側のget_valid_moves()に対応する初期合法手
const initialValidMoves: Position[] = [
  [2, 3],
  [3, 2],
  [4, 5],
  [5, 4],
];

function App() {
  return (
    <AppLayout>
      <section className="mb-8">
        <p className="text-sm font-medium text-primary">
          PLAY AGAINST AI
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          オセロをプレイ
        </h1>

        <p className="mt-3 text-muted-foreground">
          AIの思考を可視化しながら、オセロを楽しもう。
        </p>
      </section>

      <Card className="mx-auto w-full max-w-2xl">
        <CardHeader className="text-center">
          <CardTitle>Game Board</CardTitle>
          <CardDescription>
            初期盤面のプレビュー（API連携前）
          </CardDescription>
        </CardHeader>

        <CardContent className="flex justify-center">
          <GameBoard
            board={initialBoard}
            validMoves={initialValidMoves}
          />
        </CardContent>
      </Card>
    </AppLayout>
  );
}

export default App;
