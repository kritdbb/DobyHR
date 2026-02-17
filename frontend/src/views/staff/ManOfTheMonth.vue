<template>
  <div class="staff-page">
    <div class="motm-header">
      <router-link to="/staff/services" class="motm-back">← Back</router-link>
      <h1 class="page-title">🏆 Man of the Month</h1>
      <p class="page-sub">{{ month || 'Loading...' }}</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Gathering legends...</p>
    </div>

    <div v-else class="leaderboard-list">
      <!-- Most Mana Received -->
      <div class="lb-section">
        <div class="lb-title">✨ Most Mana Received</div>
        <div v-if="hasReward(rewards.motm_mana)" class="lb-reward">
          <div v-if="formatReward(rewards.motm_mana)">Winner Reward : {{ formatReward(rewards.motm_mana) }}</div>
          <div v-if="rewards.motm_mana && rewards.motm_mana.badge_id" class="lb-badge-row">
            <img v-if="rewards.motm_mana.badge_image" :src="rewards.motm_mana.badge_image" class="lb-badge-icon" />
            <span>🎖️ {{ rewards.motm_mana.badge_name || 'Badge' }}</span>
            <span v-if="badgeStats(rewards.motm_mana)" class="lb-badge-stats">{{ badgeStats(rewards.motm_mana) }}</span>
          </div>
        </div>
        <div v-if="data.most_mana_received.length === 0" class="lb-empty">No data yet</div>
        <div v-else class="lb-entries">
          <div v-for="(u, i) in data.most_mana_received" :key="'mana-' + u.user_id" class="lb-entry" :class="{ champion: i === 0 }">
            <div class="lb-rank">{{ i + 1 }}</div>
            <div class="lb-avatar">
              <img v-if="u.image" :src="u.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-ph">{{ (u.name || '?').charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ u.name }} {{ u.surname }}</div>
              <div class="lb-pos">{{ u.position }}</div>
            </div>
            <div class="lb-value mana">✨ {{ u.value.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Most Steps -->
      <div class="lb-section">
        <div class="lb-title">🥾 Most Steps</div>
        <div v-if="hasReward(rewards.motm_steps)" class="lb-reward">
          <div v-if="formatReward(rewards.motm_steps)">Winner Reward : {{ formatReward(rewards.motm_steps) }}</div>
          <div v-if="rewards.motm_steps && rewards.motm_steps.badge_id" class="lb-badge-row">
            <img v-if="rewards.motm_steps.badge_image" :src="rewards.motm_steps.badge_image" class="lb-badge-icon" />
            <span>🎖️ {{ rewards.motm_steps.badge_name || 'Badge' }}</span>
            <span v-if="badgeStats(rewards.motm_steps)" class="lb-badge-stats">{{ badgeStats(rewards.motm_steps) }}</span>
          </div>
        </div>
        <div v-if="data.most_steps.length === 0" class="lb-empty">No data yet</div>
        <div v-else class="lb-entries">
          <div v-for="(u, i) in data.most_steps" :key="'steps-' + u.user_id" class="lb-entry" :class="{ champion: i === 0 }">
            <div class="lb-rank">{{ i + 1 }}</div>
            <div class="lb-avatar">
              <img v-if="u.image" :src="u.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-ph">{{ (u.name || '?').charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ u.name }} {{ u.surname }}</div>
              <div class="lb-pos">{{ u.position }}</div>
            </div>
            <div class="lb-value steps">🥾 {{ u.value.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Most On-Time -->
      <div class="lb-section">
        <div class="lb-title">⏰ Most On-Time</div>
        <div v-if="hasReward(rewards.motm_ontime)" class="lb-reward">
          <div v-if="formatReward(rewards.motm_ontime)">Winner Reward : {{ formatReward(rewards.motm_ontime) }}</div>
          <div v-if="rewards.motm_ontime && rewards.motm_ontime.badge_id" class="lb-badge-row">
            <img v-if="rewards.motm_ontime.badge_image" :src="rewards.motm_ontime.badge_image" class="lb-badge-icon" />
            <span>🎖️ {{ rewards.motm_ontime.badge_name || 'Badge' }}</span>
            <span v-if="badgeStats(rewards.motm_ontime)" class="lb-badge-stats">{{ badgeStats(rewards.motm_ontime) }}</span>
          </div>
        </div>
        <div v-if="data.most_on_time.length === 0" class="lb-empty">No data yet</div>
        <div v-else class="lb-entries">
          <div v-for="(u, i) in data.most_on_time" :key="'ontime-' + u.user_id" class="lb-entry" :class="{ champion: i === 0 }">
            <div class="lb-rank">{{ i + 1 }}</div>
            <div class="lb-avatar">
              <img v-if="u.image" :src="u.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-ph">{{ (u.name || '?').charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ u.name }} {{ u.surname }}</div>
              <div class="lb-pos">{{ u.position }}</div>
            </div>
            <div class="lb-value ontime">⏰ {{ u.value }} days</div>
          </div>
        </div>
      </div>

      <!-- Most Gold Spent -->
      <div class="lb-section">
        <div class="lb-title">💰 Most Gold Spent</div>
        <div v-if="hasReward(rewards.motm_gold_spent)" class="lb-reward">
          <div v-if="formatReward(rewards.motm_gold_spent)">Winner Reward : {{ formatReward(rewards.motm_gold_spent) }}</div>
          <div v-if="rewards.motm_gold_spent && rewards.motm_gold_spent.badge_id" class="lb-badge-row">
            <img v-if="rewards.motm_gold_spent.badge_image" :src="rewards.motm_gold_spent.badge_image" class="lb-badge-icon" />
            <span>🎖️ {{ rewards.motm_gold_spent.badge_name || 'Badge' }}</span>
            <span v-if="badgeStats(rewards.motm_gold_spent)" class="lb-badge-stats">{{ badgeStats(rewards.motm_gold_spent) }}</span>
          </div>
        </div>
        <div v-if="data.most_gold_spent.length === 0" class="lb-empty">No data yet</div>
        <div v-else class="lb-entries">
          <div v-for="(u, i) in data.most_gold_spent" :key="'gold-' + u.user_id" class="lb-entry" :class="{ champion: i === 0 }">
            <div class="lb-rank">{{ i + 1 }}</div>
            <div class="lb-avatar">
              <img v-if="u.image" :src="u.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-ph">{{ (u.name || '?').charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ u.name }} {{ u.surname }}</div>
              <div class="lb-pos">{{ u.position }}</div>
            </div>
            <div class="lb-value gold">💰 {{ u.value.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Most Anonymous Praises -->
      <div class="lb-section">
        <div class="lb-title">💬 Most Anonymous Praises</div>
        <div v-if="hasReward(rewards.motm_praises)" class="lb-reward">
          <div v-if="formatReward(rewards.motm_praises)">Winner Reward : {{ formatReward(rewards.motm_praises) }}</div>
          <div v-if="rewards.motm_praises && rewards.motm_praises.badge_id" class="lb-badge-row">
            <img v-if="rewards.motm_praises.badge_image" :src="rewards.motm_praises.badge_image" class="lb-badge-icon" />
            <span>🎖️ {{ rewards.motm_praises.badge_name || 'Badge' }}</span>
            <span v-if="badgeStats(rewards.motm_praises)" class="lb-badge-stats">{{ badgeStats(rewards.motm_praises) }}</span>
          </div>
        </div>
        <div v-if="data.most_anonymous_praises.length === 0" class="lb-empty">No data yet</div>
        <div v-else class="lb-entries">
          <div v-for="(u, i) in data.most_anonymous_praises" :key="'praise-' + u.user_id" class="lb-entry" :class="{ champion: i === 0 }">
            <div class="lb-rank">{{ i + 1 }}</div>
            <div class="lb-avatar">
              <img v-if="u.image" :src="u.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-ph">{{ (u.name || '?').charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ u.name }} {{ u.surname }}</div>
              <div class="lb-pos">{{ u.position }}</div>
            </div>
            <div class="lb-value praise">💬 {{ u.value }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getManOfTheMonth } from '../../services/api'

export default {
  name: 'ManOfTheMonth',
  data() {
    return {
      loading: true,
      month: '',
      data: {
        most_mana_received: [],
        most_steps: [],
        most_on_time: [],
        most_gold_spent: [],
        most_anonymous_praises: [],
      },
      rewards: {},
    }
  },
  async mounted() {
    try {
      const { data } = await getManOfTheMonth()
      this.month = data.month
      this.data = data
      this.rewards = data.rewards || {}
    } catch (e) {
      console.error('Failed to load Man of the Month', e)
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatReward(config) {
      if (!config) return ''
      const parts = []
      if (config.gold > 0) parts.push(`💰 Gold +${config.gold}`)
      if (config.mana > 0) parts.push(`✨ Mana +${config.mana}`)
      if (config.str > 0) parts.push(`⚔️ STR +${config.str}`)
      if (config.def > 0) parts.push(`🛡️ DEF +${config.def}`)
      if (config.luk > 0) parts.push(`🍀 LUK +${config.luk}`)
      return parts.length ? parts.join(', ') : ''
    },
    hasReward(config) {
      if (!config) return false
      return (config.gold > 0 || config.mana > 0 || config.str > 0 || config.def > 0 || config.luk > 0 || config.badge_id)
    },
    badgeStats(config) {
      if (!config || !config.badge_id) return ''
      const parts = []
      if (config.badge_str > 0) parts.push(`STR +${config.badge_str}`)
      if (config.badge_def > 0) parts.push(`DEF +${config.badge_def}`)
      if (config.badge_luk > 0) parts.push(`LUK +${config.badge_luk}`)
      return parts.length ? `(${parts.join(', ')})` : ''
    }
  }
}
</script>

<style scoped>
.staff-page { padding: 16px 0; }

.motm-header { margin-bottom: 20px; }
.motm-back {
  display: inline-block; margin-bottom: 8px;
  color: #b8860b; font-weight: 700; font-size: 13px;
  text-decoration: none; opacity: 0.8;
}
.motm-back:hover { opacity: 1; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 24px; font-weight: 800; color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub {
  color: #8b7355; font-size: 14px; font-weight: 600;
  font-style: italic;
}

.loading-state {
  text-align: center; padding: 60px 0; color: #8b7355;
}
.loading-spinner {
  width: 36px; height: 36px; border: 3px solid rgba(212,164,76,0.2);
  border-top-color: #d4a44c; border-radius: 50%;
  animation: spin 1s linear infinite; margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Leaderboard Section ─── */
.leaderboard-list {
  display: flex; flex-direction: column; gap: 18px;
}

.lb-section {
  background: linear-gradient(135deg, rgba(17,10,30,0.7), rgba(30,14,10,0.5));
  border: 1px solid rgba(212,164,76,0.12);
  border-radius: 14px;
  padding: 16px;
}

.lb-title {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 700; color: #d4a44c;
  margin-bottom: 4px;
  letter-spacing: 0.3px;
}

.lb-reward {
  font-size: 12px;
  color: #2ecc71;
  font-weight: 600;
  margin-bottom: 12px;
  padding: 4px 0;
}

.lb-badge-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.lb-badge-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(212,164,76,0.3);
}

.lb-badge-stats {
  color: #8b7355;
  font-size: 11px;
  font-weight: 400;
}

.lb-empty {
  text-align: center; padding: 16px 0;
  color: #8b7355; font-size: 13px; font-style: italic;
}

.lb-entries {
  display: flex; flex-direction: column; gap: 6px;
}

.lb-entry {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(0,0,0,0.15);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.15s;
}
.lb-entry.champion {
  background: linear-gradient(135deg, rgba(212,164,76,0.12), rgba(184,134,11,0.08));
  border-color: rgba(212,164,76,0.2);
  box-shadow: 0 0 12px rgba(212,164,76,0.08);
}

.lb-rank {
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  background: rgba(212,164,76,0.12);
  border: 1px solid rgba(212,164,76,0.2);
  color: #d4a44c; font-size: 12px; font-weight: 800;
  flex-shrink: 0;
}
.lb-entry.champion .lb-rank {
  background: linear-gradient(135deg, #d4a44c, #b8860b);
  color: #1a0e2b; border-color: transparent;
  box-shadow: 0 0 8px rgba(212,164,76,0.3);
}

.lb-avatar {
  width: 36px; height: 36px; flex-shrink: 0;
}
.lb-avatar-img {
  width: 100%; height: 100%; border-radius: 50%;
  object-fit: cover; border: 2px solid rgba(212,164,76,0.2);
}
.lb-avatar-ph {
  width: 100%; height: 100%; border-radius: 50%;
  background: rgba(212,164,76,0.12);
  display: flex; align-items: center; justify-content: center;
  color: #d4a44c; font-weight: 800; font-size: 14px;
}

.lb-info { flex: 1; min-width: 0; }
.lb-name {
  font-size: 13px; font-weight: 700; color: #e8d5b7;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.lb-pos {
  font-size: 11px; color: #8b7355; margin-top: 1px;
}

.lb-value {
  font-size: 13px; font-weight: 800; flex-shrink: 0;
  white-space: nowrap;
}
.lb-value.mana { color: #c39bd3; }
.lb-value.steps { color: #2ecc71; }
.lb-value.ontime { color: #f39c12; }
.lb-value.gold { color: #d4a44c; }
.lb-value.praise { color: #85c1e9; }
</style>
