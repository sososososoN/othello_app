import { BrainCircuit, BookOpen, Gamepad2 } from "lucide-react";

export function AppHeader() {
  return (
    // サイト全体に共通するヘッダー
    <header className="border-b border-border bg-card/80">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
        {/* ロゴとブランド名 */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/15 p-2 text-primary">
            <BrainCircuit className="size-6" aria-hidden="true" />
          </div>

          <div>
            <p className="font-semibold tracking-tight">Othello AI Lab</p>
            <p className="text-xs text-muted-foreground">AI GAME & LEARNING</p>
          </div>
        </div>

        {/* 将来のページ切り替えに備えたナビゲーション */}
        <nav aria-label="メインナビゲーション" className="flex items-center gap-2">
          <a
            href="/"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-accent"
          >
            <Gamepad2 className="size-4" aria-hidden="true" />
            プレイ
          </a>

          <a
            href="/learn"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <BookOpen className="size-4" aria-hidden="true" />
            学ぶ
          </a>
        </nav>
      </div>
    </header>
  );
}
