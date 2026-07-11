import { afterEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchableSelect from '@/components/common/SearchableSelect.vue'

function mountSelect(props = {}) {
  return mount(SearchableSelect, {
    attachTo: document.body,
    props: { modelValue: '', options: ['Food', 'Transport', 'Utilities'], ...props },
  })
}

afterEach(() => document.body.replaceChildren())

describe('SearchableSelect', () => {
  it('opens with all options when focused', async () => {
    const wrapper = mountSelect()
    await wrapper.find('input').trigger('focus')
    expect(wrapper.text()).toContain('Food')
    expect(wrapper.text()).toContain('Transport')
  })

  it('filters options case-insensitively', async () => {
    const wrapper = mountSelect()
    const input = wrapper.find('input')
    await input.trigger('focus')
    await input.setValue('TRAN')
    expect(wrapper.text()).toContain('Transport')
    expect(wrapper.text()).not.toContain('Utilities')
  })

  it('emits and closes after selecting an option', async () => {
    const wrapper = mountSelect()
    await wrapper.find('input').trigger('focus')
    await wrapper.get('[title="Food"]').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['Food']])
    expect(wrapper.text()).not.toContain('Transport')
  })

  it('offers creation when no option matches', async () => {
    const wrapper = mountSelect()
    const input = wrapper.find('input')
    await input.trigger('focus')
    await input.setValue('Health')
    await wrapper.get('div.text-orange-600').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['Health']])
  })

  it('clears an optional selection', async () => {
    const wrapper = mountSelect({ modelValue: 'Food', allowEmpty: true, placeholder: 'All Categories' })
    await wrapper.find('input').trigger('focus')
    await wrapper.get('div.border-b').trigger('click')
    expect(wrapper.emitted('update:modelValue')).toEqual([['']])
  })

  it('closes and restores the selected value after an outside click', async () => {
    const wrapper = mountSelect({ modelValue: 'Food' })
    const input = wrapper.find('input')
    await input.trigger('focus')
    await input.setValue('other')
    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await wrapper.vm.$nextTick()
    expect((input.element as HTMLInputElement).value).toBe('Food')
    expect(wrapper.text()).not.toContain('Transport')
  })
})
