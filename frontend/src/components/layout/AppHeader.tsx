export function AppHeader() {
  return (
    // サイト全体に共通するヘッダー
    <header className="border-b border-border bg-background">
      <div className="pag-4 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <a href="/" className="flex items-center gap-3">
          <span aria-hidden="true" className="relative block size-8 shrink-0">
            <span className="absolute top-1 left-0 size-5 rounded-full bg-stone-black" />
            <span className="absolute right-0 bottom-1 size-5 rounded-full border border-board-border bg-stone-white" />
          </span>
          <span className="text-lg font-semibold tracking-[0.08em]">OTHELLO</span>
        </a>
        <nav
          aria-label="メインナビゲーション"
          className="flex items-center gap-6 text-sm"
        >
          <a href="/" aria-current="page" className="font-medium text-foreground">
            対局
          </a>
          <a
            href="/learn"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            学ぶ
          </a>
        </nav>
      </div>
    </header>
  );
}
