import client from './client'

export interface CategoryRow {
  category: string
  total_amount: number
}

export interface ChartDataset {
  label: string
  data: (number | null)[]
  borderColor: string
  borderWidth: number
  borderDash?: number[]
  pointRadius?: number
}

export interface CategoryExpenses {
  categories: CategoryRow[]
  total_expense: number
}

export interface ProgressionChartData {
  progression_datasets: ChartDataset[]
  days: number[]
}

export const getCategoryExpenses = () =>
  client
    .get<CategoryExpenses>('/api/analytics/expenses/by-category/current-month')
    .then((r) => r.data)

export const getProgressionChartData = () =>
  client
    .get<ProgressionChartData>('/api/analytics/chart/progression/current-month')
    .then((r) => r.data)
