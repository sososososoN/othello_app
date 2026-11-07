
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function App() {
  return (
    <AppLayout>
      <section className="mb-8">
        <p className="text-sm font-medium text-primary">
          PLAY AGAINST AI
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          オセロをプレイ
        </h1>
        <p className="mt-3 text-muted-foreground">
          AIの思考を可視化しながら、オセロを楽しもう。
        </p>
      </section>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Game Dashboard</CardTitle>
          <CardDescription>
            次のステップでオセロ盤面を実装します。
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button disabled>対局を開始</Button>
          <Button variant="outline" disabled>
            AI解析
          </Button>
        </CardContent>
      </Card>
    </AppLayout>
  );
}

export default App;
