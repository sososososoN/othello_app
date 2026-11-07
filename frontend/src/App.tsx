
function App() {
  return (
    // 全体の背景と最低限の余白
    <main className="min-h-screen bg-background px-6 py-12 text-foreground">
      <div className="mx-auto max-w-5xl">
        {/* アプリのタイトル */}
        <header className="mb-10">
          <p className="mb-2 text-sm font-medium text-accent">
            AI GAME & LEARNING
          </p>
          <h1 className="text-4xl font-bold tracking-tight">
            Othello AI Lab
          </h1>
          <p className="mt-3 text-muted">
            React + FastAPIで構築するAIオセロ
          </p>
        </header>

        {/* 共通テーマを使ったカード */}
        <section className="rounded-card border border-border bg-surface p-8 shadow-xl">
          <h2 className="text-xl font-semibold">
            Design System
          </h2>
          <p className="mt-3 text-muted">
            Tailwind CSSのテーマが適用されています。
          </p>

          {/* ボタンの外観確認。操作機能は次の段階で追加 */}
          <div className="mt-6 flex flex-wrap gap-3">
            <div className="rounded-control bg-accent px-5 py-3 font-semibold text-accent-foreground">
              Primary
            </div>
            <div className="rounded-control border border-border bg-surface-raised px-5 py-3">
              Secondary
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default App;
