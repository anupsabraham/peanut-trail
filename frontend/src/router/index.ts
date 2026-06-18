import {createRouter, createWebHistory} from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import TransactionsPage from '@/pages/TransactionsPage.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {path: '/', component: HomePage, meta: {title: "Dashboard"}},
        {path: '/transactions', component: TransactionsPage, meta: {title: "Transactions"}},
    ],
})

router.beforeEach((to) => {
    document.title = to.meta.title ? `${to.meta.title} - Peanut Trail` : 'Peanut Trail'
})

export default router
