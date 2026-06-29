import { apiClient } from '@/api/client'
import type {
  StandardResponse,
  PaginatedResponse,
  LeadResponse,
  LeadDetailResponse,
  LeadUpdate,
  LeadDiscoveryRequest,
  LeadDiscoveryResponse,
  BulkDeleteRequest,
  BulkStatusUpdateRequest,
  BulkActionResponse,
  LeadFilters,
} from '@/types'

export const leadsApi = {
  // GET /leads — list with filters, sorting, pagination
  list: async (filters: Partial<LeadFilters>) => {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
    )
    const { data } = await apiClient.get<
      StandardResponse<PaginatedResponse<LeadResponse>>
    >('/leads', { params })
    return data
  },

  // GET /leads/{id}
  get: async (id: string): Promise<StandardResponse<LeadDetailResponse>> => {
    const { data } = await apiClient.get<StandardResponse<LeadDetailResponse>>(
      `/leads/${id}`
    )
    return data
  },

  // PATCH /leads/{id}
  update: async (id: string, payload: LeadUpdate): Promise<StandardResponse<LeadResponse>> => {
    const { data } = await apiClient.patch<StandardResponse<LeadResponse>>(
      `/leads/${id}`,
      payload
    )
    return data
  },

  // DELETE /leads/{id}
  delete: async (id: string): Promise<StandardResponse<null>> => {
    const { data } = await apiClient.delete<StandardResponse<null>>(`/leads/${id}`)
    return data
  },

  // POST /leads/discover
  discover: async (
    payload: LeadDiscoveryRequest
  ): Promise<StandardResponse<LeadDiscoveryResponse>> => {
    const { data } = await apiClient.post<StandardResponse<LeadDiscoveryResponse>>(
      '/leads/discover',
      payload
    )
    return data
  },

  // POST /leads/bulk-delete
  bulkDelete: async (
    payload: BulkDeleteRequest
  ): Promise<StandardResponse<BulkActionResponse>> => {
    const { data } = await apiClient.post<StandardResponse<BulkActionResponse>>(
      '/leads/bulk-delete',
      payload
    )
    return data
  },

  // PATCH /leads/bulk-status
  bulkStatus: async (
    payload: BulkStatusUpdateRequest
  ): Promise<StandardResponse<BulkActionResponse>> => {
    const { data } = await apiClient.patch<StandardResponse<BulkActionResponse>>(
      '/leads/bulk-status',
      payload
    )
    return data
  },

  // GET /leads/export/csv — triggers browser download
  exportCsv: (filters: Partial<LeadFilters>) => {
    const params = new URLSearchParams(
      Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== undefined && v !== '')
      ) as Record<string, string>
    )
    const token = localStorage.getItem('lf_access_token')
    const url = `/api/v1/leads/export/csv?${params.toString()}`
    const a = document.createElement('a')
    a.href = url
    a.download = 'leads_export.csv'
    // Axios interceptor won't apply here, use fetch with auth header
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const objectUrl = URL.createObjectURL(blob)
        a.href = objectUrl
        a.click()
        URL.revokeObjectURL(objectUrl)
      })
  },
}
