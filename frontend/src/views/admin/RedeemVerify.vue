<template>
  <div>
    <div class="page-header">
      <h2>📋 Trade Verification</h2>
      <p>Review and confirm pending item trades</p>
    </div>

    <!-- Tab Filter -->
    <div class="filter-tabs">
      <button :class="['filter-tab', activeTab === 'pending' && 'filter-tab--active']" @click="activeTab = 'pending'">
        ⏳ Pending ({{ pendingItems.length }})
      </button>
      <button :class="['filter-tab', activeTab === 'completed' && 'filter-tab--active']" @click="activeTab = 'completed'">
        ✅ Completed ({{ completedItems.length }})
      </button>
    </div>

    <!-- Pending Redemptions -->
    <div v-if="activeTab === 'pending'">
      <div v-if="pendingItems.length === 0" class="empty-state card">
        <h3>No pending trades</h3>
        <p>All item requests have been processed.</p>
      </div>
      <div v-for="item in pendingItems" :key="item.id" class="redemption-card">
        <div class="redemption-left">
          <div class="redemption-avatar">🎁</div>
          <div class="redemption-info">
            <div class="redemption-user">{{ item.user_name || `Adventurer #${item.user_id}` }}</div>
            <div class="redemption-reward">{{ item.reward?.name || 'Unknown Item' }}</div>
            <div class="redemption-meta">
              <span>{{ item.reward?.point_cost || 0 }} 💰</span>
              <span>•</span>
              <span>{{ formatDate(item.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="redemption-actions">
          <button class="btn-confirm" @click="handleConfirm(item.id)" :disabled="confirming === item.id">
            {{ confirming === item.id ? '...' : '✅ Confirm' }}
          </button>
          <button class="btn-reject-sm" @click="handleReject(item.id)" :disabled="confirming === item.id">
            ❌
          </button>
        </div>
      </div>
    </div>

    <!-- Completed Redemptions -->
    <div v-if="activeTab === 'completed'">
      <div v-if="completedItems.length === 0" class="empty-state card">
        <h3>No completed trades yet</h3>
      </div>
      <div v-for="item in completedItems" :key="item.id" class="redemption-card redemption-card--done">
        <div class="redemption-left">
          <div class="redemption-avatar redemption-avatar--done">✅</div>
          <div class="redemption-info">
            <div class="redemption-user">{{ item.user_name || `Adventurer #${item.user_id}` }}</div>
            <div class="redemption-reward">{{ item.reward?.name || 'Unknown Item' }}</div>
            <div class="redemption-meta">
              <span>{{ item.reward?.point_cost || 0 }} 💰</span>
              <span>•</span>
              <span>{{ formatDate(item.created_at) }}</span>
            </div>
          </div>
        </div>
        <span class="status-done">Completed</span>
      </div>
    </div>
  </div>
</template>

<script>
import { getAllRedemptions, confirmRedemption, rejectRedemption } from '../../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      redemptions: [],
      activeTab: 'pending',
      confirming: null,
    }
  },
  computed: {
    pendingItems() {
      return this.redemptions.filter(r => r.status === 'pending')
    },
    completedItems() {
      return this.redemptions.filter(r => r.status === 'completed')
    },
  },
  async mounted() {
    await this.loadRedemptions()
  },
  methods: {
    async loadRedemptions() {
      try {
        const { data } = await getAllRedemptions()
        this.redemptions = data
      } catch (e) {
        console.error('Failed to load redemptions', e)
      }
    },
    formatDate(dt) {
      if (!dt) return ''
      return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    },
    async handleConfirm(id) {
      this.confirming = id
      try {
        await confirmRedemption(id)
        this.showToast('Trade confirmed ✅')
        await this.loadRedemptions()
      } catch (e) {
        this.showToast('Failed to confirm', 'error')
      } finally {
        this.confirming = null
      }
    },
    async handleReject(id) {
      if (!confirm('Reject this trade? Gold will be refunded.')) return
      this.confirming = id
      try {
        await rejectRedemption(id)
        this.showToast('Trade rejected, gold refunded')
        await this.loadRedemptions()
      } catch (e) {
        this.showToast('Failed to reject', 'error')
      } finally {
        this.confirming = null
      }
    },
  }
}
</script>

<style scoped>
.filter-tabs {
  display: flex; gap: 8px; margin-bottom: 20px;
}
.filter-tab {
  padding: 8px 18px; border: 2px solid rgba(212,164,76,0.15);
  border-radius: 8px; font-weight: 700; font-size: 13px;
  background: rgba(44,24,16,0.6); color: #8b7355; cursor: pointer;
  transition: all 0.2s;
}
.filter-tab:hover { border-color: rgba(212,164,76,0.3); }
.filter-tab--active {
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; border-color: transparent;
}

.redemption-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; margin-bottom: 10px;
  background: linear-gradient(145deg, rgba(44,24,16,0.7), rgba(26,26,46,0.8));
  border-radius: 12px;
  border: 2px solid rgba(212,164,76,0.12);
  transition: all 0.2s;
}
.redemption-card:hover { border-color: rgba(212,164,76,0.25); }
.redemption-card--done { opacity: 0.6; }

.redemption-left { display: flex; align-items: center; gap: 14px; }
.redemption-avatar {
  width: 42px; height: 42px; border-radius: 10px;
  background: rgba(212,164,76,0.1);
  border: 1px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.redemption-avatar--done { background: rgba(39,174,96,0.1); border-color: rgba(39,174,96,0.2); }

.redemption-info { min-width: 0; }
.redemption-user { font-weight: 700; color: #e8d5b7; font-size: 14px; }
.redemption-reward { font-weight: 600; color: #d4a44c; font-size: 13px; }
.redemption-meta { display: flex; gap: 6px; font-size: 11px; color: #8b7355; font-weight: 600; margin-top: 2px; }

.redemption-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-confirm {
  padding: 8px 16px; border: none; border-radius: 8px;
  background: linear-gradient(135deg, #1e8449, #27ae60);
  color: white; font-weight: 700; font-size: 12px;
  cursor: pointer; transition: all 0.2s;
}
.btn-confirm:hover { transform: scale(1.03); }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-reject-sm {
  padding: 8px 12px; border: 2px solid rgba(192,57,43,0.2);
  border-radius: 8px; background: rgba(192,57,43,0.1);
  font-size: 12px; cursor: pointer; transition: all 0.2s;
}
.btn-reject-sm:hover { background: rgba(192,57,43,0.2); border-color: rgba(192,57,43,0.4); }

.status-done {
  font-size: 12px; font-weight: 700; color: #27ae60;
  padding: 4px 12px; background: rgba(39,174,96,0.1);
  border-radius: 6px; border: 1px solid rgba(39,174,96,0.2);
}
</style>
