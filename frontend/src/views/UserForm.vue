<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '✏️ Edit Adventurer' : '➕ Recruit Adventurer' }}</h2>
      <p>{{ isEdit ? 'Update adventurer information' : 'Create a new adventurer profile' }}</p>
    </div>

    <!-- 3-column layout for edit mode -->
    <div :class="isEdit ? 'edit-grid' : ''">

      <!-- LEFT COLUMN — Form -->
      <div class="card form-col">
        <!-- Image Upload -->
        <div class="form-group" style="display: flex; align-items: flex-start; gap: 24px; margin-bottom: 28px;">
          <div>
            <label>Portrait</label>
            <div class="logo-upload-area" style="width: 120px; height: 120px;" @click="$refs.imageInput.click()">
              <img v-if="form.image" :src="form.image" alt="User" />
              <div v-else class="upload-placeholder">
                <span class="icon" style="font-size: 24px;">📷</span>
                <span style="font-size: 11px;">Upload</span>
              </div>
            </div>
            <input ref="imageInput" type="file" accept="image/*" @change="handleImageUpload" style="display: none;" />
          </div>
          <div style="flex: 1;">
            <div class="form-row">
              <div class="form-group">
                <label>Name *</label>
                <input v-model="form.name" class="form-input" placeholder="First name" />
              </div>
              <div class="form-group">
                <label>Surname *</label>
                <input v-model="form.surname" class="form-input" placeholder="Last name" />
              </div>
            </div>
            <div class="form-group">
              <label>Rank (ตำแหน่ง)</label>
              <input v-model="form.position" class="form-input" placeholder="e.g. Knight Captain" />
            </div>
          </div>
        </div>

        <!-- Auth Info -->
        <div class="form-row">
          <div class="form-group">
            <label>Email *</label>
            <input v-model="form.email" class="form-input" type="email" placeholder="user@kingdom.com" />
          </div>
          <div class="form-group">
            <label>Phone (เบอร์มือถือ)</label>
            <input v-model="form.phone" class="form-input" type="tel" placeholder="0812345678" maxlength="15" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Role</label>
            <select v-model="form.role" class="form-input">
              <option value="player">Player</option>
              <option value="gm">GM</option>
              <option value="god">God</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>{{ isEdit ? 'New Password (leave blank to keep current)' : 'Password *' }}</label>
          <input v-model="form.password" class="form-input" type="password" placeholder="••••••••" />
        </div>

        <!-- Department & Work Schedule -->
        <div class="form-row">
          <div class="form-group">
            <label>Guild (แผนก)</label>
            <input v-model="form.department" class="form-input" placeholder="e.g. Royal Guard" />
          </div>
          <div class="form-group">
            <label>Start Date (วันเริ่มงาน)</label>
            <input v-model="form.start_date" class="form-input" type="date" />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>📍 Default Outpost (สาขาประจำ)</label>
            <select v-model="form.default_location_id" class="form-input">
              <option :value="null">— None —</option>
              <option v-for="loc in locationsList" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>Quest Start Time</label>
            <input v-model="form.work_start_time" class="form-input" type="time" />
          </div>
          <div class="form-group">
            <label>Quest End Time</label>
            <input v-model="form.work_end_time" class="form-input" type="time" />
          </div>
        </div>

        <!-- Working Days -->
        <div style="margin-top: 8px; margin-bottom: 8px;">
          <label style="font-size: 13px; font-weight: 600; color: #8b7355; text-transform: uppercase; letter-spacing: 0.05em;">Quest Days (วันทำงาน)</label>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px;">
          <label v-for="day in allDays" :key="day.value" 
            :class="['working-day-chip', workingDaysArray.includes(day.value) ? 'active' : '']"
            @click="toggleDay(day.value)">
            {{ day.label }}
          </label>
        </div>

        <!-- Leave Days -->
        <div style="margin-top: 8px; margin-bottom: 8px;">
          <label style="font-size: 13px; font-weight: 600; color: #8b7355; text-transform: uppercase; letter-spacing: 0.05em;">Rest Allocation (วันลา)</label>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
          <div class="form-group">
            <label>Sick Rest (ลาป่วย - ชม.)</label>
            <input v-model.number="form.sick_leave_hours" class="form-input" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group">
            <label>Business Rest (ลากิจ - ชม.)</label>
            <input v-model.number="form.business_leave_hours" class="form-input" type="number" min="0" placeholder="0" />
          </div>
          <div class="form-group">
            <label>Vacation (ลาพักร้อน)</label>
            <input v-model.number="form.vacation_leave_days" class="form-input" type="number" min="0" placeholder="0" />
          </div>
        </div>

        <!-- Face Images (edit mode only) -->
        <div v-if="isEdit" style="margin-top: 16px; margin-bottom: 20px;">
          <label style="font-size: 13px; font-weight: 600; color: #8b7355; text-transform: uppercase; letter-spacing: 0.05em;">📸 Face Recognition Photos</label>
          <p style="font-size: 11px; color: #999; margin: 4px 0 10px;">Upload up to 2 clear frontal face photos for CCTV auto check-in</p>
          <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-start;">
            <div v-for="fi in faceImages" :key="fi.id" style="position: relative;">
              <img :src="apiBase + fi.image_path" style="width: 80px; height: 80px; border-radius: 8px; object-fit: cover; border: 2px solid rgba(212,164,76,0.3);" />
              <button @click="deleteFaceImage(fi.id)" style="position: absolute; top: -6px; right: -6px; width: 20px; height: 20px; border-radius: 50%; background: #e74c3c; color: white; border: none; font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center;">✕</button>
            </div>
            <div v-if="faceImages.length < 2" class="logo-upload-area" style="width: 80px; height: 80px;" @click="$refs.faceInput.click()">
              <div class="upload-placeholder">
                <span class="icon" style="font-size: 18px;">📷</span>
                <span style="font-size: 10px;">Add Face</span>
              </div>
            </div>
          </div>
          <input ref="faceInput" type="file" accept="image/*" @change="handleFaceImageUpload" style="display: none;" />
        </div>

        <!-- Actions -->
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(212,164,76,0.1);">
          <router-link to="/users" class="btn btn-secondary">Cancel</router-link>
          <button class="btn btn-primary" @click="handleSubmit" :disabled="saving">
            {{ saving ? 'Saving...' : (isEdit ? '💾 Update' : '➕ Create') }}
          </button>
        </div>
      </div>

      <!-- CENTER COLUMN — Check-in History + Coin Transactions (edit mode only) -->
      <div v-if="isEdit" class="card side-col">
        <div class="card-header" style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span class="card-title" style="font-size: 15px;">📋 Transaction Ledger</span>
              <div style="font-size: 11px; color: #8b7355;">{{ form.name }} {{ form.surname }}</div>
            </div>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-secondary btn-sm" @click="showAdjustModal = true" style="font-size: 11px; padding: 5px 12px;">
                💰 Gold
              </button>
              <button class="btn btn-secondary btn-sm" @click="showManaAdjustModal = true" style="font-size: 11px; padding: 5px 12px; background: linear-gradient(135deg, rgba(155,89,182,0.15), rgba(142,68,173,0.15)); color: #9b59b6; border-color: rgba(155,89,182,0.3);">
                🔮 Mana
              </button>
            </div>
          </div>
        </div>

        <!-- Coins summary -->
        <div style="display: flex; gap: 10px; margin-bottom: 16px;">
          <div class="stat-chip stat-gold">
            <span class="stat-icon">💰</span>
            <div>
              <div class="stat-value">{{ coinBalance }}</div>
              <div class="stat-label">Gold</div>
            </div>
          </div>
          <div class="stat-chip stat-mana">
            <span class="stat-icon">🔮</span>
            <div>
              <div class="stat-value">{{ angelCoinBalance }}</div>
              <div class="stat-label">Mana</div>
            </div>
          </div>
          <div class="stat-chip stat-blue">
            <span class="stat-icon">⚔️</span>
            <div>
              <div class="stat-value">{{ attendanceList.length }}</div>
              <div class="stat-label">Quests</div>
            </div>
          </div>
        </div>

        <!-- Tab switcher -->
        <div class="tx-tabs">
          <button :class="['tx-tab', centerTab === 'checkin' && 'tx-tab--active']" @click="centerTab = 'checkin'">⚔️ Quests</button>
          <button :class="['tx-tab', centerTab === 'coins' && 'tx-tab--active']" @click="centerTab = 'coins'">💰 Gold</button>
          <button :class="['tx-tab', centerTab === 'angel' && 'tx-tab--active']" @click="centerTab = 'angel'">🔮 Mana</button>
        </div>

        <!-- TAB 1: Check-in History -->
        <div v-if="centerTab === 'checkin'" class="timeline-list">
          <div v-if="attendanceWithCoins.length === 0" class="empty-mini">No quests yet</div>
          <div v-for="item in attendanceWithCoins" :key="'att-'+item.id" class="timeline-row">
            <div class="timeline-icon" :class="item.iconClass">{{ item.icon }}</div>
            <div style="flex: 1; min-width: 0;">
              <div class="timeline-title">{{ item.title }}</div>
              <div class="timeline-sub">{{ formatDateTime(item.timestamp) }}</div>
            </div>
            <div v-if="item.coinChange !== 0" class="timeline-badge" :class="item.coinChange > 0 ? 'badge-green' : 'badge-red'">
              {{ item.coinChange > 0 ? '+' : '' }}{{ item.coinChange }}
            </div>
            <div v-else class="timeline-badge badge-gray">—</div>
          </div>
        </div>

        <!-- TAB 2: Coins Log -->
        <div v-if="centerTab === 'coins'" class="timeline-list">
          <div v-if="coinLogsRegular.length === 0" class="empty-mini">No gold transactions yet</div>
          <div v-for="item in coinLogsRegular" :key="'coin-'+item.id" class="timeline-row">
            <div class="timeline-icon" :class="item.amount >= 0 ? 'icon-gold' : 'icon-red'">{{ item.amount >= 0 ? '💰' : '📉' }}</div>
            <div style="flex: 1; min-width: 0;">
              <div class="timeline-title">{{ item.reason }}</div>
              <div class="timeline-sub">{{ formatDateTime(item.created_at) }}</div>
            </div>
            <div style="text-align: right;">
              <div class="timeline-badge" :class="item.amount >= 0 ? 'badge-green' : 'badge-red'">
                {{ item.amount >= 0 ? '+' : '' }}{{ item.amount }}
              </div>
              <div class="running-total">Total: {{ item.runningTotal }}</div>
            </div>
          </div>
        </div>

        <!-- TAB 3: Mana Log -->
        <div v-if="centerTab === 'angel'" class="timeline-list">
          <div v-if="angelCoinLogsComputed.length === 0" class="empty-mini">No mana transactions yet</div>
          <div v-for="item in angelCoinLogsComputed" :key="'angel-'+item.id" class="timeline-row">
            <div class="timeline-icon icon-purple">🔮</div>
            <div style="flex: 1; min-width: 0;">
              <div class="timeline-title">{{ item.reason }}</div>
              <div class="timeline-sub">{{ formatDateTime(item.created_at) }}</div>
            </div>
            <div style="text-align: right;">
              <div class="timeline-badge" :class="item.amount >= 0 ? 'badge-purple' : 'badge-red'">
                {{ item.amount >= 0 ? '+' : '' }}{{ item.amount }}
              </div>
              <div class="running-total">Total: {{ item.runningTotal }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN — Pending Leaves & Redemptions (edit mode only) -->
      <div v-if="isEdit" class="card side-col">
        <div class="card-header" style="margin-bottom: 12px;">
          <span class="card-title" style="font-size: 15px;">📌 Pending Requests</span>
        </div>

        <!-- Leave Requests -->
        <div style="margin-bottom: 16px;">
          <div style="font-size: 12px; font-weight: 700; color: #8b7355; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px;">
            Rest Requests
          </div>
          <div v-if="leaveList.length === 0" class="empty-mini">No rest requests</div>
          <div v-for="leave in leaveList" :key="'l'+leave.id" class="request-row">
            <div style="flex: 1;">
              <div class="timeline-title">{{ leaveTypeLabel(leave.leave_type) }}</div>
              <div class="timeline-sub">{{ formatDate(leave.start_date) }} → {{ formatDate(leave.end_date) }}</div>
              <div v-if="leave.reason" class="timeline-sub" style="color: #a08060; font-style: italic;">{{ leave.reason }}</div>
            </div>
            <div class="timeline-badge" :class="statusClass(leave.status)">{{ leave.status }}</div>
          </div>
        </div>

        <!-- Redemption Requests -->
        <div>
          <div style="font-size: 12px; font-weight: 700; color: #8b7355; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px;">
            Trades
          </div>
          <div v-if="redemptionList.length === 0" class="empty-mini">No trades</div>
          <div v-for="redeem in redemptionList" :key="'r'+redeem.id" class="request-row">
            <div style="flex: 1;">
              <div class="timeline-title">Trade #{{ redeem.id }}</div>
              <div class="timeline-sub">{{ formatDateTime(redeem.created_at) }}</div>
            </div>
            <div class="timeline-badge" :class="statusClass(redeem.status)">{{ redeem.status }}</div>
          </div>
        </div>
      </div>

    </div>

    <!-- Adjust Gold Modal -->
    <div v-if="showAdjustModal" class="modal-overlay" @click.self="showAdjustModal = false">
      <div class="modal-content" style="max-width: 400px;">
        <h3>💰 Adjust Gold</h3>
        <p style="color: #8b7355; margin-bottom: 20px;">
          Adjusting balance for <strong style="color: #e8d5b7;">{{ form.name }} {{ form.surname }}</strong>
          <br/><span style="font-size: 13px;">Current balance: <strong style="color: #d4a44c;">{{ coinBalance }} 💰</strong></span>
        </p>
        <div class="form-group">
          <label>Amount (positive to add, negative to deduct)</label>
          <input v-model.number="adjustForm.amount" class="form-input" type="number" placeholder="e.g. 50 or -20" />
        </div>
        <div class="form-group">
          <label>Reason</label>
          <input v-model="adjustForm.reason" class="form-input" type="text" placeholder="e.g. Bonus, Penalty" />
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
          <button class="btn btn-secondary" @click="showAdjustModal = false">Cancel</button>
          <button class="btn btn-primary" @click="handleAdjustCoins" :disabled="!adjustForm.amount || !adjustForm.reason">
            Confirm
          </button>
        </div>
      </div>
    </div>

    <!-- Adjust Mana Modal -->
    <div v-if="showManaAdjustModal" class="modal-overlay" @click.self="showManaAdjustModal = false">
      <div class="modal-content" style="max-width: 400px;">
        <h3 style="color: #9b59b6;">🔮 Adjust Mana</h3>
        <p style="color: #8b7355; margin-bottom: 20px;">
          Adjusting for <strong style="color: #e8d5b7;">{{ form.name }} {{ form.surname }}</strong>
          <br/><span style="font-size: 13px;">Current balance: <strong style="color: #9b59b6;">{{ angelCoinBalance }} 🔮</strong></span>
        </p>
        <div class="form-group">
          <label>Amount to add</label>
          <input v-model.number="angelAdjustForm.amount" class="form-input" type="number" min="1" placeholder="e.g. 50" />
        </div>
        <div class="form-group">
          <label>Reason</label>
          <input v-model="angelAdjustForm.reason" class="form-input" type="text" placeholder="e.g. Monthly allocation" />
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
          <button class="btn btn-secondary" @click="showManaAdjustModal = false">Cancel</button>
          <button class="btn" style="background: linear-gradient(135deg, #8e44ad, #9b59b6); color: #fff;" @click="handleAdjustAngelCoins" :disabled="!angelAdjustForm.amount || !angelAdjustForm.reason">
            Confirm
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getUser, createUser, updateUser, uploadUserImage,
  getUserAttendance, getUserLeaves, getUserRedemptions, getUserCoinLogs,
  adjustUserCoins, grantAngelCoins, getUserAngelCoinLogs,
  getUserFaceImages, uploadUserFaceImage, deleteUserFaceImage,
  getLocations,
} from '../services/api'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export default {
  inject: ['showToast'],
  data() {
    return {
      isEdit: false,
      userId: null,
      saving: false,
      pendingImage: null,
      form: {
        email: '', password: '', role: 'player',
        name: '', surname: '', image: null, phone: '',
        department: '', work_start_time: '', work_end_time: '',
        position: '',
        sick_leave_hours: 0, business_leave_hours: 0, vacation_leave_days: 0,
        start_date: '', working_days: 'mon,tue,wed,thu,fri',
        default_location_id: null,
      },
      allDays: [
        { label: 'Mon', value: 'mon' }, { label: 'Tue', value: 'tue' },
        { label: 'Wed', value: 'wed' }, { label: 'Thu', value: 'thu' },
        { label: 'Fri', value: 'fri' }, { label: 'Sat', value: 'sat' },
        { label: 'Sun', value: 'sun' },
      ],
      attendanceList: [],
      coinLogs: [],
      angelCoinLogs: [],
      leaveList: [],
      redemptionList: [],
      coinBalance: 0,
      angelCoinBalance: 0,
      faceImages: [],
      apiBase: API_BASE,
      centerTab: 'checkin',
      showAdjustModal: false,
      adjustForm: { amount: null, reason: '' },
      showManaAdjustModal: false,
      angelAdjustForm: { amount: null, reason: '' },
      locationsList: [],
    }
  },
  computed: {
    workingDaysArray() {
      if (!this.form.working_days) return []
      return this.form.working_days.split(',').map(d => d.trim().toLowerCase())
    },
    attendanceWithCoins() {
      const statusMap = {
        present: { icon: '✅', iconClass: 'icon-green', title: 'On-time Quest', coinChange: 1 },
        late: { icon: '⏰', iconClass: 'icon-warn', title: 'Late Arrival', coinChange: -1 },
        absent: { icon: '❌', iconClass: 'icon-red', title: 'Quest Missed', coinChange: -1 },
        work_request: { icon: '📋', iconClass: 'icon-blue', title: 'Work Request', coinChange: 0 },
      }
      return this.attendanceList.map(att => {
        const info = statusMap[att.status] || { icon: '❓', iconClass: '', title: att.status, coinChange: 0 }
        return { ...att, ...info }
      })
    },
    coinLogsRegular() {
      const sorted = [...this.coinLogs].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      let running = 0
      const withTotals = sorted.map(log => {
        running += log.amount
        return { ...log, runningTotal: running }
      })
      return withTotals.reverse()
    },
    angelCoinLogsComputed() {
      const sorted = [...this.angelCoinLogs].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      let running = 0
      const withTotals = sorted.map(log => {
        running += log.amount
        return { ...log, runningTotal: running }
      })
      return withTotals.reverse()
    },
  },
  async mounted() {
    const id = this.$route.params.id
    if (id) {
      this.isEdit = true
      this.userId = parseInt(id)
      await this.loadUser()
      this.loadSideData()
      this.loadFaceImages()
    }
    await this.loadLocationsList()
  },
  methods: {
    toggleDay(day) {
      const days = this.workingDaysArray.slice()
      const idx = days.indexOf(day)
      if (idx >= 0) { days.splice(idx, 1) } else { days.push(day) }
      const order = ['mon','tue','wed','thu','fri','sat','sun']
      days.sort((a, b) => order.indexOf(a) - order.indexOf(b))
      this.form.working_days = days.join(',')
    },
    async loadUser() {
      try {
        const { data } = await getUser(this.userId)
        this.coinBalance = data.coins || 0
        this.angelCoinBalance = data.angel_coins || 0
        this.form = {
          email: data.email || '', password: '', role: data.role || 'player',
          name: data.name || '', surname: data.surname || '',
          image: data.image || null, phone: data.phone || '',
          department: data.department || '',
          work_start_time: data.work_start_time || '',
          work_end_time: data.work_end_time || '',
          position: data.position || '',
          sick_leave_hours: data.sick_leave_hours || 0,
          business_leave_hours: data.business_leave_hours || 0,
          vacation_leave_days: data.vacation_leave_days || 0,
          start_date: data.start_date || '',
          working_days: data.working_days || 'mon,tue,wed,thu,fri',
          default_location_id: data.default_location_id || null,
        }
      } catch (e) {
        this.showToast('Failed to load adventurer', 'error')
        this.$router.push('/users')
      }
    },
    async loadSideData() {
      try {
        const [attRes, coinRes, leaveRes, redeemRes, angelRes] = await Promise.all([
          getUserAttendance(this.userId),
          getUserCoinLogs(this.userId),
          getUserLeaves(this.userId),
          getUserRedemptions(this.userId),
          getUserAngelCoinLogs(this.userId).catch(() => ({ data: [] })),
        ])
        this.attendanceList = attRes.data
        this.coinLogs = coinRes.data
        this.leaveList = leaveRes.data
        this.redemptionList = redeemRes.data
        this.angelCoinLogs = angelRes.data
      } catch (e) {
        console.error('Side data load error:', e)
      }
    },
    async loadFaceImages() {
      try {
        const { data } = await getUserFaceImages(this.userId)
        this.faceImages = data
      } catch (e) { console.error('Face images load error:', e) }
    },
    async handleFaceImageUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      try {
        await uploadUserFaceImage(this.userId, file)
        this.showToast('Face image uploaded! 📸')
        await this.loadFaceImages()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Upload failed', 'error')
      }
      event.target.value = ''
    },
    async loadLocationsList() {
      try {
        const { data } = await getLocations()
        this.locationsList = data || []
      } catch (e) { console.error('Failed to load locations', e) }
    },
    async deleteFaceImage(imageId) {
      if (!confirm('Remove this face image?')) return
      try {
        await deleteUserFaceImage(this.userId, imageId)
        this.showToast('Face image removed')
        await this.loadFaceImages()
      } catch (e) {
        this.showToast('Delete failed', 'error')
      }
    },
    handleImageUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      this.pendingImage = file
      const reader = new FileReader()
      reader.onload = (e) => { this.form.image = e.target.result }
      reader.readAsDataURL(file)
    },
    async handleSubmit() {
      if (!this.form.name || !this.form.surname) {
        this.showToast('Name and surname are required', 'error'); return
      }
      if (!this.isEdit && !this.form.password) {
        this.showToast('Password is required for new adventurers', 'error'); return
      }
      this.saving = true
      try {
        const payload = { ...this.form }
        delete payload.image
        if (!payload.password || payload.password.trim() === '') delete payload.password
        if (!payload.work_start_time) payload.work_start_time = null
        if (!payload.work_end_time) payload.work_end_time = null
        if (!payload.start_date) payload.start_date = null
        if (!payload.department) payload.department = null
        if (!payload.position) payload.position = null

        let userId
        if (this.isEdit) {
          const { data } = await updateUser(this.userId, payload)
          userId = data.id
          this.showToast('Adventurer updated! ⚔️')
        } else {
          const { data } = await createUser(payload)
          userId = data.id
          this.showToast('Adventurer recruited! ⚔️')
        }
        if (this.pendingImage && userId) {
          await uploadUserImage(userId, this.pendingImage)
        }
        this.$router.push('/users')
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to save', 'error')
      } finally {
        this.saving = false
      }
    },
    formatDate(d) {
      if (!d) return '-'
      return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    },
    formatDateTime(d) {
      if (!d) return '-'
      return new Date(d).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
    },
    leaveTypeLabel(t) {
      const map = { sick: '🤒 Sick Rest', business: '💼 Business Rest', vacation: '🌴 Vacation' }
      return map[t] || t
    },
    statusClass(s) {
      const map = { pending: 'badge-warn', approved: 'badge-green', ready: 'badge-blue', completed: 'badge-green', rejected: 'badge-red' }
      return map[s] || ''
    },
    async handleAdjustCoins() {
      try {
        await adjustUserCoins(this.userId, {
          amount: this.adjustForm.amount,
          reason: this.adjustForm.reason,
        })
        this.showToast('Gold adjusted successfully!')
        this.showAdjustModal = false
        this.adjustForm = { amount: null, reason: '' }
        const { data: user } = await getUser(this.userId)
        this.coinBalance = user.coins || 0
        await this.loadSideData()
      } catch (e) {
        this.showToast('Failed to adjust gold', 'error')
      }
    },
    async handleAdjustAngelCoins() {
      try {
        const { data: user } = await grantAngelCoins(this.userId, {
          amount: this.angelAdjustForm.amount,
          reason: this.angelAdjustForm.reason,
        })
        this.showToast('Mana granted successfully! 🔮')
        this.showManaAdjustModal = false
        this.angelAdjustForm = { amount: null, reason: '' }
        this.angelCoinBalance = user.angel_coins || 0
        await this.loadSideData()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to grant mana', 'error')
      }
    },
  },
}
</script>

