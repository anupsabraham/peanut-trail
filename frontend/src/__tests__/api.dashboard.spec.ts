import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { getCategoryExpenses, getProgressionChartData } from '@/api/dashboard'

vi.mock('@/api/client', () => ({
  default: { get: vi.fn() },
}))

const mockGet = vi.mocked(client.get)

describe('getCategoryExpenses', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls the correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({
      data: { categories: [], total_expense: 0 },
    } as any)

    await getCategoryExpenses()

    expect(mockGet).toHaveBeenCalledWith('/api/analytics/expenses/by-category/current-month')
  })

  it('returns the response data', async () => {
    const payload = {
      categories: [{ category: 'Food', total_amount: 500 }],
      total_expense: 500,
    }
    mockGet.mockResolvedValueOnce({ data: payload } as any)

    const result = await getCategoryExpenses()

    expect(result).toEqual(payload)
  })
})

describe('getProgressionChartData', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls the correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({
      data: { progression_datasets: [], days: [] },
    } as any)

    await getProgressionChartData()

    expect(mockGet).toHaveBeenCalledWith('/api/analytics/chart/progression/current-month')
  })

  it('returns the response data', async () => {
    const payload = {
      progression_datasets: [{ label: 'June 2026', data: [100, 200], borderColor: '#fff', borderWidth: 1 }],
      days: [1, 2, 3],
    }
    mockGet.mockResolvedValueOnce({ data: payload } as any)

    const result = await getProgressionChartData()

    expect(result).toEqual(payload)
  })
})
