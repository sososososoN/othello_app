
import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  return (
    // 最低でも画面全体の高さを確保する
    // flex-colでヘッダーとメイン領域を縦に並べる
    <div className="flex min-h-dvh flex-col bg-background text-foreground">
      <AppHeader />

      {/*
        flex-1:
          ヘッダー以外の残りの高さを利用

        flex + items-center:
          コンテンツを横方向の中央に配置

        justify-center:
          コンテンツを縦方向の中央に配置

        py-8:
          画面が小さい場合も上下に余白を確保
      */}
      <main className="flex w-full flex-1 items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-7xl">
          {children}
        </div>
      </main>
    </div>
  );
}
