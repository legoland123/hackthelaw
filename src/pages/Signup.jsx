/* keep your polyfill exactly as-is */
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
      if (getRV) getRV(arr)
      else for (let i = 0; i < size; i++) arr[i] = Math.floor(Math.random() * 256)
      if (typeof Buffer !== 'undefined' && typeof Buffer.from === 'function') return Buffer.from(arr)
      return arr
    }
  }
})()

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import qrcode from 'qrcode'

/* Base32 + TOTP helpers (unchanged from your logic) */
const BASE32_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
function base32Encode(bytes){let b=0,v=0,o='';for(let i=0;i<bytes.length;i++){v=(v<<8)|bytes[i];b+=8;while(b>=5){o+=BASE32_ALPHABET[(v>>>(b-5))&31];b-=5}}if(b>0){o+=BASE32_ALPHABET[(v<<(5-b))&31]}return o}
function base32Decode(str){const c=str.replace(/=+$/,'').toUpperCase();const r=[];let b=0,v=0;for(let i=0;i<c.length;i++){const idx=BASE32_ALPHABET.indexOf(c[i]);if(idx===-1)continue;v=(v<<5)|idx;b+=5;if(b>=8){r.push((v>>>(b-8))&0xff);b-=8}}return new Uint8Array(r)}
async function hmacSha1(keyBytes,data){const key=await crypto.subtle.importKey('raw',keyBytes,{name:'HMAC',hash:'SHA-1'},false,['sign']);const sig=await crypto.subtle.sign('HMAC',key,data);return new Uint8Array(sig)}
function intToBuffer(num){const buf=new ArrayBuffer(8);const view=new DataView(buf);view.setUint32(0, Math.floor(num/2**32));view.setUint32(4, num>>>0);return new Uint8Array(buf)}
async function generateSecretBase32(size=20){const arr=new Uint8Array(size); if(crypto&&crypto.getRandomValues) crypto.getRandomValues(arr); else for(let i=0;i<size;i++) arr[i]=Math.floor(Math.random()*256); return base32Encode(arr)}
async function checkTotp(token, secret, windowSteps=1, period=30, digits=6){
  token=(token||'').trim(); if(!/^\d+$/.test(token)) return false
  const key=base32Decode(secret); const now=Math.floor(Date.now()/1000); const base=Math.floor(now/period)
  for(let i=-windowSteps;i<=windowSteps;i++){const ctr=base+i;const digest=await hmacSha1(key,intToBuffer(ctr));const off=digest[digest.length-1]&0x0f;const code=((digest[off]&0x7f)<<24)|((digest[off+1]&0xff)<<16)|((digest[off+2]&0xff)<<8)|(digest[off+3]&0xff);const otp=(code%(10**digits)).toString().padStart(digits,'0');if(otp===token) return true}
  return false
}

/* demo storage */
const USERS_KEY = 'localUsers'
const storageKey = (em) => `2fa:${em.toLowerCase()}`
function getUsers(){try{return JSON.parse(localStorage.getItem(USERS_KEY)||'{}')}catch(e){return{}}}
function saveUser(email,password){const u=getUsers();u[email.toLowerCase()]={password};localStorage.setItem(USERS_KEY,JSON.stringify(u))}

