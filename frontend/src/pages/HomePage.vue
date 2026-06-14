<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, LineElement, PointElement,
  LinearScale, CategoryScale, Legend, Tooltip
} from 'chart.js'
import { getCategoryExpenses, getProgressionChartData } from '@/api/dashboard'
import type { CategoryRow, ChartDataset } from '@/api/dashboard'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Legend, Tooltip)

const summary = ref<{ categories: CategoryRow[], total_expense: number } | null>(null)
const chartData = ref<{ labels: number[], datasets: ChartDataset[] } | null>(null)
const loading = ref(true)

onMounted(async () => {
  const [s, p] = await Promise.all([getCategoryExpenses(), getProgressionChartData()])
  summary.value = s
  chartData.value = {
    labels: p.days,
    datasets: p.progression_datasets.map(d => ({
      ...d,
      borderDash: d.borderDash ?? undefined,
      pointRadius: d.pointRadius ?? undefined,
    }))
  }
  loading.value = false
})
</script>

<template>
  <!-- Loading -->
  <div v-if="loading" class="flex items-center justify-center h-screen text-gray-400">
    Loading...
  </div>

  <div v-else class="max-w-6xl mx-auto px-6 py-10 space-y-8">

    <!-- Header -->
    <div class="flex items-baseline justify-between">
      <h1 class="text-2xl font-semibold text-gray-800">This Month</h1>
      <span class="text-3xl font-bold text-gray-900">
        ₹{{ summary?.total_expense.toLocaleString('en-IN') }}
      </span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

      <!-- Category table -->
      <div class="lg:col-span-1 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 text-gray-500 uppercase text-xs tracking-wide">
              <th class="text-left px-5 py-3">Category</th>
              <th class="text-right px-5 py-3">Amount</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-50">
            <tr
              v-for="row in summary?.categories"
              :key="row.category"
              class="hover:bg-gray-50 transition-colors"
            >
              <td class="px-5 py-3 text-gray-700">{{ row.category }}</td>
              <td class="px-5 py-3 text-right font-medium text-gray-900">
                ₹{{ row.total_amount.toLocaleString('en-IN') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Chart -->
      <div class="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
        <h2 class="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">Spending Progression</h2>
        <div class="h-80">
          <Line
            v-if="chartData"
            :data="chartData"
            :options="{ responsive: true, maintainAspectRatio: false }"
          />
        </div>
      </div>

    </div>
  </div>
</template>