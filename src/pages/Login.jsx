import { useEffect } from 'react'
import Login2FA from '../components/Login2FA'

export default function LoginPage({ onLogin }) {
  useEffect(() => {
    document.title = 'Login - LIT'
  }, [])

  // Page + inner Login2FA styling (grid form, nicer inputs, OTP look)
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

    .login-page{
      min-height:100vh;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:32px;
      background:transparent;
      font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
      color:var(--text);
    }

    .card{
      width:100%;
      max-width:640px;
      background:var(--card);
      border-radius:16px;
      padding:28px;
      box-shadow:0 18px 60px rgba(2,6,23,0.10);
      border:1px solid rgba(15,23,42,0.06);
    }

    h2{
      margin:0 0 8px;
      font-size:22px;
      font-weight:700;
    }
    p.lead{
      margin:0 0 18px;
      color:var(--muted);
      font-size:14px;
    }

    /* Buttons (shared with inner component) */
    .btn{
      background:var(--primary);
      color:#fff;
      padding:10px 14px;
      border-radius:10px;
      border:none;
      cursor:pointer;
      font-weight:600;
      font-size:14px;
      display:inline-flex;
      align-items:center;
      gap:8px;
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
      display:inline-flex;
      align-items:center;
      height:44px;
      line-height:1;
      font-weight:600;
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

    .footer-row{
      display:flex;
      justify-content:space-between;
      align-items:center;
      margin-top:14px;
      gap:10px;
      flex-wrap:wrap;
    }
    .note{font-size:13px;color:var(--muted)}

    /* ───────── Style inside Login2FA without editing that component ───────── */
    .login-2fa { margin-top: 8px; }
    .login-2fa form{
      display:grid !important;
      grid-template-columns: 1fr 1fr auto;
      gap:12px;
      align-items:end;
    }
    /* OTP or small forms collapse nicely on narrow screens */
    @media (max-width:640px){
      .login-2fa form{ grid-template-columns: 1fr; }
    }

    .login-2fa input{
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
    .login-2fa input:focus{
      border-color:var(--primary);
      box-shadow:0 0 0 6px var(--ring);
    }

    /* Make 6-digit field feel like OTP */
    .login-2fa input[placeholder*="6-digit"]{
      letter-spacing:.35em;
      text-align:center;
      font-variant-numeric: tabular-nums;
    }

    /* Error text from the component */
    .login-2fa [style*="var(--danger)"]{
      margin-top:8px;
      font-size:13px;
    }

    @media(max-width:520px){.card{padding:20px}}

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

  return (
    <div className="auth-scope login-page">
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
