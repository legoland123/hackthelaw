import { useState, useEffect } from 'react'
import { authenticator } from 'otplib'
import qrcode from 'qrcode'
import '../styles/auth.css'

import { Buffer } from 'buffer'
if (typeof window !== 'undefined' && !window.Buffer) window.Buffer = Buffer

const USERS_KEY = 'localUsers'
const storageKey = (em) => `2fa:${em.toLowerCase()}`

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || '{}')
  } catch (e) {
    return {}
  }
}
function getUser(email) {
  if (!email) return null
  return getUsers()[email.toLowerCase()] || null
}
function saveUser(email, password) {
  const users = getUsers()
  users[email.toLowerCase()] = { password }
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

const BASE32_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'

function generateBase32Secret(length = 20) {
  let s = ''
  const cryptoObj = window.crypto || window.msCrypto
  const bytes = new Uint8Array(length)
  if (cryptoObj && cryptoObj.getRandomValues) {
    cryptoObj.getRandomValues(bytes)
  } else {
    // fallback (not cryptographically secure) for very old environments
    for (let i = 0; i < length; i++) bytes[i] = Math.floor(Math.random() * 256)
  }
  for (let i = 0; i < length; i++) {
    s += BASE32_CHARS[bytes[i] % 32]
  }
  return s
}

function base32ToBytes(base32) {
  const clean = base32.replace(/=+$/, '').toUpperCase()
  const buffer = []
  let bits = 0
  let value = 0
  for (let i = 0; i < clean.length; i++) {
    const idx = BASE32_CHARS.indexOf(clean[i])
    if (idx === -1) continue
    value = (value << 5) | idx
    bits += 5
    if (bits >= 8) {
      bits -= 8
      buffer.push((value >>> bits) & 0xff)
    }
  }
  return new Uint8Array(buffer)
}

async function hmacSha1(keyBytes, dataBytes) {
  const cryptoSubtle = window.crypto && window.crypto.subtle
  if (!cryptoSubtle) {
    throw new Error('Web Crypto Subtle API not available')
  }
  const key = await cryptoSubtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-1' }, false, ['sign'])
  const sig = await cryptoSubtle.sign('HMAC', key, dataBytes)
  return new Uint8Array(sig)
}

function intToBytes(num) {
  const bytes = new Uint8Array(8)
  for (let i = 7; i >= 0; i--) {
    bytes[i] = num & 0xff
    num = num >>> 8
  }
  return bytes
}

async function hotpFromSecretAndCounter(secretBase32, counter) {
  const key = base32ToBytes(secretBase32)
  const counterBytes = intToBytes(counter)
  const hmac = await hmacSha1(key, counterBytes)
  const offset = hmac[hmac.length - 1] & 0x0f
  const code =
    ((hmac[offset] & 0x7f) << 24) |
    ((hmac[offset + 1] & 0xff) << 16) |
    ((hmac[offset + 2] & 0xff) << 8) |
    (hmac[offset + 3] & 0xff)
  const otp = (code % 10 ** 6).toString().padStart(6, '0')
  return otp
}

async function totpCheckWithWindow(token, secretBase32, windowSteps = 1, stepSeconds = 30) {
  if (!token) return false
  const now = Math.floor(Date.now() / 1000)
  const counter = Math.floor(now / stepSeconds)
  for (let i = -windowSteps; i <= windowSteps; i++) {
    const expected = await hotpFromSecretAndCounter(secretBase32, counter + i)
    if (expected === token) return true
  }
  return false
}

export default function Login2FA({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [step, setStep] = useState('idle') // idle | password | need-otp | setup | confirm-setup
  const [secret, setSecret] = useState(null)
  const [qrDataUrl, setQrDataUrl] = useState(null)
  const [token, setToken] = useState('')
  const [error, setError] = useState(null)
  const [is2faEnabled, setIs2faEnabled] = useState(false)

  useEffect(() => {
    if (!email) return
    const s = localStorage.getItem(storageKey(email))
    setIs2faEnabled(!!s)
  }, [email])

  const checkPassword = async (emailArg, passwordArg) => {
    const u = getUser(emailArg)
    if (!u) return false
    // demo: plain comparison. In production use hashed passwords.
    return u.password === passwordArg
  }

  const handleSignIn = async (e) => {
    e?.preventDefault()
    setError(null)
    if (!email || !password) {
      setError('Enter email and password.')
      return
    }
    const exists = getUser(email)
    if (!exists) {
      setError('Account not found. Click "Create an account" on the login page.')
      return
    }
    const ok = await checkPassword(email, password)
    if (!ok) {
      setError('Invalid credentials.')
      return
    }
    const existingSecret = localStorage.getItem(storageKey(email))
    if (existingSecret) {
      setStep('need-otp')
    } else {
      // sign in without 2FA
      onLogin && onLogin({ email })
    }
  }

  const handleVerifyOtpLogin = async (e) => {
    e?.preventDefault()
    setError(null)
    const s = localStorage.getItem(storageKey(email))
    if (!s) {
      setError('No 2FA configured for this account.')
      return
    }
    try {
      const ok = await totpCheckWithWindow(token.trim(), s, 1)
      if (!ok) {
        setError('Invalid code.')
        return
      }
      onLogin && onLogin({ email })
      setToken('')
      setStep('idle')
    } catch (err) {
      setError('Error verifying code.')
      console.error(err)
    }
  }

  // The setup flows below are kept so an already-signed-in user can enable 2FA.
  const handleStartSetup = async () => {
    setError(null)
    if (!email) {
      setError('Enter email first.')
      return
    }
    // generate a base32 secret for the user (demo only)
    const newSecret = generateBase32Secret(20)
    setSecret(newSecret)
    const otpauth = `otpauth://totp/LIT:${encodeURIComponent(email)}?secret=${newSecret}&issuer=LIT&algorithm=SHA1&digits=6&period=30`
    try {
      const qr = await qrcode.toDataURL(otpauth)
      setQrDataUrl(qr)
      setStep('confirm-setup')
    } catch (err) {
      setError('Failed to generate QR code.')
      console.error(err)
    }
  }

  const handleConfirmSetup = async (e) => {
    e?.preventDefault()
    setError(null)
    if (!secret) {
      setError('Setup not initialized.')
      return
    }
    try {
      const ok = await totpCheckWithWindow(token.trim(), secret, 1)
      if (!ok) {
        setError('Invalid code. Try again.')
        return
      }
      localStorage.setItem(storageKey(email), secret)
      setIs2faEnabled(true)
      setToken('')
      setSecret(null)
      setQrDataUrl(null)
      setStep('idle')
      onLogin && onLogin({ email })
    } catch (err) {
      setError('Error verifying code.')
      console.error(err)
    }
  }

  const handleDisable2FA = () => {
    localStorage.removeItem(storageKey(email))
    setIs2faEnabled(false)
  }

  return (
    <div className="login-2fa" style={{ marginTop: 12 }}>
      {step === 'idle' && (
        <form onSubmit={handleSignIn} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
          <input placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          <button type="submit" className="btn">Sign In</button>
          {/* <button type="button" onClick={() => setStep('setup')} className="btn-ghost">Enable 2FA</button> */}
        </form>
      )}

      {step === 'password' && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span>Signed in as {email}</span>
          {!is2faEnabled ? (
            <button onClick={handleStartSetup} className="btn">Enable 2FA</button>
          ) : (
            <button onClick={handleDisable2FA} className="btn-ghost">Disable 2FA</button>
          )}
          <button onClick={() => { setStep('idle'); setEmail(''); setPassword('') }} className="btn-ghost">Close</button>
        </div>
      )}

      {step === 'need-otp' && (
        <form onSubmit={handleVerifyOtpLogin} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input placeholder="6-digit code" value={token} onChange={e => setToken(e.target.value)} />
          <button type="submit" className="btn">Verify</button>
          <button type="button" onClick={() => setStep('idle')} className="btn-ghost">Cancel</button>
        </form>
      )}

      {step === 'confirm-setup' && (
        <form onSubmit={handleConfirmSetup} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {qrDataUrl && (
            <img
              src={qrDataUrl}
              alt="QR for Authenticator"
              style={{ width: 120, height: 120, objectFit: 'contain', display: 'block' }}
            />
          )}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <input placeholder="6-digit code from app" value={token} onChange={e => setToken(e.target.value)} />
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className="btn">Confirm</button>
              <button type="button" onClick={() => { setStep('idle'); setSecret(null); setQrDataUrl(null) }} className="btn-ghost">Cancel</button>
            </div>
          </div>
        </form>
      )}

      {error && <div style={{ color: 'var(--danger)', marginTop: 6 }}>{error}</div>}
    </div>
  )
}