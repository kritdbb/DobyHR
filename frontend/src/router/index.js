import { createRouter, createWebHistory } from 'vue-router'

const routes = [
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
    // Admin Routes
    {
        path: '/admin',
        name: 'AdminDashboard',
        component: () => import('../views/admin/AdminDashboard.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/company',
        name: 'Company',
        component: () => import('../views/CompanySettings.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/users',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/users/create',
        name: 'CreateUser',
        component: () => import('../views/UserForm.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/users/:id/edit',
        name: 'EditUser',
        component: () => import('../views/UserForm.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/approval',
        name: 'Approval',
        component: () => import('../views/ApprovalBuilder.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/approval-patterns',
        name: 'ApprovalPatterns',
        component: () => import('../views/ApprovalPatterns.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/rewards',
        name: 'Rewards',
        component: () => import('../views/admin/Rewards.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/verify-redemption',
        name: 'VerifyRedemption',
        component: () => import('../views/admin/RedeemVerify.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/reports',
        name: 'Reports',
        component: () => import('../views/admin/Reports.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/badges',
        name: 'Badges',
        component: () => import('../views/admin/BadgeManagement.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    {
        path: '/badge-quests',
        name: 'BadgeQuests',
        component: () => import('../views/admin/BadgeQuests.vue'),
        meta: { requiresAuth: true, role: 'admin' }
    },
    // Staff Routes
    {
        path: '/staff',
        component: () => import('../layouts/StaffLayout.vue'),
        meta: { requiresAuth: true },
        children: [
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
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    const user = userStr ? JSON.parse(userStr) : {}

    if (to.meta.requiresAuth) {
        if (!token) {
            next({ name: 'Login', query: { redirect: to.fullPath } })
        } else {
            // Role check
            if (to.meta.role && to.meta.role !== user.role) {
                // Allow admin to visit staff pages
                if (to.path.startsWith('/staff') && user.role === 'admin') {
                    next()
                    return
                }
                // Staff trying to access admin pages → go to staff home
                if (user.role === 'staff') {
                    next('/staff/home')
                    return
                }
                // Admin trying to access unknown role pages → go to admin
                if (user.role === 'admin') {
                    next('/admin')
                    return
                }
                next({ name: 'Login' })
            } else {
                if (to.path === '/' && user.role === 'staff') {
                    next('/staff/home')
                    return
                }
                if (to.path === '/' && user.role === 'admin') {
                    next('/admin')
                    return
                }
                next()
            }
        }
    } else {
        // If logged in and trying to access login, redirect
        if (to.path === '/login' && token) {
            if (user.role === 'admin') next('/company')
            else next('/staff/home')
            return
        }
        next()
    }
})

export default router
