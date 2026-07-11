import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import SplitTransactionDialog from '@/components/transactions/SplitTransactionDialog.vue'
import * as transactionsApi from '@/api/transactions'
import type { Category, Transaction } from '@/api/transactions'

vi.mock('@/api/transactions', () => ({
  getChildTransactions: vi.fn(),
  updateTransaction: vi.fn(),
  splitTransaction: vi.fn(),
}))

const mockGetChildren = vi.mocked(transactionsApi.getChildTransactions)
const mockUpdate = vi.mocked(transactionsApi.updateTransaction)
const mockSplit = vi.mocked(transactionsApi.splitTransaction)

const transaction: Transaction = {
  id: 10, debit_date: '2026-06-01', actual_date: '2026-06-01', narration: 'Supermarket', txn_number: 'TXN-10',
  debit_amount: '100.00', credit_amount: '0.00', vendor_id: 1, vendor_name: 'Store', category: 'Food',
  sub_category: 'Groceries', notes: 'Weekly', exclude: false, child_count: 0,
  suggestion1: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
  suggestion2: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
}

const categories: Category[] = [
  { name: 'Food', subcategories: [{ name: 'Groceries' }, { name: 'Dining' }] },
  { name: 'Transport', subcategories: [{ name: 'Fuel' }] },
]

function mountDialog() {
  return mount(SplitTransactionDialog, { attachTo: document.body, props: { transaction, categories } })
}

afterEach(() => document.body.replaceChildren())

describe('SplitTransactionDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetChildren.mockResolvedValue([])
    mockUpdate.mockResolvedValue({} as any)
    mockSplit.mockResolvedValue({} as any)
  })

  it('starts with two split rows and prevents saving an incomplete split', async () => {
    mountDialog()
    await flushPromises()
    expect(document.body.textContent).toContain('Split 1')
    expect(document.body.textContent).toContain('Split 2')
    const save = [...document.body.querySelectorAll('button')].find((button) => button.textContent?.trim() === 'Save')!
    expect(save.hasAttribute('disabled')).toBe(true)
  })

  it('loads existing child splits and saves the parent before the split payload', async () => {
    mockGetChildren.mockResolvedValue([
      { ...transaction, id: 11, debit_amount: '40.00', sub_category: 'Groceries' },
      { ...transaction, id: 12, debit_amount: '60.00', sub_category: 'Dining' },
    ])
    const wrapper = mountDialog()
    await flushPromises()
    expect(mockGetChildren).toHaveBeenCalledWith(10)
    expect(document.body.textContent).toContain('Remaining ₹0.00')

    const save = [...document.body.querySelectorAll('button')].find((button) => button.textContent?.trim() === 'Save') as HTMLButtonElement
    expect(save.disabled).toBe(false)
    save.click()
    await flushPromises()

    expect(mockUpdate).toHaveBeenCalledWith(10, expect.objectContaining({ exclude: true }))
    expect(mockSplit).toHaveBeenCalledWith(10, {
      splits: [
        { debit_amount: 40, category: 'Food', sub_category: 'Groceries', notes: 'Weekly' },
        { debit_amount: 60, category: 'Food', sub_category: 'Dining', notes: 'Weekly' },
      ],
    })
    expect(wrapper.emitted('saved')).toHaveLength(1)
  })

  it('adds a row and does not allow removing below two rows', async () => {
    mountDialog()
    await flushPromises()
    const add = [...document.body.querySelectorAll('button')].find((button) => button.textContent?.includes('Add Split')) as HTMLButtonElement
    add.click()
    await flushPromises()
    expect(document.body.textContent).toContain('Split 3')
    const removeButtons = [...document.body.querySelectorAll('button')].filter((button) => button.textContent?.trim() === '✕')
    ;(removeButtons[2] as HTMLButtonElement).click()
    await flushPromises()
    expect(document.body.textContent).not.toContain('Split 3')
    expect((removeButtons[0] as HTMLButtonElement).disabled).toBe(true)
  })
})
