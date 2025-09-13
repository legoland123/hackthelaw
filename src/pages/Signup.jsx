// polyfill: provide crypto.randomBytes for otplib BEFORE importing otplib
(function () {
  if (typeof globalThis === 'undefined') return
  const g = globalThis
  if (!g.crypto) g.crypto = {}
  const getRV =
    (g.crypto.getRandomValues && g.crypto.getRandomValues.bind(g.crypto)) ||
    (typeof window !== 'undefined' && window.crypto && window.crypto.getRandomValues && window.crypto.getRandomValues.bind(window.crypto))

  if (typeof g.crypto.randomBytes !== 'function') {
    g.crypto.randomBytes = (size) => {
      const arr = new Uint8Array(size)
      if (getRV) {
        getRV(arr)
      } else {
        // fallback - not crypto-strong if no Web Crypto available
        for (let i = 0; i < size; i++) arr[i] = Math.floor(Math.random() * 256)
      }
      // return a Buffer if Buffer is available (some libs expect Buffer)
      if (typeof Buffer !== 'undefined' && typeof Buffer.from === 'function') return Buffer.from(arr)
      return arr
    }
  }
})()

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import qrcode from 'qrcode'

const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
function base32Encode(bytes) {
  let bits = 0, value = 0, output = ''
  for (let i = 0; i < bytes.length; i++) {
    value = (value << 8) | bytes[i]
    bits += 8
    while (bits >= 5) {
      output += BASE32_ALPHABET[(value >>> (bits - 5)) & 31]
      bits -= 5
    }
  }
  if (bits > 0) {
    output += BASE32_ALPHABET[(value << (5 - bits)) & 31]
  }
  return output
}
function base32Decode(str) {
  const cleaned = str.replace(/=+$/,'').toUpperCase()
  const bytes = []
  let bits = 0, value = 0
  for (let i = 0; i < cleaned.length; i++) {
    const idx = BASE32_ALPHABET.indexOf(cleaned[i])
    if (idx === -1) continue
    value = (value << 5) | idx
    bits += 5
    if (bits >= 8) {
      bytes.push((value >>> (bits - 8)) & 0xff)
      bits -= 8
    }
  }
  return new Uint8Array(bytes)
}

async function hmacSha1(keyBytes, data) {
  const key = await crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-1' }, false, ['sign'])
  const sig = await crypto.subtle.sign('HMAC', key, data)
  return new Uint8Array(sig)
}
function intToBuffer(num) {
  const buf = new ArrayBuffer(8)
  const view = new DataView(buf)
  // big-endian
  view.setUint32(0, Math.floor(num / 2 ** 32))
  view.setUint32(4, num >>> 0)
  return new Uint8Array(buf)
}
async function generateSecretBase32(size = 20) {
  const arr = new Uint8Array(size)
  if (crypto && crypto.getRandomValues) crypto.getRandomValues(arr)
  else for (let i = 0; i < size; i++) arr[i] = Math.floor(Math.random() * 256)
  return base32Encode(arr)
}
async function checkTotp(token, secret, windowSteps = 1, period = 30, digits = 6) {
  token = (token || '').toString().trim()
  if (!/^\d+$/.test(token)) return false
  const key = base32Decode(secret)
  const now = Math.floor(Date.now() / 1000)
  const counterBase = Math.floor(now / period)
  for (let i = -windowSteps; i <= windowSteps; i++) {
    const counter = counterBase + i
    const counterBuf = intToBuffer(counter)
    const digest = await hmacSha1(key, counterBuf)
    const offset = digest[digest.length - 1] & 0x0f
    const code = ((digest[offset] & 0x7f) << 24) |
                 ((digest[offset + 1] & 0xff) << 16) |
                 ((digest[offset + 2] & 0xff) << 8) |
                 (digest[offset + 3] & 0xff)
    const otp = (code % (10 ** digits)).toString().padStart(digits, '0')
    if (otp === token) return true
  }
  return false
}

// ...existing code...

const USERS_KEY = 'localUsers'
const storageKey = (em) => `2fa:${em.toLowerCase()}`

