<template>
  <div class="staff-page">
    <h1 class="page-title">🛒 Item Shop</h1>

    <!-- Dual Balance Banner -->
    <div class="balance-row">
      <!-- Gold -->
      <div class="balance-card balance-card--gold">
        <div class="balance-inner">
          <p class="balance-label">Gold</p>
          <h2 class="balance-value">{{ myCoins }} <span class="balance-emoji">💰</span></h2>
          <p class="balance-hint">Use to acquire items</p>
        </div>
      </div>

      <!-- Mana -->
      <div class="balance-card balance-card--mana" @click="openSendModal">
        <div class="balance-inner">
          <p class="balance-label">Mana</p>
          <h2 class="balance-value">{{ myAngelCoins }} <span class="balance-emoji">✨</span></h2>
          <p class="balance-hint">Tap to gift</p>
        </div>
        <div class="tap-indicator">
          <span>Gift →</span>
        </div>
      </div>
    </div>

    <!-- Item Catalog -->
    <h3 class="section-title">⚔️ Available Items</h3>
    <div class="reward-grid">
      <div v-for="reward in rewards" :key="reward.id" class="reward-card">
        <div class="reward-img-wrap">
          <img v-if="reward.image" :src="reward.image" class="reward-img" />
          <div v-else class="reward-img-placeholder">🛡️</div>
          <div class="reward-cost-badge">{{ reward.point_cost }} 💰</div>
        </div>
        <div class="reward-body">
          <h3 class="reward-name">{{ reward.name }}</h3>
          <p class="reward-desc">{{ reward.description }}</p>
          <button class="redeem-btn"
              :class="myCoins >= reward.point_cost ? 'redeem-btn--active' : 'redeem-btn--disabled'"
              :disabled="myCoins < reward.point_cost || redeeming"
              @click="initiateRedeem(reward)">
              {{ myCoins >= reward.point_cost ? 'Acquire Item' : 'Not enough gold' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="rewards.length === 0" class="empty-state">
      <span class="empty-icon">🛒</span>
      <p class="empty-text">The merchant has no wares today</p>
    </div>

    <!-- Inventory (My Coupons) -->
    <h3 v-if="myRedemptions.length > 0" class="section-title" style="margin-top: 32px;">🎒 Your Inventory</h3>
    <div v-if="myRedemptions.length > 0" class="coupon-list">
      <div v-for="rd in myRedemptions" :key="rd.id"
           :class="['coupon-card', rd.status === 'completed' ? 'coupon-card--done' : '', rd.status === 'rejected' ? 'coupon-card--rejected' : '']">
        <div class="coupon-img">
          <img v-if="rd.reward && rd.reward.image" :src="rd.reward.image" />
          <div v-else class="coupon-img-placeholder">🛡️</div>
        </div>
        <div class="coupon-info">
          <div class="coupon-name">{{ rd.reward ? rd.reward.name : 'Item' }}</div>
          <div class="coupon-date">{{ formatDate(rd.created_at) }}</div>
        </div>
        <span v-if="rd.status === 'pending'" class="coupon-status coupon-status--pending">⏳ Pending</span>
        <span v-else-if="rd.status === 'completed'" class="coupon-status coupon-status--done">✅ Acquired</span>
        <span v-else-if="rd.status === 'rejected'" class="coupon-status coupon-status--rejected">❌ Denied</span>
        <span v-else class="coupon-status">{{ rd.status }}</span>
      </div>
    </div>

    <!-- Redeem Confirmation Modal -->
    <div v-if="confirmReward" class="modal-overlay" @click.self="confirmReward = null">
      <div class="modal-card">
        <div class="modal-reward-img">
          <img v-if="confirmReward.image" :src="confirmReward.image" />
          <div v-else class="modal-reward-img-placeholder">🛡️</div>
        </div>
        <h3 class="modal-title">{{ confirmReward.name }}</h3>
        <p v-if="confirmReward.description" class="modal-reward-detail">{{ confirmReward.description }}</p>
        <div class="modal-cost-badge">{{ confirmReward.point_cost }} 💰</div>
        <p class="modal-desc" style="margin-top: 12px;">
          Acquire this item? This will cost <span class="text-gold">{{ confirmReward.point_cost }} gold</span>.
        </p>
        <div class="modal-actions">
          <button class="modal-btn modal-btn--cancel" @click="confirmReward = null">Decline</button>
          <button class="modal-btn modal-btn--confirm" @click="processRedeem" :disabled="redeeming">
            {{ redeeming ? 'Processing...' : '⚔️ Acquire' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Send Mana Modal -->
    <div v-if="showSendModal" class="modal-overlay" @click.self="closeSendModal">
      <div class="modal-card modal-card--mana">
        <div class="modal-icon-wrap">✨</div>
        <h3 class="modal-title">Gift Mana</h3>
        <p class="modal-desc">
          Your Mana becomes <strong>Gold</strong> for the recipient!
        </p>

        <div class="form-group">
          <label class="form-label">Recipient</label>
          <select v-model="sendForm.recipientId" class="form-select">
            <option value="" disabled>Select an adventurer…</option>
            <option v-for="s in staffList" :key="s.id" :value="s.id">
              {{ s.name }} {{ s.department ? `(${s.department})` : '' }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Amount</label>
          <input v-model.number="sendForm.amount" type="number" min="1" :max="myAngelCoins"
                 class="form-input" placeholder="How much mana?" />
          <p class="form-hint">Available: {{ myAngelCoins }} ✨</p>
        </div>

        <div class="form-group">
          <label class="form-label">Message (optional)</label>
          <textarea v-model="sendForm.comment" class="form-textarea"
                    placeholder="Write a scroll message…" rows="2"></textarea>
        </div>

        <div class="modal-actions">
          <button class="modal-btn modal-btn--cancel" @click="closeSendModal">Cancel</button>
          <button class="modal-btn modal-btn--mana-confirm"
                  @click="processSend"
                  :disabled="!canSend || sending">
            {{ sending ? 'Sending...' : 'Gift ✨' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api, { getRewards, redeemReward, getMyRedemptions, sendAngelCoins, getStaffList } from '../../services/api'

export default {
    inject: ['showToast'],
    data() {
        return {
            myCoins: 0,
            myAngelCoins: 0,
            rewards: [],
            myRedemptions: [],
            redeeming: false,
            confirmReward: null,
            showSendModal: false,
            sending: false,
            staffList: [],
            sendForm: {
                recipientId: '',
                amount: 1,
                comment: '',
            },
        }
    },
    computed: {
        canSend() {
            return this.sendForm.recipientId
                && this.sendForm.amount > 0
                && this.sendForm.amount <= this.myAngelCoins
        }
    },
    async mounted() { await this.refreshData() },
    methods: {
        async refreshData() {
            try {
                const userRes = await api.get('/api/users/me')
                this.myCoins = userRes.data.coins || 0
                this.myAngelCoins = userRes.data.angel_coins || 0
                const rewardsRes = await getRewards()
                this.rewards = rewardsRes.data
                try {
                    const { data: rdData } = await getMyRedemptions()
                    this.myRedemptions = rdData
                } catch (_) { this.myRedemptions = [] }
            } catch (e) { console.error("Load failed", e) }
        },
        initiateRedeem(reward) { this.confirmReward = reward },
        async processRedeem() {
            if (!this.confirmReward) return
            this.redeeming = true
            try {
                await redeemReward({ reward_id: this.confirmReward.id })
                this.showToast('Item acquired! Check your inventory. ⚔️')
                this.confirmReward = null
                await this.refreshData()
            } catch (e) {
                this.showToast(e.response?.data?.detail || 'Trade failed', 'error')
            } finally { this.redeeming = false }
        },
        async openSendModal() {
            if (this.myAngelCoins <= 0) {
                this.showToast('You have no Mana to gift', 'error')
                return
            }
            this.sendForm = { recipientId: '', amount: 1, comment: '' }
            try {
                const res = await getStaffList()
                this.staffList = res.data
            } catch (e) {
                console.error("Failed to load adventurer list", e)
                this.staffList = []
            }
            this.showSendModal = true
        },
        closeSendModal() {
            this.showSendModal = false
        },
        async processSend() {
            if (!this.canSend) return
            this.sending = true
            try {
                await sendAngelCoins({
                    recipient_id: this.sendForm.recipientId,
                    amount: this.sendForm.amount,
                    comment: this.sendForm.comment,
                })
                const recipient = this.staffList.find(s => s.id === this.sendForm.recipientId)
                this.showToast(`Gifted ${this.sendForm.amount} Mana to ${recipient?.name || 'adventurer'}! ✨`)
                this.closeSendModal()
                await this.refreshData()
            } catch (e) {
                this.showToast(e.response?.data?.detail || 'Gift failed', 'error')
            } finally { this.sending = false }
        },
        formatDate(dt) {
            if (!dt) return ''
            return new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
        },
    }
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 20px;
}

/* Dual Balance */
.balance-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 28px; }
.balance-card {
  border-radius: 12px; padding: 22px 18px;
  color: #fff; position: relative; overflow: hidden;
  border: 2px solid;
}
.balance-card--gold {
  background: linear-gradient(135deg, rgba(184,134,11,0.3), rgba(212,164,76,0.15));
  border-color: rgba(212,164,76,0.4);
}
.balance-card--mana {
  background: linear-gradient(135deg, rgba(155,89,182,0.3), rgba(142,68,173,0.15));
  border-color: rgba(155,89,182,0.4);
  cursor: pointer; transition: all 0.2s;
}
.balance-card--mana:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 36px rgba(155,89,182,0.2);
}
.balance-inner { position: relative; z-index: 1; }
.balance-label { font-family: 'Cinzel', serif; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85; margin-bottom: 4px; }
.balance-value { font-size: 32px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
.balance-emoji { font-size: 20px; }
.balance-hint { font-size: 11px; opacity: 0.7; margin-top: 6px; font-weight: 500; }
.tap-indicator { position: absolute; bottom: 10px; right: 14px; font-size: 11px; font-weight: 700; opacity: 0.6; z-index: 1; }

/* Section */
.section-title {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 800;
  color: #d4a44c; margin-bottom: 16px;
}

/* Item Grid */
.reward-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.reward-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border-radius: 12px; overflow: hidden;
  border: 2px solid rgba(212,164,76,0.15);
  transition: all 0.2s;
}
.reward-card:hover { transform: translateY(-2px); border-color: rgba(212,164,76,0.3); box-shadow: 0 8px 24px rgba(212,164,76,0.1); }
.reward-img-wrap { height: 120px; position: relative; overflow: hidden; background: rgba(26,26,46,0.5); }
.reward-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s; }
.reward-card:hover .reward-img { transform: scale(1.06); }
.reward-img-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 40px; background: linear-gradient(135deg, rgba(212,164,76,0.1), rgba(155,89,182,0.1));
}
.reward-cost-badge {
  position: absolute; top: 8px; right: 8px;
  background: rgba(26,26,46,0.85); backdrop-filter: blur(6px);
  padding: 3px 10px; border-radius: 6px;
  font-size: 12px; font-weight: 700; color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.3);
}
.reward-body { padding: 14px; }
.reward-name { font-weight: 700; font-size: 15px; color: #e8d5b7; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.reward-desc { font-size: 12px; color: #8b7355; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 32px; }

.redeem-btn {
  width: 100%; padding: 10px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700;
  border: 2px solid; cursor: pointer; transition: all 0.15s;
}
.redeem-btn:active { transform: scale(0.97); }
.redeem-btn--active {
  color: var(--wood-dark, #2c1810);
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  border-color: #d4a44c;
  box-shadow: 0 3px 12px rgba(212,164,76,0.2);
}
.redeem-btn--disabled { color: #8b7355; background: transparent; border-color: rgba(139,115,85,0.2); cursor: not-allowed; }

/* Empty */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 16px; border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; padding: 24px;
  animation: fadeIn 0.25s ease-out;
}
.modal-card {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 2px solid #d4a44c;
  border-radius: 16px; padding: 32px 24px; max-width: 380px; width: 100%;
  box-shadow: 0 24px 64px rgba(0,0,0,0.4);
  text-align: center;
}
.modal-card--mana {
  border-color: #9b59b6;
  text-align: left;
}
.modal-card--mana .modal-title,
.modal-card--mana .modal-desc {
  text-align: center;
}
.modal-icon-wrap {
  width: 60px; height: 60px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px; font-size: 28px;
  background: rgba(155,89,182,0.15);
  border: 2px solid rgba(155,89,182,0.3);
}
.modal-title { font-family: 'Cinzel', serif; font-size: 20px; font-weight: 800; color: #d4a44c; margin-bottom: 8px; }
.modal-desc { font-size: 14px; color: #8b7355; margin-bottom: 24px; }

.modal-reward-img {
  width: 100%; height: 160px; border-radius: 12px;
  overflow: hidden; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(212,164,76,0.1), rgba(155,89,182,0.1));
}
.modal-reward-img img { width: 100%; height: 100%; object-fit: cover; }
.modal-reward-img-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 48px;
}
.modal-reward-detail { font-size: 13px; color: #8b7355; margin-bottom: 12px; line-height: 1.5; }
.modal-cost-badge {
  display: inline-block;
  background: rgba(212,164,76,0.1);
  border: 2px solid rgba(212,164,76,0.3);
  padding: 6px 16px; border-radius: 8px;
  font-size: 16px; font-weight: 800; color: #d4a44c;
}

.text-gold { color: #d4a44c; font-weight: 700; }
.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.modal-btn {
  padding: 12px 0; border-radius: 8px; font-weight: 700; font-size: 14px;
  border: 2px solid transparent; cursor: pointer; transition: all 0.15s;
}
.modal-btn:active { transform: scale(0.97); }
.modal-btn--cancel { color: #8b7355; background: transparent; border-color: rgba(139,115,85,0.2); }
.modal-btn--cancel:hover { background: rgba(212,164,76,0.05); }
.modal-btn--confirm {
  color: #1c1208;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  border-color: #d4a44c;
  box-shadow: 0 4px 16px rgba(212,164,76,0.2);
}
.modal-btn--mana-confirm {
  color: #fff;
  background: linear-gradient(135deg, #7b2d8e, #9b59b6);
  border-color: #9b59b6;
  box-shadow: 0 4px 16px rgba(155,89,182,0.3);
}
.modal-btn--mana-confirm:disabled { opacity: 0.5; cursor: not-allowed; }

/* Form Elements */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 13px; font-weight: 700; color: #d4a44c; margin-bottom: 6px; }
.form-select,
.form-input,
.form-textarea {
  width: 100%; padding: 12px 14px;
  border-radius: 8px; border: 2px solid rgba(212,164,76,0.2);
  font-size: 14px; font-weight: 500;
  color: #e8d5b7; background: rgba(26,26,46,0.8);
  outline: none; transition: border-color 0.2s; box-sizing: border-box;
}
.form-select:focus,
.form-input:focus,
.form-textarea:focus { border-color: #d4a44c; background: rgba(26,26,46,0.95); }
.form-textarea { resize: none; font-family: inherit; }
.form-hint { font-size: 11px; color: #8b7355; margin-top: 4px; font-weight: 500; }
.form-select option { background: #1a1a2e; color: #e8d5b7; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* Coupon Cards */
.coupon-list { display: flex; flex-direction: column; gap: 10px; }
.coupon-card {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.6), rgba(26,26,46,0.7));
  border-radius: 10px; border: 1px solid rgba(212,164,76,0.15);
  transition: all 0.2s;
}
.coupon-card--done { opacity: 0.5; filter: grayscale(0.6); }
.coupon-card--rejected { opacity: 0.4; filter: grayscale(0.8); }
.coupon-img {
  width: 48px; height: 48px; border-radius: 8px;
  overflow: hidden; flex-shrink: 0;
  background: rgba(212,164,76,0.1);
  display: flex; align-items: center; justify-content: center;
}
.coupon-img img { width: 100%; height: 100%; object-fit: cover; }
.coupon-img-placeholder { font-size: 22px; }
.coupon-info { flex: 1; min-width: 0; }
.coupon-name { font-weight: 700; color: #e8d5b7; font-size: 14px; }
.coupon-date { font-size: 11px; color: #8b7355; font-weight: 500; }
.coupon-status {
  font-size: 11px; font-weight: 700;
  padding: 4px 10px; border-radius: 6px; flex-shrink: 0;
}
.coupon-status--pending { background: rgba(212,164,76,0.15); color: #d4a44c; }
.coupon-status--done { background: rgba(39,174,96,0.15); color: #27ae60; }
.coupon-status--rejected { background: rgba(192,57,43,0.15); color: #e74c3c; }
</style>
