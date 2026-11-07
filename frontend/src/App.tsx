
function App() {
  return (
    // 画面全体をダークテーマにする
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
      {/* 中央のカード */}
      <section className="w-full max-w-lg rounded-2xl border border-emerald-800 bg-slate-900 p-8 text-center shadow-xl">
        <h1 className="text-3xl font-bold text-white">
          Othello AI Lab
        </h1>

        <p className="mt-4 text-slate-300">
          React + TypeScript + Tailwind CSS
        </p>

        <div className="mt-6 rounded-lg bg-emerald-500 px-5 py-3 font-semibold text-slate-950">
          セットアップ確認
        </div>
      </section>
    </main>
  );
}

export default App;
