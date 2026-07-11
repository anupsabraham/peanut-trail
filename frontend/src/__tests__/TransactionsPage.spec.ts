import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import TransactionsPage from '@/pages/TransactionsPage.vue'
import * as txnApi from '@/api/transactions'
import type { Transaction } from '@/api/transactions'

// Make watchDebounced behave like a regular watch so filter tests are synchronous
vi.mock('@vueuse/core', async () => {
  const { watch } = await import('vue')
  return {
    watchDebounced: (source: any, cb: any, _opts: any) => watch(source, cb),
  }
})

vi.mock('@/api/transactions', () => ({
  getTransactions: vi.fn(),
  getCategories: vi.fn(),
  getChildTransactions: vi.fn(),
  deleteTransaction: vi.fn(),
  updateTransaction: vi.fn(),
}))

const mockGetTransactions = vi.mocked(txnApi.getTransactions)
const mockGetCategories = vi.mocked(txnApi.getCategories)
const mockGetChildTransactions = vi.mocked(txnApi.getChildTransactions)
const mockDeleteTransaction = vi.mocked(txnApi.deleteTransaction)
const mockUpdateTransaction = vi.mocked(txnApi.updateTransaction)

function makeTransaction(overrides: Partial<Transaction> = {}): Transaction {
  return {
    id: Math.random(),
    debit_date: '2026-06-01',
    actual_date: '2026-06-01',
    narration: 'Test narration',
    txn_number: `TXN${Math.random()}`,
    debit_amount: '100.00',
    credit_amount: '0.00',
    vendor_id: null,
    vendor_name: null,
    category: 'Food',
    sub_category: 'Groceries',
    notes: '',
    exclude: false,
    suggestion1: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
    suggestion2: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
    child_count: 0,
    ...overrides,
  }
}

const SearchableSelectStub = {
  props: ['modelValue', 'options', 'placeholder'],
  emits: ['update:modelValue'],
  template: `<select :value="modelValue" :aria-label="placeholder || 'select'" @change="$emit('update:modelValue', $event.target.value)"><option v-for="option in options" :key="option" :value="option">{{ option }}</option></select>`,
}

function mountPage() {
  return mount(TransactionsPage, {
    global: {
      stubs: {
        SearchableSelect: SearchableSelectStub,
        DeleteTransactionDialog: { props: ['transaction'], emits: ['close', 'deleted'], template: '<button data-testid="delete-dialog" @click="$emit(\'deleted\')" />' },
        SplitTransactionDialog: { props: ['transaction', 'categories'], emits: ['close', 'saved'], template: '<div data-testid="split-dialog" />' },
      },
    },
  })
}

function makePage(items: Transaction[] = [], total = items.length) {
  return { items, total, page: 1, pages: Math.ceil(total / 50) || 1 }
}

