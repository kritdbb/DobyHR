<template>
  <div class="staff-page">
    <h1 class="page-title">📜 Guild Services</h1>
    <p class="page-sub">Choose your path, adventurer</p>

    <div class="service-grid">
      <!-- Leave Request -->
      <router-link to="/staff/leave" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">🏨</div>
          <span v-if="badges.leave" class="notif-badge">{{ badges.leave }}</span>
        </div>
        <span class="service-label">Leave Request</span>
        <span class="service-desc">Request time off</span>
      </router-link>

      <!-- ReQuest Board -->
      <router-link to="/staff/approvals" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">📜</div>
          <span v-if="badges.approvals" class="notif-badge">{{ badges.approvals }}</span>
        </div>
        <span class="service-label">ReQuest Board</span>
        <span class="service-desc">Review requests</span>
      </router-link>

      <!-- Item Shop -->
      <router-link to="/staff/redeem" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">⚔️🛡️</div>
        </div>
        <span class="service-label">Item Shop</span>
        <span class="service-desc">Gold &amp; Mana ✨</span>
      </router-link>

      <!-- Magic Shop -->
      <router-link to="/staff/magic-shop" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">🔮</div>
        </div>
        <span class="service-label">Magic Shop</span>
        <span class="service-desc">Spend Gold on magic</span>
      </router-link>

      <!-- Coupon Inventory -->
      <router-link to="/staff/coupons" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">🎟️</div>
          <span v-if="badges.coupons" class="notif-badge">{{ badges.coupons }}</span>
        </div>
        <span class="service-label">Coupon Inventory</span>
        <span class="service-desc">Your items</span>
      </router-link>

      <!-- Town People -->
      <router-link to="/staff/town-people" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">⚔️👥</div>
        </div>
        <span class="service-label">Town People</span>
        <span class="service-desc">Fellow adventurers</span>
      </router-link>

      <!-- My Profile -->
      <router-link to="/staff/profile" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">🛡️</div>
        </div>
        <span class="service-label">Character</span>
        <span class="service-desc">Edit your info</span>
      </router-link>

      <!-- Logout -->
      <button @click="logout" class="service-card service-card--logout">
        <div class="icon-wrap">
          <div class="service-icon service-icon--danger">🚪</div>
        </div>
        <span class="service-label">Leave Guild</span>
        <span class="service-desc">Sign out</span>
      </button>
    </div>
  </div>
</template>

<script>
import {
  getMyLeaves,
  getPendingLeaveApprovals,
  getPendingRedemptionApprovals,
  getMyRedemptions,
} from '../../services/api'

export default {
  name: 'StaffServices',
  data() {
    return {
      badges: {
        leave: 0,
        approvals: 0,
        coupons: 0,
      },
    }
  },
  async mounted() {
    await this.loadBadges()
  },
  methods: {
    async loadBadges() {
      try {
        const [leavesRes, pendingLeavesRes, pendingRedeemRes, couponsRes] = await Promise.all([
          getMyLeaves().catch(() => ({ data: [] })),
          getPendingLeaveApprovals().catch(() => ({ data: [] })),
          getPendingRedemptionApprovals().catch(() => ({ data: [] })),
          getMyRedemptions().catch(() => ({ data: [] })),
        ])

        this.badges.leave = (leavesRes.data || []).filter(l => l.status === 'pending').length
        this.badges.approvals = (pendingLeavesRes.data || []).length + (pendingRedeemRes.data || []).length
        this.badges.coupons = (couponsRes.data || []).filter(
          c => c.status === 'ready' || c.status === 'approved' || c.status === 'pending'
        ).length
      } catch (e) {
        console.error('Failed to load badges', e)
      }
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px;
  font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub {
  color: #8b7355;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 24px;
  font-style: italic;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.service-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 16px 22px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.2);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}
.service-card:hover {
  transform: translateY(-3px);
  border-color: #d4a44c;
  box-shadow: 0 8px 28px rgba(212,164,76,0.15);
}
.service-card:active {
  transform: scale(0.97);
}
.service-card--logout {
  grid-column: span 2;
  max-width: 50%;
  justify-self: center;
  border-color: rgba(192,57,43,0.2);
}
.service-card--logout:hover {
  border-color: #c0392b;
  box-shadow: 0 8px 28px rgba(192,57,43,0.15);
}

.icon-wrap {
  position: relative;
  display: inline-flex;
  margin-bottom: 12px;
}

.service-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  background: rgba(212,164,76,0.1);
  border: 1px solid rgba(212,164,76,0.2);
}
.service-icon--danger {
  background: rgba(192,57,43,0.1);
  border-color: rgba(192,57,43,0.2);
}

.notif-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: #c0392b;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  line-height: 20px;
  text-align: center;
  border: 2px solid rgba(44,24,16,0.9);
  box-shadow: 0 2px 8px rgba(192,57,43,0.4);
  animation: badgePop 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.service-label {
  font-family: 'Cinzel', serif;
  font-weight: 700;
  font-size: 14px;
  color: #e8d5b7;
  margin-bottom: 2px;
}

.service-desc {
  font-size: 12px;
  color: #8b7355;
  font-weight: 600;
}

@keyframes badgePop {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
