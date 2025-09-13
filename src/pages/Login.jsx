import { useEffect } from 'react'
import Login2FA from '../components/Login2FA'

export default function LoginPage({ onLogin }) {
  useEffect(() => {
    document.title = 'Login - LIT'
  }, [])

  const css = `
    :root{
      --bg:#f8fafc;
      --card:#ffffff;
      --muted:#6b7280;
      --primary:#2563eb;
      --danger:#ef4444;
    }
    .login-page{
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
    p.lead{
      margin:0 0 16px;
      color:var(--muted);
      font-size:14px;
    }
    .footer-row{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-top:12px;
      gap:8px;
      flex-wrap:wrap;
    }

    /* Primary filled button (matches signup) */
    .btn{
      background:var(--primary);
      color:#fff;
      padding:10px 14px;
      border-radius:8px;
      border:none;
      cursor:pointer;
      font-weight:600;
      font-size:14px;
      display:inline-flex;
      align-items:center;
      gap:8px;
    }
    .btn:hover{ filter:brightness(0.95); }

    /* Smaller ghost button for links / secondary actions */
    .btn-ghost{
      background:transparent;
      border:1px solid #e6e9ef;
      padding:8px 12px;
      border-radius:8px;
      color:var(--muted);
      cursor:pointer;
      text-decoration:none;
      display:inline-flex;
      align-items:center;
      font-size:14px;
      height:40px;
      line-height:1;
    }

    .note{font-size:13px;color:var(--muted)}
    @media(max-width:520px){.card{padding:20px}}
  `

  return (
    <div className="login-page">
      <style>{css}</style>
      <div className="card">
        <h2>Sign in</h2>
        <p className="lead">Login requires a 6-digit TOTP code from your authenticator app.</p>

        <Login2FA onLogin={onLogin} />

        <div className="footer-row">
          <span className="note">Don't have an account? Create one with 2FA required.</span>
          <a href="/signup" className="btn-ghost">Create an account</a>
        </div>
      </div>
    </div>
  )
}