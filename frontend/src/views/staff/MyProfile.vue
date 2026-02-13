<template>
  <div class="staff-page">
    <h1 class="page-title">🛡️ Character Sheet</h1>
    <p class="page-sub">Manage your adventurer info</p>

    <div v-if="loading" style="text-align: center; padding: 40px; color: #8b7355;">Loading...</div>

    <div v-else class="profile-stack">
      <!-- Profile Card -->
      <div class="profile-card">
        <div class="avatar-section" @click="$refs.imageInput.click()">
          <img v-if="user.image" :src="user.image" class="avatar-img" />
          <div v-else class="avatar-placeholder">{{ user.name?.charAt(0) || '?' }}</div>
          <div class="avatar-overlay">📷</div>
          <input ref="imageInput" type="file" accept="image/*" @change="handleImageUpload" style="display: none;" />
        </div>
        <div class="profile-name">{{ user.name }} {{ user.surname }}</div>
        <div class="profile-position">{{ user.position || 'Adventurer' }}</div>
        <div class="profile-dept">{{ user.department || '-' }}</div>
        
        <!-- Dynamic Badges -->
        <div class="badges-row" v-if="myBadges.length > 0">
          <div v-for="badge in myBadges.slice(0, 6)" :key="badge.id" class="badge-circle" :title="badge.badge_name">
            <img v-if="badge.badge_image" :src="badge.badge_image" class="badge-circle-img" />
            <span v-else class="badge-circle-fb">🏅</span>
          </div>
          <div v-if="myBadges.length > 6" class="badge-more-tag">+{{ myBadges.length - 6 }}</div>
        </div>

        <div class="profile-stats">
          <div class="stat"><span class="stat-val stat-val--gold">{{ user.coins || 0 }}</span><span class="stat-lbl">💰 Gold</span></div>
          <div class="stat"><span class="stat-val stat-val--mana">{{ user.angel_coins || 0 }}</span><span class="stat-lbl">✨ Mana</span></div>
        </div>
      </div>

      <!-- Power Stats Card -->
      <div class="edit-card power-stats-card">
        <div class="edit-title">⚔️ Power Stats</div>
        <div class="power-stats-grid">
          <div class="power-stat">
            <div class="power-stat-header">
              <span class="power-stat-icon">⚔️</span>
              <span class="power-stat-name">STR</span>
              <span class="power-stat-total">{{ stats.total_str }}</span>
            </div>
            <div class="power-stat-bar">
              <div class="power-stat-fill str-fill" :style="{width: statBarWidth(stats.total_str) + '%'}"></div>
            </div>
            <div class="power-stat-detail">Base {{ stats.base_str }} + Badge {{ stats.badge_str }}</div>
          </div>
          <div class="power-stat">
            <div class="power-stat-header">
              <span class="power-stat-icon">🛡️</span>
              <span class="power-stat-name">DEF</span>
              <span class="power-stat-total">{{ stats.total_def }}</span>
            </div>
            <div class="power-stat-bar">
              <div class="power-stat-fill def-fill" :style="{width: statBarWidth(stats.total_def) + '%'}"></div>
            </div>
            <div class="power-stat-detail">Base {{ stats.base_def }} + Badge {{ stats.badge_def }}</div>
          </div>
          <div class="power-stat">
            <div class="power-stat-header">
              <span class="power-stat-icon">🍀</span>
              <span class="power-stat-name">LUK</span>
              <span class="power-stat-total">{{ stats.total_luk }}</span>
            </div>
            <div class="power-stat-bar">
              <div class="power-stat-fill luk-fill" :style="{width: statBarWidth(stats.total_luk) + '%'}"></div>
            </div>
            <div class="power-stat-detail">Base {{ stats.base_luk }} + Badge {{ stats.badge_luk }}</div>
          </div>
        </div>
      </div>

      <!-- Phone -->
      <div class="edit-card">
        <div class="edit-title">📱 Communication Crystal</div>
        <div class="edit-form">
          <input v-model="phone" class="form-input" placeholder="e.g. 0812345678" maxlength="15" />
          <button class="btn-save" @click="savePhone" :disabled="savingPhone">
            {{ savingPhone ? 'Saving...' : '💾 Save' }}
          </button>
        </div>
      </div>

      <!-- Password -->
      <div class="edit-card">
        <div class="edit-title">🔒 Change Passphrase</div>
        <div class="edit-form-col">
          <input v-model="oldPassword" class="form-input" type="password" placeholder="Current passphrase" />
          <input v-model="newPassword" class="form-input" type="password" placeholder="New passphrase" />
          <input v-model="confirmPassword" class="form-input" type="password" placeholder="Confirm passphrase" />
          <button class="btn-save" @click="changePassword" :disabled="savingPw || !oldPassword || !newPassword">
            {{ savingPw ? 'Changing...' : '🔑 Change Passphrase' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Status Message -->
    <div v-if="statusMsg" :class="['status-msg', statusType === 'error' ? 'status-msg--error' : 'status-msg--success']">
      {{ statusMsg }}
    </div>
  </div>
</template>

<script>
import api, { getMyStats, getMyBadges } from '../../services/api'

export default {
  name: 'MyProfile',
  inject: ['showToast'],
  data() {
    return {
      loading: true,
      user: {},
      phone: '',
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      savingPhone: false,
      savingPw: false,
      statusMsg: '',
      statusType: '',
      stats: { base_str: 1, base_def: 1, base_luk: 1, badge_str: 0, badge_def: 0, badge_luk: 0, total_str: 1, total_def: 1, total_luk: 1 },
      myBadges: [],
    }
  },
  async mounted() {
    await this.loadProfile()
  },
  methods: {
    async loadProfile() {
      this.loading = true
      try {
        const { data } = await api.get('/api/users/me')
        this.user = data
        this.phone = data.phone || ''
      } catch (e) {
        console.error('Failed to load profile', e)
      } finally {
        this.loading = false
      }
      // Load stats and badges in parallel
      try {
        const [sRes, bRes] = await Promise.all([
          getMyStats().catch(() => ({ data: this.stats })),
          getMyBadges().catch(() => ({ data: [] })),
        ])
        this.stats = sRes.data
        this.myBadges = bRes.data
      } catch (e) { /* ignore */ }
    },
    async savePhone() {
      this.savingPhone = true
      try {
        const { data } = await api.put('/api/users/me/profile', { phone: this.phone })
        this.user = data
        this.showToast('Crystal updated! 📱')
      } catch (e) {
        this.showToast('Failed to update', 'error')
      } finally {
        this.savingPhone = false
      }
    },
    async changePassword() {
      if (this.newPassword !== this.confirmPassword) {
        this.showToast('Passphrases do not match', 'error')
        return
      }
      if (this.newPassword.length < 4) {
        this.showToast('Passphrase must be at least 4 characters', 'error')
        return
      }
      this.savingPw = true
      try {
        await api.put('/api/users/me/password', {
          old_password: this.oldPassword,
          new_password: this.newPassword,
        })
        this.showToast('Passphrase changed! 🔑')
        this.oldPassword = ''
        this.newPassword = ''
        this.confirmPassword = ''
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to change passphrase', 'error')
      } finally {
        this.savingPw = false
      }
    },
    async handleImageUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      try {
        const formData = new FormData()
        formData.append('file', file)
        const { data } = await api.post('/api/users/me/upload-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        this.user = data
        // Sync localStorage so other pages see the new image
        const stored = JSON.parse(localStorage.getItem('user') || '{}')
        stored.image = data.image
        localStorage.setItem('user', JSON.stringify(stored))
        this.showToast('Portrait updated! 📷')
      } catch (e) {
        this.showToast('Failed to upload portrait', 'error')
      }
    },
    statBarWidth(val) {
      return Math.min(100, (val / 50) * 100)
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
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; margin-bottom: 24px; font-style: italic; }

.profile-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 480px;
  margin: 0 auto;
}

/* Profile Card */
.profile-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.9), rgba(26,26,46,0.95));
  border: 2px solid rgba(212,164,76,0.3);
  border-radius: 16px;
  padding: 28px 20px;
  text-align: center;
}

