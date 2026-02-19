<template>
  <div class="admin-page">
    <div class="page-header-bar">
      <div>
        <h1 class="page-title">🏪 Badge Shop Manager</h1>
        <p class="page-sub">List badges for sale with Gold, Mana, or Thank You Cards</p>
      </div>
      <button class="btn-create" @click="openCreate">➕ Add Shop Item</button>
    </div>

    <!-- Shop Items Table -->
    <div class="shop-table-wrap">
      <table class="shop-table" v-if="items.length">
        <thead>
          <tr>
            <th>Badge</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Sold</th>
            <th>Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" :class="{ 'row-inactive': !item.active }">
            <td class="cell-badge">
              <img v-if="item.badge_image" :src="item.badge_image" class="badge-thumb" />
              <span v-else class="badge-thumb-ph">🏅</span>
              <div>
                <div class="badge-name">{{ item.badge_name }}</div>
                <div class="badge-stats-mini" v-if="item.badge_stat_str || item.badge_stat_def || item.badge_stat_luk">
                  <span v-if="item.badge_stat_str" class="st str">⚔️+{{ item.badge_stat_str }}</span>
                  <span v-if="item.badge_stat_def" class="st def">🛡️+{{ item.badge_stat_def }}</span>
                  <span v-if="item.badge_stat_luk" class="st luk">🍀+{{ item.badge_stat_luk }}</span>
                </div>
              </div>
            </td>
            <td>
              <span class="price-tag">{{ priceIcon(item.price_type) }} {{ item.price_amount }} {{ priceLabel(item.price_type) }}</span>
            </td>
            <td>{{ item.stock !== null ? item.stock : '∞' }}</td>
            <td>{{ item.sold || 0 }}</td>
            <td>
              <span :class="item.active ? 'status-on' : 'status-off'">{{ item.active ? '✅' : '❌' }}</span>
            </td>
            <td class="cell-actions">
              <button class="btn-edit-sm" @click="openEdit(item)">✏️</button>
              <button class="btn-del-sm" @click="deleteItem(item)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <div class="empty-icon">🏪</div>
        <p>No items in the shop yet. Click "Add Shop Item" to start.</p>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <h2 class="modal-title">{{ editing ? '✏️ Edit Shop Item' : '➕ Add Shop Item' }}</h2>

        <div class="form-group">
          <label>Badge</label>
          <select v-model="form.badge_id" class="form-input">
            <option v-for="b in badges" :key="b.id" :value="b.id">
              {{ b.name }}
              <template v-if="b.stat_str || b.stat_def || b.stat_luk">
                (⚔️{{ b.stat_str }} 🛡️{{ b.stat_def }} 🍀{{ b.stat_luk }})
              </template>
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Price Type</label>
          <select v-model="form.price_type" class="form-input">
            <option value="gold">💰 Gold</option>
            <option value="mana">✨ Mana</option>
            <option value="thankyou">💌 Thank You Cards</option>
          </select>
        </div>

        <div class="form-group">
          <label>Price Amount</label>
          <input v-model.number="form.price_amount" type="number" min="1" class="form-input" />
        </div>

        <div class="form-group">
          <label>Stock (leave empty for unlimited)</label>
          <input v-model.number="form.stock" type="number" min="0" class="form-input" placeholder="∞ Unlimited" />
        </div>

        <div v-if="editing" class="form-group">
          <label>Active</label>
          <label class="toggle-label">
            <input type="checkbox" v-model="form.active" />
            <span>{{ form.active ? '✅ Active' : '❌ Inactive' }}</span>
          </label>
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showModal = false">Cancel</button>
          <button class="btn-save" @click="saveItem" :disabled="!form.badge_id || saving">
            {{ saving ? 'Saving...' : (editing ? '💾 Save' : '➕ Add') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getBadges, adminGetBadgeShopItems, adminCreateBadgeShopItem, adminUpdateBadgeShopItem, adminDeleteBadgeShopItem } from '../../services/api'

export default {
  name: 'BadgeShopAdmin',
  inject: ['showToast'],
  data() {
    return {
      items: [],
      badges: [],
      showModal: false,
      editing: null,
      saving: false,
      form: {
        badge_id: null,
        price_type: 'gold',
        price_amount: 10,
        stock: null,
        active: true,
      },
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [itemsRes, badgesRes] = await Promise.all([
          adminGetBadgeShopItems(),
          getBadges(),
        ])
        this.items = itemsRes.data || []
        this.badges = badgesRes.data || []
      } catch (e) {
        console.error('Failed to load badge shop data', e)
      }
    },
    openCreate() {
      this.editing = null
      this.form = { badge_id: this.badges[0]?.id || null, price_type: 'gold', price_amount: 10, stock: null, active: true }
      this.showModal = true
    },
    openEdit(item) {
      this.editing = item.id
      this.form = {
        badge_id: item.badge_id,
        price_type: item.price_type,
        price_amount: item.price_amount,
        stock: item.stock,
        active: item.active,
      }
      this.showModal = true
    },
    async saveItem() {
      this.saving = true
      try {
        const payload = { ...this.form }
        if (!payload.stock && payload.stock !== 0) payload.stock = null
        if (this.editing) {
          await adminUpdateBadgeShopItem(this.editing, payload)
          this.showToast('Shop item updated! ✏️')
        } else {
          await adminCreateBadgeShopItem(payload)
          this.showToast('Shop item added! 🏪')
        }
        this.showModal = false
        await this.loadData()
      } catch (e) {
        const msg = e.response?.data?.detail || 'Save failed'
        this.showToast(msg, 'error')
      } finally {
        this.saving = false
      }
    },
    async deleteItem(item) {
      if (!confirm(`Delete shop listing for "${item.badge_name}"?`)) return
      try {
        await adminDeleteBadgeShopItem(item.id)
        this.showToast('Item removed 🗑️')
        await this.loadData()
      } catch (e) {
        this.showToast('Delete failed', 'error')
      }
    },
    priceIcon(type) {
      return { gold: '💰', mana: '✨', thankyou: '💌' }[type] || '💰'
    },
    priceLabel(type) {
      return { gold: 'Gold', mana: 'Mana', thankyou: 'Thank You' }[type] || ''
    },
  },
}
</script>

