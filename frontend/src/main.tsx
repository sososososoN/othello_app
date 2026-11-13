import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import "./index.css";
import { AppRouter } from "./AppRouter";

const container = document.getElementById("root");

if (!container) {
  throw new Error("Root element was not found");
}

createRoot(container).render(
  <StrictMode>
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  </StrictMode>,
);
