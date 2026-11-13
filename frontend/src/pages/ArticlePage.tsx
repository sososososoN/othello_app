import { Link, useParams } from "react-router";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { AppLayout } from "@/components/layout/AppLayout";
import { MinimaxDemo } from "@/components/learning/MinimaxDemo";
import { getArticle } from "@/content/articles";

export function ArticlePage() {
  // URLの /learn/:slug から記事IDを取得
  const { slug } = useParams<{ slug: string }>();
  const article = slug ? getArticle(slug) : undefined;

  // 存在しない記事を開いた場合
  if (!article) {
    return (
      <AppLayout>
        <div className="mx-auto max-w-3xl space-y-4">
          <h1 className="text-xl font-semibold">記事が見つかりません</h1>
          <Link to="/learn" className="text-sm text-primary underline">
            記事一覧へ戻る
          </Link>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-3xl">
        <Link to="/learn" className="text-sm text-muted-foreground hover:text-primary">
          ← 記事一覧へ戻る
        </Link>

        <p className="mt-8 text-sm text-primary">{article.level}</p>

        {/* Markdown内の見出しや本文をReactとして描画 */}
        <article className="mt-4 space-y-5 leading-8 [&_h1]:text-2xl [&_h1]:font-semibold [&_h2]:mt-10 [&_h2]:border-b [&_h2]:border-border [&_h2]:pb-2 [&_h2]:text-xl [&_h2]:font-semibold [&_li]:ml-5 [&_ol]:list-decimal [&_strong]:font-semibold [&_ul]:list-disc">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.content}</ReactMarkdown>
        </article>

        {/* Minimaxの記事だけに探索木デモを表示 */}
        {article.slug === "minimax" && (
          <section className="mt-12 border-t border-border pt-8">
            <MinimaxDemo />
          </section>
        )}
      </div>
    </AppLayout>
  );
}
