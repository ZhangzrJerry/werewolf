import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: Home
        },
        {
            path: '/game/:gameId',
            name: 'game-detail',
            component: () => import('../views/GameDetail.vue')
        },
        {
            path: '/learning-chain/:role',
            name: 'learning-chain',
            component: () => import('../views/LearningChain.vue')
        },
        {
            path: '/doc',
            name: 'documentation',
            beforeEnter() {
                window.location.href = `${import.meta.env.BASE_URL}doc.html`
            }
        }
    ]
})

export default router