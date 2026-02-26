<template>
  <div class="staff-page">
    <h1 class="page-title">📜 Approval Board</h1>
    <p class="page-sub">Review and manage pending quests</p>

    <!-- Tabs -->
    <div class="tab-bar">
      <button @click="tab = 'leaves'" :class="['tab-btn', tab === 'leaves' && 'tab-btn--active']">
        🏨 Leave ({{ pendingLeaves.length }})
      </button>
      <button @click="tab = 'redemptions'" :class="['tab-btn', tab === 'redemptions' && 'tab-btn--active']">
        🛒 Trade ({{ pendingRedemptions.length }})
      </button>
      <button @click="tab = 'expenses'" :class="['tab-btn', tab === 'expenses' && 'tab-btn--active']">
        💰 Expense ({{ pendingExpenses.length }})
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loading-icon">⏳</div>
      <p class="loading-text">Loading quests...</p>
    </div>

    <!-- Leave Tab -->
    <div v-else-if="tab === 'leaves'" class="card-list">
      <div v-if="pendingLeaves.length === 0" class="empty-state">
        <div class="empty-icon">⚔️</div>
        <p class="empty-text">No pending leave requests</p>
      </div>

      <div v-for="item in pendingLeaves" :key="item.id" class="approval-card approval-card--leave">
        <div class="card-top">
          <div>
            <div class="card-name">{{ item.user_name }}</div>
            <div class="card-type">{{ item.leave_type }} leave</div>
          </div>
          <span class="badge-pill">{{ item.evidence_image ? 'รออนุมัติอีกครั้ง' : 'pending' }}</span>
        </div>
        <div class="card-detail" v-if="item.start_time">
          📅 {{ formatDate(item.start_date) }} {{ item.start_time }}–{{ item.end_time }}
        </div>
        <div class="card-detail" v-else>📅 {{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
        <div class="card-detail" v-if="item.reason">💬 {{ item.reason }}</div>
        <!-- Evidence image for sick leave re-approval -->
        <div v-if="item.evidence_image" class="file-attachments">
          <div class="attach-thumb" @click="openViewer(item.evidence_image)">
            <img :src="apiBase + item.evidence_image" class="thumb-img" />
            <span class="thumb-label">หลักฐาน</span>
          </div>
        </div>
        <div class="card-actions">
          <button @click="handleApproveLeave(item.id)" :disabled="processing" class="btn-approve">✅ Accept</button>
          <button @click="confirmRejectLeave(item)" :disabled="processing" class="btn-reject">❌ Deny</button>
        </div>
      </div>
    </div>

    <!-- Redemption Tab -->
    <div v-else-if="tab === 'redemptions'" class="card-list">
      <div v-if="pendingRedemptions.length === 0" class="empty-state">
        <div class="empty-icon">🛒</div>
        <p class="empty-text">No pending trade requests</p>
      </div>

      <div v-for="item in pendingRedemptions" :key="item.id" class="approval-card approval-card--redeem">
        <div class="card-top">
          <div>
            <div class="card-name">{{ item.user_name }}</div>
            <div class="card-type">🛒 {{ item.reward_name }} · {{ item.point_cost }} 💰</div>
          </div>
          <span class="badge-pill">pending</span>
        </div>
        <div class="card-detail" v-if="item.created_at">Requested: {{ formatDateTime(item.created_at) }}</div>
        <div class="card-actions">
          <button @click="handleApproveRedeem(item.id)" :disabled="processing" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectRedeem(item.id)" :disabled="processing" class="btn-reject">❌ Deny</button>
        </div>
      </div>
    </div>

    <!-- Expense Tab -->
    <div v-else-if="tab === 'expenses'" class="card-list">
      <div v-if="pendingExpenses.length === 0" class="empty-state">
        <div class="empty-icon">💰</div>
        <p class="empty-text">No pending expense requests</p>
      </div>

      <div v-for="item in pendingExpenses" :key="item.id" class="approval-card approval-card--expense">
        <div class="card-top">
          <div>
            <div class="card-name">{{ item.user_name }}</div>
            <div class="card-type">{{ item.expense_type === 'GENERAL' ? '📄' : '🚗' }} {{ item.expense_type }} Expense</div>
          </div>
          <span class="badge-pill">{{ item.current_step }}/{{ item.total_steps }}</span>
        </div>

        <div class="card-detail">📅 {{ item.expense_type === 'GENERAL' ? item.expense_date : item.travel_date }}</div>
        <div class="card-detail" v-if="item.description">💬 {{ item.description }}</div>
        <div class="card-detail expense-amount">💰 ฿{{ (item.expense_type === 'GENERAL' ? item.amount : item.total_amount).toLocaleString() }}</div>

        <!-- File preview -->
        <div class="file-attachments">
          <template v-if="item.expense_type === 'GENERAL' && item.file_path">
            <div class="attach-thumb" @click="openViewer(item.file_path)">
              <img v-if="!isPdf(item.file_path)" :src="apiBase + item.file_path" class="thumb-img" />
              <div v-else class="thumb-pdf">📄 PDF</div>
            </div>
          </template>
          <template v-if="item.expense_type === 'TRAVEL'">
            <div v-if="item.outbound_image" class="attach-thumb" @click="openViewer(item.outbound_image)">
              <img :src="apiBase + item.outbound_image" class="thumb-img" />
              <span class="thumb-label">Out</span>
            </div>
            <div v-if="item.return_image" class="attach-thumb" @click="openViewer(item.return_image)">
              <img :src="apiBase + item.return_image" class="thumb-img" />
              <span class="thumb-label">Return</span>
            </div>
            <div v-for="att in item.attachments" :key="att.id" class="attach-thumb" @click="openViewer(att.file_path)">
              <img :src="apiBase + att.file_path" class="thumb-img" />
            </div>
          </template>
        </div>

        <div v-if="item.expense_type === 'TRAVEL'" class="travel-detail">
          <span>🚗 {{ item.vehicle_type }} · {{ item.km_outbound }}km + {{ item.km_return }}km</span>
          <span v-if="item.other_cost > 0"> · Other: ฿{{ item.other_cost.toLocaleString() }}</span>
        </div>

        <div class="card-actions">
          <button @click="handleApproveExpense(item.id)" :disabled="processing" class="btn-approve">✅ Approve</button>
          <button @click="handleRejectExpense(item.id)" :disabled="processing" class="btn-reject">❌ Reject</button>
        </div>
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

    <!-- Reject Sick Leave Confirmation -->
    <div v-if="showRejectConfirm" class="viewer-overlay" @click.self="showRejectConfirm = false">
      <div class="viewer-content" @click.stop style="background:linear-gradient(145deg,#2c1810,#1a1a2e); padding:28px; border-radius:16px; border:2px solid #d4a44c; max-width:380px; text-align:center;">
        <div style="font-size:40px; margin-bottom:12px;">⚠️</div>
        <h3 style="color:#d4a44c; font-size:18px; margin-bottom:12px;">ยืนยันการ Reject</h3>
        <p style="color:#e8d5b7; font-size:14px; line-height:1.6; margin-bottom:20px;">
          หาก <strong>Reject</strong> การลาป่วยของ <strong>{{ rejectTarget?.user_name }}</strong><br>
          จะถือว่าพนักงาน<strong style="color:#e74c3c;">ขาดงาน</strong>ในวันนั้นทันที<br>
          และจะถูก<strong style="color:#e74c3c;">หัก Gold ขาดงาน</strong>
        </p>
        <div style="display:flex; gap:10px;">
          <button class="btn-approve" @click="showRejectConfirm = false" style="flex:1;">ยกเลิก</button>
          <button class="btn-reject" @click="doRejectLeave" style="flex:1;">❌ ยืนยัน Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getPendingLeaveApprovals, getPendingRedemptionApprovals,
  approveLeave, rejectLeave,
  approveRedemption, rejectRedemption,
  getPendingExpenseApprovals, approveExpense, rejectExpense,
} from '../../services/api'

export default {
  name: 'StaffApprovals',
  inject: ['showToast'],
  data() {
    return {
      tab: 'leaves',
      loading: true,
      processing: false,
      pendingLeaves: [],
      pendingRedemptions: [],
      pendingExpenses: [],
      viewerOpen: false,
      viewerSrc: '',
      apiBase: import.meta.env.VITE_API_URL || '',
      showRejectConfirm: false,
      rejectTarget: null,
    }
  },
  async mounted() { await this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const [lRes, rRes, eRes] = await Promise.all([
          getPendingLeaveApprovals(),
          getPendingRedemptionApprovals(),
          getPendingExpenseApprovals(),
        ])
        this.pendingLeaves = lRes.data
        this.pendingRedemptions = rRes.data
        this.pendingExpenses = eRes.data || []
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async handleApproveLeave(id) {
      this.processing = true
      try { await approveLeave(id); this.showToast('Leave approved! ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    async handleRejectLeave(id) {
      this.processing = true
      try { await rejectLeave(id); this.showToast('Leave denied ❌'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    confirmRejectLeave(item) {
      if (item.leave_type === 'sick') {
        this.rejectTarget = item
        this.showRejectConfirm = true
      } else {
        this.handleRejectLeave(item.id)
      }
    },
    async doRejectLeave() {
      const id = this.rejectTarget?.id
      this.showRejectConfirm = false
      this.rejectTarget = null
      if (id) await this.handleRejectLeave(id)
    },
    async handleApproveRedeem(id) {
      this.processing = true
      try { await approveRedemption(id); this.showToast('Trade approved! 🛒'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    async handleRejectRedeem(id) {
      this.processing = true
      try { await rejectRedemption(id); this.showToast('Trade denied & gold refunded'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    async handleApproveExpense(id) {
      this.processing = true
      try { await approveExpense(id); this.showToast('Expense approved! 💰'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    async handleRejectExpense(id) {
      this.processing = true
      try { await rejectExpense(id); this.showToast('Expense rejected'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    openViewer(src) { this.viewerSrc = src; this.viewerOpen = true },
    isPdf(path) { return path && path.toLowerCase().endsWith('.pdf') },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-GB') : '' },
    formatDateTime(d) {
      if (!d) return ''
      const dt = new Date(d)
      return dt.toLocaleDateString('en-GB') + ' ' + dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; margin-bottom: 20px; font-style: italic; }

/* Tabs */
.tab-bar {
  display: flex;
  background: rgba(44,24,16,0.6);
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 20px;
}
.tab-btn {
  flex: 1;
  padding: 10px 0;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  background: transparent;
  color: #8b7355;
  transition: all 0.2s;
}
.tab-btn--active {
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208;
  box-shadow: 0 2px 12px rgba(212,164,76,0.2);
}

/* Cards */
.card-list { display: flex; flex-direction: column; gap: 12px; }
.approval-card {
  padding: 16px 18px;
  border-radius: 10px;
  border-left: 4px solid;
  background: rgba(44,24,16,0.6);
}
.approval-card--leave { border-color: #d4a44c; }
.approval-card--redeem { border-color: #9b59b6; }
.approval-card--expense { border-color: #27ae60; }
.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.card-name { font-weight: 700; font-size: 15px; color: #e8d5b7; }
.card-type { font-size: 12px; color: #d4a44c; font-weight: 700; text-transform: uppercase; }
.card-detail { font-size: 13px; color: #8b7355; margin-bottom: 4px; }
.expense-amount { color: #2ecc71; font-weight: 700; }
.card-actions { display: flex; gap: 10px; margin-top: 14px; }
.btn-approve {
  flex: 1; padding: 11px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, #1e8449, #27ae60);
  border: 1px solid #2ecc71; cursor: pointer; transition: all 0.15s;
}
.btn-approve:active { transform: scale(0.97); }
.btn-reject {
  flex: 1; padding: 11px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700; color: #e74c3c;
  background: rgba(192,57,43,0.15);
  border: 1px solid rgba(192,57,43,0.3);
  cursor: pointer; transition: all 0.15s;
}
.btn-reject:active { transform: scale(0.97); }

.badge-pill {
  padding: 3px 12px; border-radius: 6px;
  font-size: 10px; font-weight: 800; text-transform: uppercase;
  background: rgba(212,164,76,0.15); color: #d4a44c; border: 1px solid rgba(212,164,76,0.3);
}

/* File attachments */
.file-attachments { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.attach-thumb { position: relative; cursor: pointer; border-radius: 8px; overflow: hidden; border: 1px solid rgba(212,164,76,0.2); }
.thumb-img { width: 64px; height: 64px; object-fit: cover; display: block; }
.thumb-pdf { width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: rgba(212,164,76,0.1); font-size: 12px; color: #d4a44c; font-weight: 700; }
.thumb-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.6); color: #fff; font-size: 9px; text-align: center; padding: 1px 0; font-weight: 700; }

.travel-detail { font-size: 12px; color: #8b7355; margin-bottom: 4px; }

/* Fullscreen Viewer */
.viewer-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.92); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.viewer-close { position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.2); border: none; color: #fff; font-size: 20px; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; z-index: 10000; }
.viewer-content { max-width: 90vw; max-height: 90vh; overflow: auto; }
.viewer-img { max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; }
.viewer-pdf { width: 90vw; height: 90vh; border: none; border-radius: 8px; }

/* Empty / Loading */
.empty-state {
  padding: 40px 16px; text-align: center; border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 40px; margin-bottom: 10px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

.loading-state { text-align: center; padding: 48px 0; }
.loading-icon { font-size: 36px; animation: bounce 1s infinite; margin-bottom: 10px; }
.loading-text { color: #8b7355; font-weight: 600; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
</style>
