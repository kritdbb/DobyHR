<template>
  <div class="battle-admin">
    <div class="page-header">
      <h2>⚔️ Battle Arena</h2>
      <p>จัดการคู่ต่อสู้และกำหนดรางวัล</p>
    </div>

    <!-- ═══ Reward Settings ═══ -->
    <div class="settings-card">
      <h3 class="settings-title">🏆 Reward / Penalty Settings</h3>
      <div class="reward-grid">
        <div class="reward-col winner-col">
          <div class="reward-label">🏆 Winner Takes</div>
          <div class="reward-fields">
            <label><span>💰 Gold</span><input v-model.number="rewards.winner_gold" type="number" min="0" /></label>
            <label><span>✨ Mana</span><input v-model.number="rewards.winner_mana" type="number" min="0" /></label>
            <label><span>⚔️ STR</span><input v-model.number="rewards.winner_str" type="number" min="0" /></label>
            <label><span>🛡️ DEF</span><input v-model.number="rewards.winner_def" type="number" min="0" /></label>
            <label><span>🍀 LUK</span><input v-model.number="rewards.winner_luk" type="number" min="0" /></label>
          </div>
        </div>
        <div class="reward-col loser-col">
          <div class="reward-label">💀 Loser Loses</div>
          <div class="reward-fields">
            <label><span>💰 Gold</span><input v-model.number="rewards.loser_gold" type="number" min="0" /></label>
            <label><span>✨ Mana</span><input v-model.number="rewards.loser_mana" type="number" min="0" /></label>
            <label><span>⚔️ STR</span><input v-model.number="rewards.loser_str" type="number" min="0" /></label>
            <label><span>🛡️ DEF</span><input v-model.number="rewards.loser_def" type="number" min="0" /></label>
            <label><span>🍀 LUK</span><input v-model.number="rewards.loser_luk" type="number" min="0" /></label>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ New Matches ═══ -->
    <div class="matches-card">
      <h3 class="settings-title">➕ Create Matches</h3>
      <div v-for="(match, idx) in newMatches" :key="idx" class="match-row">
        <div class="match-fighters">
          <select v-model="match.player_a_id" class="player-select" @change="onSelectChange(idx)">
            <option :value="null" disabled>— Player A —</option>
            <option v-for="s in staffList" :key="'a'+s.id" :value="s.id" :disabled="isStaffUsed(s.id, idx)">
              {{ s.name }} {{ s.surname }} (STR {{ s.str }} / DEF {{ s.def }} / LUK {{ s.luk }})
            </option>
          </select>
          <span class="match-vs">⚔️</span>
          <select v-model="match.player_b_id" class="player-select" @change="onSelectChange(idx)">
            <option :value="null" disabled>— Player B —</option>
            <option v-for="s in staffList" :key="'b'+s.id" :value="s.id" :disabled="isStaffUsed(s.id, idx)">
              {{ s.name }} {{ s.surname }} (STR {{ s.str }} / DEF {{ s.def }} / LUK {{ s.luk }})
            </option>
          </select>
        </div>
        <div class="match-controls">
          <button class="btn-random" @click="randomPair(idx)" title="Random pair">🎲</button>
          <input v-model="match.scheduled_time" type="datetime-local" class="time-input" />
          <button class="btn-remove" @click="removeMatch(idx)" v-if="newMatches.length > 1" title="Remove">🗑️</button>
        </div>
      </div>
      <div class="match-actions">
        <button class="btn-add" @click="addMatch">➕ Add Match</button>
        <button class="btn-save" @click="saveMatches" :disabled="saving">
          {{ saving ? '⏳ Saving...' : '💾 Save All' }}
        </button>
      </div>
    </div>

    <!-- ═══ Scheduled Battles ═══ -->
    <div class="scheduled-card">
      <h3 class="settings-title">📋 Scheduled Battles</h3>
      <div v-if="scheduledBattles.length === 0" class="empty-msg">ยังไม่มี battle ที่กำลังจะแข่ง</div>
      <div v-for="b in scheduledBattles" :key="b.id" class="scheduled-row">
        <div class="scheduled-fighters">
          <div class="sched-player">
            <img v-if="b.player_a && b.player_a.image" :src="b.player_a.image" class="sched-avatar" />
            <span v-else class="sched-avatar-ph">{{ (b.player_a?.name || '?').charAt(0) }}</span>
            <span class="sched-name">{{ b.player_a?.name }}</span>
          </div>
          <span class="sched-vs">⚔️</span>
          <div class="sched-player">
            <img v-if="b.player_b && b.player_b.image" :src="b.player_b.image" class="sched-avatar" />
            <span v-else class="sched-avatar-ph">{{ (b.player_b?.name || '?').charAt(0) }}</span>
            <span class="sched-name">{{ b.player_b?.name }}</span>
          </div>
        </div>
        <div class="sched-info">
          <span class="sched-time">📅 {{ formatTime(b.scheduled_time) }}</span>
          <span v-if="b.winner_gold || b.loser_gold" class="sched-reward">
            🏆+{{ b.winner_gold }}G / 💀-{{ b.loser_gold }}G
          </span>
        </div>
        <button class="btn-delete" @click="deleteBattle(b.id)">🗑️</button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../services/api'

