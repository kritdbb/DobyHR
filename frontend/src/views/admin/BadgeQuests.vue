<template>
  <div class="admin-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">🎯 Badge Quest</h1>
        <p class="page-subtitle">Auto-award badges when adventurers meet conditions</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-evaluate" @click="runEvaluate" :disabled="evaluating">
          {{ evaluating ? '⏳ Evaluating…' : '⚡ Evaluate Now' }}
        </button>
        <button class="btn btn-create" @click="openCreate">➕ New Quest</button>
      </div>
    </div>

    <!-- Evaluate result banner -->
    <div v-if="evalResult" class="eval-banner" @click="evalResult = null">
      🏅 Awarded <strong>{{ evalResult.awarded }}</strong> reward(s)
      <span v-if="evalResult.details.length"> —
        <span v-for="(d, i) in evalResult.details" :key="i">
          {{ d.user_name }} → {{ d.reward }}<span v-if="i < evalResult.details.length - 1">, </span>
        </span>
      </span>
      <span v-else> — no new awards</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">Loading quests…</div>

    <!-- Quest List -->
    <div v-else-if="quests.length === 0" class="empty-state">
      <div class="empty-icon">🎯</div>
      <p>No quests yet. Create one to start auto-awarding badges!</p>
    </div>
    <div v-else class="quest-grid">
      <div v-for="q in quests" :key="q.id" class="quest-card" :class="{ 'quest-card--inactive': !q.is_active }">
        <div class="quest-card-header">
          <div class="quest-badge-icon">
            <img v-if="q.badge_image" :src="q.badge_image" class="quest-badge-img" />
            <span v-else>{{ rewardIcon(q.reward_type) }}</span>
          </div>
          <div class="quest-card-info">
            <div class="quest-card-name">{{ q.badge_name || rewardLabel(q) }}</div>
            <div class="quest-card-query">
              <code>{{ q.condition_query || `${q.condition_type} >= ${q.threshold}` }}</code>
            </div>
            <div v-if="q.reward_type !== 'badge'" class="quest-reward-tag">🎁 {{ rewardLabel(q) }}</div>
          </div>
          <span class="quest-status" :class="q.is_active ? 'status-active' : 'status-inactive'">
            {{ q.is_active ? '✅ Active' : '⏸ Inactive' }}
          </span>
          <span v-if="q.max_awards" class="quest-limit" :class="{ 'quest-limit--full': q.current_awards >= q.max_awards }">
            🏆 {{ q.current_awards || 0 }}/{{ q.max_awards }}
          </span>
        </div>
        <div v-if="q.description" class="quest-card-desc">{{ q.description }}</div>
        <div class="quest-card-footer">
          <span class="quest-card-date">{{ formatDate(q.created_at) }}</span>
          <div class="quest-card-actions">
            <button class="btn-icon" title="Edit" @click="openEdit(q)">✏️</button>
            <button class="btn-icon" title="Delete" @click="deleteQuest(q.id)">🗑️</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-box">
        <h3 class="modal-title">{{ editingId ? '✏️ Edit Quest' : '✨ New Quest' }}</h3>

        <!-- Reward Type -->
        <label class="form-label">🎁 REWARD TYPE</label>
        <select v-model="form.reward_type" class="form-input">
          <option value="badge">🏅 Badge</option>
          <option value="gold">💰 Gold</option>
          <option value="mana">🔮 Mana</option>
          <option value="str">⚔️ STR</option>
          <option value="def">🛡️ DEF</option>
          <option value="luk">🍀 LUK</option>
          <option value="coupon">🎫 Coupon (Item)</option>
        </select>

        <!-- Badge Selection (only for badge type) -->
        <template v-if="form.reward_type === 'badge'">
          <label class="form-label">BADGE TO AWARD</label>
          <select v-model="form.badge_id" class="form-input">
            <option value="">— Select Badge —</option>
            <option v-for="b in badges" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </template>

        <!-- Reward Value (for non-badge types) -->
        <template v-if="form.reward_type !== 'badge'">
          <label class="form-label">{{ form.reward_type === 'coupon' ? 'COUPON ITEM' : 'REWARD AMOUNT' }}</label>
          <select v-if="form.reward_type === 'coupon'" v-model="form.reward_value" class="form-input">
            <option :value="0">— Select Coupon Item —</option>
            <option v-for="r in rewards" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
          <input v-else v-model.number="form.reward_value" type="number" min="1" class="form-input" placeholder="e.g. 10" />
        </template>

        <!-- Query Input -->
        <label class="form-label">📜 CONDITION QUERY</label>
        <textarea
          v-model="form.condition_query"
          class="form-textarea query-input"
          placeholder="e.g. total_steps >= 50 AND mana_sent > 3"
          rows="3"
          spellcheck="false"
        ></textarea>

        <!-- Query Validation -->
        <div v-if="queryValidation" class="query-validation" :class="queryValidation.valid ? 'valid' : 'invalid'">
          <template v-if="queryValidation.valid">
            ✅ Valid — {{ queryValidation.condition_count }} condition(s) using fields: {{ queryValidation.fields.join(', ') }}
          </template>
          <template v-else>
            ❌ {{ queryValidation.error }}
          </template>
        </div>

        <!-- Preview Button & Result -->
        <button class="btn btn-preview" @click="previewQuery" :disabled="!form.condition_query || previewing">
          {{ previewing ? '⏳ Querying…' : '🔍 Preview — Who matches?' }}
        </button>
        <div v-if="previewResult" class="preview-result">
          <div class="preview-header">
            🎯 <strong>{{ previewResult.matching_users }}</strong> / {{ previewResult.total_users }} users match
          </div>
          <div v-if="previewResult.users.length" class="preview-users">
            <div v-for="u in previewResult.users" :key="u.user_id" class="preview-user">
              <img v-if="u.user_image" :src="u.user_image" class="preview-user-img" />
              <span v-else class="preview-user-ph">👤</span>
              <div class="preview-user-info">
                <div class="preview-user-name">{{ u.user_name }}</div>
                <div class="preview-user-vals">
                  <span v-for="(val, field) in u.field_values" :key="field" class="preview-field-tag">
                    {{ field }}={{ val }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Available Fields (collapsible) -->
        <details class="fields-panel">
          <summary class="fields-toggle">📖 Available Fields ({{ fields.length }})</summary>
          <div class="fields-list">
            <div v-for="f in fields" :key="f.field" class="field-row" @click="insertField(f.example)">
              <code class="field-name">{{ f.field }}</code>
              <span class="field-desc">{{ f.desc }}</span>
              <code class="field-example">{{ f.example }}</code>
            </div>
          </div>
        </details>

        <!-- Example Queries (collapsible) -->
        <details class="fields-panel">
          <summary class="fields-toggle">💡 Example Queries</summary>
          <div class="fields-list">
            <div class="field-row" @click="form.condition_query = 'total_steps >= 1000'">
              <code class="field-example">total_steps >= 1000</code>
              <span class="field-desc">Walked 1000+ steps total</span>
            </div>
            <div class="field-row" @click="form.condition_query = 'mana_sent >= 5 AND mana_received >= 5'">
              <code class="field-example">mana_sent >= 5 AND mana_received >= 5</code>
              <span class="field-desc">Sent & received Mana 5+ times</span>
            </div>
            <div class="field-row" @click="form.condition_query = 'checkin_streak >= 10'">
              <code class="field-example">checkin_streak >= 10</code>
              <span class="field-desc">10 consecutive days on time</span>
            </div>
            <div class="field-row" @click="form.condition_query = 'revival_prayers >= 3 AND scroll_purchased >= 2'">
              <code class="field-example">revival_prayers >= 3 AND scroll_purchased >= 2</code>
              <span class="field-desc">Revival hero & scroll collector</span>
            </div>
            <div class="field-row" @click="form.condition_query = 'base_str >= 15 OR base_def >= 15 OR base_luk >= 15'">
              <code class="field-example">base_str >= 15 OR base_def >= 15 OR base_luk >= 15</code>
              <span class="field-desc">Any stat reaches 15+</span>
            </div>
          </div>
        </details>

        <!-- Description -->
        <label class="form-label">DESCRIPTION (OPTIONAL)</label>
        <input v-model="form.description" class="form-input" placeholder="e.g. Walk 100k steps total" />

        <!-- Max Awards -->
        <label class="form-label">MAX AWARDS (OPTIONAL - LEAVE BLANK FOR UNLIMITED)</label>
        <input v-model.number="form.max_awards" type="number" min="1" class="form-input" placeholder="e.g. 10 — auto-disable after 10 awards" />

        <!-- Active Toggle -->
        <label class="form-checkbox">
          <input type="checkbox" v-model="form.is_active" /> ACTIVE
        </label>

        <div class="modal-actions">
          <button class="btn btn-cancel" @click="showModal = false">Cancel</button>
          <button class="btn btn-save" @click="saveQuest" :disabled="saving || !form.condition_query || (form.reward_type === 'badge' && !form.badge_id)">
            {{ saving ? '⏳ Saving…' : (editingId ? 'Update' : 'Create') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api, { getBadges, getRewards } from '../../services/api'

export default {
  name: 'BadgeQuests',
  inject: ['showToast'],
  data() {
    return {
      quests: [],
      badges: [],
      rewards: [],
      fields: [],
      loading: true,
      showModal: false,
      editingId: null,
      saving: false,
      evaluating: false,
      previewing: false,
      evalResult: null,
      previewResult: null,
      queryValidation: null,
      form: {
        badge_id: '',
        condition_query: '',
        description: '',
        is_active: true,
        max_awards: null,
        reward_type: 'badge',
        reward_value: 0,
      },
    }
  },
  watch: {
    'form.condition_query'(val) {
      this.previewResult = null
      if (val && val.trim()) {
        this.validateQueryLocal(val)
      } else {
        this.queryValidation = null
      }
    },
  },
  async mounted() {
    await this.loadAll()
  },
  methods: {
    async loadAll() {
      this.loading = true
      try {
        const [questsRes, badgesRes, fieldsRes, rewardsRes] = await Promise.all([
          api.get('/api/badge-quests/'),
          getBadges(),
          api.get('/api/badge-quests/fields'),
          getRewards(),
        ])
        this.quests = questsRes.data
        this.badges = badgesRes.data
        this.fields = fieldsRes.data
        this.rewards = rewardsRes.data
      } catch (e) {
        this.showToast('Failed to load data', 'error')
      }
      this.loading = false
    },
    validateQueryLocal(query) {
      // Client-side basic validation
      const fieldNames = this.fields.map(f => f.field)
      const ops = ['>=', '<=', '!=', '==', '>', '<']
      const parts = query.split(/\s+(?:AND|OR)\s+/i)
      const conditions = []
      for (const part of parts) {
        const match = part.trim().match(/^(\w+)\s*(>=|<=|!=|==|>|<)\s*(\d+)$/)
        if (!match) {
          this.queryValidation = { valid: false, error: `Invalid: "${part.trim()}". Use: field >= value` }
          return
        }
        const [, field, op, val] = match
        if (!fieldNames.includes(field)) {
          this.queryValidation = { valid: false, error: `Unknown field: "${field}"` }
          return
        }
        conditions.push(field)
      }
      this.queryValidation = {
        valid: true,
        fields: [...new Set(conditions)],
        condition_count: conditions.length,
      }
    },
    insertField(example) {
      if (this.form.condition_query) {
        this.form.condition_query += ' AND ' + example
      } else {
        this.form.condition_query = example
      }
    },
    async previewQuery() {
      if (!this.form.condition_query) return
      this.previewing = true
      try {
        const res = await api.post('/api/badge-quests/preview', { query: this.form.condition_query })
        this.previewResult = res.data
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Preview failed', 'error')
      }
      this.previewing = false
    },
    openCreate() {
      this.editingId = null
      this.form = { badge_id: '', condition_query: '', description: '', is_active: true, max_awards: null, reward_type: 'badge', reward_value: 0 }
      this.previewResult = null
      this.queryValidation = null
      this.showModal = true
    },
    openEdit(q) {
      this.editingId = q.id
      this.form = {
        badge_id: q.badge_id || '',
        condition_query: q.condition_query || (q.condition_type ? `${q.condition_type} >= ${q.threshold}` : ''),
        description: q.description || '',
        is_active: q.is_active,
        max_awards: q.max_awards || null,
        reward_type: q.reward_type || 'badge',
        reward_value: q.reward_value || 0,
      }
      this.previewResult = null
      this.queryValidation = null
      this.showModal = true
    },
    async saveQuest() {
      this.saving = true
      try {
        const body = {
          badge_id: this.form.reward_type === 'badge' ? this.form.badge_id : null,
          condition_query: this.form.condition_query,
          description: this.form.description || null,
          is_active: this.form.is_active,
          max_awards: this.form.max_awards || null,
          reward_type: this.form.reward_type,
          reward_value: this.form.reward_value || 0,
        }
        if (this.editingId) {
          await api.put(`/api/badge-quests/${this.editingId}`, body)
          this.showToast('Quest updated! ⚔️')
        } else {
          await api.post('/api/badge-quests/', body)
          this.showToast('Quest created! 🎯')
        }
        this.showModal = false
        await this.loadAll()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Save failed', 'error')
      }
      this.saving = false
    },
    async deleteQuest(id) {
      if (!confirm('Delete this quest?')) return
      try {
        await api.delete(`/api/badge-quests/${id}`)
        this.showToast('Quest deleted')
        await this.loadAll()
      } catch (e) {
        this.showToast('Delete failed', 'error')
      }
    },
    async runEvaluate() {
      this.evaluating = true
      try {
        const res = await api.post('/api/badge-quests/evaluate')
        this.evalResult = res.data
        this.showToast(`Awarded ${res.data.awarded} reward(s)`)
      } catch (e) {
        this.showToast('Evaluation failed', 'error')
      }
      this.evaluating = false
    },
    rewardIcon(type) {
      const icons = { badge: '🏅', gold: '💰', mana: '🔮', str: '⚔️', def: '🛡️', luk: '🍀', coupon: '🎫' }
      return icons[type] || '🏅'
    },
    rewardLabel(q) {
      const t = q.reward_type || 'badge'
      const v = q.reward_value || 0
      if (t === 'badge') return q.badge_name || 'Badge'
      if (t === 'gold') return `+${v} Gold`
      if (t === 'mana') return `+${v} Mana`
      if (t === 'str') return `+${v} STR`
      if (t === 'def') return `+${v} DEF`
      if (t === 'luk') return `+${v} LUK`
      if (t === 'coupon') {
        const item = this.rewards.find(r => r.id === v)
        return item ? `🎫 ${item.name}` : `Coupon #${v}`
      }
      return t
    },
    formatDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    },
  },
}
</script>

<style scoped>
.admin-page { padding: 24px; max-width: 900px; margin: 0 auto; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
.page-title { font-family: 'Cinzel', serif; font-size: 22px; color: #d4a44c; margin: 0; }
.page-subtitle { font-size: 13px; color: #8b7355; margin: 4px 0 0; }
.header-actions { display: flex; gap: 10px; }

/* Buttons */
.btn {
  padding: 10px 18px; border-radius: 10px;
  font-weight: 700; font-size: 13px; cursor: pointer;
  border: 1px solid transparent; transition: all .2s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-create { background: linear-gradient(135deg, #d4a44c, #b8860b); color: #1c1208; border-color: #d4a44c; }
.btn-create:hover:not(:disabled) { box-shadow: 0 0 12px rgba(212,164,76,0.3); }
.btn-evaluate { background: rgba(46,204,113,0.15); color: #2ecc71; border-color: rgba(46,204,113,0.3); }
.btn-evaluate:hover:not(:disabled) { background: rgba(46,204,113,0.25); }
.btn-save { background: linear-gradient(135deg, #d4a44c, #b8860b); color: #1c1208; }
.btn-cancel { background: rgba(255,255,255,0.05); color: #8b7355; border-color: rgba(255,255,255,0.1); }
.btn-preview { width: 100%; padding: 10px; margin: 8px 0; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; background: rgba(52,152,219,0.15); color: #3498db; border: 1px solid rgba(52,152,219,0.3); transition: all .2s; }
.btn-preview:hover:not(:disabled) { background: rgba(52,152,219,0.25); }
.btn-preview:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-icon { background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px; opacity: 0.7; transition: opacity .2s; }
.btn-icon:hover { opacity: 1; }

/* Eval Banner */
.eval-banner {
  padding: 12px 16px; border-radius: 10px; margin-bottom: 16px;
  background: rgba(46,204,113,0.1); border: 1px solid rgba(46,204,113,0.25);
  color: #2ecc71; font-size: 13px; cursor: pointer;
}

/* Loading & Empty */
.loading { text-align: center; padding: 40px; color: #8b7355; }
.empty-state { text-align: center; padding: 60px 20px; color: #8b7355; font-size: 14px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }

/* Quest Grid */
.quest-grid { display: flex; flex-direction: column; gap: 12px; }
.quest-card {
  padding: 16px; border-radius: 12px;
  background: rgba(44,24,16,0.6); border: 1px solid rgba(212,164,76,0.15);
  transition: all .2s;
}
.quest-card:hover { border-color: rgba(212,164,76,0.3); }
.quest-card--inactive { opacity: 0.55; }
.quest-card-header { display: flex; align-items: center; gap: 12px; }
.quest-badge-icon { width: 40px; height: 40px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); display: flex; align-items: center; justify-content: center; font-size: 18px; }
.quest-badge-img { width: 100%; height: 100%; object-fit: cover; }
.quest-card-info { flex: 1; min-width: 0; }
.quest-card-name { font-weight: 700; font-size: 14px; color: #d4a44c; }
.quest-card-query { margin-top: 2px; }
.quest-card-query code { font-size: 12px; color: #3498db; background: rgba(52,152,219,0.1); padding: 2px 8px; border-radius: 4px; font-family: 'Fira Code', 'SF Mono', monospace; }
.quest-status { font-size: 11px; font-weight: 700; flex-shrink: 0; }
.status-active { color: #2ecc71; }
.status-inactive { color: #8b7355; }
.quest-card-desc { font-size: 12px; color: #8b7355; margin-top: 8px; padding-left: 52px; }
.quest-card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding-left: 52px; }
.quest-card-date { font-size: 11px; color: #6b5a3e; }
.quest-card-actions { display: flex; gap: 6px; }

.quest-limit { font-size: 11px; font-weight: 700; flex-shrink: 0; color: #d4a44c; background: rgba(212,164,76,0.1); padding: 2px 8px; border-radius: 6px; }
.quest-limit--full { color: #e74c3c; background: rgba(231,76,60,0.1); }
.quest-reward-tag { font-size: 11px; font-weight: 700; color: #f1c40f; margin-top: 3px; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }
.modal-box {
  background: linear-gradient(145deg, #1e0e0a, #1a1a2e);
  border: 1px solid rgba(212,164,76,0.3); border-radius: 16px;
  padding: 24px; width: 100%; max-width: 560px;
  max-height: 85vh; overflow-y: auto;
}
.modal-title { font-family: 'Cinzel', serif; font-size: 18px; color: #d4a44c; margin: 0 0 16px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 16px; }

/* Form */
.form-label { display: block; font-size: 11px; font-weight: 800; color: #8b7355; letter-spacing: 0.05em; margin: 14px 0 6px; }
.form-input, .form-textarea {
  width: 100%; padding: 10px 12px; border-radius: 8px; font-size: 14px;
  background: rgba(0,0,0,0.3); border: 1px solid rgba(212,164,76,0.2);
  color: #e8d5b7; box-sizing: border-box;
}
.form-input:focus, .form-textarea:focus { outline: none; border-color: rgba(212,164,76,0.5); }
.form-textarea { resize: vertical; font-family: 'Fira Code', 'SF Mono', 'Menlo', monospace; }
.query-input { font-size: 14px; color: #3498db; line-height: 1.5; }
.form-checkbox { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #8b7355; margin-top: 12px; }

/* Query Validation */
.query-validation { font-size: 12px; padding: 6px 10px; border-radius: 6px; margin-top: 6px; }
.query-validation.valid { color: #2ecc71; background: rgba(46,204,113,0.08); }
.query-validation.invalid { color: #e74c3c; background: rgba(231,76,60,0.08); }

/* Preview Result */
.preview-result { margin: 10px 0; padding: 12px; border-radius: 10px; background: rgba(0,0,0,0.2); border: 1px solid rgba(52,152,219,0.15); }
.preview-header { font-size: 14px; color: #d4a44c; margin-bottom: 8px; }
.preview-users { display: flex; flex-direction: column; gap: 6px; max-height: 200px; overflow-y: auto; }
.preview-user { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; background: rgba(255,255,255,0.03); }
.preview-user-img { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.preview-user-ph { font-size: 16px; }
.preview-user-info { flex: 1; }
.preview-user-name { font-size: 13px; color: #e8d5b7; font-weight: 600; }
.preview-user-vals { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 2px; }
.preview-field-tag { font-size: 10px; padding: 1px 6px; border-radius: 4px; background: rgba(52,152,219,0.1); color: #3498db; font-family: 'Fira Code', 'SF Mono', monospace; }

/* Fields Panel */
.fields-panel { margin-top: 10px; border: 1px solid rgba(212,164,76,0.1); border-radius: 8px; overflow: hidden; }
.fields-toggle { padding: 10px 12px; font-size: 12px; font-weight: 700; color: #d4a44c; cursor: pointer; background: rgba(212,164,76,0.05); list-style: none; }
.fields-toggle::-webkit-details-marker { display: none; }
.fields-toggle::before { content: '▶ '; font-size: 10px; }
details[open] > .fields-toggle::before { content: '▼ '; }
.fields-list { padding: 4px; }
.field-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  transition: background .15s;
}
.field-row:hover { background: rgba(212,164,76,0.08); }
.field-name { font-size: 12px; color: #3498db; background: rgba(52,152,219,0.1); padding: 2px 6px; border-radius: 4px; flex-shrink: 0; min-width: 110px; }
.field-desc { font-size: 12px; color: #8b7355; flex: 1; }
.field-example { font-size: 11px; color: #6b5a3e; flex-shrink: 0; }
</style>
