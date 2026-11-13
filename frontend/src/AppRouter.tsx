import { Route, Routes } from "react-router";

import App from "./App";
import { LearnPage } from "./pages/LearnPage";
import { ArticlePage } from "./pages/ArticlePage";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/learn" element={<LearnPage />} />
      <Route path="/learn/:slug" element={<ArticlePage />} />
      <Route path="*" element={<p>ページが見つかりません</p>} />
    </Routes>
  );
}
