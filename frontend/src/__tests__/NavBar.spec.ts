import {describe, expect, it} from 'vitest'
import {mount, RouterLinkStub} from '@vue/test-utils'
import NavBar from '@/components/common/NavBar.vue'

function mountNavBar() {
    return mount(NavBar, {
        global: {
            stubs: {RouterLink: RouterLinkStub},
        },
    })
}

describe('NavBar', () => {
    it('renders the app title', () => {
        const wrapper = mountNavBar()
        expect(wrapper.text()).toContain('Peanut Trail')
    })

    it('has a Dashboard nav link pointing to /', () => {
        const wrapper = mountNavBar()
        const links = wrapper.findAllComponents(RouterLinkStub)
        const dashboard = links.find((l) => l.text() === 'Dashboard')
        expect(dashboard).toBeDefined()
        expect(dashboard!.props('to')).toBe('/')
    })

    it('has a Transactions nav link pointing to /transactions', () => {
        const wrapper = mountNavBar()
        const links = wrapper.findAllComponents(RouterLinkStub)
        const transactions = links.find((l) => l.text() === 'Transactions')
        expect(transactions).toBeDefined()
        expect(transactions!.props('to')).toBe('/transactions')
    })

    it('has an Upload nav link pointing to /upload', () => {
        const wrapper = mountNavBar()
        const links = wrapper.findAllComponents(RouterLinkStub)
        const upload = links.find((l) => l.text() === 'Upload')
        expect(upload).toBeDefined()
        expect(upload!.props('to')).toBe('/upload')
    })

    it('has a logo link pointing to /', () => {
        const wrapper = mountNavBar()
        const links = wrapper.findAllComponents(RouterLinkStub)
        const logoLink = links.find((l) => l.props('to') === '/' && l.find('img').exists())
        expect(logoLink).toBeDefined()
    })
})
