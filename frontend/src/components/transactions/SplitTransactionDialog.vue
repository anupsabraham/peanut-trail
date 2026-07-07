<script setup lang="ts">
import {computed, ref} from 'vue'
import {splitTransaction, type Transaction} from '@/api/transactions'


interface SplitRow {
  debit_amount: number
  category: string
  sub_category: string
  notes: string
}

const props = defineProps<{
  transaction: Transaction
  categories: string[]
  subcategories: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const rows = ref<SplitRow[]>([
  {
    debit_amount: Number(props.transaction.debit_amount),
    category: props.transaction.category,
    sub_category: props.transaction.sub_category,
    notes: props.transaction.notes,
  },
  {
    debit_amount: 0,
    category: '',
    sub_category: '',
    notes: ''
  },
])

const total = computed(() =>
    rows.value.reduce(
        (sum, row) => sum + Number(row.debit_amount || 0),
        0,
    ),
)

const remaining = computed(
    () => Number(props.transaction.debit_amount) - total.value,
)

const canSave = computed(() =>
    rows.value.length >= 2 &&
    remaining.value === 0 &&
    rows.value.every(r =>
        r.debit_amount > 0 &&
        r.category &&
        r.sub_category
    ),
)

function addRow() {
  rows.value.push({
    debit_amount: 0,
    category: '',
    sub_category: '',
    notes: '',
  })
}

function removeRow(index: number) {
  if (rows.value.length <= 2)
    return
  rows.value.splice(index, 1)
}

async function save() {
  if (!canSave.value)
    return

  await splitTransaction(
      props.transaction.id,
      {
        splits: rows.value
      },
  )

  emit('saved')
}

function amountChanged(index: number) {
  if (rows.value.length !== 2)
    return

  if (index !== 0)
    return

  rows.value[1].debit_amount = Math.max(0, Number(props.transaction.debit_amount) - Number(rows.value[0].debit_amount))
}

</script>
<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="w-full max-w-4xl rounded-xl bg-white shadow-xl">

        <!-- Header -->
        <div class="border-b px-6 py-4">
          <h2 class="text-xl font-semibold">
            Split Transaction
          </h2>

          <div class="mt-2 text-sm text-gray-500">
            <div>{{ transaction.narration }}</div>
            <div class="font-mono text-xs">
              {{ transaction.txn_number }}
            </div>
          </div>
        </div>

        <!-- Body -->
        <div class="p-6 space-y-4">

          <!-- Compact header -->
          <div class="flex items-center justify-between text-sm">
            <div>
              <div class="font-medium">
                {{ transaction.vendor_name || transaction.narration }}
              </div>
              <div class="text-xs text-gray-500 font-mono">
                {{ transaction.txn_number }}
              </div>
            </div>

            <div class="text-right">
              <div class="text-xs text-gray-500">
                Original
              </div>

              <div class="font-medium">
                ₹{{ transaction.debit_amount }}
              </div>

              <div
                  class="text-xs font-medium"
                  :class="{
          'text-green-600': remaining === 0,
          'text-red-600': remaining < 0,
          'text-orange-500': remaining > 0,
        }"
              >
                Remaining ₹{{ remaining.toFixed(2) }}
              </div>
            </div>
          </div>

          <!-- Same table style as Transactions page -->
          <div class="overflow-hidden rounded-2xl border border-gray-100 shadow-sm">

            <table class="w-full text-sm">

              <thead>
              <tr class="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                <th class="px-3 py-3 text-left">
                  Type
                </th>

                <th class="px-3 py-3 text-right">
                  Amount
                </th>

                <th class="px-3 py-3 text-left">
                  Category
                </th>

                <th class="px-3 py-3 text-left">
                  Subcategory
                </th>

                <th class="px-3 py-3 text-left">
                  Notes
                </th>

                <th class="px-3 py-3 w-12"></th>
              </tr>
              </thead>

              <tbody class="divide-y divide-gray-50">

              <!-- Original -->

              <tr class="bg-gray-50">

                <td class="px-3 py-2 text-xs font-medium text-gray-500">
                  Original
                </td>

                <td class="px-3 py-2 text-right font-medium">
                  ₹{{ transaction.debit_amount }}
                </td>

                <td class="px-3 py-2">
                  {{ transaction.category }}
                </td>

                <td class="px-3 py-2">
                  {{ transaction.sub_category }}
                </td>

                <td class="px-3 py-2">
                  {{ transaction.notes }}
                </td>

                <td></td>

              </tr>

              <!-- Editable rows -->

              <tr
                  v-for="(row, index) in rows"
                  :key="index"
              >

                <td class="px-3 py-2 text-xs text-gray-500">
                  Split {{ index + 1 }}
                </td>

                <td class="px-3 py-2">

                  <input
                      v-model.number="row.debit_amount"
                      @input="amountChanged(index)"
                      type="number"
                      class="border border-gray-200 rounded px-2 py-1 text-xs w-24 text-right focus:outline-none focus:ring-1 focus:ring-gray-300"
                  />

                </td>

                <td class="px-3 py-2">

                  <select
                      v-model="row.category"
                      class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
                  >
                    <option value="">—</option>

                    <option
                        v-for="c in categories"
                        :key="c"
                        :value="c"
                    >
                      {{ c }}
                    </option>

                  </select>

                </td>

                <td class="px-3 py-2">

                  <select
                      v-model="row.sub_category"
                      class="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-300"
                  >
                    <option value="">—</option>

                    <option
                        v-for="s in subcategories"
                        :key="s"
                        :value="s"
                    >
                      {{ s }}
                    </option>

                  </select>

                </td>

                <td class="px-3 py-2">

                  <input
                      v-model="row.notes"
                      class="border border-gray-200 rounded px-2 py-1 text-xs w-40 focus:outline-none focus:ring-1 focus:ring-gray-300"
                  />

                </td>

                <td class="px-3 py-2 text-center">

                  <button
                      @click="removeRow(index)"
                      :disabled="rows.length <= 2"
                      class="text-red-600 hover:text-red-700 disabled:text-gray-300"
                  >
                    ✕
                  </button>

                </td>

              </tr>

              </tbody>

            </table>
            <div class="m-4">
              <button
                  @click="addRow"
                  class="rounded border border-gray-200 px-3 py-2 text-sm hover:bg-gray-50"
              >
                + Add Split
              </button>
            </div>
          </div>


        </div>

        <!-- Footer -->
        <div class="px-6 pb-6 pt-4">
          <div class="mt-6 flex justify-end gap-3">
            <button
                @click="$emit('close')"
                class="rounded border px-4 py-2 hover:bg-gray-50"
            >
              Cancel
            </button>

            <button
                :disabled="!canSave"
                @click="save"
                class="rounded bg-orange-400 px-4 py-2 text-white hover:bg-orange-300 disabled:bg-gray-300"
            >
              Split
            </button>
          </div>

        </div>
      </div>
    </div>
  </Teleport>
</template>