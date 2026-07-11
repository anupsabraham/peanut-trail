import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import {
  deleteTransaction,
  getCategories,
  getChildTransactions,
  getTransactions,
  splitTransaction,
  updateTransaction,
} from '@/api/transactions'

vi.mock('@/api/client', () => ({
  default: { get: vi.fn(), delete: vi.fn(), patch: vi.fn(), post: vi.fn() },
}))

const mockGet = vi.mocked(client.get)
const mockDelete = vi.mocked(client.delete)
const mockPatch = vi.mocked(client.patch)
const mockPost = vi.mocked(client.post)

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

describe('transaction mutations and supporting resources', () => {
  beforeEach(() => vi.clearAllMocks())

  it('deletes a transaction by id', async () => {
    mockDelete.mockResolvedValueOnce({} as any)
    await deleteTransaction(42)
    expect(mockDelete).toHaveBeenCalledWith('/api/transactions/42')
  })

  it('updates a transaction and returns its response data', async () => {
    const payload = { category: 'Food', sub_category: 'Dining', exclude: false }
    mockPatch.mockResolvedValueOnce({ data: { id: 42, ...payload } } as any)
    await expect(updateTransaction(42, payload)).resolves.toEqual({ id: 42, ...payload })
    expect(mockPatch).toHaveBeenCalledWith('/api/transactions/42', payload)
  })

  it('submits a split payload and returns its response data', async () => {
    const payload = { splits: [{ debit_amount: 60, category: 'Food', sub_category: 'Dining', notes: '' }] }
    mockPost.mockResolvedValueOnce({ data: { created: 1 } } as any)
    await expect(splitTransaction(42, payload)).resolves.toEqual({ created: 1 })
    expect(mockPost).toHaveBeenCalledWith('/api/transactions/42/split', payload)
  })

  it('gets child transactions for a parent', async () => {
    const children = [{ id: 43 }]
    mockGet.mockResolvedValueOnce({ data: children } as any)
    await expect(getChildTransactions(42)).resolves.toEqual(children)
    expect(mockGet).toHaveBeenCalledWith('/api/transactions/42/children')
  })

  it('gets the category hierarchy', async () => {
    const categories = { categories: [{ name: 'Food', subcategories: [{ name: 'Dining' }] }] }
    mockGet.mockResolvedValueOnce({ data: categories } as any)
    await expect(getCategories()).resolves.toEqual(categories)
    expect(mockGet).toHaveBeenCalledWith('/api/transactions/categories')
  })
})
