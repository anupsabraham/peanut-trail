<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { watchDebounced } from '@vueuse/core'
import {
  getTransactions
} from '@/api/transactions'
import type { Transaction } from '@/api/transactions'

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

const categories = computed(() =>
  [...new Set(items.value.map(t => t.category).filter(Boolean))].sort()
)

const subcategories = computed(() =>
  [...new Set(items.value.map(t => t.sub_category).filter(Boolean))].sort()
)
// Track per-row edits
const edits = ref<Record<number, Partial<Transaction>>>({})

const loading = ref(false)

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
  if (!edits.value[txn.id]) edits.value[txn.id] = { ...txn }
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

watchDebounced([
    search,
    filterVendor,
    filterMinAmount,
    filterMaxAmount,
], () => {page.value=1; load()},
    { debounce: 500 }
)
watch([
  filterCategory,
  filterStartDate,
  filterEndDate,
  filterExclude], () => { page.value = 1; load() })
watch(page, load)

onMounted(() =>{
  load()
})

</script>

<template>
  <div class="max-w-[1400px] mx-auto px-6 py-8 space-y-4">

    <!-- Filters -->
    <div class="flex gap-3 flex-wrap items-center">
      <input
        v-model="search"
        placeholder="Search narration / txn number..."
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-gray-300"
      />
      <select
        v-model="filterCategory"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300"
      >
        <option value="">All Categories</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <input v-model="filterVendor" placeholder="Vendor..."
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />

      <input type="date" v-model="filterStartDate"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />

      <input type="date" v-model="filterEndDate"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300" />

      <input type="number" v-model="filterMinAmount" placeholder="Min ₹"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-gray-300" />

      <input type="number" v-model="filterMaxAmount" placeholder="Max ₹"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-gray-300" />

      <select v-model="filterExclude"
        class="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300">
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
            <th class="px-3 py-3 text-center">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr
            v-for="txn in items"
            :key="txn.id"
            :class="['hover:bg-gray-50 transition-colors', txn.exclude ? 'opacity-50' : '']"
          >
            <!-- Debit Date -->
            <td class="px-3 py-2">
              <input type="date" v-model="getEdit(txn).debit_date"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Actual Date -->
            <td class="px-3 py-2">
              <input type="date" v-model="getEdit(txn).actual_date"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Narration -->
            <td class="px-3 py-2">
              <input v-model="getEdit(txn).narration"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-56 focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Txn Number -->
            <td class="px-3 py-2">
              <input v-model="getEdit(txn).txn_number"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-36 font-mono focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Amount -->
            <td class="px-3 py-2">
              <input type="number" v-model="getEdit(txn).debit_amount"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-24 text-right focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Vendor (non-editable) -->
            <td class="px-3 py-2 text-gray-500 text-xs">{{ txn.vendor_name }}</td>

            <!-- Category -->
            <td class="px-3 py-2">
              <select
                v-model="getEdit(txn).category"
                class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="">—</option>
                <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
              </select>
            </td>

            <!-- Subcategory -->
            <td class="px-3 py-2">
              <select
                v-model="getEdit(txn).sub_category"
                class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
              >
                <option value="">—</option>
                <option v-for="s in subcategories" :key="s" :value="s">{{ s }}</option>
              </select>
            </td>

            <!-- Notes -->
            <td class="px-3 py-2">
              <input v-model="getEdit(txn).notes"
                class="border border-gray-200 rounded px-2 py-1 text-xs w-28 focus:outline-none focus:ring-1 focus:ring-gray-300" />
            </td>

            <!-- Exclude -->
            <td class="px-3 py-2 text-center">
              <input type="checkbox" v-model="getEdit(txn).exclude" class="rounded" />
            </td>

            <!-- Suggestions -->
            <td class="px-3 py-2">
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
            <td class="px-3 py-2 text-center">
              <div class="flex gap-1 justify-center">
                <button
                  class="text-xs bg-gray-800 hover:bg-gray-700 text-white rounded px-2 py-1 transition-colors">
                  Save
                </button>
                <button
                  class="text-xs bg-red-50 hover:bg-red-100 text-red-600 rounded px-2 py-1 transition-colors">
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between text-sm text-gray-500">
      <span>Page {{ page }} of {{ pages }}</span>
      <div class="flex gap-2">
        <button
          :disabled="page <= 1"
          @click="page--"
          class="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:bg-gray-50"
        >Prev</button>
        <button
          :disabled="page >= pages"
          @click="page++"
          class="px-3 py-1 rounded border border-gray-200 disabled:opacity-30 hover:bg-gray-50"
        >Next</button>
      </div>
    </div>

  </div>
</template>