export default {
  name: 'BattleArena',
  inject: ['showToast'],
  data() {
    return {
      staffList: [],
      scheduledBattles: [],
      saving: false,
      rewards: {
        winner_gold: 10, winner_mana: 0, winner_str: 0, winner_def: 0, winner_luk: 0,
        loser_gold: 5, loser_mana: 0, loser_str: 0, loser_def: 0, loser_luk: 0,
      },
      newMatches: [this.emptyMatch()],
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    emptyMatch() {
      return { player_a_id: null, player_b_id: null, scheduled_time: '' }
    },
    async loadData() {
      try {
        const [staffRes, battlesRes] = await Promise.all([
          api.get('/api/pvp/admin/staff'),
          api.get('/api/pvp/admin/list'),
        ])
        this.staffList = staffRes.data || []
        this.scheduledBattles = battlesRes.data || []
      } catch (e) {
        console.error('Failed to load data:', e)
      }
    },
    addMatch() {
      this.newMatches.push(this.emptyMatch())
    },
    removeMatch(idx) {
      this.newMatches.splice(idx, 1)
    },
    isStaffUsed(staffId, currentIdx) {
      // Check if staff is already selected in another match row (different from current row)
      for (let i = 0; i < this.newMatches.length; i++) {
        if (i === currentIdx) continue
        if (this.newMatches[i].player_a_id === staffId || this.newMatches[i].player_b_id === staffId) return true
      }
      return false
    },
    onSelectChange() {
      // noop — just triggers reactivity
    },
    async randomPair(idx) {
      try {
        const res = await api.post('/api/pvp/admin/random-pair')
        const pair = res.data
        if (pair.length >= 2) {
          this.newMatches[idx].player_a_id = pair[0].id
          this.newMatches[idx].player_b_id = pair[1].id
        }
      } catch (e) {
        this.showToast?.('❌ Failed to random pair', 'error')
      }
    },
    async saveMatches() {
      // Validate
      const valid = this.newMatches.filter(m => m.player_a_id && m.player_b_id && m.scheduled_time)
      if (valid.length === 0) {
        this.showToast?.('⚠️ กรุณาเลือก player และเวลาอย่างน้อย 1 คู่', 'error')
        return
      }

      this.saving = true
      try {
        const payload = {
          matches: valid.map(m => ({
            player_a_id: m.player_a_id,
            player_b_id: m.player_b_id,
            scheduled_time: m.scheduled_time,
          })),
          ...this.rewards,
        }
        await api.post('/api/pvp/admin/create', payload)
        this.showToast?.(`✅ สร้าง ${valid.length} battle(s) สำเร็จ!`, 'success')
        this.newMatches = [this.emptyMatch()]
        await this.loadData()
      } catch (e) {
        this.showToast?.('❌ ' + (e.response?.data?.detail || 'Failed to create'), 'error')
      } finally {
        this.saving = false
      }
    },
    async deleteBattle(id) {
      if (!confirm('ลบ battle นี้?')) return
      try {
        await api.delete(`/api/pvp/admin/delete/${id}`)
        this.showToast?.('🗑️ ลบแล้ว', 'success')
        await this.loadData()
      } catch (e) {
        this.showToast?.('❌ Failed to delete', 'error')
      }
    },
    formatTime(iso) {
      if (!iso) return '—'
      // scheduled_time is stored as naive Bangkok time (UTC+7)
      const isoWithTz = iso.includes('+') || iso.includes('Z') ? iso : iso + '+07:00'
      const d = new Date(isoWithTz)
      return d.toLocaleString('th-TH', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Asia/Bangkok' })
    },
  },
}
</script>

<style scoped>
.battle-admin { max-width: 800px; margin: 0 auto; padding: 20px; }

.page-header h2 { color: #d4a44c; margin: 0; }
.page-header p { color: #8b7355; margin: 4px 0 20px; font-size: 14px; }

/* ═══ Cards ═══ */
.settings-card, .matches-card, .scheduled-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 1px solid rgba(212,164,76,0.15);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}
.settings-title { color: #d4a44c; font-size: 16px; margin: 0 0 14px; }

/* ═══ Reward Grid ═══ */
.reward-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.reward-label { font-weight: 700; font-size: 14px; margin-bottom: 8px; }
.winner-col .reward-label { color: #ffd700; }
.loser-col .reward-label { color: #ff6b6b; }
.reward-fields { display: flex; flex-direction: column; gap: 6px; }
.reward-fields label {
  display: flex; align-items: center; gap: 8px;
}
.reward-fields label span { font-size: 13px; color: #c8b89a; min-width: 60px; }
.reward-fields input {
  flex: 1;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(212,164,76,0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #e0d5c0;
  font-size: 14px;
  max-width: 80px;
}
.reward-fields input:focus { border-color: #d4a44c; outline: none; }

/* ═══ Match Rows ═══ */
.match-row {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(212,164,76,0.1);
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}
.match-fighters { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.match-vs { font-size: 18px; flex-shrink: 0; }
.player-select {
  flex: 1;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(212,164,76,0.2);
  border-radius: 6px;
  padding: 8px 10px;
  color: #e0d5c0;
  font-size: 13px;
}
.player-select option { background: #1a1a2e; color: #e0d5c0; }
.match-controls { display: flex; align-items: center; gap: 8px; }
.time-input {
  flex: 1;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(212,164,76,0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #e0d5c0;
  font-size: 13px;
}
.time-input::-webkit-calendar-picker-indicator { filter: invert(0.7); }
.btn-random {
  background: rgba(206,147,216,0.15);
  border: 1px solid rgba(206,147,216,0.3);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-random:hover { background: rgba(206,147,216,0.3); }
.btn-remove {
  background: rgba(255,60,60,0.1);
  border: 1px solid rgba(255,60,60,0.2);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 16px;
  cursor: pointer;
}
.btn-remove:hover { background: rgba(255,60,60,0.25); }

/* ═══ Action Buttons ═══ */
.match-actions { display: flex; gap: 12px; margin-top: 12px; }
.btn-add {
  flex: 1;
  padding: 10px;
  background: rgba(212,164,76,0.08);
  border: 1px dashed rgba(212,164,76,0.3);
  border-radius: 8px;
  color: #d4a44c;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-add:hover { background: rgba(212,164,76,0.15); }
.btn-save {
  flex: 1;
  padding: 10px;
  background: linear-gradient(135deg, rgba(212,164,76,0.3), rgba(255,215,0,0.15));
  border: 1px solid rgba(212,164,76,0.4);
  border-radius: 8px;
  color: #ffd700;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover { background: rgba(212,164,76,0.4); }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* ═══ Scheduled List ═══ */
.empty-msg { color: #8b7355; text-align: center; padding: 20px; font-size: 14px; }
.scheduled-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(212,164,76,0.08);
  border-radius: 8px;
  margin-bottom: 8px;
}
.scheduled-fighters { display: flex; align-items: center; gap: 8px; flex: 1; }
.sched-player { display: flex; align-items: center; gap: 6px; }
.sched-avatar {
  width: 32px; height: 32px; border-radius: 50%; object-fit: cover;
  border: 2px solid rgba(212,164,76,0.2);
}
.sched-avatar-ph {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(212,164,76,0.1);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; color: #8b7355; font-size: 14px;
}
.sched-name { font-size: 13px; color: #c8b89a; font-weight: 600; }
.sched-vs { font-size: 14px; }
.sched-info { display: flex; flex-direction: column; gap: 2px; }
.sched-time { font-size: 12px; color: #8b7355; }
.sched-reward { font-size: 11px; color: #d4a44c; }
.btn-delete {
  background: rgba(255,60,60,0.1);
  border: 1px solid rgba(255,60,60,0.2);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}
.btn-delete:hover { background: rgba(255,60,60,0.25); }

@media (max-width: 600px) {
  .reward-grid { grid-template-columns: 1fr; }
  .match-fighters { flex-direction: column; }
  .match-vs { display: none; }
  .scheduled-fighters { flex-direction: column; gap: 4px; }
}
</style>
