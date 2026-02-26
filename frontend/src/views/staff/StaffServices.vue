<template>
  <div class="staff-page">
    <h1 class="page-title">📜 Guild Services</h1>
    <p class="page-sub">Choose your path, adventurer</p>

    <div class="service-grid">
      <!-- Row 1: Leave Request | Expense Request -->
      <router-link to="/staff/leave" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/leave_request.webp" class="service-icon-img" />
          <span v-if="badges.leave" class="notif-badge">{{ badges.leave }}</span>
        </div>
        <span class="service-label">Leave Request</span>
        <span class="service-desc">Request time off</span>
      </router-link>

      <router-link to="/staff/expense" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/expense_request.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Expense Request</span>
        <span class="service-desc">Claim expenses</span>
      </router-link>

      <!-- Row 2: Approval Board | Coupon Inventory -->
      <router-link to="/staff/approvals" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/approval_board.webp" class="service-icon-img" />
          <span v-if="badges.approvals" class="notif-badge">{{ badges.approvals }}</span>
        </div>
        <span class="service-label">Approval Board</span>
        <span class="service-desc">Review requests</span>
      </router-link>

      <router-link to="/staff/coupons" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/coupon_inventory.webp" class="service-icon-img" />
          <span v-if="badges.coupons" class="notif-badge">{{ badges.coupons }}</span>
        </div>
        <span class="service-label">Coupon Inventory</span>
        <span class="service-desc">Your items</span>
      </router-link>

      <!-- Row 3: Item Shop | Magic Shop -->
      <router-link to="/staff/redeem" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/item_shop.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Item Shop</span>
        <span class="service-desc">Gold &amp; Mana ✨</span>
      </router-link>

      <router-link to="/staff/magic-shop" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/magic_shop.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Magic Shop</span>
        <span class="service-desc">Spend Gold on magic</span>
      </router-link>

      <router-link to="/staff/badge-shop" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/badge_shop.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Badge Shop</span>
        <span class="service-desc">Collect badges</span>
      </router-link>

      <!-- Row 4: Character | Step Counter -->
      <router-link to="/staff/profile" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/my_charactor.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Character</span>
        <span class="service-desc">Edit your info</span>
      </router-link>

      <router-link to="/staff/fitbit" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/step_counter.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Step Counter</span>
        <span class="service-desc">Track your walks</span>
      </router-link>

      <!-- Row 5: Town People -->
      <router-link to="/staff/town-people" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/people.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Town People</span>
        <span class="service-desc">Fellow adventurers</span>
      </router-link>

      <!-- Row 5 (right): Revival Records -->
      <router-link to="/staff/revival-records" class="service-card">
        <div class="icon-wrap">
          <img src="/icons/revive_record.webp" class="service-icon-img" />
        </div>
        <span class="service-label">Revival Records</span>
        <span class="service-desc">Hall of Fame</span>
      </router-link>

      <!-- Row 6: Man of the Month -->
      <router-link to="/staff/man-of-the-month" class="service-card">
        <div class="icon-wrap">
          <div class="service-icon">🏆</div>
        </div>
        <span class="service-label">Man of the Month</span>
        <span class="service-desc">Monthly legends</span>
      </router-link>

    </div>

    <!-- Leave Guild bar -->
    <button @click="logout" class="leave-bar">
      🚪 Leave Guild
    </button>
  </div>
</template>

<script>
import api from '../../services/api'

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
        const { data } = await api.get('/api/combined/services-data')
        this.badges = data.badges || { leave: 0, approvals: 0, coupons: 0 }
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
.leave-bar {
  display: block;
  width: 100%;
  margin-top: 28px;
  padding: 12px 0;
  border: none;
  border-top: 1px solid rgba(192,57,43,0.25);
  background: transparent;
  color: #8b6355;
  font-family: 'Cinzel', serif;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: color 0.2s ease;
}
.leave-bar:hover {
  color: #c0392b;
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

.service-icon-img {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(212,164,76,0.3);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3), 0 0 12px rgba(212,164,76,0.1);
  transition: all 0.3s ease;
}
.service-card:hover .service-icon-img {
  border-color: #d4a44c;
  box-shadow: 0 4px 20px rgba(212,164,76,0.35), 0 0 16px rgba(212,164,76,0.2);
  transform: scale(1.08);
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
