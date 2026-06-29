import { apiClient } from '@/api/client'
import type {
  StandardResponse,
  DashboardSummaryResponse,
  DistributionResponse,
  RecentLeadsResponse,
} from '@/types'

export const dashboardApi = {
  summary: async (): Promise<StandardResponse<DashboardSummaryResponse>> => {
    const { data } = await apiClient.get<StandardResponse<DashboardSummaryResponse>>(
      '/dashboard/summary'
    )
    return data
  },

  recentLeads: async (
    limit = 10,
    offset = 0
  ): Promise<StandardResponse<RecentLeadsResponse>> => {
    const { data } = await apiClient.get<StandardResponse<RecentLeadsResponse>>(
      '/dashboard/recent-leads',
      { params: { limit, offset } }
    )
    return data
  },

  statusDistribution: async (): Promise<StandardResponse<DistributionResponse>> => {
    const { data } = await apiClient.get<StandardResponse<DistributionResponse>>(
      '/dashboard/status-distribution'
    )
    return data
  },

  industryDistribution: async (): Promise<StandardResponse<DistributionResponse>> => {
    const { data } = await apiClient.get<StandardResponse<DistributionResponse>>(
      '/dashboard/industry-distribution'
    )
    return data
  },

  cityDistribution: async (): Promise<StandardResponse<DistributionResponse>> => {
    const { data } = await apiClient.get<StandardResponse<DistributionResponse>>(
      '/dashboard/city-distribution'
    )
    return data
  },
}

export const analysisApi = {
  analyze: async (lead_id: string) => {
    const { data } = await apiClient.post('/analysis/website', { lead_id })
    return data
  },
}

export const screenshotsApi = {
  capture: async (lead_id: string) => {
    const { data } = await apiClient.post('/screenshots/capture', { lead_id })
    return data
  },
}

export const auditsApi = {
  run: async (lead_id: string) => {
    const { data } = await apiClient.post('/audits/run', { lead_id })
    return data
  },
}

export const outreachApi = {
  generate: async (lead_id: string) => {
    const { data } = await apiClient.post('/outreach/generate', { lead_id })
    return data
  },
}
