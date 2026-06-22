import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { RouterLinkStub } from '@vue/test-utils'
import App from '../App.vue'

describe('App', () => {
  it('renders NavBar', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
          RouterView: { template: '<div />' },
        },
      },
    })
    expect(wrapper.text()).toContain('Peanut Trail')
  })

  it('renders a RouterView slot for page content', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
          RouterView: { template: '<div data-testid="router-view" />' },
        },
      },
    })
    expect(wrapper.find('[data-testid="router-view"]').exists()).toBe(true)
  })
})
