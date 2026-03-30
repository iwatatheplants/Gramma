import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from '../gramma.jsx'

// ── Mock Claude.ai artifact storage with localStorage ──
window.storage = {
  async get(key) {
    const val = localStorage.getItem(key)
    return val ? { value: val } : null
  },
  async set(key, value) {
    localStorage.setItem(key, value)
  },
}

// ── API key setup ──
// Reads from VITE_ANTHROPIC_API_KEY in .env, or prompts once and stores in localStorage.
function getApiKey() {
  if (import.meta.env.VITE_ANTHROPIC_API_KEY) return import.meta.env.VITE_ANTHROPIC_API_KEY
  let key = localStorage.getItem('gramma-api-key')
  if (!key) {
    key = prompt(
      'Enter your Anthropic API key to use Gramma locally.\n' +
      'Get one free at: console.anthropic.com\n\n' +
      '(Stored only in your browser — never sent anywhere except Anthropic)'
    )
    if (key) localStorage.setItem('gramma-api-key', key.trim())
  }
  return key || ''
}

// ── Intercept fetch to inject auth headers on Anthropic API calls ──
// gramma.jsx calls https://api.anthropic.com directly — this patches in
// the key without touching the app code.
const _fetch = window.fetch
window.fetch = (url, opts = {}) => {
  if (typeof url === 'string' && url.includes('api.anthropic.com')) {
    opts = {
      ...opts,
      headers: {
        ...opts.headers,
        'x-api-key': getApiKey(),
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-request-origin': 'user-provided',
      },
    }
  }
  return _fetch(url, opts)
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
