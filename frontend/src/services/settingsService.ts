import { apiClient } from '@/api/client'
import type {
  StandardResponse,
  UserResponse,
  UserProfileUpdate,
  ChangePasswordRequest,
  UserSettingsResponse,
  UserPreferencesUpdate,
  AccountSummaryResponse,
} from '@/types'

export const settingsApi = {
  getProfile: async (): Promise<StandardResponse<UserResponse>> => {
    const { data } = await apiClient.get<StandardResponse<UserResponse>>(
      '/settings/profile'
    )
    return data
  },

  updateProfile: async (
    payload: UserProfileUpdate
  ): Promise<StandardResponse<UserResponse>> => {
    const { data } = await apiClient.patch<StandardResponse<UserResponse>>(
      '/settings/profile',
      payload
    )
    return data
  },

  changePassword: async (
    payload: ChangePasswordRequest
  ): Promise<StandardResponse<null>> => {
    const { data } = await apiClient.patch<StandardResponse<null>>(
      '/settings/change-password',
      payload
    )
    return data
  },

  getPreferences: async (): Promise<StandardResponse<UserSettingsResponse>> => {
    const { data } = await apiClient.get<StandardResponse<UserSettingsResponse>>(
      '/settings/preferences'
    )
    return data
  },

  updatePreferences: async (
    payload: UserPreferencesUpdate
  ): Promise<StandardResponse<UserSettingsResponse>> => {
    const { data } = await apiClient.patch<StandardResponse<UserSettingsResponse>>(
      '/settings/preferences',
      payload
    )
    return data
  },

  getAccountSummary: async (): Promise<StandardResponse<AccountSummaryResponse>> => {
    const { data } = await apiClient.get<StandardResponse<AccountSummaryResponse>>(
      '/settings/account-summary'
    )
    return data
  },
}
