<script setup lang="ts">
import type {Transaction} from "@/api/transactions.ts";

const props = defineProps<{
  transaction: Transaction
}>()

</script>

<template>
  <Teleport to="body">
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <h2 class="text-lg font-semibold text-gray-900">
          Delete Transaction?
        </h2>

        <p class="mt-2 text-sm text-gray-600">
          This action cannot be undone.
        </p>

        <div class="mt-4 rounded-lg bg-gray-50 p-4 text-sm">
          <div><strong>Date:</strong> {{ props.transaction.actual_date }}</div>
          <div><strong>Description:</strong> {{ props.transaction.narration }}</div>
          <div><strong>TXN #:</strong> {{ props.transaction.txn_number }}</div>
          <div><strong>Amount:</strong> ₹{{ props.transaction.debit_amount }}</div>
          <div><strong>Vendor:</strong> {{ props.transaction.vendor_name }}</div>
          <div><strong>Category:</strong> {{ props.transaction.category }}</div>
          <div><strong>Subcategory:</strong> {{ props.transaction.sub_category }}</div>
          <div><strong>Notes:</strong> {{ props.transaction.notes }}</div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button
              @click="$emit('close')"
              class="rounded border px-4 py-2 hover:bg-gray-50"
          >
            Cancel
          </button>

          <button
              @click="$emit('deleted')"
              class="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>