<style scoped>
.edit-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 20px;
  align-items: start;
}
.form-col { max-width: none; }
.side-col {
  max-height: 85vh;
  overflow-y: auto;
}

/* Working day chips */
.working-day-chip {
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(44,24,16,0.6);
  border: 2px solid rgba(212,164,76,0.15);
  color: #8b7355;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.working-day-chip:hover { border-color: rgba(212,164,76,0.3); color: #d4a44c; transform: translateY(-1px); }
.working-day-chip.active {
  background: linear-gradient(135deg, rgba(212,164,76,0.15), rgba(184,134,11,0.15));
  border-color: #d4a44c; color: #d4a44c;
}

/* Stat chips */
.stat-chip {
  display: flex; align-items: center; gap: 10px;
  flex: 1; padding: 10px 14px;
  border-radius: 8px;
}
.stat-gold { background: rgba(212,164,76,0.08); border: 1px solid rgba(212,164,76,0.15); }
.stat-mana { background: rgba(155,89,182,0.08); border: 1px solid rgba(155,89,182,0.15); }
.stat-blue { background: rgba(41,128,185,0.08); border: 1px solid rgba(41,128,185,0.15); }
.stat-icon { font-size: 20px; }
.stat-value { font-size: 18px; font-weight: 800; color: #e8d5b7; }
.stat-label { font-size: 10px; color: #8b7355; font-weight: 600; text-transform: uppercase; }

/* Timeline */
.timeline-list {
  display: flex; flex-direction: column; gap: 2px;
}
.timeline-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 8px;
  transition: background 0.2s;
}
.timeline-row:hover { background: rgba(212,164,76,0.04); }
.timeline-icon {
  width: 30px; height: 30px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
}
.icon-green { background: rgba(39,174,96,0.1); }
.icon-warn { background: rgba(212,164,76,0.1); }
.icon-gold { background: rgba(212,164,76,0.1); }
.icon-red { background: rgba(192,57,43,0.1); }

.timeline-title { font-size: 12px; font-weight: 600; color: #e8d5b7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.timeline-sub { font-size: 10px; color: #8b7355; }

.timeline-badge {
  font-size: 10px; font-weight: 700; padding: 2px 8px;
  border-radius: 6px; text-transform: uppercase; flex-shrink: 0;
  white-space: nowrap;
}
.badge-green { background: rgba(39,174,96,0.1); color: #27ae60; }
.badge-warn { background: rgba(212,164,76,0.1); color: #d4a44c; }
.badge-red { background: rgba(192,57,43,0.1); color: #c0392b; }
.badge-blue { background: rgba(41,128,185,0.1); color: #2980b9; }
.badge-purple { background: rgba(155,89,182,0.1); color: #9b59b6; }
.badge-gray { background: rgba(139,115,85,0.1); color: #8b7355; }

.icon-blue { background: rgba(41,128,185,0.1); }
.icon-purple { background: rgba(155,89,182,0.1); }

/* Tab switcher */
.tx-tabs {
  display: flex; gap: 4px; margin-bottom: 12px;
  background: rgba(44,24,16,0.4); border-radius: 8px; padding: 3px;
}
.tx-tab {
  flex: 1; padding: 6px 8px; border: none; border-radius: 6px;
  font-size: 11px; font-weight: 600; cursor: pointer;
  background: transparent; color: #8b7355; transition: all 0.2s;
}
.tx-tab:hover { color: #d4a44c; }
.tx-tab--active {
  background: rgba(212,164,76,0.1); color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.2);
}

/* Running total label */
.running-total {
  font-size: 9px; color: #8b7355; margin-top: 2px;
  font-weight: 600; letter-spacing: 0.02em;
}

/* Request rows */
.request-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  border: 1px solid rgba(212,164,76,0.08);
  margin-bottom: 6px;
  transition: all 0.2s;
}
.request-row:hover { background: rgba(212,164,76,0.04); border-color: rgba(212,164,76,0.15); }

.empty-mini {
  text-align: center; color: #8b7355; font-size: 12px;
  padding: 16px; font-style: italic;
}

@media (max-width: 1200px) {
  .edit-grid { grid-template-columns: 1fr; }
  .side-col { max-height: none; }
}
</style>
