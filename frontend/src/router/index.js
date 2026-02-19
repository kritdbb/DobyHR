import { createRouter, createWebHistory } from 'vue-router'

const ADMIN_ROLES = ['god', 'gm']

const routes = [
    {
        path: '/',
        redirect: '/login'
    },
    {
        path: '/oauth/callback',
        name: 'OAuthCallback',
        component: () => import('../views/OAuthCallback.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/sso',
        name: 'SSO',
        component: () => import('../views/Login.vue'),
        meta: { layout: 'empty' }
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        meta: { layout: 'empty' }
    },
    // Admin Routes (God + GM)
    {
        path: '/admin',
        name: 'AdminDashboard',
        component: () => import('../views/admin/AdminDashboard.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/battle-arena',
        name: 'BattleArena',
        component: () => import('../views/admin/BattleArena.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/artifact-shop',
        name: 'ArtifactShop',
        component: () => import('../views/admin/ArtifactShop.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/company',
        name: 'Company',
        component: () => import('../views/CompanySettings.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/users',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/users/create',
        name: 'CreateUser',
        component: () => import('../views/UserForm.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/users/:id/edit',
        name: 'EditUser',
        component: () => import('../views/UserForm.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/approval',
        name: 'Approval',
        component: () => import('../views/ApprovalBuilder.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/approval-patterns',
        name: 'ApprovalPatterns',
        component: () => import('../views/ApprovalPatterns.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/rewards',
        name: 'Rewards',
        component: () => import('../views/admin/Rewards.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/verify-redemption',
        name: 'VerifyRedemption',
        component: () => import('../views/admin/RedeemVerify.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/reports',
        name: 'Reports',
        component: () => import('../views/admin/Reports.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/badges',
        name: 'Badges',
        component: () => import('../views/admin/BadgeManagement.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/badge-quests',
        name: 'BadgeQuests',
        component: () => import('../views/admin/BadgeQuests.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/badge-shop-admin',
        name: 'BadgeShopAdmin',
        component: () => import('../views/admin/BadgeShopAdmin.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    {
        path: '/fortune-wheel',
        name: 'FortuneWheel',
        component: () => import('../views/admin/FortuneWheel.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    // Staff (Player) Routes
    {
        path: '/staff',
        component: () => import('../layouts/StaffLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: '',
                redirect: '/staff/home'
            },
            {
                path: 'home',
                component: () => import('../views/staff/StaffHome.vue')
            },
            {
                path: 'check-in',
                component: () => import('../views/staff/CheckIn.vue')
            },
            {
                path: 'services',
                component: () => import('../views/staff/StaffServices.vue')
            },
            {
                path: 'leave',
                component: () => import('../views/staff/LeaveRequest.vue')
            },
            {
                path: 'redeem',
                component: () => import('../views/staff/RedeemPoints.vue')
            },
            {
                path: 'approvals',
                component: () => import('../views/staff/StaffApprovals.vue')
            },
            {
                path: 'coupons',
                component: () => import('../views/staff/StaffCoupons.vue')
            },
            {
                path: 'profile',
                component: () => import('../views/staff/MyProfile.vue')
            },
            {
                path: 'town-people',
                component: () => import('../views/staff/TownPeople.vue')
            },
            {
                path: 'magic-shop',
                component: () => import('../views/staff/MagicShop.vue')
            },
            {
                path: 'fitbit',
                component: () => import('../views/staff/FitbitSteps.vue')
            },
            {
                path: 'expense',
                component: () => import('../views/staff/StaffExpenseRequest.vue')
            },
            {
                path: 'revival-records',
                component: () => import('../views/staff/RevivalRecords.vue')
            },
            {
                path: 'man-of-the-month',
                component: () => import('../views/staff/ManOfTheMonth.vue')
            },
            {
                path: 'arena/:id',
                component: () => import('../views/staff/ArenaBattle.vue')
            },
            {
                path: 'badge-shop',
                component: () => import('../views/staff/BadgeShop.vue')
            },
        ]
    },
    {
        path: '/expense-management',
        name: 'ExpenseManagement',
        component: () => import('../views/admin/ExpenseManagement.vue'),
        meta: { requiresAuth: true, role: 'gm' }
    },
    // Catch-all: redirect unknown paths to login
    {
        path: '/:pathMatch(.*)*',
        redirect: '/login'
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// Token validation — checks if stored token is still valid after server restart
let tokenValidated = false
async function validateToken() {
    if (tokenValidated) return true
    const token = localStorage.getItem('token')
    if (!token) return false
    try {
        const res = await fetch((import.meta.env.VITE_API_URL || '') + '/api/attendance/today-status', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            return false
        }
        tokenValidated = true
        return true
    } catch {
        // Network error — assume token is valid (offline mode)
        return true
    }
}

router.beforeEach(async (to, from, next) => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    const user = userStr ? JSON.parse(userStr) : {}

    // If route requires auth
    if (to.meta.requiresAuth) {
        if (!token) {
            next({ name: 'Login', query: { redirect: to.fullPath } })
            return
        }

        // Validate token on first navigation (catches stale tokens after server restart)
        const valid = await validateToken()
        if (!valid) {
            next({ name: 'Login', query: { redirect: to.fullPath } })
            return
        }

        // Role check
        if (to.meta.role) {
            if (ADMIN_ROLES.includes(user.role)) {
                next()
                return
            }
            next('/staff/home')
            return
        }

        // Staff pages — allow all authenticated users
        if (to.path.startsWith('/staff')) {
            next()
            return
        }

        // Root redirect
        if (to.path === '/') {
            if (ADMIN_ROLES.includes(user.role)) {
                next('/admin')
            } else {
                next('/staff/home')
            }
            return
        }

        next()
    } else {
        // If logged in and trying to access login, redirect to appropriate home
        if ((to.path === '/login' || to.path === '/') && token) {
            const valid = await validateToken()
            if (valid) {
                if (ADMIN_ROLES.includes(user.role)) next('/admin')
                else next('/staff/home')
                return
            }
        }
        next()
    }
})

export default router
