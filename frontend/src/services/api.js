import axios from 'axios'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    headers: {
        'Content-Type': 'application/json',
    },
    paramsSerializer: {
        indexes: null,  // Sends array as user_ids=1&user_ids=2 (FastAPI compatible)
    },
})

// Add a request interceptor to include the auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Redirect to login on 401 (expired token) + detailed error logging
api.interceptors.response.use(
    (response) => {
        // Log successful requests in dev mode
        if (import.meta.env.DEV) {
            console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} → ${response.status}`)
        }
        return response
    },
    (error) => {
        const method = error.config?.method?.toUpperCase() || '???'
        const url = error.config?.url || '???'
        const status = error.response?.status || 'NETWORK_ERROR'
        const detail = error.response?.data?.detail || error.message

        // Always log API errors clearly
        console.error(`❌ API ERROR: ${method} ${url} → ${status}`)
        console.error(`   Detail: ${typeof detail === 'object' ? JSON.stringify(detail) : detail}`)
        if (error.config?.data) {
            try {
                const body = typeof error.config.data === 'string' ? error.config.data : JSON.stringify(error.config.data)
                console.error(`   Request body: ${body}`)
            } catch (_) { }
        }

        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            if (window.location.pathname !== '/login') {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export const login = (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    return api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
}

export const ssoLogin = (credential) => api.post('/auth/sso', { credential })
export const getGoogleClientId = () => api.get('/auth/google-client-id')

// === Company ===
export const getCompany = () => api.get('/api/company/')
export const updateCompany = (data) => api.put('/api/company/', data)
export const uploadCompanyLogo = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/company/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
}

// === Users ===
export const getUsers = (params) => api.get('/api/users/', { params })
export const getUser = (id) => api.get(`/api/users/${id}`)
export const createUser = (data) => api.post('/api/users/', data)
export const updateUser = (id, data) => api.put(`/api/users/${id}`, data)
export const deleteUser = (id) => api.delete(`/api/users/${id}`)
export const uploadUserImage = (id, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/users/${id}/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
}
export const getDepartments = () => api.get('/api/users/departments/list')
export const getUserAttendance = (id) => api.get(`/api/users/${id}/attendance`)
export const getUserLeaves = (id) => api.get(`/api/users/${id}/leaves`)
export const getUserRedemptions = (id) => api.get(`/api/users/${id}/redemptions`)

// === Approval Flows ===
export const getApprovalFlows = () => api.get('/api/approval-flows/')
export const getApprovalFlow = (id) => api.get(`/api/approval-flows/${id}`)
export const getApprovalFlowByUser = (userId) => api.get(`/api/approval-flows/user/${userId}`)
export const createApprovalFlow = (data) => api.post('/api/approval-flows/', data)
export const updateApprovalFlow = (id, data) => api.put(`/api/approval-flows/${id}`, data)
export const deleteApprovalFlow = (id) => api.delete(`/api/approval-flows/${id}`)
export const createFlowFromPattern = (targetUserId, patternId) =>
    api.post(`/api/approval-flows/from-pattern?target_user_id=${targetUserId}&pattern_id=${patternId}`)

// === Approval Patterns ===
export const getApprovalPatterns = () => api.get('/api/approval-patterns/')
export const getApprovalPattern = (id) => api.get(`/api/approval-patterns/${id}`)
export const createApprovalPattern = (data) => api.post('/api/approval-patterns/', data)
export const updateApprovalPattern = (id, data) => api.put(`/api/approval-patterns/${id}`, data)
export const deleteApprovalPattern = (id) => api.delete(`/api/approval-patterns/${id}`)

// --- Leaves ---
export const requestLeave = (data) => api.post('/api/leaves/request', data)
export const getMyLeaves = () => api.get('/api/leaves/my-leaves')
export const getLeaveQuota = () => api.get('/api/leaves/quota')
export const getAllLeaves = (params) => api.get('/api/leaves/all', { params })
export const approveLeave = (id) => api.put(`/api/leaves/${id}/approve`)
export const rejectLeave = (id) => api.put(`/api/leaves/${id}/reject`)
export const getPendingLeaveApprovals = () => api.get('/api/leaves/pending-approvals')

// --- Admin Tools ---
export const processAbsentPenalties = (date) => api.post('/api/admin/process-absent-penalties', null, { params: date ? { target_date: date } : {} })

// --- Attendance ---
export const checkIn = (lat, lon) => api.post('/api/attendance/check-in', { latitude: lat, longitude: lon })
export const getMyAttendance = () => api.get('/api/attendance/my-history')
export const getTodayCheckInStatus = () => api.get('/api/attendance/today-status')

// --- Rewards (Admin) ---
export const getRewards = () => api.get('/api/rewards/')
export const createReward = (data) => api.post('/api/rewards/', data)
export const updateReward = (id, data) => api.put(`/api/rewards/${id}`, data)
export const deleteReward = (id) => api.delete(`/api/rewards/${id}`)
export const getAllRedemptions = (params) => api.get('/api/rewards/redemptions/all', { params })

// --- Redemption (Staff) ---
export const redeemReward = (data) => api.post('/api/rewards/redeem', data)
export const getMyRedemptions = () => api.get('/api/rewards/my-redemptions')
export const getPendingRedemptionApprovals = () => api.get('/api/rewards/pending-approvals')
export const rejectRedemption = (id) => api.post(`/api/rewards/${id}/reject`)

// --- Verification (HR/Admin) ---
export const verifyRedemption = (uuid) => api.get(`/api/rewards/verify/${uuid}`)
export const approveRedemption = (id) => api.post(`/api/rewards/${id}/approve`)
export const handoverRedemption = (uuid) => api.post(`/api/rewards/verify/${uuid}/handover`)
export const confirmRedemption = (id) => api.post(`/api/rewards/${id}/approve`)

// --- Reward Image Upload ---
export const uploadRewardImage = (rewardId, formData) => api.post(`/api/rewards/${rewardId}/upload-image`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })

// --- Coin Management (Admin) ---
export const adjustUserCoins = (userId, data) => api.post(`/api/users/${userId}/coins`, data)
export const getUserCoinLogs = (userId) => api.get(`/api/users/${userId}/coin-logs`)

// --- Angel Coins ---
export const grantAngelCoins = (userId, data) => api.post(`/api/users/${userId}/angel-coins`, data)
export const sendAngelCoins = (data) => api.post('/api/users/angel-coins/send', data)
export const getStaffList = () => api.get('/api/users/staff/list')

// --- Reports (Admin) ---
export const getAttendanceReport = (params) => api.get('/api/reports/attendance', { params })
export const getCoinReport = (params) => api.get('/api/reports/coins', { params })
export const getLeaveSummary = () => api.get('/api/reports/leaves')

// --- Work Requests ---
export const getPendingWorkRequests = () => api.get('/api/work-requests/pending-approvals')
export const approveWorkRequest = (id) => api.put(`/api/work-requests/${id}/approve`)
export const rejectWorkRequest = (id) => api.put(`/api/work-requests/${id}/reject`)

// --- Angel Coin Logs ---
export const getUserAngelCoinLogs = (userId) => api.get(`/api/users/${userId}/angel-coin-logs`)

// --- Badges ---
export const getBadges = () => api.get('/api/badges')
export const createBadge = (formData) => api.post('/api/badges', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const deleteBadge = (id) => api.delete(`/api/badges/${id}`)
export const awardBadge = (badgeId, userIds) => api.post(`/api/badges/${badgeId}/award`, { user_ids: userIds })
export const revokeBadge = (badgeId, userId) => api.delete(`/api/badges/${badgeId}/revoke/${userId}`)
export const getBadgeHolders = (badgeId) => api.get(`/api/badges/${badgeId}/holders`)
export const getMyBadges = () => api.get('/api/badges/user/me')
export const getUserBadges = (userId) => api.get(`/api/badges/user/${userId}`)
export const getMyStats = () => api.get('/api/badges/stats/me')
export const getUserStats = (userId) => api.get(`/api/badges/stats/${userId}`)
export const getRecentBadgeAwards = (limit = 50) => api.get(`/api/badges/awards/recent?limit=${limit}`)
export const getTownPeople = () => api.get('/api/badges/town-people')
export const buyMagicItem = (itemType, params = {}) => api.post(`/api/badges/magic-shop/buy?item_type=${itemType}${params.status_text ? '&status_text=' + encodeURIComponent(params.status_text) : ''}`)

export default api
