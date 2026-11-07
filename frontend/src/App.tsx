
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
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      {/* shadcn/uiのカード */}
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Othello AI Lab</CardTitle>
          <CardDescription>
            React + Tailwind CSS + shadcn/ui
          </CardDescription>
        </CardHeader>

        <CardContent className="flex gap-3">
          {/* 次のStepで実際のゲーム操作につなげる */}
          <Button>ゲームを始める</Button>
          <Button variant="outline">AI解析</Button>
        </CardContent>
      </Card>
    </main>
  );
}

export default App;
