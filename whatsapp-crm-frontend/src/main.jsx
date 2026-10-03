// main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { Toaster } from 'sonner'
import { applyTheme } from './lib/theme'

// Apply the saved theme before first paint to avoid a light/dark flash.
applyTheme()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster position="top-right" richColors closeButton />
  </React.StrictMode>
)