<style scoped>
.admin-page { padding: 24px; max-width: 1100px; margin: 0 auto; }

.page-header-bar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 28px; flex-wrap: wrap; gap: 12px;
}
.page-title {
  font-family: 'Cinzel', serif; font-size: 26px; font-weight: 800;
  color: #d4a44c; text-shadow: 0 2px 8px rgba(212,164,76,0.2); margin: 0;
}
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; font-style: italic; margin: 4px 0 0; }

.btn-create {
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
  border: none; padding: 10px 20px; border-radius: 10px;
  font-weight: 700; font-size: 14px; cursor: pointer;
  transition: all .2s; font-family: 'Cinzel', serif;
}
.btn-create:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(212,164,76,0.4); }

/* Table */
.shop-table-wrap { overflow-x: auto; }
.shop-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 6px;
}
.shop-table th {
  text-align: left;
  padding: 8px 14px;
  color: #8b7355;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.shop-table td {
  padding: 12px 14px;
  background: linear-gradient(145deg, rgba(44,24,16,0.7), rgba(26,26,46,0.8));
  color: #e8d5b7;
  font-size: 14px;
}
.shop-table tr td:first-child { border-radius: 10px 0 0 10px; }
.shop-table tr td:last-child { border-radius: 0 10px 10px 0; }
.row-inactive td { opacity: 0.5; }

.cell-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}
.badge-thumb {
  width: 40px; height: 40px; border-radius: 50%; object-fit: cover;
  border: 2px solid rgba(212,164,76,0.3);
}
.badge-thumb-ph {
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(212,164,76,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
}
.badge-name {
  font-family: 'Cinzel', serif; font-weight: 700; font-size: 14px; color: #d4a44c;
}
.badge-stats-mini { display: flex; gap: 4px; margin-top: 2px; }
.st { font-size: 10px; font-weight: 700; }
.st.str { color: #e74c3c; }
.st.def { color: #3498db; }
.st.luk { color: #2ecc71; }

.price-tag { font-weight: 700; color: #d4a44c; }
.status-on { color: #2ecc71; }
.status-off { color: #e74c3c; }

.cell-actions { display: flex; gap: 6px; }
.btn-edit-sm, .btn-del-sm {
  background: transparent; border: 1px solid rgba(212,164,76,0.2);
  border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 14px;
  transition: all .2s;
}
.btn-edit-sm:hover { background: rgba(52,152,219,0.2); border-color: rgba(52,152,219,0.4); }
.btn-del-sm:hover { background: rgba(192,57,43,0.2); border-color: rgba(192,57,43,0.4); }

.empty-state { text-align: center; padding: 60px 20px; color: #8b7355; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}
.modal-box {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 1px solid rgba(212,164,76,0.3); border-radius: 16px;
  padding: 28px; width: 100%; max-width: 440px; max-height: 85vh; overflow-y: auto;
}
.modal-title { font-family: 'Cinzel', serif; font-size: 20px; color: #d4a44c; margin: 0 0 20px; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; color: #b8860b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 10px 14px; background: rgba(26,26,46,0.8);
  border: 1px solid rgba(212,164,76,0.2); border-radius: 8px;
  color: #e8dcc8; font-size: 14px; box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: rgba(212,164,76,0.5); }

.toggle-label {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  color: #e8d5b7; font-size: 14px;
}

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-cancel { background: transparent; color: #8b7355; border: 1px solid rgba(139,115,85,0.3); padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-save {
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
  border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 700;
}
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