function getUsers() {
  try { return JSON.parse(localStorage.getItem(USERS_KEY) || '{}') } catch (e) { return {} }
}
function saveUser(email, password) {
  const users = getUsers()
  users[email.toLowerCase()] = { password }
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

// ...existing code...

export default function SignupPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  // 2FA is mandatory now; remove the optional checkbox
  const [secret, setSecret] = useState(null)
  const [qrDataUrl, setQrDataUrl] = useState(null)
  const [token, setToken] = useState('')
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { document.title = 'Sign up - LIT' }, [])

  // new CSS for nicer UI
  const css = `
    :root{
      --bg:#f5f7fb;
      --card:#ffffff;
      --muted:#6b7280;
      --primary:#2563eb;
      --danger:#ef4444;
    }
    .signup-page{
      min-height:100vh;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:32px;
      background:linear-gradient(180deg,#f8fafc,#eef2ff);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
    }
    .card{
      width:100%;
      max-width:560px;
      background:var(--card);
      border-radius:12px;
      padding:32px;
      box-shadow:0 10px 30px rgba(2,6,23,0.08);
      border:1px solid rgba(15,23,42,0.04);
    }
    h2{
      margin:0 0 12px;
      font-size:20px;
      color:#0f172a;
    }
    .form{
      display:flex;
      flex-direction:column;
      gap:12px;
      margin-top:8px;
    }
    .input, input{
      padding:10px 12px;
      border-radius:8px;
      border:1px solid #e6e9ef;
      background:transparent;
      font-size:14px;
      outline:none;
      color:#0f172a;
    }
    .input:focus, input:focus{
      border-color:var(--primary);
      box-shadow:0 0 0 6px rgba(37,99,235,0.06);
    }
    .controls{display:flex;gap:8px;align-items:center}
    .note{color:var(--muted);font-size:13px}
    .qr{display:block;margin:8px 0;height:140px;border-radius:8px;box-shadow:0 6px 18px rgba(2,6,23,0.06);object-fit:contain}
    .actions{display:flex;gap:8px}
    .btn{background:var(--primary);color:#fff;padding:10px 14px;border-radius:8px;border:none;cursor:pointer;font-weight:600}
    .btn:hover{filter:brightness(0.95)}
    .btn-ghost{background:transparent;border:1px solid #e6e9ef;padding:8px 12px;border-radius:8px;color:var(--muted);cursor:pointer}
    .error{color:var(--danger);margin-top:6px;font-size:13px}
    @media(max-width:520px){.card{padding:20px}}
  `

  const handleStart2FA = async () => {
    if (!email) { setError('Enter email first'); return }
    if (!password) { setError('Enter password first'); return }
    if (!confirm) { setError('Confirm password first'); return }
    setError(null)
    const s = await generateSecretBase32()
    setSecret(s)
    const issuer = encodeURIComponent('LIT')
    const acct = encodeURIComponent(email)
    const otpauth = `otpauth://totp/${issuer}:${acct}?secret=${s}&issuer=${issuer}&algorithm=SHA1&digits=6&period=30`
    const qr = await qrcode.toDataURL(otpauth)
    setQrDataUrl(qr)
  }

  const handleSubmit = async (e) => {
    e?.preventDefault()
    setError(null)
    if (!email || !password) { setError('Enter email and password'); return }
    if (password !== confirm) { setError('Passwords do not match'); return }

    const users = getUsers()
    if (users[email.toLowerCase()]) {
      setError('Account already exists. Go to login.')
      return
    }

    // 2FA is mandatory: require generated secret and a valid token
    if (!secret || !qrDataUrl) {
      setError('Generate the QR code and scan it in your authenticator, then enter the code.')
      return
    }
    const ok = await checkTotp((token || '').trim(), secret)
    if (!ok) {
      setError('Invalid 2FA code. Try again.')
      return
    }
    // persist secret
    localStorage.setItem(storageKey(email), secret)

    // save account (demo)
    saveUser(email, password)

    // set session and navigate
    localStorage.setItem('authUser', JSON.stringify({ email }))
    onLogin && onLogin({ email })
    navigate('/', { replace: true })
  }

  return (
    <div className="signup-page">
      <style>{css}</style>
      <div className="card">
        <h2>Create account (2FA required)</h2>
        <form onSubmit={handleSubmit} className="form">
          <input className="input" placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input" placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          <input className="input" placeholder="confirm password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} />

          <div className="note">
            Two-factor authentication via authenticator app is required. Generate the QR, scan it in your app, then enter the 6-digit code below to complete signup.
          </div>

          <div className="controls">
            <button type="button" onClick={handleStart2FA} className="btn">Generate QR</button>
            <span className="note">Scan in Google Authenticator / Authy</span>
          </div>

          {qrDataUrl && <img src={qrDataUrl} alt="qr" className="qr" />}

          <input className="input" placeholder="6-digit code from app" value={token} onChange={e => setToken(e.target.value)} />

          <div className="actions">
            <button className="btn" type="submit">Create account</button>
            <a href="/login" className="btn-ghost" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>Back to login</a>
          </div>

          {error && <div className="error">{error}</div>}
        </form>
      </div>
    </div>
  )
}