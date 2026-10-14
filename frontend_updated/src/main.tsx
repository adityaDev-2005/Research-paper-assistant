import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/inter'
import './styles.css'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'

window.addEventListener('error', (e) => { const r = document.getElementById('root'); if (r && !r.children.length) r.innerHTML = '<pre style="padding:24px;white-space:pre-wrap">Startup error: ' + String(e.message).replace(/</g, '&lt;') + '</pre>' })

createRoot(document.getElementById('root')!).render(<StrictMode><ErrorBoundary><App /></ErrorBoundary></StrictMode>)
