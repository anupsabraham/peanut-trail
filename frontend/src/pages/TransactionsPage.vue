<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue'
import {watchDebounced} from '@vueuse/core'
import {
  type Category,
  deleteTransaction,
  getCategories,
  getChildTransactions,
  getTransactions,
  type Transaction,
  updateTransaction
} from '@/api/transactions'
import SplitTransactionDialog from '@/components/transactions/SplitTransactionDialog.vue'
import DeleteTransactionDialog from "@/components/transactions/DeleteTransactionDialog.vue";

const items = ref<Transaction[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 50
const pages = ref(1)

const search = ref('')
const filterCategory = ref('')
const filterVendor = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterMinAmount = ref<number | undefined>(undefined)
const filterMaxAmount = ref<number | undefined>(undefined)
const filterExclude = ref('')

const expandedTransactions = ref<Set<number>>(new Set())
const childTransactions = ref<Record<number, Transaction[]>>({})

const txnToDelete = ref<Transaction | null>(null)
const txnToSplit = ref<Transaction | null>(null)

const categoryData = ref<Category[]>([])

// Track per-row edits
const edits = ref<Record<number, Partial<Transaction>>>({})

const loading = ref(false)

const categories = computed(() =>
    categoryData.value.map(c => c.name)
)

async function load() {
  loading.value = true
  const res = await getTransactions({
    page: page.value,
    page_size: pageSize,
    search: search.value || undefined,
    category: filterCategory.value || undefined,
    vendor: filterVendor.value || undefined,
    start_date: filterStartDate.value || undefined,
    end_date: filterEndDate.value || undefined,
    min_amount: filterMinAmount.value,
    max_amount: filterMaxAmount.value,
    exclude_filter: filterExclude.value || undefined,
  })
  items.value = res.items
  total.value = res.total
  pages.value = res.pages
  edits.value = {}
  loading.value = false
}

function getEdit(txn: Transaction) {
  if (!edits.value[txn.id]) edits.value[txn.id] = {...txn}
  return edits.value[txn.id]
}

function applySuggestion(txn: Transaction, s: Transaction['suggestion1']) {
  if (!s.category) return
  edits.value[txn.id] = {
    ...getEdit(txn),
    category: s.category,
    sub_category: s.sub_category ?? '',
    notes: s.notes ?? '',
  }
}

function confirmDelete(txn: Transaction) {
  txnToDelete.value = txn
}

function split(txn: Transaction) {
  txnToSplit.value = txn
}

async function deleteConfirmed() {
  if (!txnToDelete.value) return

  try {
    await deleteTransaction(txnToDelete.value.id)
  } finally {
    txnToDelete.value = null
    await load()
  }
}

async function splitCompleted() {
  txnToSplit.value = null
  await load()
}

async function save(txn: Transaction) {
  const edit = edits.value[txn.id]
  if (!edit) return
  try {
    await updateTransaction(txn.id, {
      debit_date: edit.debit_date,
      actual_date: edit.actual_date,
      narration: edit.narration,
      txn_number: edit.txn_number,
      debit_amount: edit.debit_amount,
      category: edit.category,
      sub_category: edit.sub_category,
      notes: edit.notes,
      exclude: edit.exclude
    })
  } finally {
    await load()
  }
}

async function toggleChildren(txn: Transaction) {
  if (!txn.child_count)
    return
  if (expandedTransactions.value.has(txn.id)) {
    expandedTransactions.value.delete(txn.id)
    return
  }

  expandedTransactions.value.add(txn.id)

  if (!childTransactions.value[txn.id]) {
    childTransactions.value[txn.id] = await getChildTransactions(txn.id)
  }
}

async function loadCategories() {
  const response = await getCategories()
  categoryData.value = response.categories
}

function getSubcategories(category: string): string[] {
  return (
      categoryData.value.find(c => c.name === category)?.subcategories.map(s => s.name) ?? []
  )
}

watchDebounced(
    [search, filterVendor, filterMinAmount, filterMaxAmount],
    () => {
      page.value = 1
      load()
    },
    {debounce: 500},
)
watch([filterCategory, filterStartDate, filterEndDate, filterExclude], () => {
  page.value = 1
  load()
})
watch(page, load)

onMounted(() => {
  load()
  loadCategories()
})
</script>

<template>
  <div class="max-w-[1400px] mx-auto px-6 py-8 space-y-4">
    <!-- Filters -->
    <div class="flex gap-3 flex-wrap items-center">
      <input
          v-model="search"
          placeholder="Search ..."
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-gray-300"
      />
      <select
          v-model="filterCategory"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      >
        <option value="">All Categories</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <input
          v-model="filterVendor"
          placeholder="Vendor..."
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      />

      <input
          type="date"
          v-model="filterStartDate"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      />

      <input
          type="date"
          v-model="filterEndDate"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      />

      <input
          type="number"
          v-model="filterMinAmount"
          placeholder="Min ₹"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-gray-300"
      />

      <input
          type="number"
          v-model="filterMaxAmount"
          placeholder="Max ₹"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-gray-300"
      />

      <select
          v-model="filterExclude"
          class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      >
        <option value="">All</option>
        <option value="false">Active</option>
        <option value="true">Excluded</option>
      </select>
      <span class="text-sm text-gray-400 ml-auto">{{ total }} transactions</span>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-2xl border border-gray-100 shadow-sm">
      <table class="w-full text-sm">
        <thead>
        <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
          <th class="w-8"></th>
          <th class="px-3 py-3 text-left">Debit Date</th>
          <th class="px-3 py-3 text-left">Actual Date</th>
          <th class="px-3 py-3 text-left w-64">Narration</th>
          <th class="px-3 py-3 text-left">Txn #</th>
          <th class="px-3 py-3 text-right">Amount</th>
          <th class="px-3 py-3 text-left">Vendor</th>
          <th class="px-3 py-3 text-left">Category</th>
          <th class="px-3 py-3 text-left">Subcategory</th>
          <th class="px-3 py-3 text-left">Notes</th>
          <th class="px-3 py-3 text-center">Exclude</th>
          <th class="px-3 py-3 text-left">Suggestions</th>
          <th class="px-3 py-3 text-center sticky right-0 z-20 bg-gray-50">Actions</th>
        </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
        <template
            v-for="txn in items"
            :key="txn.id"
        >
          <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-2 text-center">

              <button
                  v-if="txn.child_count > 0"
                  @click="toggleChildren(txn)"
                  class="text-gray-500 hover:text-gray-700"
              >
                {{ expandedTransactions.has(txn.id) ? '▼' : '▶' }}
              </button>

            </td>
            <!-- Debit Date -->
            <td class="px-3 py-2">
              <input
                  type="date"
                  v-model="getEdit(txn).debit_date"
                  :class="['border border-gray-200 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:ring-1 focus:ring-gray-300', txn.exclude ? 'opacity-50' : '']"
              />
            </td>

            <!-- Actual Date -->
            <td class="px-3 py-2">
              <input
                  type="date"
                  v-model="getEdit(txn).actual_date"
                  :class="['border border-gray-200 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:ring-1 focus:ring-gray-300', txn.exclude ? 'opacity-50' : '']"
              />
            </td>

            <!-- Narration -->
            <td class="px-3 py-2">
              <input
                  v-model="getEdit(txn).narration"
                  :class="['border border-gray-200 rounded px-2 py-1 text-xs w-56 focus:outline-none focus:ring-1 focus:ring-gray-300', txn.exclude ? 'opacity-50' : '']"
              />
            </td>

            <!-- Txn Number -->
            <td class="px-3 py-2">
              <input
                  v-model="getEdit(txn).txn_number"
                  :class="['border border-gray-200 rounded px-2 py-1 text-xs w-36 font-mono focus:outline-none focus:ring-1 focus:ring-gray-300', txn.exclude ? 'opacity-50' : '']"
              />
            </td>

            <!-- Amount -->
            <td class="px-3 py-2">
              <input
                  type="number"
                  v-model="getEdit(txn).debit_amount"
                  :class="['border border-gray-200 rounded px-2 py-1 text-xs w-24 text-right focus:outline-none focus:ring-1 focus:ring-gray-300', txn.exclude ? 'opacity-50' : '']"
              />
            </td>

            <!-- Vendor (non-editable) -->
            <td :class="['px-3 py-2 text-gray-500 text-xs', txn.exclude ? 'opacity-50' : '']">{{ txn.vendor_name }}</td>

            <!-- Category -->
            <td :class="['px-3 py-2', txn.exclude ? 'opacity-50' : '']">
              <select
                  v-model="getEdit(txn).category"
                  class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="">—</option>
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </td>

            <!-- Subcategory -->
            <td :class="['px-3 py-2', txn.exclude ? 'opacity-50' : '']">
              <select
                  v-model="getEdit(txn).sub_category"
                  class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="">—</option>
                <option v-for="s in getSubcategories(getEdit(txn).category)" :key="s" :value="s">{{ s }}</option>
              </select>
            </td>

            <!-- Notes -->
            <td :class="['px-3 py-2', txn.exclude ? 'opacity-50' : '']">
              <input
                  v-model="getEdit(txn).notes"
                  class="border border-gray-200 rounded px-2 py-1 text-xs w-28 focus:outline-none focus:ring-1 focus:ring-gray-300"
              />
            </td>

            <!-- Exclude -->
            <td :class="['px-3 py-2 text-center', txn.exclude ? 'opacity-50' : '']">
              <input type="checkbox" v-model="getEdit(txn).exclude" class="rounded"/>
            </td>

            <!-- Suggestions -->
            <td :class="['px-3 py-2', txn.exclude ? 'opacity-50' : '']">
              <div class="flex flex-col gap-1">
                <button
                    v-if="txn.suggestion1?.category"
                    @click="applySuggestion(txn, txn.suggestion1)"
                    class="text-left text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 rounded px-2 py-0.5 truncate max-w-[160px]"
                    :title="`${txn.suggestion1.category} / ${txn.suggestion1.sub_category}`"
                >
                  {{ txn.suggestion1.category }} · {{ txn.suggestion1.sub_category }}
                </button>
                <button
                    v-if="txn.suggestion2?.category"
                    @click="applySuggestion(txn, txn.suggestion2)"
                    class="text-left text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 rounded px-2 py-0.5 truncate max-w-[160px]"
                    :title="`${txn.suggestion2.category} / ${txn.suggestion2.sub_category}`"
                >
                  {{ txn.suggestion2.category }} · {{ txn.suggestion2.sub_category }}
                </button>
              </div>
            </td>

            <!-- Actions -->
            <td class="px-3 py-2 text-center sticky right-0 bg-white opacity-100">
              <div class="flex gap-1 justify-center">
                <button :disabled="txn.child_count !== 0"
                        @click="save(txn)"
                        :class="['text-xs bg-gray-800 hover:bg-gray-700 text-white rounded px-2 py-1 transition-colors', txn.child_count > 0 ? 'opacity-50': '']"
                >
                  Save
                </button>
                <button @click="split(txn)"
                        class="text-xs bg-orange-400 hover:bg-orange-300 text-white rounded px-2 py-1 transition-colors"
                >
                  {{ txn.child_count > 0 ? "Edit" : "Split" }}
                </button>
                <button @click="confirmDelete(txn)"
                        class="text-xs bg-red-50 hover:bg-red-100 text-red-600 rounded px-2 py-1 transition-colors"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
          <tr
              v-for="child in childTransactions[txn.id] || []"
              v-show="expandedTransactions.has(txn.id)"
              :key="child.id"
              class="bg-gray-50"
          >

            <td></td>

            <td class="px-3 py-2 text-xs text-gray-500">
              {{ child.debit_date }}
            </td>

            <td class="px-3 py-2 text-xs text-gray-500">
              {{ child.actual_date }}
            </td>

            <td class="px-3 py-2 pl-10">
              <div class="single-line-truncate">
                {{ child.narration }}
              </div>
            </td>

            <td class="px-3 py-2 font-mono text-xs">
              {{ child.txn_number }}
            </td>

            <td class="px-3 py-2 text-center">
              {{ child.debit_amount }}
            </td>

            <td class="px-3 py-2 single-line-truncate">
              {{ child.vendor_name }}
            </td>

            <td class="px-3 py-2">
              {{ child.category }}
            </td>

            <td class="px-3 py-2">
              {{ child.sub_category }}
            </td>

            <td class="px-3 py-2">
              {{ child.notes }}
            </td>

            <td class="px-3 py-2 text-center">
              {{ child.exclude ? "✓" : "" }}
            </td>

            <td></td>

            <td class="sticky right-0 bg-gray-50"></td>

          </tr>
        </template>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between text-sm text-gray-500">
      <span class="flex items-center gap-2">
        Page
        <input
            v-model.number="page"
            type="number"
            :min="1"
            :max="pages"
            @change="page = Math.min(Math.max(page, 1), pages)"
            class="w-16 rounded border border-gray-300 px-2 py-1 text-center"
        />
        of {{ pages }}
      </span>

      <div class="flex gap-2">
        <button
            :disabled="page <= 1"
            @click="page--"
            class="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:bg-gray-50"
        >
          Prev
        </button>
        <button
            :disabled="page >= pages"
            @click="page++"
            class="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  </div>
  <DeleteTransactionDialog
      v-if="txnToDelete"
      :transaction="txnToDelete"
      @close="txnToDelete = null"
      @deleted="deleteConfirmed"
  />
  <SplitTransactionDialog
      v-if="txnToSplit"
      :transaction="txnToSplit"
      :categories="categoryData"
      @close="txnToSplit = null"
      @saved="splitCompleted"
  />
</template>

<style scoped>
.single-line-truncate {
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* Adds the '...' automatically */
  max-width: 200px;
}
</style>