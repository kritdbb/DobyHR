<template>
  <div>
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2>📜 Guild Chronicles</h2>
        <p>View kingdom records and logs</p>
      </div>
      <button class="btn btn-secondary" @click="exportCSV">⬇️ Export Scroll</button>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button :class="['tab', activeTab === 'attendance' ? 'active' : '']" @click="activeTab = 'attendance'">
            ⚔️ Attendance
        </button>
        <button :class="['tab', activeTab === 'coins' ? 'active' : '']" @click="activeTab = 'coins'">
            💰 Gold Movement
        </button>
        <button :class="['tab', activeTab === 'leaves' ? 'active' : '']" @click="activeTab = 'leaves'">
            🏨 Leave Summary
        </button>
        <button :class="['tab', activeTab === 'pending' ? 'active' : '']" @click="activeTab = 'pending'">
            📋 Pending Rests
        </button>
        <button :class="['tab', activeTab === 'expenses' ? 'active' : '']" @click="activeTab = 'expenses'">
            💰 Expenses
        </button>
        <button :class="['tab', activeTab === 'mana' ? 'active' : '']" @click="activeTab = 'mana'">
            ✨ Mana Gifts
        </button>
    </div>

    <!-- Filters -->
    <div class="card" v-if="activeTab !== 'leaves'" style="margin-bottom: 20px; padding: 16px; overflow: visible; position: relative; z-index: 10;">
        <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
            <div class="form-group" style="margin-bottom: 0;">
                <label>Start Date</label>
                <input v-model="filters.start_date" type="date" class="form-input" />
            </div>
             <div class="form-group" style="margin-bottom: 0;">
                <label>End Date</label>
                <input v-model="filters.end_date" type="date" class="form-input" />
            </div>
             <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 200px; position: relative;">
                <label>Adventurers</label>
                <div class="multi-select-input" @click="showUserDropdown = !showUserDropdown">
                    <div v-if="filters.user_ids.length === 0" class="placeholder">All Members</div>
                    <div v-else class="selected-chips">
                        <span v-for="uid in filters.user_ids" :key="uid" class="chip">
                            {{ getUserName(uid) }}
                            <span class="chip-x" @click.stop="removeUser(uid)">×</span>
                        </span>
                    </div>
                    <span class="dropdown-arrow">▾</span>
                </div>
                <div v-if="showUserDropdown" class="dropdown-list">
                    <input v-model="userSearch" class="dropdown-search" placeholder="🔍 Search..." @click.stop />
                    <div v-for="u in filteredUserOptions" :key="u.id" 
                        class="dropdown-item" 
                        :class="{ selected: filters.user_ids.includes(u.id) }"
                        @click.stop="toggleUser(u.id)">
                        <span class="check">{{ filters.user_ids.includes(u.id) ? '☑' : '☐' }}</span>
                        {{ u.name }} {{ u.surname }}
                    </div>
                    <div v-if="filteredUserOptions.length === 0" style="padding: 8px 12px; color: #8b7355; font-size: 12px;">No members found</div>
                </div>
            </div>
            <button class="btn btn-primary" @click="loadData">Filter</button>
        </div>
    </div>

    <!-- Charts Section -->
    <div v-if="activeTab === 'attendance' && attendanceChartData" class="card" style="margin-bottom: 20px; height: 300px;">
        <LineChart :data="attendanceChartData" :options="chartOptions" />
    </div>
    <div v-if="activeTab === 'leaves' && leaveChartData" class="card" style="margin-bottom: 20px; height: 300px;">
        <PieChart :data="leaveChartData" :options="chartOptions" />
    </div>

    <!-- Attendance Table -->
    <div v-if="activeTab === 'attendance'" class="card">
        <h3>Attendance Log</h3>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date Time</th>
                        <th>Adventurer</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in attendanceData" :key="item.id">
                        <td>{{ formatDate(item.timestamp) }}</td>
                        <td>{{ item.user_name }}</td>
                        <td><span class="status-badge" :style="getStatusColor(item.status)">{{ item.status }}</span></td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span v-if="item.check_in_method === 'face'">📸 Face</span>
                                <span v-else>📍 GPS</span>
                                <img v-if="item.face_image_path" :src="apiBase + item.face_image_path"
                                     style="width: 32px; height: 32px; border-radius: 4px; object-fit: cover; border: 1px solid rgba(212,164,76,0.3);" />
                                <span v-if="item.face_confidence" style="font-size: 11px; color: #8b7355;">
                                    {{ (item.face_confidence * 100).toFixed(1) }}%
                                </span>
                            </div>
                        </td>
                    </tr>
                    <tr v-if="attendanceData.length === 0">
                        <td colspan="4" style="text-align: center; color: #8b7355;">No records found</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Coin Table -->
    <div v-if="activeTab === 'coins'" class="card">
        <h3>Gold Movement Log</h3>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date Time</th>
                        <th>Adventurer</th>
                        <th>Amount</th>
                        <th>Reason</th>
                        <th>By</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in coinData" :key="item.id">
                        <td>{{ formatDate(item.created_at) }}</td>
                        <td>{{ item.user_name }}</td>
                        <td :style="{ color: item.amount > 0 ? '#27ae60' : '#c0392b', fontWeight: 'bold' }">
                            {{ item.amount > 0 ? '+' : '' }}{{ item.amount }}
                        </td>
                        <td>{{ item.reason }}</td>
                        <td>{{ item.created_by || 'System' }}</td>
                    </tr>
                     <tr v-if="coinData.length === 0">
                        <td colspan="5" style="text-align: center; color: #8b7355;">No records found</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Leave Summary Table -->
    <div v-if="activeTab === 'leaves'" class="card">
         <h3>Annual Leave Summary</h3>
         <div v-if="loading" class="loading">Loading...</div>
         <div v-else class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Adventurer</th>
                        <th>Sick (Taken/Quota)</th>
                        <th>Business (Taken/Quota)</th>
                        <th>Vacation (Taken/Quota)</th>
                        <th>Pending Request</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in leaveData" :key="item.user_id">
                         <td><strong>{{ item.user_name }}</strong></td>
                         <td>{{ item.sick_taken }} / {{ item.sick_quota || '-' }}</td>
                         <td>{{ item.business_taken }} / {{ item.business_quota || '-' }}</td>
                         <td>{{ item.vacation_taken }} / {{ item.vacation_quota || '-' }}</td>
                         <td>
                            <span v-if="item.total_pending > 0" style="color: #d4a44c; font-weight: bold;">
                                {{ item.total_pending }} pending
                            </span>
                            <span v-else>-</span>
                         </td>
                    </tr>
                </tbody>
            </table>
         </div>
    </div>

    <!-- Pending Leaves Table -->
    <div v-if="activeTab === 'pending'" class="card">
         <h3>Pending Rest Requests</h3>
         <div v-if="loading" class="loading">Loading...</div>
         <div v-else class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Adventurer</th>
                        <th>Type</th>
                        <th>Start</th>
                        <th>End</th>
                        <th>Reason</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="item in pendingLeaves" :key="item.id">
                         <td>{{ getUserName(item.user_id) || `Adventurer #${item.user_id}` }}</td>
                         <td><span class="status-badge" style="background: rgba(212,164,76,0.1); color: #d4a44c; border: 1px solid rgba(212,164,76,0.2);">{{ item.leave_type }}</span></td>
                         <td>{{ item.start_date }}</td>
                         <td>{{ item.end_date }}</td>
                         <td>{{ item.reason }}</td>
                         <td style="display: flex; gap: 6px;">
                             <button class="btn btn-primary" style="font-size: 12px; padding: 4px 12px;" @click="handleApprove(item.id)">✅ Approve</button>
                             <button class="btn btn-secondary" style="font-size: 12px; padding: 4px 12px; background: #c0392b;" @click="handleReject(item.id)">❌ Reject</button>
                         </td>
                    </tr>
                    <tr v-if="pendingLeaves.length === 0">
                        <td colspan="6" style="text-align: center; color: #8b7355;">No pending requests 🎉</td>
                    </tr>
                </tbody>
            </table>
         </div>
    </div>

    <!-- Expense Report: Per-User Cards -->
    <template v-if="activeTab === 'expenses'">
      <div v-if="loading" class="loading">Loading...</div>
      <template v-else>
        <!-- Grand Total Banner -->
        <div v-if="expenseUserCards.length > 0" class="card" style="margin-bottom: 20px;">
          <h3>💰 Company Expense Summary</h3>
          <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 12px;">
            <div class="summary-box">
              <div class="summary-label">📄 General</div>
              <div class="summary-value" style="color: #3498db;">฿{{ expenseGrandTotal.general.toLocaleString() }}</div>
            </div>
            <div class="summary-box">
              <div class="summary-label">🚗 Travel</div>
              <div class="summary-value" style="color: #2ecc71;">฿{{ expenseGrandTotal.travel.toLocaleString() }}</div>
            </div>
            <div class="summary-box">
              <div class="summary-label">🏢 Center</div>
              <div class="summary-value" style="color: #9b59b6;">฿{{ expenseGrandTotal.center.toLocaleString() }}</div>
            </div>
            <div class="summary-box grand">
              <div class="summary-label">⚔️ Grand Total</div>
              <div class="summary-value">฿{{ expenseGrandTotal.all.toLocaleString() }}</div>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="expenseUserCards.length === 0" class="card" style="text-align: center; padding: 40px; color: #8b7355;">
          No expense records found
        </div>

        <!-- Per-user cards -->
        <div v-for="uc in expenseUserCards" :key="uc.user_id" class="expense-user-card">
          <div class="euc-header" @click="toggleExpUser(uc.user_id)">
            <div class="euc-user">
              <div class="euc-name">{{ uc.name }}</div>
              <div class="euc-count">{{ uc.items.length }} items</div>
            </div>
            <div class="euc-summary">
              <span v-if="uc.generalTotal > 0" class="euc-stat" style="color: #3498db;">📄 ฿{{ uc.generalTotal.toLocaleString() }}</span>
              <span v-if="uc.travelTotal > 0" class="euc-stat" style="color: #2ecc71;">🚗 ฿{{ uc.travelTotal.toLocaleString() }}</span>
              <span v-if="uc.centerTotal > 0" class="euc-stat" style="color: #9b59b6;">🏢 ฿{{ uc.centerTotal.toLocaleString() }}</span>
              <span class="euc-stat euc-total">💰 ฿{{ uc.total.toLocaleString() }}</span>
            </div>
            <span class="euc-chevron" :class="{ open: expandedExpUsers[uc.user_id] }">▾</span>
          </div>
          <div v-if="expandedExpUsers[uc.user_id]" class="euc-body">
            <table>
              <thead>
                <tr>
                  <th>Type</th><th>Date</th><th>Description</th><th>Amount</th><th>Status</th><th>Files</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="exp in uc.items" :key="exp.id">
                  <td>
                    <span class="status-badge" :style="exp.expense_type === 'GENERAL' ? 'background: rgba(52,152,219,0.1); color: #3498db; border: 1px solid rgba(52,152,219,0.2);' : exp.expense_type === 'CENTER' ? 'background: rgba(155,89,182,0.1); color: #9b59b6; border: 1px solid rgba(155,89,182,0.2);' : 'background: rgba(46,204,113,0.1); color: #2ecc71; border: 1px solid rgba(46,204,113,0.2);'">
                      {{ exp.expense_type === 'GENERAL' ? '📄' : exp.expense_type === 'CENTER' ? '🏢' : '🚗' }} {{ exp.expense_type }}
                    </span>
                  </td>
                  <td>{{ exp.expense_type === 'TRAVEL' ? exp.travel_date : exp.expense_date }}</td>
                  <td>{{ exp.description || (exp.expense_type === 'TRAVEL' ? `${exp.vehicle_type} ${exp.km_outbound}+${exp.km_return}km` : '-') }}</td>
                  <td style="font-weight: 700;">฿{{ getExpAmount(exp).toLocaleString() }}</td>
                  <td><span class="status-badge" :style="getExpenseStatusColor(exp.status)">{{ exp.status }}</span></td>
                  <td>
                    <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                      <div v-if="exp.file_path" class="report-thumb" @click="openViewer(exp.file_path)">
                        <img v-if="!isPdf(exp.file_path)" :src="apiBase + exp.file_path" />
                        <span v-else class="pdf-mini">PDF</span>
                      </div>
                      <div v-if="exp.outbound_image" class="report-thumb" @click="openViewer(exp.outbound_image)"><img :src="apiBase + exp.outbound_image" /></div>
                      <div v-if="exp.return_image" class="report-thumb" @click="openViewer(exp.return_image)"><img :src="apiBase + exp.return_image" /></div>
                      <div v-for="att in exp.attachments" :key="att.id" class="report-thumb" @click="openViewer(att.file_path)"><img :src="apiBase + att.file_path" /></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </template>

    <!-- Mana Gift Report -->
    <div v-if="activeTab === 'mana' && manaReport.summary.length > 0" class="card" style="margin-bottom: 20px;">
        <h3>✨ Mana Gift Summary</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Adventurer</th>
                        <th>Sent</th>
                        <th>Received</th>
                        <th># Sent</th>
                        <th># Received</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="s in manaReport.summary" :key="s.user_id">
                        <td>{{ s.user_name }}</td>
                        <td style="color: #e74c3c; font-weight: 700;">{{ s.total_sent }}</td>
                        <td style="color: #2ecc71; font-weight: 700;">{{ s.total_received }}</td>
                        <td>{{ s.send_count }}</td>
                        <td>{{ s.receive_count }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div v-if="activeTab === 'mana'" class="card">
        <h3>Mana Gift Transactions</h3>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Amount</th>
                        <th>As</th>
                        <th>Comment</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(t, i) in manaReport.transactions" :key="i">
                        <td>{{ formatDate(t.timestamp) }}</td>
                        <td>{{ t.sender_name }}</td>
                        <td>{{ t.recipient_name }}</td>
                        <td style="font-weight: 700;">{{ t.amount }}</td>
                        <td><span class="status-badge" :style="t.delivery_type === 'gold' ? 'background: rgba(212,164,76,0.1); color: #d4a44c; border: 1px solid rgba(212,164,76,0.2);' : 'background: rgba(155,89,182,0.1); color: #9b59b6; border: 1px solid rgba(155,89,182,0.2);'">{{ t.delivery_type === 'gold' ? '💰 Gold' : '✨ Mana' }}</span></td>
                        <td>{{ t.comment || '-' }}</td>
                    </tr>
                    <tr v-if="manaReport.transactions.length === 0">
                        <td colspan="6" style="text-align: center; color: #8b7355;">No mana gifts found</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Fullscreen Viewer -->
    <div v-if="viewerOpen" class="viewer-overlay" @click="viewerOpen = false">
      <button class="viewer-close" @click="viewerOpen = false">✕</button>
      <div class="viewer-content" @click.stop>
        <img v-if="!isPdf(viewerSrc)" :src="apiBase + viewerSrc" class="viewer-img" />
        <iframe v-else :src="apiBase + viewerSrc" class="viewer-pdf"></iframe>
      </div>
    </div>
  </div>
</template>

<script>
import { getAttendanceReport, getCoinReport, getLeaveSummary, getAllLeaves, approveLeave, rejectLeave, getUsers, getExpenseReport, getManaGiftReport } from '../../services/api'

export default {
    inject: ['showToast'],
    data() {
        return {
            activeTab: 'attendance',
            filters: {
                start_date: '',
                end_date: '',
                user_ids: []
            },
            allUsers: [],
            showUserDropdown: false,
            userSearch: '',
            attendanceData: [],
            coinData: [],
            leaveData: [],
            pendingLeaves: [],
            expenseData: [],
            manaReport: { summary: [], transactions: [] },
            expandedExpUsers: {},
            loading: false,
            attendanceChartData: null,
            leaveChartData: null,
            chartOptions: {
                responsive: true,
                maintainAspectRatio: false
            },
            viewerOpen: false,
            viewerSrc: '',
            apiBase: import.meta.env.VITE_API_URL || ''
        }
    },
    watch: {
        activeTab() {
            this.loadData()
        }
    },
    async mounted() {
        const end = new Date()
        const start = new Date()
        start.setDate(start.getDate() - 7)
        this.filters.start_date = start.toISOString().split('T')[0]
        this.filters.end_date = end.toISOString().split('T')[0]
        
        await this.loadUserList()
        this.loadData()
        document.addEventListener('click', this.closeDropdown)
    },
    beforeUnmount() {
        document.removeEventListener('click', this.closeDropdown)
    },
    computed: {
        filteredUserOptions() {
            if (!this.userSearch) return this.allUsers
            const q = this.userSearch.toLowerCase()
            return this.allUsers.filter(u => 
                `${u.name} ${u.surname}`.toLowerCase().includes(q)
            )
        },
        expenseSummary() {
            let general = 0, travel = 0, center = 0, generalCount = 0, travelCount = 0, centerCount = 0
            this.expenseData.forEach(e => {
                if (e.status === 'REJECTED') return
                if (e.expense_type === 'GENERAL') {
                    general += (e.amount || 0)
                    generalCount++
                } else if (e.expense_type === 'CENTER') {
                    center += (e.amount || 0)
                    centerCount++
                } else {
                    travel += (e.total_amount || 0)
                    travelCount++
                }
            })
            return { general, travel, center, total: general + travel + center, generalCount, travelCount, centerCount }
        },
        expenseUserCards() {
            // Filter out rejected, group by user
            const nonRejected = this.expenseData.filter(e => e.status !== 'REJECTED')
            const groups = {}
            for (const exp of nonRejected) {
                const key = exp.user_id
                if (!groups[key]) {
                    groups[key] = {
                        user_id: exp.user_id,
                        name: exp.user_name,
                        items: [],
                        generalTotal: 0,
                        travelTotal: 0,
                        centerTotal: 0,
                        total: 0,

                    }
                }
                groups[key].items.push(exp)
                const amt = this.getExpAmount(exp)
                if (exp.expense_type === 'GENERAL') groups[key].generalTotal += amt
                else if (exp.expense_type === 'TRAVEL') groups[key].travelTotal += amt
                else if (exp.expense_type === 'CENTER') groups[key].centerTotal += amt
                groups[key].total += amt
            }
            return Object.values(groups).sort((a, b) => b.total - a.total)
        },
        expenseGrandTotal() {
            const cards = this.expenseUserCards
            return {
                general: cards.reduce((s, u) => s + u.generalTotal, 0),
                travel: cards.reduce((s, u) => s + u.travelTotal, 0),
                center: cards.reduce((s, u) => s + u.centerTotal, 0),
                all: cards.reduce((s, u) => s + u.total, 0),
            }
        }
    },
    methods: {
        async loadUserList() {
            try {
                const { data } = await getUsers()
                this.allUsers = data
            } catch (e) { console.error('Failed to load users', e) }
        },
        toggleUser(id) {
            const idx = this.filters.user_ids.indexOf(id)
            if (idx >= 0) this.filters.user_ids.splice(idx, 1)
            else this.filters.user_ids.push(id)
        },
        removeUser(id) {
            this.filters.user_ids = this.filters.user_ids.filter(x => x !== id)
        },
        getUserName(id) {
            const u = this.allUsers.find(x => x.id === id)
            return u ? `${u.name} ${u.surname}` : `#${id}`
        },
        closeDropdown(e) {
            if (!e.target.closest('.form-group')) this.showUserDropdown = false
        },
        async loadData() {
            this.loading = true
            this.attendanceChartData = null
            this.leaveChartData = null
            this.showUserDropdown = false
            
            try {
                if (this.activeTab === 'attendance') {
                    const params = {}
                    if (this.filters.start_date) params.start_date = this.filters.start_date
                    if (this.filters.end_date) params.end_date = this.filters.end_date
                    if (this.filters.user_ids.length > 0) params.user_ids = this.filters.user_ids
                    
                    const { data } = await getAttendanceReport(params)
                    this.attendanceData = data
                    this.prepareAttendanceChart()
                }
                else if (this.activeTab === 'coins') {
                    const params = {}
                    if (this.filters.start_date) params.start_date = this.filters.start_date
                    if (this.filters.end_date) params.end_date = this.filters.end_date
                    if (this.filters.user_ids.length > 0) params.user_ids = this.filters.user_ids
                    
                    const { data } = await getCoinReport(params)
                    this.coinData = data
                }
                else if (this.activeTab === 'leaves') {
                    const { data } = await getLeaveSummary()
                    this.leaveData = data
                    this.prepareLeaveChart()
                }
                else if (this.activeTab === 'pending') {
                    const { data } = await getAllLeaves({ status: 'pending' })
                    this.pendingLeaves = data
                }
                else if (this.activeTab === 'expenses') {
                    const params = {}
                    if (this.filters.start_date) params.start_date = this.filters.start_date
                    if (this.filters.end_date) params.end_date = this.filters.end_date
                    if (this.filters.user_ids.length > 0) params.user_ids = this.filters.user_ids
                    const { data } = await getExpenseReport(params)
                    this.expenseData = data
                }
                else if (this.activeTab === 'mana') {
                    const params = {}
                    if (this.filters.start_date) params.start_date = this.filters.start_date
                    if (this.filters.end_date) params.end_date = this.filters.end_date
                    const { data } = await getManaGiftReport(params)
                    this.manaReport = data
                }
                
            } catch (e) {
                console.error("Report load failed", e)
                this.showToast("Failed to load report", "error")
            } finally {
                this.loading = false
            }
        },
        prepareAttendanceChart() {
            const grouped = {}
            this.attendanceData.forEach(item => {
                const date = item.timestamp.split('T')[0]
                grouped[date] = (grouped[date] || 0) + 1
            })
            
            const labels = Object.keys(grouped).sort()
            const data = labels.map(date => grouped[date])
            
            this.attendanceChartData = {
                labels,
                datasets: [{
                    label: 'Daily Check-ins',
                    backgroundColor: '#2980b9',
                    borderColor: '#2980b9',
                    data,
                    tension: 0.2
                }]
            }
        },
        prepareLeaveChart() {
            let sick = 0, business = 0, vacation = 0
            this.leaveData.forEach(u => {
                sick += u.sick_taken
                business += u.business_taken
                vacation += u.vacation_taken
            })
            
            this.leaveChartData = {
                labels: ['Sick', 'Business', 'Vacation'],
                datasets: [{
                    backgroundColor: ['#c0392b', '#d4a44c', '#2980b9'],
                    data: [sick, business, vacation]
                }]
            }
        },
        exportCSV() {
            let data = []
            let filename = `guild-chronicle-${this.activeTab}-${new Date().toISOString().split('T')[0]}.csv`
            
            if (this.activeTab === 'attendance') {
                data = this.attendanceData.map(r => ({
                    Date: r.timestamp,
                    User: r.user_name,
                    Status: r.status
                }))
            } else if (this.activeTab === 'coins') {
                data = this.coinData.map(r => ({
                    Date: r.created_at,
                    User: r.user_name,
                    Amount: r.amount,
                    Reason: r.reason,
                    By: r.created_by
                }))
            } else {
                data = this.leaveData.map(u => ({
                    User: u.user_name,
                    SickTaken: u.sick_taken,
                    SickQuota: u.sick_quota,
                    BusinessTaken: u.business_taken,
                    BusinessQuota: u.business_quota,
                    VacationTaken: u.vacation_taken,
                    VacationQuota: u.vacation_quota,
                    Pending: u.total_pending
                }))
            }
            
            if (data.length === 0) {
                this.showToast("No data to export", "warning")
                return
            }
            
            const headers = Object.keys(data[0]).join(',')
            const rows = data.map(row => Object.values(row).map(v => `"${v}"`).join(',')).join('\n')
            const csvContent = "data:text/csv;charset=utf-8," + headers + '\n' + rows
            
            const encodedUri = encodeURI(csvContent)
            const link = document.createElement("a")
            link.setAttribute("href", encodedUri)
            link.setAttribute("download", filename)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        },
        formatDate(dateStr) {
            if (!dateStr) return '-'
            return new Date(dateStr).toLocaleString('en-GB', { 
                year: 'numeric', month: '2-digit', day: '2-digit', 
                hour: '2-digit', minute: '2-digit',
                timeZone: 'Asia/Bangkok'
            })
        },
        getStatusColor(status) {
            if (status === 'late') return 'background: rgba(192,57,43,0.1); color: #c0392b; border: 1px solid rgba(192,57,43,0.2);'
            if (status === 'on_time' || status === 'present') return 'background: rgba(39,174,96,0.1); color: #27ae60; border: 1px solid rgba(39,174,96,0.2);'
            return 'background: rgba(212,164,76,0.1); color: #d4a44c; border: 1px solid rgba(212,164,76,0.2);'
        },
        async handleApprove(id) {
            try {
                await approveLeave(id)
                this.showToast('Rest approved!')
                this.loadData()
            } catch (e) {
                this.showToast(e.response?.data?.detail || 'Failed to approve', 'error')
            }
        },
        async handleReject(id) {
            try {
                await rejectLeave(id)
                this.showToast('Rest rejected')
                this.loadData()
            } catch (e) {
                this.showToast(e.response?.data?.detail || 'Failed to reject', 'error')
            }
        },
        openViewer(src) { this.viewerSrc = src; this.viewerOpen = true },
        isPdf(path) { return path && path.toLowerCase().endsWith('.pdf') },
        toggleExpUser(userId) {
            this.expandedExpUsers = { ...this.expandedExpUsers, [userId]: !this.expandedExpUsers[userId] }
        },
        getExpAmount(exp) {
            return exp.expense_type === 'TRAVEL' ? (exp.total_amount || 0) : (exp.amount || 0)
        },
        getExpenseStatusColor(status) {
            if (status === 'PENDING') return 'background: rgba(230,126,34,0.1); color: #e67e22; border: 1px solid rgba(230,126,34,0.2);'
            if (status === 'ALL_APPROVED') return 'background: rgba(46,204,113,0.1); color: #2ecc71; border: 1px solid rgba(46,204,113,0.2);'
            if (status === 'CONFIRMED') return 'background: rgba(52,152,219,0.1); color: #3498db; border: 1px solid rgba(52,152,219,0.2);'
            if (status === 'REJECTED') return 'background: rgba(192,57,43,0.1); color: #c0392b; border: 1px solid rgba(192,57,43,0.2);'
            return 'background: rgba(212,164,76,0.1); color: #d4a44c; border: 1px solid rgba(212,164,76,0.2);'
        }
    }
}
</script>

<style scoped>
.tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.tab {
    padding: 10px 22px;
    background: rgba(44,24,16,0.6);
    border: 2px solid rgba(212,164,76,0.15);
    border-radius: 8px;
    color: #8b7355;
    cursor: pointer;
    font-weight: 700;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 14px;
}

.tab:hover {
    background: rgba(212,164,76,0.06);
    border-color: rgba(212,164,76,0.3);
    color: #d4a44c;
    transform: translateY(-1px);
}

.tab.active {
    background: linear-gradient(135deg, #b8860b, #d4a44c);
    color: #1c1208;
    border-color: transparent;
    box-shadow: 0 4px 16px rgba(212,164,76,0.3);
}

.status-badge {
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
}

/* Multi-select Dropdown */
.multi-select-input {
    min-height: 38px;
    padding: 4px 30px 4px 10px;
    border-radius: 8px;
    border: 2px solid rgba(212,164,76,0.15);
    background: rgba(44,24,16,0.6);
    cursor: pointer;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    position: relative;
    transition: border-color 0.2s;
}
.multi-select-input:hover { border-color: rgba(212,164,76,0.3); }
.placeholder { color: #8b7355; font-size: 13px; font-weight: 600; }
.dropdown-arrow {
    position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
    color: #8b7355; font-size: 14px;
}
.selected-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.chip {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(212,164,76,0.1);
    border: 1px solid rgba(212,164,76,0.2);
    padding: 2px 8px; border-radius: 6px;
    font-size: 11px; font-weight: 700; color: #d4a44c;
    white-space: nowrap;
}
.chip-x {
    cursor: pointer; font-size: 14px; line-height: 1;
    color: #d4a44c; font-weight: 800;
}
.chip-x:hover { color: #c0392b; }
.dropdown-list {
    position: absolute; top: 100%; left: 0; right: 0;
    background: #1a1a2e; border: 2px solid rgba(212,164,76,0.2);
    border-radius: 8px; margin-top: 4px;
    max-height: 220px; overflow-y: auto;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    z-index: 100;
}
.dropdown-search {
    width: 100%; padding: 8px 12px; border: none;
    border-bottom: 1px solid rgba(212,164,76,0.1);
    font-size: 13px; font-weight: 600; outline: none;
    box-sizing: border-box;
    background: transparent;
    color: #e8d5b7;
}
.dropdown-item {
    padding: 8px 12px; cursor: pointer;
    font-size: 13px; font-weight: 600; color: #e8d5b7;
    transition: background 0.15s;
    display: flex; align-items: center; gap: 6px;
}
.dropdown-item:hover { background: rgba(212,164,76,0.06); }
.dropdown-item.selected { background: rgba(212,164,76,0.08); color: #d4a44c; }
.check { font-size: 14px; }

/* Summary boxes */
.summary-box {
  background: rgba(26,26,46,0.6); border: 1px solid rgba(212,164,76,0.15); border-radius: 10px; padding: 14px; text-align: center;
}
.summary-box.grand {
  border-color: rgba(212,164,76,0.4); background: linear-gradient(135deg, rgba(44,24,16,0.8), rgba(26,26,46,0.7));
}
.summary-label { font-size: 13px; font-weight: 700; color: #8b7355; margin-bottom: 6px; }
.summary-value { font-size: 22px; font-weight: 800; color: #d4a44c; font-family: 'Cinzel', serif; }
.summary-box.grand .summary-value { font-size: 26px; text-shadow: 0 2px 8px rgba(212,164,76,0.3); }
.summary-count { font-size: 11px; color: #8b7355; margin-top: 4px; font-weight: 600; }

/* Report thumbs */
.report-thumb { width: 36px; height: 36px; border-radius: 4px; overflow: hidden; cursor: pointer; border: 1px solid rgba(212,164,76,0.2); }
.report-thumb img { width: 100%; height: 100%; object-fit: cover; }
.pdf-mini { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(212,164,76,0.1); font-size: 8px; font-weight: 800; color: #d4a44c; }

/* Viewer */
.viewer-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.92); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.viewer-close { position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.2); border: none; color: #fff; font-size: 20px; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; z-index: 10000; }
.viewer-content { max-width: 90vw; max-height: 90vh; overflow: auto; }
.viewer-img { max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; }
.viewer-pdf { width: 90vw; height: 90vh; border: none; border-radius: 8px; }

/* Expense User Cards */
.expense-user-card {
  background: linear-gradient(135deg, rgba(17,10,30,0.5), rgba(30,14,10,0.35));
  border: 1px solid rgba(212,164,76,0.1);
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.expense-user-card:hover { border-color: rgba(212,164,76,0.25); }
.euc-header {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 18px; cursor: pointer;
  transition: background 0.15s;
}
.euc-header:hover { background: rgba(212,164,76,0.04); }
.euc-user { flex: 1; min-width: 0; }
.euc-name { font-size: 14px; font-weight: 700; color: #e8d5b7; }
.euc-count { font-size: 11px; color: #8b7355; }
.euc-summary { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.euc-stat { font-size: 12px; font-weight: 700; white-space: nowrap; }
.euc-total { color: #d4a44c; font-size: 14px; }
.euc-chevron { font-size: 16px; color: #8b7355; transition: transform 0.2s; }
.euc-chevron.open { transform: rotate(180deg); }
.euc-body { border-top: 1px solid rgba(212,164,76,0.08); padding: 0 18px 14px; }
.euc-body table { margin-top: 10px; }
.euc-body th { font-size: 11px; padding: 8px 10px; }
.euc-body td { font-size: 12px; padding: 8px 10px; }
</style>
