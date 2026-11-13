import minimaxContent from "./minimax.md?raw";

export type Article = {
  slug: string;
  title: string;
  description: string;
  level: string;
  content: string;
};

export const articles: readonly Article[] = [
  {
    slug: "minimax",
    title: "Minimax法とは？",
    description: "相手も最善の手を選ぶと仮定して、最適な手を探索する方法",
    level: "初級",
    content: minimaxContent,
  },
];

export function getArticle(slug: string): Article | undefined {
  return articles.find((article) => article.slug === slug);
}
