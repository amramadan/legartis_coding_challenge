import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState('loading...')

  useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui' }}>
      <h1>Legartis – Clause Tracker</h1>
      <p>Backend health: <b>{status}</b></p>
    </div>
  )
}

export default App
