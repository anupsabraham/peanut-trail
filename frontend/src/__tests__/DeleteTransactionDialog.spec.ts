import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DeleteTransactionDialog from '@/components/transactions/DeleteTransactionDialog.vue'
import type { Transaction } from '@/api/transactions'

const transaction: Transaction = {
  id: 1, debit_date: '2026-06-01', actual_date: '2026-06-02', narration: 'Coffee shop', txn_number: 'TXN-1',
  debit_amount: '125.00', credit_amount: '0.00', vendor_id: 2, vendor_name: 'Cafe', category: 'Food',
  sub_category: 'Dining', notes: 'Team meeting', exclude: false, child_count: 0,
  suggestion1: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
  suggestion2: { category: null, sub_category: null, notes: null, confidence: 0, auto_prefill: false },
}

afterEach(() => document.body.replaceChildren())

describe('DeleteTransactionDialog', () => {
  it('shows transaction details', () => {
    const wrapper = mount(DeleteTransactionDialog, { attachTo: document.body, props: { transaction } })
    expect(document.body.textContent).toContain('Coffee shop')
    expect(document.body.textContent).toContain('₹125.00')
    expect(document.body.textContent).toContain('Team meeting')
    wrapper.unmount()
  })

  it('emits close and deleted from the matching actions', async () => {
    const wrapper = mount(DeleteTransactionDialog, { attachTo: document.body, props: { transaction } })
    const buttons = document.body.querySelectorAll('button')
    ;(buttons[0] as HTMLButtonElement).click()
    ;(buttons[1] as HTMLButtonElement).click()
    expect(wrapper.emitted('close')).toHaveLength(1)
    expect(wrapper.emitted('deleted')).toHaveLength(1)
    wrapper.unmount()
  })
})
