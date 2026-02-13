<template>
  <div class="staff-page">
    <!-- Character Card -->
    <div class="character-card">
      <div class="character-portrait">
        <img v-if="userImage" :src="userImage" class="portrait-img" />
        <div v-else class="portrait-placeholder">{{ userName.charAt(0) || '?' }}</div>
        <div class="portrait-frame"></div>
      </div>
      <h1 class="character-name">⚔️ {{ userName }}</h1>
      <p class="character-class">{{ userPosition || 'Adventurer' }}</p>
      
      <!-- Badges Row -->
      <div class="badges-row" @click="showBadgeModal = true" v-if="myBadges.length > 0">
        <div v-for="badge in myBadges.slice(0, 8)" :key="badge.id" class="badge-circle" :title="badge.badge_name">
          <img v-if="badge.badge_image" :src="badge.badge_image" class="badge-circle-img" />
          <span v-else class="badge-circle-fallback">🏅</span>
        </div>
        <div v-if="myBadges.length > 8" class="badge-more">+{{ myBadges.length - 8 }}</div>
      </div>

      <!-- Power Stats -->
      <div class="power-row">
        <div class="power-item str"><span class="power-icon">⚔️</span> STR <span class="power-val">{{ myStats.total_str }}</span></div>
        <div class="power-item def"><span class="power-icon">🛡️</span> DEF <span class="power-val">{{ myStats.total_def }}</span></div>
        <div class="power-item luk"><span class="power-icon">🍀</span> LUK <span class="power-val">{{ myStats.total_luk }}</span></div>
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value gold">{{ myCoins }}</span>
          <span class="stat-label">💰 Gold</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-value mana">{{ myAngelCoins }}</span>
          <span class="stat-label">✨ Mana</span>
        </div>
      </div>
    </div>

    <!-- Quest Board: Pending Approvals -->
    <div v-if="pendingLeaves.length > 0 || pendingRedemptions.length > 0 || pendingWorkRequests.length > 0" class="section">
      <h2 class="section-title">📜 Quest Board</h2>

      <!-- Pending Leaves -->
      <div v-for="item in pendingLeaves" :key="'leave-'+item.id" class="quest-card quest-card--leave">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">🏖️</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">{{ item.leave_type }} leave</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-detail">📅 {{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
        <div class="quest-detail" v-if="item.reason">💬 {{ item.reason }}</div>
        <div class="quest-actions">
          <button @click="handleApproveLeave(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectLeave(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>

      <!-- Pending Redemptions -->
      <div v-for="item in pendingRedemptions" :key="'redeem-'+item.id" class="quest-card quest-card--redeem">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">🛒</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">Trade: {{ item.reward_name }} ({{ item.point_cost }} 💰)</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-actions">
          <button @click="handleApproveRedeem(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectRedeem(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>

      <!-- Pending Work Requests -->
      <div v-for="item in pendingWorkRequests" :key="'wr-'+item.id" class="quest-card quest-card--work">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">📋</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">Special Mission (non-working day)</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-detail" v-if="item.check_in_time">🕐 Quest started: {{ item.check_in_time }}</div>
        <div class="quest-actions">
          <button @click="handleApproveWorkRequest(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectWorkRequest(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>
    </div>

    <!-- Gold Ledger -->
    <div class="section">
      <h2 class="section-title">💰 Gold Ledger</h2>
      <div v-if="coinLogs.length === 0" class="empty-state">
        <div class="empty-icon">💰</div>
        <p class="empty-text">No gold transactions yet</p>
      </div>
      <div v-else class="coin-list">
        <div v-for="log in coinLogs.slice(0, 5)" :key="log.id" class="coin-item">
          <span class="coin-dot">{{ log.amount >= 0 ? '🟢' : '🔴' }}</span>
          <div class="coin-info">
            <div class="coin-reason">{{ log.reason }}</div>
            <div class="coin-date">{{ formatDateTime(log.created_at) }}</div>
          </div>
          <span :class="['coin-amount', log.amount >= 0 ? 'coin-amount--plus' : 'coin-amount--minus']">
            {{ log.amount >= 0 ? '+' : '' }}{{ log.amount }}
          </span>
        </div>
        <button v-if="coinLogs.length > 5" class="btn-see-more" @click="showGoldModal = true">
          📜 See More ({{ coinLogs.length }} total)
        </button>
      </div>
    </div>

    <!-- Mana Received -->
    <div v-if="angelCoinReceipts.length > 0" class="section">
      <h2 class="section-title">✨ Mana Received</h2>
      <div class="mana-receipts">
        <div v-for="receipt in angelCoinReceipts" :key="receipt.id" class="mana-receipt-card">
          <div class="mana-receipt-icon">✨</div>
          <div class="mana-receipt-body">
            <div class="mana-receipt-text">{{ receipt.reason }}</div>
            <div class="mana-receipt-amount">+{{ receipt.amount }} 💰</div>
            <div class="mana-receipt-date">{{ formatDateTime(receipt.created_at) }}</div>
          </div>
        </div>
        <div class="balance-bar">
          <span>Your treasury</span>
          <span class="balance-value">💰 {{ myCoins }} Gold  &nbsp;|&nbsp; ✨ {{ myAngelCoins }} Mana</span>
        </div>
      </div>
    </div>

    <!-- Town Crier: Badge Awards -->
    <div class="section">
      <h2 class="section-title">📢 Town Crier</h2>
      <div v-if="recentAwards.length === 0" class="empty-state">
        <div class="empty-icon">📯</div>
        <p class="empty-text">No proclamations from the kingdom yet 🏰</p>
      </div>
      <div v-else class="award-announce-list">
        <div v-for="a in recentAwards.slice(0, 5)" :key="a.id" class="award-announce-card">
          <!-- Badge event -->
          <template v-if="a.type === 'badge'">
            <div class="award-announce-badge">
              <img v-if="a.badge_image" :src="a.badge_image" class="award-announce-img" />
              <span v-else class="award-announce-fb">🏅</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> received <strong>{{ a.badge_name }}</strong>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}{{ a.detail ? ` • by ${a.detail}` : '' }}
              </div>
            </div>
          </template>
          <!-- Mana event -->
          <template v-else-if="a.type === 'mana'">
            <div class="award-announce-badge mana-icon-circle">
              <span>✨</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} Mana</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Lucky Draw event -->
          <template v-else-if="a.type === 'lucky_draw'">
            <div class="award-announce-badge draw-icon-circle">
              <span>🎰</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> won <strong class="draw-highlight">{{ a.amount }} Gold</strong> from Lucky Draw!
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Magic Lottery event -->
          <template v-else-if="a.type === 'magic_lottery'">
            <div class="award-announce-badge lottery-icon-circle">
              <span>🎲</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> used <strong class="lottery-highlight">Magic Lottery</strong> — {{ a.reason }}
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
        </div>
        <button v-if="recentAwards.length > 5" class="btn-see-more" @click="showTownCrierModal = true">
          📯 See More ({{ recentAwards.length }} proclamations)
        </button>
      </div>
    </div>

    <!-- Gold Ledger Full Modal -->
    <div v-if="showGoldModal" class="badge-modal-overlay" @click.self="showGoldModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">💰 Gold Ledger ({{ coinLogs.length }})</h3>
        <div class="coin-list modal-coin-list">
          <div v-for="log in coinLogs.slice(0, 50)" :key="log.id" class="coin-item">
            <span class="coin-dot">{{ log.amount >= 0 ? '🟢' : '🔴' }}</span>
            <div class="coin-info">
              <div class="coin-reason">{{ log.reason }}</div>
              <div class="coin-date">{{ formatDateTime(log.created_at) }}</div>
            </div>
            <span :class="['coin-amount', log.amount >= 0 ? 'coin-amount--plus' : 'coin-amount--minus']">
              {{ log.amount >= 0 ? '+' : '' }}{{ log.amount }}
            </span>
          </div>
        </div>
        <button class="badge-modal-close" @click="showGoldModal = false">Close</button>
      </div>
    </div>

    <!-- Town Crier Full Modal -->
    <div v-if="showTownCrierModal" class="badge-modal-overlay" @click.self="showTownCrierModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">📢 Town Crier ({{ recentAwards.length }})</h3>
        <div class="award-announce-list modal-award-list">
          <div v-for="a in recentAwards.slice(0, 50)" :key="a.id" class="award-announce-card">
            <template v-if="a.type === 'badge'">
              <div class="award-announce-badge">
                <img v-if="a.badge_image" :src="a.badge_image" class="award-announce-img" />
                <span v-else class="award-announce-fb">🏅</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> received <strong>{{ a.badge_name }}</strong>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}{{ a.detail ? ` • by ${a.detail}` : '' }}
                </div>
              </div>
            </template>
            <template v-else-if="a.type === 'mana'">
              <div class="award-announce-badge mana-icon-circle">
                <span>✨</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} Mana</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Lucky Draw event -->
            <template v-else-if="a.type === 'lucky_draw'">
              <div class="award-announce-badge draw-icon-circle">
                <span>🎰</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> won <strong class="draw-highlight">{{ a.amount }} Gold</strong> from Lucky Draw!
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Magic Lottery event -->
            <template v-else-if="a.type === 'magic_lottery'">
              <div class="award-announce-badge lottery-icon-circle">
                <span>🎲</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> used <strong class="lottery-highlight">Magic Lottery</strong> — {{ a.reason }}
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
          </div>
        </div>
        <button class="badge-modal-close" @click="showTownCrierModal = false">Close</button>
      </div>
    </div>
    <div v-if="showBadgeModal" class="badge-modal-overlay" @click.self="showBadgeModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">🏅 My Badges ({{ myBadges.length }})</h3>
        <div class="badge-list">
          <div v-for="b in myBadges" :key="b.id" class="badge-list-item">
            <div class="badge-list-icon">
              <img v-if="b.badge_image" :src="b.badge_image" class="badge-list-img" />
              <span v-else class="badge-list-fallback">🏅</span>
            </div>
            <div class="badge-list-info">
              <div class="badge-list-name">{{ b.badge_name }}</div>
              <div class="badge-list-desc">{{ b.badge_description || '' }}</div>
              <div class="badge-list-stats" v-if="b.stat_str || b.stat_def || b.stat_luk">
                <span v-if="b.stat_str" class="mini-stat str">⚔️+{{ b.stat_str }}</span>
                <span v-if="b.stat_def" class="mini-stat def">🛡️+{{ b.stat_def }}</span>
                <span v-if="b.stat_luk" class="mini-stat luk">🍀+{{ b.stat_luk }}</span>
              </div>
              <div class="badge-list-date">Awarded {{ formatBadgeDate(b.awarded_at) }}{{ b.awarded_by ? ` by ${b.awarded_by}` : '' }}</div>
            </div>
          </div>
        </div>
        <button class="badge-modal-close" @click="showBadgeModal = false">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import api, {
  getPendingLeaveApprovals, getPendingRedemptionApprovals,
  approveLeave, rejectLeave,
  approveRedemption, rejectRedemption,
  getPendingWorkRequests, approveWorkRequest, rejectWorkRequest,
  getMyBadges, getRecentBadgeAwards, getMyStats,
} from '../../services/api'

