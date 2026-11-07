
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

// バックエンドと同じ初期盤面
// 0: 空きマス、1: 黒石、2: 白石
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

// 初期状態で黒が置ける4か所
const initialValidMoves: Position[] = [
  [2, 3],
  [3, 2],
  [4, 5],
  [5, 4],
];

function App() {
  return (
    <AppLayout>
      {/*
        mx-auto:
          コンテンツ全体を横方向の中央へ

        max-w-2xl:
          コンテンツの最大幅を制限
      */}
      <div className="mx-auto w-full max-w-2xl">
        {/* タイトル部分 */}
        <section className="mb-8 text-center">
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

        {/* 盤面カード */}
        <Card className="w-full">
          <CardHeader className="text-center">
            <CardTitle>Game Board</CardTitle>

            <CardDescription>
              初期盤面のプレビュー（API連携前）
            </CardDescription>
          </CardHeader>

          {/* カード内部の盤面も中央揃え */}
          <CardContent className="flex justify-center">
            <GameBoard
              board={initialBoard}
              validMoves={initialValidMoves}
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}

export default App;
