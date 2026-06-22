import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import HomePage from '@/pages/HomePage.vue'
import * as dashboardApi from '@/api/dashboard'

// Chart.js has no canvas in jsdom — stub both the lib and the component
vi.mock('chart.js', () => ({
  Chart: class {
    static register() {}
  },
  LineElement: {},
  PointElement: {},
  LinearScale: {},
  CategoryScale: {},
  Legend: {},
  Tooltip: {},
}))

vi.mock('vue-chartjs', () => ({
  Line: { render: () => null },
}))

vi.mock('@/api/dashboard', () => ({
  getCategoryExpenses: vi.fn(),
  getProgressionChartData: vi.fn(),
}))

const mockGetCategoryExpenses = vi.mocked(dashboardApi.getCategoryExpenses)
const mockGetProgressionChartData = vi.mocked(dashboardApi.getProgressionChartData)

function makeSummary(categories = [{ category: 'Food', total_amount: 1500 }], total = 1500) {
  return { categories, total_expense: total }
}

function makeChartData() {
  return {
    progression_datasets: [{ label: 'June 2026', data: [100], borderColor: '#fff', borderWidth: 1 }],
    days: Array.from({ length: 31 }, (_, i) => i + 1),
  }
}

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetCategoryExpenses.mockResolvedValue(makeSummary())
    mockGetProgressionChartData.mockResolvedValue(makeChartData())
  })

  it('shows a loading indicator before data arrives', () => {
    // Don't flush promises — component is still loading
    const wrapper = mount(HomePage)
    expect(wrapper.text()).toContain('Loading')
  })

  it('hides the loading indicator after data arrives', async () => {
    const wrapper = mount(HomePage)
    await flushPromises()
    expect(wrapper.text()).not.toContain('Loading')
  })

  it('calls getCategoryExpenses on mount', async () => {
    mount(HomePage)
    await flushPromises()
    expect(mockGetCategoryExpenses).toHaveBeenCalledOnce()
  })

  it('calls getProgressionChartData on mount', async () => {
    mount(HomePage)
    await flushPromises()
    expect(mockGetProgressionChartData).toHaveBeenCalledOnce()
  })

  it('displays the total expense', async () => {
    mockGetCategoryExpenses.mockResolvedValueOnce(makeSummary([], 4250))
    const wrapper = mount(HomePage)
    await flushPromises()
    expect(wrapper.text()).toContain('4,250')
  })

  it('renders a row for each category', async () => {
    mockGetCategoryExpenses.mockResolvedValueOnce(
      makeSummary([
        { category: 'Food', total_amount: 1200 },
        { category: 'Transport', total_amount: 800 },
        { category: 'Bills', total_amount: 400 },
      ]),
    )
    const wrapper = mount(HomePage)
    await flushPromises()
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(3)
    expect(wrapper.text()).toContain('Food')
    expect(wrapper.text()).toContain('Transport')
    expect(wrapper.text()).toContain('Bills')
  })

  it('renders an empty table when there are no categories', async () => {
    mockGetCategoryExpenses.mockResolvedValueOnce(makeSummary([], 0))
    const wrapper = mount(HomePage)
    await flushPromises()
    expect(wrapper.findAll('tbody tr')).toHaveLength(0)
    expect(wrapper.text()).toContain('0')
  })

  it('renders the chart container', async () => {
    const wrapper = mount(HomePage)
    await flushPromises()
    // The chart section heading should be present
    expect(wrapper.text()).toContain('Spending Progression')
  })
})
