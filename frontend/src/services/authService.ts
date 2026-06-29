import { apiClient, tokenStorage } from '@/api/client'
import type { StandardResponse, UserResponse, TokenResponse } from '@/types'

// Login uses form-data (OAuth2PasswordRequestForm on the backend)
export const authApi = {
  login: async (email: string, password: string): Promise<TokenResponse> => {
    const form = new URLSearchParams()
    form.append('username', email) // backend field is 'username'
    form.append('password', password)

    const { data } = await apiClient.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  register: async (payload: {
    email: string
    password: string
    full_name?: string
  }): Promise<StandardResponse<UserResponse>> => {
    const { data } = await apiClient.post<StandardResponse<UserResponse>>(
      '/auth/register',
      payload
    )
    return data
  },

  me: async (): Promise<StandardResponse<UserResponse>> => {
    const { data } = await apiClient.get<StandardResponse<UserResponse>>('/auth/me')
    return data
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      tokenStorage.clear()
    }
  },

  refresh: async (refresh_token: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token,
    })
    return data
  },
}
