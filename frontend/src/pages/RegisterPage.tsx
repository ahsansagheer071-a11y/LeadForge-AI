import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getErrorMessage } from '@/utils'
import { Zap, Loader } from 'lucide-react'

export default function RegisterPage() {
  const { register, login } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }
    setIsLoading(true)
    try {
      await register(email, password, fullName || undefined)
      // Auto-login after register
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-bg">
      <div className="auth-card animate-fade-in">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32 }}>
          <div style={{
            width: 36, height: 36, background: 'var(--color-brand)',
            borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Zap size={18} color="#fff" strokeWidth={2.5} />
          </div>
          <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.02em' }}>
            LeadForge AI
          </span>
        </div>

        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Create your account</h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 14, marginBottom: 28 }}>
          Start discovering and converting leads with AI
        </p>

        {error && (
          <div style={{
            background: 'var(--color-error-subtle)', border: '1px solid #ef444420',
            borderRadius: 8, padding: '10px 14px', marginBottom: 20,
            color: 'var(--color-error)', fontSize: 13
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label className="label">Full name (optional)</label>
            <input
              className="input"
              type="text"
              placeholder="Jane Smith"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Email address</label>
            <input
              className="input"
              type="email"
              placeholder="you@agency.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button className="btn btn-primary btn-lg" type="submit" disabled={isLoading}
            style={{ marginTop: 4 }}>
            {isLoading ? <Loader size={16} className="animate-spin" /> : null}
            {isLoading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p style={{ marginTop: 24, textAlign: 'center', fontSize: 13, color: 'var(--color-text-secondary)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--color-brand)', fontWeight: 500 }}>
            Sign in
          </Link>
        </p>
      </div>

      <style>{`
        .auth-bg {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--color-background);
          background-image: radial-gradient(ellipse at 50% 0%, #6366f115 0%, transparent 60%);
          padding: 24px;
        }
        .auth-card {
          width: 100%;
          max-width: 400px;
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-xl);
          padding: 36px;
        }
      `}</style>
    </div>
  )
}
