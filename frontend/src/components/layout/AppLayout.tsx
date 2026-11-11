import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <AppHeader />

      {/* 縦中央配置をやめ、ヘッダー直下からコンテンツを表示 */}
      <main className="mx-auto w-full max-w-7xl px-5 py-6 sm:px-8 sm:py-10">
        {children}
      </main>
    </div>
  );
}
