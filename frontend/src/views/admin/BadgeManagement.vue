<template>
  <div class="admin-page">
    <div class="page-header-bar">
      <div>
        <h1 class="page-title">🏅 Badge Forge</h1>
        <p class="page-sub">Create and award badges to adventurers</p>
      </div>
      <button class="btn-create" @click="editingBadgeId = null; newBadge = { name: '', description: '', stat_str: 0, stat_def: 0, stat_luk: 0 }; badgeFile = null; previewUrl = null; showCreateModal = true">⚒️ Forge New Badge</button>
    </div>

    <!-- Badge Grid -->
    <div class="badge-grid">
      <div v-for="badge in badges" :key="badge.id" class="badge-card" @click="openBadgeDetail(badge)">
        <div class="badge-icon-wrap">
          <img v-if="badge.image" :src="badge.image" class="badge-icon" />
          <div v-else class="badge-icon-placeholder">🏅</div>
        </div>
        <div class="badge-name">{{ badge.name }}</div>
        <div class="badge-stats-mini" v-if="badge.stat_str || badge.stat_def || badge.stat_luk">
          <span v-if="badge.stat_str" class="stat-tag str">⚔️{{ badge.stat_str }}</span>
          <span v-if="badge.stat_def" class="stat-tag def">🛡️{{ badge.stat_def }}</span>
          <span v-if="badge.stat_luk" class="stat-tag luk">🍀{{ badge.stat_luk }}</span>
        </div>
        <div class="badge-holders">{{ badge.holder_count || 0 }} holders</div>
      </div>

      <div v-if="badges.length === 0" class="empty-state">
        <div class="empty-icon">⚒️</div>
        <p>No badges forged yet. Create your first badge!</p>
      </div>
    </div>

    <!-- Create Badge Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-box">
        <h2 class="modal-title">{{ editingBadgeId ? '✏️ Edit Badge' : '⚒️ Forge New Badge' }}</h2>
        <div class="form-group">
          <label>Badge Name</label>
          <input v-model="newBadge.name" class="form-input" placeholder="e.g. Dragon Slayer" />
        </div>
        <div class="form-group">
          <label>Description (optional)</label>
          <input v-model="newBadge.description" class="form-input" placeholder="Awarded for..." />
        </div>
        <div class="form-group">
          <label>Badge Image</label>
          <div class="image-upload-area" @click="$refs.badgeImg.click()">
            <img v-if="previewUrl" :src="previewUrl" class="upload-preview" />
            <div v-else class="upload-placeholder">📷 Click to upload</div>
            <input ref="badgeImg" type="file" accept="image/*" @change="handleBadgeImage" style="display:none" />
          </div>
        </div>
        <div class="form-group">
          <label>Power Stats</label>
          <div class="stat-inputs">
            <div class="stat-input-group">
              <span class="stat-icon">⚔️</span>
              <label class="stat-label">STR</label>
              <input v-model.number="newBadge.stat_str" type="number" class="form-input stat-num" />
            </div>
            <div class="stat-input-group">
              <span class="stat-icon">🛡️</span>
              <label class="stat-label">DEF</label>
              <input v-model.number="newBadge.stat_def" type="number" class="form-input stat-num" />
            </div>
            <div class="stat-input-group">
              <span class="stat-icon">🍀</span>
              <label class="stat-label">LUK</label>
              <input v-model.number="newBadge.stat_luk" type="number" class="form-input stat-num" />
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showCreateModal = false">Cancel</button>
          <button class="btn-save" @click="saveBadge" :disabled="!newBadge.name || creating">
            {{ creating ? 'Saving...' : (editingBadgeId ? '💾 Save Changes' : '⚒️ Forge Badge') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Badge Detail / Award Modal -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-box modal-box--wide">
        <div class="detail-header">
          <div class="detail-badge-icon">
            <img v-if="selectedBadge.image" :src="selectedBadge.image" class="detail-img" />
            <div v-else class="detail-img-placeholder">🏅</div>
          </div>
          <div>
            <h2 class="modal-title" style="margin:0">{{ selectedBadge.name }}</h2>
            <p class="detail-desc">{{ selectedBadge.description || 'No description' }}</p>
          </div>
          <button class="btn-edit" @click="openEditBadge" title="Edit badge">✏️</button>
          <button class="btn-delete" @click="confirmDeleteBadge" title="Delete badge">🗑️</button>
          <button class="btn-push" @click.stop="pushToProd(selectedBadge)" :disabled="pushing" title="Push to Production">{{ pushing ? '⏳' : '🚀' }}</button>
        </div>
        <!-- Stats display -->
        <div class="detail-stats" v-if="selectedBadge.stat_str || selectedBadge.stat_def || selectedBadge.stat_luk">
          <div class="detail-stat"><span class="stat-icon">⚔️</span> STR {{ (selectedBadge.stat_str || 0) >= 0 ? '+' : '' }}{{ selectedBadge.stat_str || 0 }}</div>
          <div class="detail-stat"><span class="stat-icon">🛡️</span> DEF {{ (selectedBadge.stat_def || 0) >= 0 ? '+' : '' }}{{ selectedBadge.stat_def || 0 }}</div>
          <div class="detail-stat"><span class="stat-icon">🍀</span> LUK {{ (selectedBadge.stat_luk || 0) >= 0 ? '+' : '' }}{{ selectedBadge.stat_luk || 0 }}</div>
        </div>

        <!-- Award section -->
        <div class="award-section">
          <h3 class="section-title">🎁 Award to Adventurers</h3>
          <div class="award-row">
            <select v-model="selectedUserIds" multiple class="form-select">
              <option v-for="u in availableUsers" :key="u.id" :value="u.id">
                {{ u.name }} {{ u.surname || '' }}
              </option>
            </select>
            <button class="btn-save btn-sm" @click="awardBadge" :disabled="selectedUserIds.length === 0 || awarding">
              {{ awarding ? '...' : '🎁 Award' }}
            </button>
          </div>
        </div>

        <!-- Current holders -->
        <div class="holders-section">
          <h3 class="section-title">👥 Current Holders ({{ holders.length }})</h3>
          <div v-if="holders.length === 0" class="empty-holders">No holders yet</div>
          <div v-for="h in holders" :key="h.user_id" class="holder-row">
            <img v-if="h.user_image" :src="h.user_image" class="holder-avatar" />
            <div v-else class="holder-avatar-placeholder">{{ h.user_name?.charAt(0) || '?' }}</div>
            <div class="holder-info">
              <div class="holder-name">{{ h.user_name }}</div>
              <div class="holder-date">Awarded {{ formatDate(h.awarded_at) }}{{ h.awarded_by ? ` by ${h.awarded_by}` : '' }}</div>
            </div>
            <button class="btn-revoke" @click="revokeBadge(h.user_id)">Revoke</button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showDetailModal = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getBadges, createBadge, updateBadge, deleteBadge, awardBadge, revokeBadge, getBadgeHolders, getUsers, pushBadgeToProd } from '../../services/api'

export default {
  name: 'BadgeManagement',
  inject: ['showToast'],
  data() {
    return {
      badges: [],
      allUsers: [],
      showCreateModal: false,
      showDetailModal: false,
      newBadge: { name: '', description: '', stat_str: 0, stat_def: 0, stat_luk: 0 },
      editingBadgeId: null,
      badgeFile: null,
      previewUrl: null,
      creating: false,
      selectedBadge: {},
      holders: [],
      selectedUserIds: [],
      awarding: false,
      pushing: false,
    }
  },
  computed: {
    availableUsers() {
      const holderIds = this.holders.map(h => h.user_id)
      return this.allUsers.filter(u => !holderIds.includes(u.id))
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [bRes, uRes] = await Promise.all([
          getBadges(),
          getUsers(),
        ])
        this.badges = bRes.data
        this.allUsers = uRes.data
      } catch (e) {
        console.error('Failed to load badges', e)
      }
    },
    handleBadgeImage(e) {
      const file = e.target.files[0]
      if (!file) return
      this.badgeFile = file
      this.previewUrl = URL.createObjectURL(file)
    },
    async saveBadge() {
      this.creating = true
      try {
        const fd = new FormData()
        fd.append('name', this.newBadge.name)
        if (this.newBadge.description) fd.append('description', this.newBadge.description)
        fd.append('stat_str', this.newBadge.stat_str || 0)
        fd.append('stat_def', this.newBadge.stat_def || 0)
        fd.append('stat_luk', this.newBadge.stat_luk || 0)
        if (this.badgeFile) fd.append('file', this.badgeFile)
        if (this.editingBadgeId) {
          await updateBadge(this.editingBadgeId, fd)
          this.showToast('Badge updated! ✏️')
        } else {
          await createBadge(fd)
          this.showToast('Badge forged! 🏅')
        }
        this.showCreateModal = false
        this.editingBadgeId = null
        this.newBadge = { name: '', description: '', stat_str: 0, stat_def: 0, stat_luk: 0 }
        this.badgeFile = null
        this.previewUrl = null
        await this.loadData()
      } catch (e) {
        this.showToast('Failed to save badge', 'error')
      } finally {
        this.creating = false
      }
    },
    openEditBadge() {
      this.editingBadgeId = this.selectedBadge.id
      this.newBadge = {
        name: this.selectedBadge.name,
        description: this.selectedBadge.description || '',
        stat_str: this.selectedBadge.stat_str || 0,
        stat_def: this.selectedBadge.stat_def || 0,
        stat_luk: this.selectedBadge.stat_luk || 0,
      }
      this.badgeFile = null
      this.previewUrl = this.selectedBadge.image || null
      this.showDetailModal = false
      this.showCreateModal = true
    },
    async openBadgeDetail(badge) {
      this.selectedBadge = badge
      this.selectedUserIds = []
      this.showDetailModal = true
      try {
        const { data } = await getBadgeHolders(badge.id)
        this.holders = data
      } catch (e) {
        this.holders = []
      }
    },
    async awardBadge() {
      this.awarding = true
      try {
        await awardBadge(this.selectedBadge.id, this.selectedUserIds)
        this.showToast(`Badge awarded! 🎁`)
        this.selectedUserIds = []
        const { data } = await getBadgeHolders(this.selectedBadge.id)
        this.holders = data
        await this.loadData()
      } catch (e) {
        this.showToast('Award failed', 'error')
      } finally {
        this.awarding = false
      }
    },
    async revokeBadge(userId) {
      if (!confirm('Revoke this badge?')) return
      try {
        await revokeBadge(this.selectedBadge.id, userId)
        this.showToast('Badge revoked')
        const { data } = await getBadgeHolders(this.selectedBadge.id)
        this.holders = data
        await this.loadData()
      } catch (e) {
        this.showToast('Revoke failed', 'error')
      }
    },
    async confirmDeleteBadge() {
      if (!confirm(`Delete badge "${this.selectedBadge.name}"? This will remove it from all users.`)) return
      try {
        await deleteBadge(this.selectedBadge.id)
        this.showToast('Badge destroyed 💀')
        this.showDetailModal = false
        await this.loadData()
      } catch (e) {
        this.showToast('Delete failed', 'error')
      }
    },
    formatDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    },
    async pushToProd(badge) {
      if (!confirm(`Push "${badge.name}" to Production?`)) return
      this.pushing = true
      try {
        const { data } = await pushBadgeToProd(badge.id)
        this.showToast(`🚀 ${data.prod_response?.action === 'updated' ? 'Updated' : 'Created'} on Production!`)
      } catch (e) {
        const msg = e.response?.data?.detail || 'Push failed'
        this.showToast(msg, 'error')
      } finally {
        this.pushing = false
      }
    },
  }
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

