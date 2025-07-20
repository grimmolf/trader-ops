import type { RouteRecordRaw } from 'vue-router'

// Lazy-loaded route components
const DashboardView = () => import('../views/DashboardView.vue')
const AccountsView = () => import('../views/AccountsView.vue')
const OrdersView = () => import('../views/OrdersView.vue')
const PositionsView = () => import('../views/PositionsView.vue')
const BacktestView = () => import('../views/BacktestView.vue')
const SettingsView = () => import('../views/SettingsView.vue')

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: {
      title: 'Trading Dashboard',
      requiresAuth: false // For now, no auth required
    }
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: AccountsView,
    meta: {
      title: 'Account Management',
      requiresAuth: false
    }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: OrdersView,
    meta: {
      title: 'Order Management',
      requiresAuth: false
    }
  },
  {
    path: '/positions',
    name: 'Positions',
    component: PositionsView,
    meta: {
      title: 'Position Management',
      requiresAuth: false
    }
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: BacktestView,
    meta: {
      title: 'Strategy Backtesting',
      requiresAuth: false
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: {
      title: 'Settings',
      requiresAuth: false
    }
  },
  {
    // Catch-all route for 404s
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue'),
    meta: {
      title: 'Page Not Found'
    }
  }
]

// Router navigation guards would go here
export function setupRouterGuards(router: any) {
  router.beforeEach((to: any, from: any, next: any) => {
    // Set page title
    document.title = to.meta?.title 
      ? `${to.meta.title} - TraderTerminal` 
      : 'TraderTerminal'
    
    // Auth guard (placeholder for future implementation)
    if (to.meta?.requiresAuth) {
      // Check authentication status
      // For now, just continue
    }
    
    next()
  })
  
  router.afterEach((to: any, from: any) => {
    // Analytics or logging could go here
    console.log(`Navigated from ${from.name} to ${to.name}`)
  })
}