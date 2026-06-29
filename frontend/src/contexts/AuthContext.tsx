// ─────────────────────────────────────────────────────────
// AuthContext — global authentication state
// Handles: login, logout, register, persistent session restore
// ─────────────────────────────────────────────────────────
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { authApi } from '@/services/authService'
import { tokenStorage } from '@/api/client'
import type { UserResponse } from '@/types'

interface AuthContextValue {
  user: UserResponse | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (email: string, password: string, full_name?: string) => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount: restore session from stored tokens
  const restoreSession = useCallback(async () => {
    const token = tokenStorage.getAccess()
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const res = await authApi.me()
      setUser(res.data)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  const login = async (email: string, password: string) => {
    const tokens = await authApi.login(email, password)
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    const res = await authApi.me()
    setUser(res.data)
  }

  const logout = async () => {
    await authApi.logout()
    setUser(null)
    tokenStorage.clear()
  }

  const register = async (email: string, password: string, full_name?: string) => {
    await authApi.register({ email, password, full_name })
  }

  const refreshUser = async () => {
    const res = await authApi.me()
    setUser(res.data)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        register,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