/* Badge Grid */
.badge-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}
.badge-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.9), rgba(26,26,46,0.95));
  border: 1px solid rgba(212,164,76,0.2); border-radius: 14px;
  padding: 20px 12px; text-align: center; cursor: pointer;
  transition: all .2s;
}
.badge-card:hover { border-color: rgba(212,164,76,0.5); transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }

.badge-icon-wrap { width: 72px; height: 72px; margin: 0 auto 10px; }
.badge-icon { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; border: 2px solid rgba(212,164,76,0.4); }
.badge-icon-placeholder { width: 100%; height: 100%; border-radius: 50%; background: linear-gradient(135deg, #b8860b, #d4a44c); display: flex; align-items: center; justify-content: center; font-size: 28px; }
.badge-name { font-family: 'Cinzel', serif; font-size: 14px; font-weight: 700; color: #d4a44c; margin-bottom: 4px; }
.badge-holders { font-size: 11px; color: #8b7355; }
.badge-stats-mini { display: flex; gap: 4px; justify-content: center; margin-bottom: 6px; flex-wrap: wrap; }
.stat-tag { font-size: 10px; padding: 1px 6px; border-radius: 6px; font-weight: 700; }
.stat-tag.str { background: rgba(231,76,60,0.15); color: #e74c3c; }
.stat-tag.def { background: rgba(52,152,219,0.15); color: #3498db; }
.stat-tag.luk { background: rgba(46,204,113,0.15); color: #2ecc71; }

.empty-state { grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: #8b7355; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }

/* Modals */
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
.modal-box--wide { max-width: 560px; }
.modal-title { font-family: 'Cinzel', serif; font-size: 20px; color: #d4a44c; margin: 0 0 20px; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; color: #b8860b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 10px 14px; background: rgba(26,26,46,0.8);
  border: 1px solid rgba(212,164,76,0.2); border-radius: 8px;
  color: #e8dcc8; font-size: 14px; box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: rgba(212,164,76,0.5); }

.image-upload-area {
  border: 2px dashed rgba(212,164,76,0.3); border-radius: 12px;
  padding: 20px; text-align: center; cursor: pointer; transition: all .2s;
}
.image-upload-area:hover { border-color: rgba(212,164,76,0.5); }
.upload-preview { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; }
.upload-placeholder { color: #8b7355; font-size: 14px; }

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.btn-cancel { background: transparent; color: #8b7355; border: 1px solid rgba(139,115,85,0.3); padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-save {
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
  border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 700;
}
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-sm { padding: 6px 14px; font-size: 13px; }

/* Detail modal */
.detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.detail-badge-icon { flex-shrink: 0; }
.detail-img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; border: 2px solid #d4a44c; }
.detail-img-placeholder { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #b8860b, #d4a44c); display: flex; align-items: center; justify-content: center; font-size: 28px; }
.detail-desc { color: #8b7355; font-size: 13px; margin: 4px 0 0; }
.btn-delete { background: rgba(192,57,43,0.2); color: #e74c3c; border: 1px solid rgba(192,57,43,0.3); padding: 6px 10px; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-delete:hover { background: rgba(192,57,43,0.4); }
.btn-edit { background: rgba(52,152,219,0.2); color: #3498db; border: 1px solid rgba(52,152,219,0.3); padding: 6px 10px; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-edit:hover { background: rgba(52,152,219,0.4); }
.btn-push { background: rgba(46,204,113,0.2); color: #2ecc71; border: 1px solid rgba(46,204,113,0.3); padding: 6px 10px; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-push:hover { background: rgba(46,204,113,0.4); }
.btn-push:disabled { opacity: 0.5; cursor: not-allowed; }

.detail-stats { display: flex; gap: 12px; margin-bottom: 20px; padding: 10px 14px; background: rgba(212,164,76,0.06); border-radius: 10px; border: 1px solid rgba(212,164,76,0.1); }
.detail-stat { font-size: 13px; color: #e8dcc8; font-weight: 600; }
.stat-icon { margin-right: 2px; }

.stat-inputs { display: flex; gap: 10px; }
.stat-input-group { flex: 1; text-align: center; }
.stat-label { display: block; font-size: 11px; color: #8b7355; margin-bottom: 4px; font-weight: 700; }
.stat-num { text-align: center; padding: 8px 4px; width: 100%; }

.section-title { font-family: 'Cinzel', serif; font-size: 15px; color: #d4a44c; margin: 0 0 12px; }

.award-section { margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid rgba(212,164,76,0.15); }
.award-row { display: flex; gap: 10px; align-items: flex-start; }
.form-select {
  flex: 1; padding: 8px; background: rgba(26,26,46,0.8);
  border: 1px solid rgba(212,164,76,0.2); border-radius: 8px;
  color: #e8dcc8; font-size: 13px; min-height: 90px;
}
.form-select option { padding: 4px 8px; }

.holders-section { margin-bottom: 16px; }
.empty-holders { color: #8b7355; font-size: 13px; font-style: italic; padding: 12px 0; }
.holder-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid rgba(212,164,76,0.08);
}
.holder-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid rgba(212,164,76,0.3); }
.holder-avatar-placeholder {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  color: #1c1208; font-size: 14px; font-weight: 700;
}
.holder-info { flex: 1; }
.holder-name { color: #e8dcc8; font-size: 14px; font-weight: 600; }
.holder-date { color: #8b7355; font-size: 11px; }
.btn-revoke { background: transparent; color: #e74c3c; border: 1px solid rgba(192,57,43,0.3); padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 600; }
.btn-revoke:hover { background: rgba(192,57,43,0.2); }
</style>