export default function SignupPage({ onLogin }) {
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [confirm,setConfirm]=useState('')
  const [secret,setSecret]=useState(null)
  const [qrDataUrl,setQrDataUrl]=useState(null)
  const [token,setToken]=useState('')
  const [error,setError]=useState(null)
  const navigate=useNavigate()

  useEffect(()=>{document.title='Sign up - LIT'},[])

  const css = `
    :root{
      --bg:#f8fafc;
      --card:#ffffff;
      --muted:#6b7280;
      --primary:#2563eb;
      --primary-600:#1d4ed8;
      --ring: rgba(37,99,235,.15);
      --danger:#ef4444;
      --text:#0f172a;
      --border:#e6e9ef;
    }

    .signup-page{
      min-height:100vh;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:32px;
      background:transparent;
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      color:var(--text);
    }
    .card{
      width:100%;
      max-width:680px;
      background:var(--card);
      border-radius:16px;
      padding:28px;
      box-shadow:0 18px 60px rgba(2,6,23,.10);
      border:1px solid rgba(15,23,42,.06);
    }
    h2{ margin:0 0 10px; font-size:22px; font-weight:700; }
    .note{color:var(--muted); font-size:13px;}

    .form{
      display:grid;
      grid-template-columns: 1fr 1fr;
      gap:12px;
      margin-top:10px;
    }
    .form .full{ grid-column: 1 / -1; }

    input{
      height:44px;
      padding:0 12px;
      border-radius:10px;
      border:1px solid var(--border);
      background:#fff;
      font-size:14px;
      color:var(--text);
      outline:none;
      transition: box-shadow .15s, border-color .15s;
    }
    input:focus{
      border-color:var(--primary);
      box-shadow:0 0 0 6px var(--ring);
    }

    .actions{
      display:flex;
      gap:10px;
      align-items:center;
      margin-top:4px;
    }

    .btn{
      background:var(--primary);
      color:#fff;
      padding:10px 14px;
      border-radius:10px;
      border:none;
      cursor:pointer;
      font-weight:600;
      height:44px;
    }
    .btn-ghost{
      background:transparent;
      border:1px solid var(--border);
      padding:10px 12px;
      border-radius:10px;
      color:var(--muted);
      cursor:pointer;
      text-decoration:none;
      height:44px;
      display:inline-flex;
      align-items:center;
    }
    /* === Disable hover color shifts === */
    .btn:hover,
    .btn:active {
      background: var(--primary);        /* stay the same */
      filter: none;
    }

    .btn-ghost:hover,
    .btn-ghost:active {
      background: transparent;           /* no fill on hover */
      border-color: var(--border);
      color: var(--muted);
    }

    /* Keep cards steady (no hover glow) */
    .card:hover {
      box-shadow: 0 10px 30px rgba(2,6,23,0.08); /* same as default */
    }

    /* Links in those buttons shouldn’t change color on hover */
    a.btn-ghost:hover,
    a.btn:hover {
      color: inherit;
      text-decoration: none;
    }

    /* Optional: prevent subtle input hover tweaks (focus is kept) */
    input:hover,
    .login-2fa input:hover {
      border-color: inherit;
      box-shadow: none;
    }

    .qr-row{
      display:grid;
      grid-template-columns: 180px 1fr;
      gap:14px;
      align-items:start;
    }
    .qr{
      width:180px;height:180px;border-radius:12px;
      box-shadow:0 12px 30px rgba(2,6,23,.10);
      object-fit:contain;background:#fff;
    }

    .error{ color:var(--danger); font-size:13px; margin-top:6px; grid-column: 1 / -1; }

    @media (max-width:720px){
      .form{ grid-template-columns: 1fr; }
      .qr-row{ grid-template-columns: 1fr; }
    }

    /* --- Kill all hover color/shine inside auth pages --- */
    .auth-scope .btn,
    .auth-scope .btn-ghost {
      transition: none !important;
    }

    /* Filled buttons: never change on hover/active/focus */
    .auth-scope .btn:hover,
    .auth-scope .btn:active,
    .auth-scope .btn:focus {
      background: var(--primary) !important;
      color: #fff !important;
      filter: none !important;
      box-shadow: none !important;
    }

    /* Ghost buttons: never fill or recolor on hover */
    .auth-scope .btn-ghost:hover,
    .auth-scope .btn-ghost:active,
    .auth-scope .btn-ghost:focus {
      background: transparent !important;
      color: var(--muted) !important;
      border-color: var(--border, #2a3142) !important; /* fallback if --border missing */
    }

    /* Card should not glow/change on hover */
    .auth-scope .card:hover {
      box-shadow: 0 10px 30px rgba(2,6,23,0.08) !important;
    }

    /* Links in this scope should not turn blue on hover */
    .auth-scope a:hover,
    .auth-scope a:active {
      color: inherit !important;
      text-decoration: none !important;
    }

    /* Inputs shouldn't alter on hover (focus still shows) */
        .auth-scope input:hover {
      border-color: inherit !important;
      box-shadow: none !important;
    }

    /* --- AUTH PAGE HARD OVERRIDES (wins over app styles) --- */
    .auth-scope {
      /* if your global .card:hover uses --surface-elevated, neutralize it here */
      --surface-elevated: var(--card) !important;
    }

    /* freeze the card look on hover/focus */
    .auth-scope .card,
    .auth-scope .card:hover,
    .auth-scope .card:active,
    .auth-scope .card:focus,
    .auth-scope .card:focus-within {
      background: var(--card) !important;
      box-shadow: 0 10px 30px rgba(2,6,23,0.08) !important;
      border-color: rgba(15,23,42,0.04) !important;
      cursor: default !important;
      transform: none !important;
      filter: none !important;
    }

    /* stop buttons from changing on hover */
    .auth-scope .btn,
    .auth-scope .btn-ghost {
      transition: none !important;
    }
    .auth-scope .btn:hover,
    .auth-scope .btn:active,
    .auth-scope .btn:focus {
      background: var(--primary) !important;  /* keep filled btn constant */
      color: #fff !important;
      filter: none !important;
      transform: none !important;
      box-shadow: none !important;
    }
    .auth-scope .btn-ghost:hover,
    .auth-scope .btn-ghost:active,
    .auth-scope .btn-ghost:focus {
      background: transparent !important;     /* keep ghost btn constant */
      color: var(--muted) !important;
      border-color: #e6e9ef !important;
      filter: none !important;
      transform: none !important;
      box-shadow: none !important;
    }

    /* kill link hover color shifts inside auth */
    .auth-scope a:hover,
    .auth-scope a:active,
    .auth-scope a:focus {
      color: inherit !important;
      text-decoration: none !important;
    }

    /* inputs shouldn't react to hover (focus can stay) */
    .auth-scope input:hover {
      border-color: inherit !important;
      box-shadow: none !important;
    }

  `

  const handleStart2FA = async () => {
    if (!email) return setError('Enter email first')
    if (!password) return setError('Enter password first')
    if (!confirm) return setError('Confirm password first')
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

    if (!email || !password) return setError('Enter email and password')
    if (password !== confirm) return setError('Passwords do not match')

    const users = getUsers()
    if (users[email.toLowerCase()]) return setError('Account already exists. Go to login.')

    if (!secret || !qrDataUrl) return setError('Generate the QR and scan it in your authenticator, then enter the 6-digit code below.')
    const ok = await checkTotp((token||'').trim(), secret)
    if (!ok) return setError('Invalid 2FA code. Try again.')

    localStorage.setItem(storageKey(email), secret)
    saveUser(email, password)

    localStorage.setItem('authUser', JSON.stringify({ email }))
    onLogin && onLogin({ email })
    navigate('/', { replace: true })
  }

  return (
    <div className="auth-scope signup-page">
      <style>{css}</style>
      <div className="card">
        <h2>Create account (2FA required)</h2>

        <form onSubmit={handleSubmit} className="form">
          <input className="full" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <input placeholder="confirm password" type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} />

          <div className="full note">
            Two-factor authentication via an authenticator app is required. Generate the QR, scan it, then enter the 6-digit code to complete signup.
          </div>

          <div className="full actions">
            <button type="button" onClick={handleStart2FA} className="btn">Generate QR</button>
            <span className="note">Scan in Google Authenticator / 1Password / Authy</span>
          </div>

          {qrDataUrl && (
            <div className="full qr-row">
              <img src={qrDataUrl} alt="Authenticator QR code" className="qr" />
              <div style={{display:'grid', gap:12}}>
                <input
                  placeholder="6-digit code from app"
                  value={token}
                  onChange={e=>setToken(e.target.value.replace(/\\D/g,''))}
                />
                <div className="actions">
                  <button className="btn" type="submit">Create account</button>
                  <a href="/login" className="btn-ghost">Back to login</a>
                </div>
              </div>
            </div>
          )}

          {!qrDataUrl && (
            <div className="full actions" style={{justifyContent:'space-between'}}>
              <span className="note">QR not generated yet.</span>
              <a href="/login" className="btn-ghost">Back to login</a>
            </div>
          )}

          {error && <div className="error">{error}</div>}
        </form>
      </div>
    </div>
  )
}