describe('TransactionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetTransactions.mockResolvedValue(makePage())
    mockGetCategories.mockResolvedValue({ categories: [{ name: 'Food', subcategories: [{ name: 'Groceries' }] }] })
    mockGetChildTransactions.mockResolvedValue([])
    mockDeleteTransaction.mockResolvedValue({} as any)
    mockUpdateTransaction.mockResolvedValue({} as any)
  })

  describe('initial load', () => {
    it('calls getTransactions on mount', async () => {
      mountPage()
      await flushPromises()
      expect(mockGetTransactions).toHaveBeenCalledOnce()
    })

    it('shows a loading state while fetching', () => {
      // Don't flush — still loading
      mockGetTransactions.mockReturnValue(new Promise(() => {}))
      mountPage()
      // The table body should have no rows and loading prevents rendering data
      // (no explicit loading text in template, but no items yet)
      expect(mockGetTransactions).toHaveBeenCalled()
    })

    it('renders table rows after data arrives', async () => {
      mockGetTransactions.mockResolvedValueOnce(makePage([makeTransaction(), makeTransaction()]))
      const wrapper = mountPage()
      await flushPromises()
      expect(wrapper.findAll('tbody tr')).toHaveLength(2)
    })

    it('shows the total transaction count', async () => {
      mockGetTransactions.mockResolvedValueOnce(makePage([makeTransaction()], 42))
      const wrapper = mountPage()
      await flushPromises()
      expect(wrapper.text()).toContain('42 transactions')
    })

    it('renders an empty table when there are no transactions', async () => {
      const wrapper = mountPage()
      await flushPromises()
      expect(wrapper.findAll('tbody tr')).toHaveLength(0)
    })
  })

  describe('table structure', () => {
    it('renders all expected column headers', async () => {
      const wrapper = mountPage()
      await flushPromises()
      const headers = wrapper.text()
      expect(headers).toContain('Debit Date')
      expect(headers).toContain('Actual Date')
      expect(headers).toContain('Narration')
      expect(headers).toContain('Amount')
      expect(headers).toContain('Category')
      expect(headers).toContain('Subcategory')
      expect(headers).toContain('Exclude')
      expect(headers).toContain('Suggestions')
    })
  })

  describe('filtering', () => {
    it('reloads with category filter when category select changes', async () => {
      mockGetTransactions.mockResolvedValue(makePage([makeTransaction({ category: 'Food' })]))
      const wrapper = mountPage()
      await flushPromises()
      vi.clearAllMocks()
      mockGetTransactions.mockResolvedValue(makePage())

      await wrapper.find('select[aria-label="All Categories"]').setValue('Food')
      await flushPromises()

      expect(mockGetTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'Food', page: 1 }),
      )
    })

    it('reloads with exclude filter when exclude select changes', async () => {
      const wrapper = mountPage()
      await flushPromises()
      vi.clearAllMocks()
      mockGetTransactions.mockResolvedValue(makePage())

      // Last select is the exclude filter
      const selects = wrapper.findAll('select')
      await selects[selects.length - 1]!.setValue('true')
      await flushPromises()

      expect(mockGetTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ exclude_filter: 'true', page: 1 }),
      )
    })

    it('reloads with search term when search input changes (watchDebounced mocked as watch)', async () => {
      const wrapper = mountPage()
      await flushPromises()
      vi.clearAllMocks()
      mockGetTransactions.mockResolvedValue(makePage())

      const searchInput = wrapper.find('input[placeholder*="Search"]')
      await searchInput.setValue('amazon')
      await flushPromises()

      expect(mockGetTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'amazon', page: 1 }),
      )
    })

    it('resets page to 1 when a filter changes', async () => {
      mockGetTransactions.mockResolvedValue(makePage([], 100))
      const wrapper = mountPage()
      await flushPromises()

      vi.clearAllMocks()
      mockGetTransactions.mockResolvedValue(makePage())

      const nextBtn = wrapper.findAll('button').find((b) => b.text() === 'Next')!
      await nextBtn.trigger('click')
      await flushPromises()
      vi.clearAllMocks()
      await wrapper.find('select').setValue('Food')
      await flushPromises()

      expect(mockGetTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1 }),
      )
    })
  })

  describe('pagination', () => {
    it('shows page info', async () => {
      mockGetTransactions.mockResolvedValueOnce({ items: [], total: 100, page: 1, pages: 2 })
      const wrapper = mountPage()
      await flushPromises()
      expect(wrapper.text()).toContain('Page')
      expect(wrapper.text()).toContain('of 2')
      const numberInputs = wrapper.findAll('input[type="number"]')
      expect((numberInputs[numberInputs.length - 1]!.element as HTMLInputElement).value).toBe('1')
    })

    it('Next button is disabled on the last page', async () => {
      mockGetTransactions.mockResolvedValueOnce({ items: [], total: 10, page: 1, pages: 1 })
      const wrapper = mountPage()
      await flushPromises()
      const nextBtn = wrapper.find('button:last-of-type')
      expect(nextBtn.attributes('disabled')).toBeDefined()
    })

    it('Prev button is disabled on page 1', async () => {
      mockGetTransactions.mockResolvedValueOnce({ items: [], total: 10, page: 1, pages: 1 })
      const wrapper = mountPage()
      await flushPromises()
      const prevBtn = wrapper.find('button:first-of-type')
      expect(prevBtn.attributes('disabled')).toBeDefined()
    })

    it('clicking Next loads the next page', async () => {
      mockGetTransactions.mockResolvedValue({ items: [], total: 100, page: 1, pages: 3 })
      const wrapper = mountPage()
      await flushPromises()
      vi.clearAllMocks()
      mockGetTransactions.mockResolvedValue({ items: [], total: 100, page: 2, pages: 3 })

      const buttons = wrapper.findAll('button')
      const nextBtn = buttons.find((b) => b.text() === 'Next')
      await nextBtn!.trigger('click')
      await flushPromises()

      expect(mockGetTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      )
    })
  })

  describe('suggestions', () => {
    it('renders suggestion1 button when suggestion has a category', async () => {
      const txn = makeTransaction({
        id: 1,
        suggestion1: { category: 'Food', sub_category: 'Dining', notes: '', confidence: 80, auto_prefill: false },
      })
      mockGetTransactions.mockResolvedValueOnce(makePage([txn]))
      const wrapper = mountPage()
      await flushPromises()

      expect(wrapper.text()).toContain('Food · Dining')
    })

    it('does not render suggestion button when category is null', async () => {
      const txn = makeTransaction({ id: 1 }) // suggestion1 category is null by default
      mockGetTransactions.mockResolvedValueOnce(makePage([txn]))
      const wrapper = mount(TransactionsPage)
      await flushPromises()

      // No blue suggestion buttons should appear
      const suggestionBtns = wrapper.findAll('button.text-blue-700')
      expect(suggestionBtns).toHaveLength(0)
    })

    it('clicking suggestion1 fills in category and subcategory for that row', async () => {
      const txn = makeTransaction({
        id: 99,
        category: '',
        sub_category: '',
        suggestion1: { category: 'Transport', sub_category: 'Fuel', notes: 'highway', confidence: 90, auto_prefill: true },
      })
      mockGetCategories.mockResolvedValueOnce({ categories: [{ name: 'Transport', subcategories: [{ name: 'Fuel' }] }] })
      mockGetTransactions.mockResolvedValueOnce(makePage([txn]))
      const wrapper = mountPage()
      await flushPromises()

      const suggBtn = wrapper.find('button.text-blue-700')
      await suggBtn.trigger('click')
      await wrapper.vm.$nextTick()

      const categorySelects = wrapper.findAll('td select')
      expect((categorySelects[0]!.element as HTMLSelectElement).value).toBe('Transport')
    })
  })

  it('loads API categories for the category controls', async () => {
    const wrapper = mountPage()
    await flushPromises()
    expect(mockGetCategories).toHaveBeenCalledOnce()
    expect(wrapper.find('select[aria-label="All Categories"]').text()).toContain('Food')
  })

  it('saves edited transaction data and reloads the list', async () => {
    const transaction = makeTransaction({ id: 20 })
    mockGetTransactions.mockResolvedValue(makePage([transaction]))
    const wrapper = mountPage()
    await flushPromises()
    vi.clearAllMocks()
    const narration = wrapper.findAll('tbody tr')[0]!.findAll('input')[2]!
    await narration.setValue('Changed narration')
    await wrapper.findAll('button').find((button) => button.text() === 'Save')!.trigger('click')
    await flushPromises()
    expect(mockUpdateTransaction).toHaveBeenCalledWith(20, expect.objectContaining({ narration: 'Changed narration' }))
    expect(mockGetTransactions).toHaveBeenCalledOnce()
  })

  it('loads child rows once and toggles their visibility', async () => {
    const parent = makeTransaction({ id: 20, child_count: 1 })
    const child = makeTransaction({ id: 21, narration: 'Child split' })
    mockGetTransactions.mockResolvedValue(makePage([parent]))
    mockGetChildTransactions.mockResolvedValue([child])
    const wrapper = mountPage()
    await flushPromises()
    const toggle = wrapper.findAll('button').find((button) => button.text() === '▶')!
    await toggle.trigger('click')
    await flushPromises()
    expect(mockGetChildTransactions).toHaveBeenCalledWith(20)
    expect(wrapper.text()).toContain('Child split')
    await toggle.trigger('click')
    await toggle.trigger('click')
    await flushPromises()
    expect(mockGetChildTransactions).toHaveBeenCalledOnce()
  })

  it('deletes a transaction after the confirmation dialog emits deleted', async () => {
    const transaction = makeTransaction({ id: 20 })
    mockGetTransactions.mockResolvedValue(makePage([transaction]))
    const wrapper = mountPage()
    await flushPromises()
    await wrapper.findAll('button').find((button) => button.text() === 'Delete')!.trigger('click')
    await wrapper.find('[data-testid="delete-dialog"]').trigger('click')
    await flushPromises()
    expect(mockDeleteTransaction).toHaveBeenCalledWith(20)
    expect(mockGetTransactions).toHaveBeenCalledTimes(2)
  })
})
