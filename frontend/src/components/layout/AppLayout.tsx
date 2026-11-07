
import type { ReactNode } from "react";
import { AppHeader } from "./AppHeader";

// childrenにはページ固有のReact要素が入る
type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-dvh bg-background text-foreground">
      <AppHeader />

      {/* 全ページで共通の横幅と余白 */}
      <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:py-12">
        {children}
      </main>
    </div>
  );
}