export default {
  name: 'StaffHome',
  inject: ['showToast'],
  data() {
    return {
      userName: '',
      userImage: '',
      userPosition: '',
      pendingLeaves: [],
      pendingRedemptions: [],
      pendingWorkRequests: [],
      coinLogs: [],
      angelCoinReceipts: [],
      myCoins: 0,
      myAngelCoins: 0,
      myBadges: [],
      showBadgeModal: false,
      myStats: { total_str: 1, total_def: 1, total_luk: 1, base_str: 1, base_def: 1, base_luk: 1, badge_str: 0, badge_def: 0, badge_luk: 0 },
      recentAwards: [],
      showGoldModal: false,
      showTownCrierModal: false,
    }
  },
  async mounted() {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const u = JSON.parse(userStr)
      this.userName = [u.name, u.surname].filter(Boolean).join(' ') || 'Adventurer'
      this.userImage = u.image || ''
      this.userPosition = u.position || ''
    }
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const userStr = localStorage.getItem('user')
        const u = userStr ? JSON.parse(userStr) : {}

        const [lRes, rRes, wRes] = await Promise.all([
          getPendingLeaveApprovals().catch(() => ({ data: [] })),
          getPendingRedemptionApprovals().catch(() => ({ data: [] })),
          getPendingWorkRequests().catch(() => ({ data: [] })),
        ])
        this.pendingLeaves = lRes.data
        this.pendingRedemptions = rRes.data
        this.pendingWorkRequests = wRes.data

        const userId = u.id || u.user_id
        if (userId) {
          try {
            const [coinRes, userRes] = await Promise.all([
              api.get(`/api/users/${userId}/coin-logs`),
              api.get(`/api/users/${userId}`).catch(() => null),
            ])
            const allLogs = coinRes.data || []
            this.coinLogs = allLogs.slice(0, 50)
            this.angelCoinReceipts = allLogs.filter(l => l.reason && l.reason.includes('Received Angel Coins')).slice(0, 5)
            if (userRes && userRes.data) {
              this.myCoins = userRes.data.coins || 0
              this.myAngelCoins = userRes.data.angel_coins || 0
              this.userImage = userRes.data.image || this.userImage
              this.userPosition = userRes.data.position || this.userPosition
              this.userName = [userRes.data.name, userRes.data.surname].filter(Boolean).join(' ') || this.userName
              // Sync localStorage with latest data
              const stored = JSON.parse(localStorage.getItem('user') || '{}')
              stored.image = userRes.data.image
              stored.name = userRes.data.name
              stored.surname = userRes.data.surname
              stored.position = userRes.data.position
              localStorage.setItem('user', JSON.stringify(stored))
            }
          } catch (e) {
            this.coinLogs = []
          }
        }
      } catch (e) {
        console.error('Home load error:', e)
      }
      // Load badges and recent awards separately
      try {
        const [badgeRes, awardRes, statsRes] = await Promise.all([
          getMyBadges().catch(() => ({ data: [] })),
          getRecentBadgeAwards(50).catch(() => ({ data: [] })),
          getMyStats().catch(() => ({ data: this.myStats })),
        ])
        this.myBadges = badgeRes.data
        this.recentAwards = awardRes.data
        this.myStats = statsRes.data
      } catch (e) {
        this.myBadges = []
        this.recentAwards = []
      }
    },
    async handleApproveLeave(id) {
      try { await approveLeave(id); this.showToast('Quest accepted! ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectLeave(id) {
      try { await rejectLeave(id); this.showToast('Quest denied'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleApproveRedeem(id) {
      try { await approveRedemption(id); this.showToast('Trade approved! 🛒'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectRedeem(id) {
      try { await rejectRedemption(id); this.showToast('Trade rejected'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleApproveWorkRequest(id) {
      try { await approveWorkRequest(id); this.showToast('Mission accepted! Gold granted. ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectWorkRequest(id) {
      try { await rejectWorkRequest(id); this.showToast('Mission denied'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-GB') : '' },
    formatDateTime(d) {
      if (!d) return ''
      const dt = new Date(d)
      return dt.toLocaleDateString('en-GB') + ' ' + dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    },
    formatBadgeDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

/* Character Card */
.character-card {
  text-align: center;
  background: linear-gradient(145deg, rgba(44,24,16,0.9), rgba(26,26,46,0.95));
  border: 2px solid rgba(212,164,76,0.4);
  border-radius: 16px;
  padding: 28px 20px;
  margin-bottom: 28px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  position: relative;
  overflow: hidden;
}
.character-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, transparent, #d4a44c, transparent);
}

.character-portrait {
  width: 100px; height: 100px;
  margin: 0 auto 16px;
  position: relative;
}
.portrait-img {
  width: 100%; height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #d4a44c;
  box-shadow: 0 0 20px rgba(212,164,76,0.3);
}
.portrait-placeholder {
  width: 100%; height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  color: #1c1208; font-size: 36px; font-weight: 800;
  border: 3px solid #d4a44c;
  box-shadow: 0 0 20px rgba(212,164,76,0.3);
}

.character-name {
  font-family: 'Cinzel', serif;
  font-size: 22px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 2px;
}
.character-class {
  font-size: 13px; color: #b8860b;
  font-weight: 600; font-style: italic;
  margin-bottom: 16px;
}

/* Badge Row */
.badges-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 16px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 10px;
  transition: background .2s;
}
.badges-row:hover { background: rgba(212,164,76,0.08); }
.badge-circle {
  width: 36px; height: 36px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(212,164,76,0.3);
  transition: transform .2s;
}
.badge-circle:hover { transform: scale(1.15); }
.badge-circle-img { width: 100%; height: 100%; object-fit: cover; }
.badge-circle-fallback {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 16px;
}
.badge-more {
  font-size: 11px; color: #b8860b; font-weight: 700;
  padding: 2px 8px; background: rgba(212,164,76,0.1);
  border-radius: 8px;
}

/* Power Stats Row */
.power-row {
  display: flex; justify-content: center; gap: 12px;
  margin-bottom: 14px;
}
.power-item {
  font-size: 11px; font-weight: 700; padding: 3px 10px;
  border-radius: 8px; display: flex; align-items: center; gap: 3px;
}
.power-item.str { background: rgba(231,76,60,0.1); color: #e74c3c; }
.power-item.def { background: rgba(52,152,219,0.1); color: #3498db; }
.power-item.luk { background: rgba(46,204,113,0.1); color: #2ecc71; }
.power-val { font-size: 14px; font-weight: 800; margin-left: 2px; }
.power-icon { font-size: 12px; }

/* Badge Modal */
.badge-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}
.badge-modal {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 1px solid rgba(212,164,76,0.3); border-radius: 16px;
  padding: 24px; width: 100%; max-width: 400px; max-height: 80vh; overflow-y: auto;
}
.badge-modal-title {
  font-family: 'Cinzel', serif; font-size: 18px; color: #d4a44c; margin: 0 0 16px;
}
.badge-list-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid rgba(212,164,76,0.1);
}
.badge-list-item:last-child { border-bottom: none; }
.badge-list-icon { width: 44px; height: 44px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); }
.badge-list-img { width: 100%; height: 100%; object-fit: cover; }
.badge-list-fallback { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 20px; }
.badge-list-info { flex: 1; }
.badge-list-name { font-family: 'Cinzel', serif; font-size: 14px; font-weight: 700; color: #d4a44c; }
.badge-list-desc { font-size: 12px; color: #8b7355; }
.badge-list-date { font-size: 11px; color: #6b5a3e; margin-top: 2px; }
.badge-modal-close {
  margin-top: 16px; width: 100%; padding: 10px;
  background: rgba(212,164,76,0.1); color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.2); border-radius: 10px;
  cursor: pointer; font-weight: 700; font-size: 14px;
}
.badge-modal-close:hover { background: rgba(212,164,76,0.2); }
.badge-list-stats { display: flex; gap: 4px; margin-top: 3px; }
.mini-stat { font-size: 10px; padding: 1px 5px; border-radius: 5px; font-weight: 700; }
.mini-stat.str { background: rgba(231,76,60,0.15); color: #e74c3c; }
.mini-stat.def { background: rgba(52,152,219,0.15); color: #3498db; }
.mini-stat.luk { background: rgba(46,204,113,0.15); color: #2ecc71; }

/* Award Announcements (Town Crier) */
.award-announce-list { display: flex; flex-direction: column; gap: 8px; }
.award-announce-card {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(44,24,16,0.5);
  border: 1px solid rgba(212,164,76,0.08);
}
.award-announce-badge { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); }
.award-announce-img { width: 100%; height: 100%; object-fit: cover; }
.award-announce-fb { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 16px; }
.award-announce-body { flex: 1; }
.award-announce-text { font-size: 13px; color: #e8dcc8; }
.award-announce-text strong { color: #d4a44c; }
.award-announce-meta { font-size: 11px; color: #6b5a3e; margin-top: 2px; }
.mana-icon-circle {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.mana-highlight { color: #9b59b6; }
.draw-icon-circle {
  background: linear-gradient(135deg, #d4a44c, #b8860b);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.draw-highlight { color: #d4a44c; }
.lottery-icon-circle {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.lottery-highlight { color: #9b59b6; }

/* See More Button */
.btn-see-more {
  display: block; width: 100%; margin-top: 8px;
  padding: 8px; text-align: center;
  background: rgba(212,164,76,0.06);
  border: 1px dashed rgba(212,164,76,0.2);
  border-radius: 8px; color: #b8860b;
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all .2s;
}
.btn-see-more:hover { background: rgba(212,164,76,0.12); border-color: rgba(212,164,76,0.4); }

/* Modal list variants */
.modal-coin-list { max-height: 60vh; overflow-y: auto; }
.modal-award-list { max-height: 60vh; overflow-y: auto; }

/* Stats */
.stats-bar {
  display: flex;
  justify-content: center;
  gap: 24px;
  align-items: center;
}
.stat-item { text-align: center; }
.stat-value { font-size: 28px; font-weight: 800; display: block; line-height: 1.1; }
.stat-value.gold { color: #d4a44c; }
.stat-value.mana { color: #9b59b6; }
.stat-label { font-size: 11px; color: #8b7355; font-weight: 700; }
.stat-divider { width: 2px; height: 36px; background: rgba(212,164,76,0.2); border-radius: 1px; }

/* Sections */
.section { margin-bottom: 28px; }
.section-title {
  font-family: 'Cinzel', serif;
  font-size: 14px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #d4a44c;
  margin-bottom: 14px;
}

/* Quest Cards */
.quest-card {
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid;
  background: rgba(44,24,16,0.7);
  border-color: rgba(212,164,76,0.3);
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
  margin-bottom: 12px;
}
.quest-card--leave { border-color: #d4a44c; }
.quest-card--redeem { border-color: #9b59b6; }
.quest-card--work { border-color: #27ae60; }
.quest-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.quest-info { display: flex; align-items: center; gap: 10px; }
.quest-emoji { font-size: 24px; }
.quest-name { font-weight: 700; font-size: 14px; color: #e8d5b7; }
.quest-type { font-size: 11px; color: #8b7355; font-weight: 700; text-transform: uppercase; }
.quest-detail { font-size: 13px; color: #b8a080; margin-bottom: 4px; }
.quest-badge {
  padding: 2px 10px; border-radius: 6px;
  font-size: 10px; font-weight: 800; text-transform: uppercase;
  background: rgba(212,164,76,0.15); color: #d4a44c; border: 1px solid rgba(212,164,76,0.3);
}
.quest-actions { display: flex; gap: 10px; margin-top: 12px; }
.btn-approve {
  flex: 1; padding: 10px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700;
  color: #fff; background: linear-gradient(135deg, #1e8449, #27ae60);
  border: 1px solid #2ecc71; cursor: pointer; transition: all 0.15s;
}
.btn-approve:active { transform: scale(0.97); }
.btn-reject {
  flex: 1; padding: 10px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700;
  color: #e74c3c; background: rgba(192,57,43,0.15);
  border: 1px solid rgba(192,57,43,0.3); cursor: pointer; transition: all 0.15s;
}
.btn-reject:active { transform: scale(0.97); }

/* Empty State */
.empty-state {
  padding: 32px 16px; text-align: center;
  border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

/* Gold List */
.coin-list { display: flex; flex-direction: column; gap: 8px; }
.coin-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 10px;
  background: rgba(44,24,16,0.6);
  border: 1px solid rgba(212,164,76,0.1);
}
.coin-dot { font-size: 18px; flex-shrink: 0; }
.coin-info { flex: 1; min-width: 0; }
.coin-reason { font-weight: 700; font-size: 14px; color: #e8d5b7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.coin-date { font-size: 11px; color: #8b7355; }
.coin-amount { font-weight: 800; font-size: 14px; flex-shrink: 0; }
.coin-amount--plus { color: #27ae60; }
.coin-amount--minus { color: #e74c3c; }

/* Mana Receipts */
.mana-receipts { display: flex; flex-direction: column; gap: 10px; }
.mana-receipt-card {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 14px 16px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(155,89,182,0.15), rgba(142,68,173,0.1));
  border: 1px solid rgba(155,89,182,0.2);
}
.mana-receipt-icon { font-size: 28px; flex-shrink: 0; }
.mana-receipt-body { flex: 1; min-width: 0; }
.mana-receipt-text { font-weight: 700; font-size: 14px; color: #c39bd3; margin-bottom: 2px; }
.mana-receipt-amount { font-weight: 800; font-size: 15px; color: #27ae60; }
.mana-receipt-date { font-size: 11px; color: #9b59b6; margin-top: 2px; }
.balance-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 16px; border-radius: 8px;
  background: rgba(212,164,76,0.08);
  border: 1px solid rgba(212,164,76,0.15);
  font-size: 13px; font-weight: 700; color: #8b7355;
}
.balance-value { color: #d4a44c; }
</style>