.avatar-section {
  position: relative; width: 100px; height: 100px;
  margin: 0 auto 16px; cursor: pointer;
  border-radius: 50%; overflow: hidden;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder {
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  color: #1c1208; font-size: 36px; font-weight: 800;
}
.avatar-overlay {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; opacity: 0;
  transition: opacity 0.2s;
}
.avatar-section:hover .avatar-overlay { opacity: 1; }

.profile-name { font-family: 'Cinzel', serif; font-size: 18px; font-weight: 800; color: #d4a44c; }
.profile-position { font-size: 13px; color: #b8860b; font-weight: 700; margin-top: 4px; }
.profile-dept { font-size: 12px; color: #8b7355; font-weight: 600; }

/* Dynamic Badges */
.badges-row {
  display: flex; align-items: center; justify-content: center;
  gap: 5px; margin: 10px 0;
}
.badge-circle { width: 30px; height: 30px; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); }
.badge-circle-img { width: 100%; height: 100%; object-fit: cover; }
.badge-circle-fb { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 14px; }
.badge-more-tag { font-size: 10px; color: #b8860b; font-weight: 700; }

/* Power Stats */
.power-stats-card { margin-top: 0; }
.power-stats-grid { display: flex; flex-direction: column; gap: 14px; }
.power-stat-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.power-stat-icon { font-size: 16px; }
.power-stat-name { font-family: 'Cinzel', serif; font-size: 13px; font-weight: 800; color: #e8dcc8; }
.power-stat-total { margin-left: auto; font-size: 18px; font-weight: 800; color: #d4a44c; }
.power-stat-bar {
  height: 8px; background: rgba(26,26,46,0.8); border-radius: 4px; overflow: hidden;
}
.power-stat-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.str-fill { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.def-fill { background: linear-gradient(90deg, #3498db, #2980b9); }
.luk-fill { background: linear-gradient(90deg, #2ecc71, #27ae60); }
.power-stat-detail { font-size: 10px; color: #6b5a3e; margin-top: 2px; }

.profile-stats {
  display: flex; gap: 12px; justify-content: center; margin-top: 16px;
}
.stat { text-align: center; }
.stat-val { font-size: 20px; font-weight: 800; display: block; }
.stat-val--gold { color: #d4a44c; }
.stat-val--mana { color: #9b59b6; }
.stat-lbl { font-size: 10px; color: #8b7355; font-weight: 600; }

/* Edit Section */
.edit-section { display: flex; flex-direction: column; gap: 16px; }

.edit-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.7), rgba(26,26,46,0.8));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 12px;
  padding: 20px 24px;
}
.edit-title { font-family: 'Cinzel', serif; font-size: 15px; font-weight: 800; color: #d4a44c; margin-bottom: 12px; }

.edit-form { display: flex; gap: 10px; align-items: flex-end; }
.edit-form-col { display: flex; flex-direction: column; gap: 10px; }

.form-input {
  padding: 10px 14px; border-radius: 8px;
  border: 2px solid rgba(212,164,76,0.2);
  font-size: 14px; font-weight: 600; color: #e8d5b7;
  background: rgba(26,26,46,0.8);
  width: 100%; box-sizing: border-box;
  transition: border-color 0.2s;
}
.form-input:focus { outline: none; border-color: #d4a44c; }

.btn-save {
  padding: 10px 20px; border-radius: 8px;
  border: 2px solid #d4a44c;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; font-weight: 800; font-size: 13px;
  cursor: pointer; white-space: nowrap;
  transition: all 0.2s;
}
.btn-save:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(212,164,76,0.3); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* Status */
.status-msg {
  margin-top: 16px; padding: 12px 20px; border-radius: 8px;
  font-weight: 700; font-size: 13px; text-align: center;
  border: 2px solid;
}
.status-msg--success { background: rgba(39,174,96,0.1); color: #27ae60; border-color: rgba(39,174,96,0.3); }
.status-msg--error { background: rgba(192,57,43,0.1); color: #e74c3c; border-color: rgba(192,57,43,0.3); }

@media (max-width: 600px) {
  .profile-stack { max-width: 100%; }
}
</style>
