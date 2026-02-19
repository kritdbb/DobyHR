<template>
  <div class="staff-page">
    <div class="bs-header">
      <router-link to="/staff/services" class="bs-back">← Back</router-link>
      <h1 class="page-title">🏪 Badge Shop</h1>
      <p class="page-sub">Collect powerful badges to boost your stats</p>
      <div class="bs-balances">
        <span class="bal gold">💰 {{ balances.gold }} Gold</span>
        <span class="bal mana">✨ {{ balances.mana }} Mana</span>
        <span class="bal ty">💌 {{ balances.thankyou }} Thank You</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bs-loading">
      <div class="spinner"></div>
      <span>Loading shop...</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="!catalog.length" class="bs-empty">
      <div class="bs-empty-icon">🏪</div>
      <p>No badges for sale yet</p>
      <p class="bs-empty-sub">Check back later, adventurer!</p>
    </div>

    <!-- Badge Catalog grouped by currency -->
    <template v-else>
      <!-- Gold Items -->
      <div v-if="goldItems.length" class="bs-section">
        <h2 class="bs-section-title">💰 Gold Badges</h2>
        <div class="bs-grid">
          <div v-for="item in goldItems" :key="item.id"
               class="bs-card" :class="{ 'bs-card--owned': item.owned }">
            <div class="bs-card-img">
              <img v-if="item.badge_image" :src="item.badge_image" />
              <span v-else class="bs-card-icon">🏅</span>
              <span v-if="item.owned" class="bs-owned-tag">✓ Owned</span>
            </div>
            <div class="bs-card-name">{{ item.badge_name }}</div>
            <div class="bs-card-desc" v-if="item.badge_description">{{ item.badge_description }}</div>
            <div class="bs-card-stats" v-if="item.badge_stat_str || item.badge_stat_def || item.badge_stat_luk">
              <span v-if="item.badge_stat_str" class="st str">⚔️ +{{ item.badge_stat_str }}</span>
              <span v-if="item.badge_stat_def" class="st def">🛡️ +{{ item.badge_stat_def }}</span>
              <span v-if="item.badge_stat_luk" class="st luk">🍀 +{{ item.badge_stat_luk }}</span>
            </div>
            <div class="bs-card-footer">
              <span class="bs-price">💰 {{ item.price_amount }}</span>
              <span v-if="item.remaining !== null" class="bs-stock">{{ item.remaining }} left</span>
            </div>
            <button class="bs-buy-btn" :disabled="item.owned || buying === item.id"
                    @click="confirmBuy(item)">
              {{ buying === item.id ? 'Buying...' : (item.owned ? 'Owned' : '🛒 Buy') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Mana Items -->
      <div v-if="manaItems.length" class="bs-section">
        <h2 class="bs-section-title">✨ Mana Badges</h2>
        <div class="bs-grid">
          <div v-for="item in manaItems" :key="item.id"
               class="bs-card" :class="{ 'bs-card--owned': item.owned }">
            <div class="bs-card-img">
              <img v-if="item.badge_image" :src="item.badge_image" />
              <span v-else class="bs-card-icon">🏅</span>
              <span v-if="item.owned" class="bs-owned-tag">✓ Owned</span>
            </div>
            <div class="bs-card-name">{{ item.badge_name }}</div>
            <div class="bs-card-desc" v-if="item.badge_description">{{ item.badge_description }}</div>
            <div class="bs-card-stats" v-if="item.badge_stat_str || item.badge_stat_def || item.badge_stat_luk">
              <span v-if="item.badge_stat_str" class="st str">⚔️ +{{ item.badge_stat_str }}</span>
              <span v-if="item.badge_stat_def" class="st def">🛡️ +{{ item.badge_stat_def }}</span>
              <span v-if="item.badge_stat_luk" class="st luk">🍀 +{{ item.badge_stat_luk }}</span>
            </div>
            <div class="bs-card-footer">
              <span class="bs-price">✨ {{ item.price_amount }}</span>
              <span v-if="item.remaining !== null" class="bs-stock">{{ item.remaining }} left</span>
            </div>
            <button class="bs-buy-btn bs-buy-btn--mana" :disabled="item.owned || buying === item.id"
                    @click="confirmBuy(item)">
              {{ buying === item.id ? 'Buying...' : (item.owned ? 'Owned' : '🛒 Buy') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Thank You Items -->
      <div v-if="tyItems.length" class="bs-section">
        <h2 class="bs-section-title">💌 Thank You Badges</h2>
        <div class="bs-grid">
          <div v-for="item in tyItems" :key="item.id"
               class="bs-card" :class="{ 'bs-card--owned': item.owned }">
            <div class="bs-card-img">
              <img v-if="item.badge_image" :src="item.badge_image" />
              <span v-else class="bs-card-icon">🏅</span>
              <span v-if="item.owned" class="bs-owned-tag">✓ Owned</span>
            </div>
            <div class="bs-card-name">{{ item.badge_name }}</div>
            <div class="bs-card-desc" v-if="item.badge_description">{{ item.badge_description }}</div>
            <div class="bs-card-stats" v-if="item.badge_stat_str || item.badge_stat_def || item.badge_stat_luk">
              <span v-if="item.badge_stat_str" class="st str">⚔️ +{{ item.badge_stat_str }}</span>
              <span v-if="item.badge_stat_def" class="st def">🛡️ +{{ item.badge_stat_def }}</span>
              <span v-if="item.badge_stat_luk" class="st luk">🍀 +{{ item.badge_stat_luk }}</span>
            </div>
            <div class="bs-card-footer">
              <span class="bs-price">💌 {{ item.price_amount }}</span>
              <span v-if="item.remaining !== null" class="bs-stock">{{ item.remaining }} left</span>
            </div>
            <button class="bs-buy-btn bs-buy-btn--ty" :disabled="item.owned || buying === item.id"
                    @click="confirmBuy(item)">
              {{ buying === item.id ? 'Buying...' : (item.owned ? 'Owned' : '🛒 Buy') }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Purchase History -->
    <div v-if="purchases.length" class="bs-section">
      <h2 class="bs-section-title" style="margin-top: 16px;">📜 Purchase History</h2>
      <div class="bs-history">
        <div v-for="p in purchases" :key="p.id" class="bs-history-row">
          <img v-if="p.badge_image" :src="p.badge_image" class="bs-history-img" />
          <span v-else class="bs-history-icon">🏅</span>
          <div class="bs-history-info">
            <span class="bs-history-name">{{ p.badge_name }}</span>
            <span class="bs-history-meta">
              {{ priceIcon(p.price_type) }} {{ p.price_amount }} · {{ formatDate(p.purchased_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="confirmItem" class="modal-overlay" @click.self="confirmItem = null">
      <div class="modal-card">
        <div class="modal-badge-img">
          <img v-if="confirmItem.badge_image" :src="confirmItem.badge_image" />
          <span v-else class="modal-badge-icon">🏅</span>
        </div>
        <h3 class="modal-title">Purchase "{{ confirmItem.badge_name }}"?</h3>
        <div class="modal-price">
          {{ priceIcon(confirmItem.price_type) }} {{ confirmItem.price_amount }}
          {{ priceLabel(confirmItem.price_type) }}
        </div>
        <div class="modal-stats" v-if="confirmItem.badge_stat_str || confirmItem.badge_stat_def || confirmItem.badge_stat_luk">
          <span v-if="confirmItem.badge_stat_str">⚔️ STR +{{ confirmItem.badge_stat_str }}</span>
          <span v-if="confirmItem.badge_stat_def">🛡️ DEF +{{ confirmItem.badge_stat_def }}</span>
          <span v-if="confirmItem.badge_stat_luk">🍀 LUK +{{ confirmItem.badge_stat_luk }}</span>
        </div>
        <div class="modal-actions">
          <button class="modal-btn modal-btn--cancel" @click="confirmItem = null">Cancel</button>
          <button class="modal-btn modal-btn--confirm" @click="processBuy" :disabled="buying">
            {{ buying ? 'Processing...' : '⚔️ Acquire' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getBadgeShopCatalog, buyBadgeShopItem, getMyBadgeShopPurchases } from '../../services/api'

export default {
  name: 'BadgeShop',
  inject: ['showToast'],
  data() {
    return {
      loading: true,
      catalog: [],
      balances: { gold: 0, mana: 0, thankyou: 0 },
      purchases: [],
      buying: null,
      confirmItem: null,
    }
  },
  computed: {
    goldItems() { return this.catalog.filter(i => i.price_type === 'gold') },
    manaItems() { return this.catalog.filter(i => i.price_type === 'mana') },
    tyItems() { return this.catalog.filter(i => i.price_type === 'thankyou') },
  },
  async mounted() {
    await this.refreshData()
  },
  methods: {
    async refreshData() {
      this.loading = true
      try {
        const [catRes, purRes] = await Promise.all([
          getBadgeShopCatalog(),
          getMyBadgeShopPurchases(),
        ])
        this.catalog = catRes.data.items || []
        this.balances = catRes.data.balances || { gold: 0, mana: 0, thankyou: 0 }
        this.purchases = purRes.data || []
      } catch (e) {
        console.error('Badge Shop load error', e)
      } finally {
        this.loading = false
      }
    },
    confirmBuy(item) {
      if (item.owned) return
      this.confirmItem = item
    },
    async processBuy() {
      if (!this.confirmItem) return
      this.buying = this.confirmItem.id
      try {
        const { data } = await buyBadgeShopItem(this.confirmItem.id)
        if (this.showToast) this.showToast(data.message || 'Badge purchased!', 'success')
        this.confirmItem = null
        await this.refreshData()
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        if (this.showToast) this.showToast(msg, 'error')
        else alert(msg)
      } finally {
        this.buying = null
      }
    },
    priceIcon(type) {
      return { gold: '💰', mana: '✨', thankyou: '💌' }[type] || '💰'
    },
    priceLabel(type) {
      return { gold: 'Gold', mana: 'Mana', thankyou: 'Thank You Cards' }[type] || ''
    },
    formatDate(dt) {
      if (!dt) return ''
      const d = new Date(dt)
      return d.toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' })
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.bs-header { margin-bottom: 24px; }
.bs-back {
  display: inline-block;
  color: #8b7355;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 8px;
  transition: color 0.2s;
}
.bs-back:hover { color: #d4a44c; }

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
  font-style: italic;
  margin-bottom: 12px;
}

.bs-balances {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.bal {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid rgba(255,255,255,0.1);
}
.bal.gold { background: rgba(212,164,76,0.15); color: #d4a44c; border-color: rgba(212,164,76,0.3); }
.bal.mana { background: rgba(100,150,255,0.12); color: #7db4ff; border-color: rgba(100,150,255,0.25); }
.bal.ty   { background: rgba(255,150,180,0.12); color: #ffb0c8; border-color: rgba(255,150,180,0.25); }

/* Loading */
.bs-loading {
  text-align: center;
  padding: 60px 0;
  color: #8b7355;
  font-size: 14px;
}
.spinner {
  width: 32px; height: 32px;
  border: 3px solid rgba(212,164,76,0.2);
  border-top-color: #d4a44c;
  border-radius: 50%;
  margin: 0 auto 12px;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Empty */
.bs-empty {
  text-align: center;
  padding: 60px 0;
  color: #8b7355;
}
.bs-empty-icon { font-size: 48px; margin-bottom: 12px; }
.bs-empty-sub { font-size: 12px; opacity: 0.7; }

/* Section */
.bs-section { margin-bottom: 28px; }
.bs-section-title {
  font-family: 'Cinzel', serif;
  font-size: 18px;
  font-weight: 700;
  color: #e8d5b7;
  margin-bottom: 14px;
}

/* Grid */
.bs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* Card */
.bs-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.92));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 16px 12px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.25s ease;
  position: relative;
}
.bs-card:hover {
  border-color: rgba(212,164,76,0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.bs-card--owned {
  opacity: 0.6;
  border-color: rgba(100,200,100,0.3);
}
.bs-card--owned:hover { transform: none; }

.bs-card-img {
  position: relative;
  width: 64px; height: 64px;
  margin-bottom: 10px;
}
.bs-card-img img {
  width: 64px; height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(212,164,76,0.4);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.bs-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px; height: 64px;
  border-radius: 50%;
  background: rgba(212,164,76,0.1);
  border: 2px solid rgba(212,164,76,0.2);
  font-size: 28px;
}
.bs-owned-tag {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(46,139,87,0.9);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 8px;
  border-radius: 8px;
  white-space: nowrap;
}

.bs-card-name {
  font-family: 'Cinzel', serif;
  font-weight: 700;
  font-size: 13px;
  color: #e8d5b7;
  margin-bottom: 4px;
  line-height: 1.3;
}
.bs-card-desc {
  font-size: 11px;
  color: #8b7355;
  line-height: 1.3;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bs-card-stats {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.st {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(255,255,255,0.05);
}
.st.str { color: #e74c3c; }
.st.def { color: #3498db; }
.st.luk { color: #2ecc71; }

.bs-card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.bs-price {
  font-size: 14px;
  font-weight: 800;
  color: #d4a44c;
}
.bs-stock {
  font-size: 11px;
  color: #8b7355;
  font-style: italic;
}

.bs-buy-btn {
  width: 100%;
  padding: 8px 0;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #d4a44c, #b8862d);
  color: #1a1a2e;
  font-family: 'Cinzel', serif;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.bs-buy-btn:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(212,164,76,0.3);
}
.bs-buy-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.bs-buy-btn--mana {
  background: linear-gradient(135deg, #5b8def, #3a6cd4);
  color: #fff;
}
.bs-buy-btn--ty {
  background: linear-gradient(135deg, #e77c9c, #c44d6e);
  color: #fff;
}

/* History */
.bs-history {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bs-history-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(44,24,16,0.6);
  border: 1px solid rgba(212,164,76,0.1);
}
.bs-history-img {
  width: 36px; height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(212,164,76,0.3);
}
.bs-history-icon { font-size: 24px; }
.bs-history-info {
  display: flex;
  flex-direction: column;
}
.bs-history-name {
  font-weight: 700;
  font-size: 13px;
  color: #e8d5b7;
}
.bs-history-meta {
  font-size: 11px;
  color: #8b7355;
}

/* Confirmation Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.modal-card {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 2px solid rgba(212,164,76,0.3);
  border-radius: 16px;
  padding: 28px 24px 20px;
  max-width: 340px;
  width: 100%;
  text-align: center;
  animation: modalIn 0.3s ease;
}
@keyframes modalIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-badge-img { margin-bottom: 14px; }
.modal-badge-img img {
  width: 80px; height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(212,164,76,0.4);
  box-shadow: 0 4px 20px rgba(212,164,76,0.2);
}
.modal-badge-icon { font-size: 56px; }

.modal-title {
  font-family: 'Cinzel', serif;
  font-size: 18px;
  font-weight: 700;
  color: #e8d5b7;
  margin-bottom: 8px;
}
.modal-price {
  font-size: 16px;
  font-weight: 800;
  color: #d4a44c;
  margin-bottom: 8px;
}
.modal-stats {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 16px;
  font-size: 13px;
  font-weight: 600;
  color: #aaa;
}
.modal-actions {
  display: flex;
  gap: 10px;
}
.modal-btn {
  flex: 1;
  padding: 10px 0;
  border: none;
  border-radius: 8px;
  font-family: 'Cinzel', serif;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.modal-btn--cancel {
  background: rgba(255,255,255,0.08);
  color: #8b7355;
  border: 1px solid rgba(255,255,255,0.1);
}
.modal-btn--cancel:hover { background: rgba(255,255,255,0.12); }
.modal-btn--confirm {
  background: linear-gradient(135deg, #d4a44c, #b8862d);
  color: #1a1a2e;
}
.modal-btn--confirm:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(212,164,76,0.35);
}
.modal-btn--confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
