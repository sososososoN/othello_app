import { Link } from "react-router";

import { AppLayout } from "@/components/layout/AppLayout";
import { articles } from "@/content/articles";

export function LearnPage() {
  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl space-y-10">
        <header className="border-b border-border pb-5">
          <h1 className="text-2xl font-semibold">アルゴリズムを学ぶ</h1>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            オセロのCPUが次の一手を決める仕組みを、解説とデモから学びます。
          </p>
        </header>

        <section aria-labelledby="articles-heading" className="space-y-4">
          <h2 id="articles-heading" className="text-lg font-semibold">
            学習コラム
          </h2>

          <div className="grid gap-4 sm:grid-cols-2">
            {articles.map((article) => (
              <Link
                key={article.slug}
                to={`/learn/${article.slug}`}
                className="block rounded-md border border-border p-5 transition-colors hover:border-primary focus-visible:outline-2 focus-visible:outline-primary"
              >
                <span className="text-xs text-primary">{article.level}</span>
                <h3 className="mt-2 font-semibold">{article.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {article.description}
                </p>
                <span className="mt-5 inline-block text-sm font-medium text-primary">
                  記事を読む →
                </span>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
