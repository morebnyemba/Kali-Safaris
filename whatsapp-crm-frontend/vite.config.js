// whatsappcrm-frontend/vite.config.js
import path from "path"
import tailwindcss from "@tailwindcss/vite" // Assuming you're using this plugin for Tailwind
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // This configuration is for the Vite development server.
    // The `allowedHosts` option specifies which hostnames are permitted to access the dev server.
    // This is a security measure to prevent DNS rebinding attacks.
    //
    // If you are using a tunneling service like ngrok to expose your local dev server
    // and you see a "Blocked request" error, you may need to add your ngrok hostname here.
    // e.g., 'my-tunnel.ngrok-free.app'
    allowedHosts: [
      'localhost',
      '127.0.0.1',
    ],
    // You can also specify the port if it's not the default 5173
    // port: 5173, 
  }
})
