import client from './client'

export interface Suggestion {
    category: string | null
    sub_category: string | null
    notes: string | null
    confidence: number
    auto_prefill: boolean
}

export interface Transaction {
    id: number
    debit_date: string
    actual_date: string
    narration: string
    txn_number: string
    debit_amount: string
    credit_amount: string
    vendor_id: number | null
    vendor_name: string | null
    category: string
    sub_category: string
    notes: string
    exclude: boolean
    suggestion1: Suggestion
    suggestion2: Suggestion
}

export interface PaginatedTransactions {
    items: Transaction[]
    total: number
    page: number
    pages: number
}

export const getTransactions = (params: {
    page?: number
    page_size?: number
    search?: string
    category?: string
    vendor?: string
    start_date?: string
    end_date?: string
    min_amount?: number
    max_amount?: number
    exclude_filter?: string
}) => client.get<PaginatedTransactions>('/api/transactions', {params}).then((r) => r.data)

export const deleteTransaction = (id: Number) =>
    client.delete(`/api/transactions/${id}`)
