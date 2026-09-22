import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Used for `npm run dev` only; the built production bundle is served by
// nginx, which proxies /api to the backend service instead (nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://backend:8000",
    },
  },
});
