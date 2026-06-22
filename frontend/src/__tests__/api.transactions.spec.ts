import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { getTransactions } from '@/api/transactions'

vi.mock('@/api/client', () => ({
  default: { get: vi.fn() },
}))

const mockGet = vi.mocked(client.get)

const emptyPage = { items: [], total: 0, page: 1, pages: 1 }

describe('getTransactions', () => {
  beforeEach(() => vi.clearAllMocks())

  it('calls /api/transactions', async () => {
    mockGet.mockResolvedValueOnce({ data: emptyPage } as any)

    await getTransactions({})

    expect(mockGet).toHaveBeenCalledWith('/api/transactions', { params: {} })
  })

  it('passes page param', async () => {
    mockGet.mockResolvedValueOnce({ data: emptyPage } as any)

    await getTransactions({ page: 3 })

    expect(mockGet).toHaveBeenCalledWith('/api/transactions', { params: { page: 3 } })
  })

  it('passes search param', async () => {
    mockGet.mockResolvedValueOnce({ data: emptyPage } as any)

    await getTransactions({ search: 'amazon' })

    expect(mockGet).toHaveBeenCalledWith('/api/transactions', { params: { search: 'amazon' } })
  })

  it('passes multiple filter params together', async () => {
    mockGet.mockResolvedValueOnce({ data: emptyPage } as any)

    await getTransactions({ category: 'Food', min_amount: 100, max_amount: 500 })

    expect(mockGet).toHaveBeenCalledWith('/api/transactions', {
      params: { category: 'Food', min_amount: 100, max_amount: 500 },
    })
  })

  it('passes date range params', async () => {
    mockGet.mockResolvedValueOnce({ data: emptyPage } as any)

    await getTransactions({ start_date: '2026-01-01', end_date: '2026-06-30' })

    expect(mockGet).toHaveBeenCalledWith('/api/transactions', {
      params: { start_date: '2026-01-01', end_date: '2026-06-30' },
    })
  })

  it('returns the response data', async () => {
    const payload = {
      items: [{ id: 1, txn_number: 'T001' }],
      total: 1,
      page: 1,
      pages: 1,
    }
    mockGet.mockResolvedValueOnce({ data: payload } as any)

    const result = await getTransactions({})

    expect(result).toEqual(payload)
  })
})
