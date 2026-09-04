import path from "path"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/dashboard": {
        target: "http://127.0.0.1:8000",
        bypass: (req) => {
          if (req.headers.accept?.includes("text/html")) {
            return "/index.html"
          }
        },
      },
      "/admin": "http://127.0.0.1:8000",
      "/webhooks": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/payments": {
        target: "http://127.0.0.1:8000",
        bypass: (req) => {
          if (req.headers.accept?.includes("text/html")) {
            return "/index.html"
          }
        },
      },
      "/agent": "http://127.0.0.1:8000",
    },
  },
})
