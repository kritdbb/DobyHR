<template>
  <div class="staff-page">
    <h1 class="page-title">📜 Approval Board</h1>
    <p class="page-sub">Review and manage pending quests</p>

    <!-- Tabs -->
    <div class="tab-bar">
      <button @click="tab = 'leaves'" :class="['tab-btn', tab === 'leaves' && 'tab-btn--active']">
        🏨 Rest ({{ pendingLeaves.length }})
      </button>
      <button @click="tab = 'redemptions'" :class="['tab-btn', tab === 'redemptions' && 'tab-btn--active']">
        🛒 Trade ({{ pendingRedemptions.length }})
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
        <p class="empty-text">No pending rest requests</p>
      </div>

      <div v-for="item in pendingLeaves" :key="item.id" class="approval-card approval-card--leave">
        <div class="card-top">
          <div>
            <div class="card-name">{{ item.user_name }}</div>
            <div class="card-type">{{ item.leave_type }} rest</div>
          </div>
          <span class="badge-pill">pending</span>
        </div>
        <div class="card-detail">📅 {{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
        <div class="card-detail" v-if="item.reason">💬 {{ item.reason }}</div>
        <div class="card-actions">
          <button @click="handleApproveLeave(item.id)" :disabled="processing" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectLeave(item.id)" :disabled="processing" class="btn-reject">❌ Deny</button>
        </div>
      </div>
    </div>

    <!-- Redemption Tab -->
    <div v-else class="card-list">
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
  </div>
</template>

<script>
import {
  getPendingLeaveApprovals, getPendingRedemptionApprovals,
  approveLeave, rejectLeave,
  approveRedemption, rejectRedemption,
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
    }
  },
  async mounted() { await this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const [lRes, rRes] = await Promise.all([
          getPendingLeaveApprovals(),
          getPendingRedemptionApprovals(),
        ])
        this.pendingLeaves = lRes.data
        this.pendingRedemptions = rRes.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async handleApproveLeave(id) {
      this.processing = true
      try { await approveLeave(id); this.showToast('Rest approved! ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
    },
    async handleRejectLeave(id) {
      this.processing = true
      try { await rejectLeave(id); this.showToast('Rest denied'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
      finally { this.processing = false }
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
  font-size: 13px;
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
.card-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.card-name { font-weight: 700; font-size: 15px; color: #e8d5b7; }
.card-type { font-size: 12px; color: #d4a44c; font-weight: 700; text-transform: uppercase; }
.card-detail { font-size: 13px; color: #8b7355; margin-bottom: 4px; }
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
