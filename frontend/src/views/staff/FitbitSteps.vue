<template>
  <div class="staff-page">
    <!-- RPG Header Frame -->
    <div class="rpg-header-frame">
      <div class="rpg-corner rpg-corner--tl"></div>
      <div class="rpg-corner rpg-corner--tr"></div>
      <div class="rpg-corner rpg-corner--bl"></div>
      <div class="rpg-corner rpg-corner--br"></div>
      <router-link to="/staff/services" class="fit-back">← Back</router-link>
      <div class="rpg-header-inner">
        <div class="rpg-header-icon">🥾</div>
        <h1 class="rpg-header-title">Adventurer's Pedometer</h1>
        <p class="rpg-header-sub">Track your daily quests on foot</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Consulting the oracle...</p>
    </div>

    <!-- Not Connected -->
    <div v-else-if="!connected" class="connect-section">
      <div class="connect-card">
        <div class="connect-icon">⌚</div>
        <h2 class="connect-title">Link Your Fitbit</h2>
        <p class="connect-desc">Connect your Fitbit to track walking steps and compete with fellow adventurers</p>
        <button @click="authorize" class="connect-btn" :disabled="authLoading">
          {{ authLoading ? '⏳ Opening portal...' : '🔗 Connect Fitbit' }}
        </button>
      </div>
    </div>

    <!-- Connected -->
    <div v-else class="steps-content">
      <!-- Today's Steps -->
      <div class="today-card">
        <div class="today-header">
          <span class="today-label">Today's Journey</span>
          <button @click="syncAndRefresh" class="sync-btn" :disabled="syncing">
            {{ syncing ? '⏳' : '🔄' }} {{ syncing ? 'Syncing...' : 'Sync' }}
          </button>
        </div>
        <div class="today-steps">
          <span class="steps-number">{{ todaySteps.toLocaleString() }}</span>
          <span class="steps-unit">steps</span>
        </div>
        <!-- Single progress bar -->
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: dailyProgress + '%' }"></div>
        </div>
        <div class="progress-label">
          <span>🏁 Goal: {{ (daily2Goal.enabled ? daily2Goal.target : dailyGoal.target).toLocaleString() }} steps</span>
          <span>{{ daily2Goal.enabled ? daily2Progress : dailyProgress }}%</span>
        </div>
      </div>

      <!-- Daily Goal -->
      <div class="quests-card">
        <h3 class="section-title">⚔️ Daily Step Quest</h3>
        <p class="section-sub">Reach your daily goal to earn rewards (resets at midnight)</p>
        <div class="quest-row" :class="{ 'quest-row--done': dailyGoal.claimed, 'quest-row--ready': dailyGoal.reached && !dailyGoal.claimed }">
          <div class="quest-icon">
            <span v-if="dailyGoal.claimed">✅</span>
            <span v-else-if="dailyGoal.reached">⭐</span>
            <span v-else>🔒</span>
          </div>
          <div class="quest-info">
            <div class="quest-name">🗡️ Walk {{ dailyGoal.target.toLocaleString() }} steps</div>
            <div class="quest-reward">
              <span v-if="dailyGoal.str > 0" class="reward-tag reward-str">STR +{{ dailyGoal.str }}</span>
              <span v-if="dailyGoal.def > 0" class="reward-tag reward-def">DEF +{{ dailyGoal.def }}</span>
              <span v-if="dailyGoal.luk > 0" class="reward-tag reward-luk">LUK +{{ dailyGoal.luk }}</span>
              <span v-if="dailyGoal.gold > 0" class="reward-tag reward-gold">Gold +{{ dailyGoal.gold }}</span>
              <span v-if="dailyGoal.mana > 0" class="reward-tag reward-mana">Mana +{{ dailyGoal.mana }}</span>
              <span v-if="!hasAnyReward(dailyGoal)" class="reward-tag reward-none">No reward set</span>
            </div>
          </div>
          <button v-if="dailyGoal.reached && !dailyGoal.claimed" @click="claimReward('daily')"
                  class="claim-btn" :disabled="claiming">
            Claim
          </button>
          <span v-else-if="dailyGoal.claimed" class="claimed-label">Claimed</span>
          <span v-else class="locked-label">{{ todaySteps.toLocaleString() }}/{{ dailyGoal.target.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Daily Tier 2 Quest -->
      <div v-if="daily2Goal.enabled" class="quests-card">
        <h3 class="section-title">⚔️ Daily Step Quest II</h3>
        <p class="section-sub">Higher goal, bigger bounty (resets at midnight)</p>
        <div class="quest-row" :class="{ 'quest-row--done': daily2Goal.claimed, 'quest-row--ready': daily2Goal.reached && !daily2Goal.claimed }">
          <div class="quest-icon">
            <span v-if="daily2Goal.claimed">✅</span>
            <span v-else-if="daily2Goal.reached">⭐</span>
            <span v-else>🔒</span>
          </div>
          <div class="quest-info">
            <div class="quest-name">🗡️ Walk {{ daily2Goal.target.toLocaleString() }} steps</div>
            <div class="quest-reward">
              <span v-if="daily2Goal.str > 0" class="reward-tag reward-str">STR +{{ daily2Goal.str }}</span>
              <span v-if="daily2Goal.def > 0" class="reward-tag reward-def">DEF +{{ daily2Goal.def }}</span>
              <span v-if="daily2Goal.luk > 0" class="reward-tag reward-luk">LUK +{{ daily2Goal.luk }}</span>
              <span v-if="daily2Goal.gold > 0" class="reward-tag reward-gold">Gold +{{ daily2Goal.gold }}</span>
              <span v-if="daily2Goal.mana > 0" class="reward-tag reward-mana">Mana +{{ daily2Goal.mana }}</span>
              <span v-if="!hasAnyReward(daily2Goal)" class="reward-tag reward-none">No reward set</span>
            </div>
          </div>
          <button v-if="daily2Goal.reached && !daily2Goal.claimed" @click="claimReward('daily2')"
                  class="claim-btn" :disabled="claiming">
            Claim
          </button>
          <span v-else-if="daily2Goal.claimed" class="claimed-label">Claimed</span>
          <span v-else class="locked-label">{{ todaySteps.toLocaleString() }}/{{ daily2Goal.target.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Monthly Quest -->
      <div v-if="monthlyGoal.enabled" class="monthly-card">
        <h3 class="section-title">🗓️ Monthly Walk Quest</h3>
        <p class="section-sub">Walk {{ monthlyGoal.target.toLocaleString() }} steps this month</p>
        <div class="monthly-progress-wrap">
          <div class="monthly-bar-track">
            <div class="monthly-bar-fill" :style="{ width: monthlyProgress + '%' }"></div>
          </div>
          <div class="monthly-stats">
            <span>{{ monthlySteps.toLocaleString() }} / {{ monthlyGoal.target.toLocaleString() }}</span>
            <span>{{ monthlyProgress }}%</span>
          </div>
        </div>
        <div class="monthly-reward-row" :class="{ 'quest-row--done': monthlyGoal.claimed, 'quest-row--ready': monthlyGoal.reached && !monthlyGoal.claimed }">
          <div class="quest-icon">
            <span v-if="monthlyGoal.claimed">✅</span>
            <span v-else-if="monthlyGoal.reached">⭐</span>
            <span v-else>🔒</span>
          </div>
          <div class="quest-info">
            <div class="quest-name">🏅 Monthly Walker</div>
            <div class="quest-reward">
              <span v-if="monthlyGoal.str > 0" class="reward-tag reward-str">STR +{{ monthlyGoal.str }}</span>
              <span v-if="monthlyGoal.def > 0" class="reward-tag reward-def">DEF +{{ monthlyGoal.def }}</span>
              <span v-if="monthlyGoal.luk > 0" class="reward-tag reward-luk">LUK +{{ monthlyGoal.luk }}</span>
              <span v-if="monthlyGoal.gold > 0" class="reward-tag reward-gold">Gold +{{ monthlyGoal.gold }}</span>
              <span v-if="monthlyGoal.mana > 0" class="reward-tag reward-mana">Mana +{{ monthlyGoal.mana }}</span>
            </div>
          </div>
          <button v-if="monthlyGoal.reached && !monthlyGoal.claimed" @click="claimReward('monthly')"
                  class="claim-btn" :disabled="claiming">
            Claim
          </button>
          <span v-else-if="monthlyGoal.claimed" class="claimed-label">Claimed ✅</span>
          <span v-else class="locked-label">In progress</span>
        </div>
      </div>

      <!-- Weekly Chart -->
      <div class="chart-card">
        <h3 class="section-title">📊 Weekly Journey Log</h3>
        <div class="bar-chart">
          <div v-for="day in weeklyData" :key="day.date" class="bar-col">
            <div class="bar-value">{{ formatSteps(day.steps) }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ height: barHeight(day.steps) + '%' }" :class="{ 'bar-fill--today': day.isToday }"></div>
            </div>
            <div class="bar-label" :class="{ 'bar-label--today': day.isToday }">{{ day.dayName }}</div>
          </div>
        </div>
        <div class="weekly-total">
          🗺️ Weekly Total: <strong>{{ weeklyTotal.toLocaleString() }}</strong> steps
        </div>
      </div>

      <!-- Leaderboard -->
      <div class="leaderboard-card">
        <h3 class="section-title">🏆 Guild Leaderboard</h3>
        <p class="section-sub">This week's top walkers</p>
        <div v-if="leaderboard.length === 0" class="empty-lb">
          <div style="font-size: 36px; margin-bottom: 8px;">🦶</div>
          <p>No step data yet this week. Start walking!</p>
        </div>
        <div v-else class="lb-list">
          <div v-for="entry in leaderboard" :key="entry.user_id" class="lb-row" :class="{ 'lb-row--me': entry.user_id === myId }">
            <div class="lb-rank" :class="rankClass(entry.rank)">
              {{ entry.rank <= 3 ? rankMedal(entry.rank) : '#' + entry.rank }}
            </div>
            <div class="lb-avatar">
              <img v-if="entry.image" :src="entry.image" class="lb-avatar-img" />
              <div v-else class="lb-avatar-fallback">{{ entry.name.charAt(0) }}</div>
            </div>
            <div class="lb-info">
              <div class="lb-name">{{ entry.name }}</div>
              <div class="lb-pos">{{ entry.position || 'Adventurer' }}</div>
            </div>
            <div class="lb-steps">{{ entry.total_steps.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Disconnect -->
      <div class="disconnect-wrap">
        <button @click="disconnect" class="disconnect-btn">🔌 Disconnect Fitbit</button>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getFitbitAuthUrl, fitbitCallback, getFitbitStatus, syncFitbitSteps,
  getMyFitbitSteps, getFitbitLeaderboard, disconnectFitbit,
  getStepGoals, claimStepReward
} from '../../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      loading: true,
      connected: false,
      authLoading: false,
      syncing: false,
      claiming: false,
      steps: [],
      leaderboard: [],
      myId: null,
      goals: {
        today_steps: 0,
        daily_goal: { target: 5000, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false },
        daily2_goal: { target: 0, enabled: false, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false },
        monthly_steps: 0,
        monthly_goal: { target: 75000, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false, enabled: true },
      },
    }
  },
  computed: {
    todaySteps() {
      return this.goals.today_steps || 0
    },
    dailyGoal() {
      return this.goals.daily_goal || { target: 5000, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false }
    },
    dailyProgress() {
      const t = this.dailyGoal.target || 1
      return Math.min(100, Math.round((this.todaySteps / t) * 100))
    },
    daily2Goal() {
      return this.goals.daily2_goal || { target: 0, enabled: false, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false }
    },
    daily2Progress() {
      const t = this.daily2Goal.target || 1
      return Math.min(100, Math.round((this.todaySteps / t) * 100))
    },
    monthlyGoal() {
      return this.goals.monthly_goal || { target: 0, enabled: false }
    },
    monthlySteps() {
      return this.goals.monthly_steps || 0
    },
    monthlyProgress() {
      const t = this.monthlyGoal.target || 1
      return Math.min(100, Math.round((this.monthlySteps / t) * 100))
    },
    weeklyData() {
      const days = []
      const today = new Date()
      const dayOfWeek = today.getDay()
      const monday = new Date(today)
      monday.setDate(today.getDate() - ((dayOfWeek + 6) % 7))
      const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
      for (let i = 0; i < 7; i++) {
        const d = new Date(monday)
        d.setDate(monday.getDate() + i)
        const dateStr = d.toISOString().split('T')[0]
        const entry = this.steps.find(s => s.date === dateStr)
        days.push({
          date: dateStr,
          steps: entry ? entry.steps : 0,
          dayName: dayNames[i],
          isToday: dateStr === today.toISOString().split('T')[0],
        })
      }
      return days
    },
    weeklyTotal() {
      return this.weeklyData.reduce((sum, d) => sum + d.steps, 0)
    },
    maxSteps() {
      return Math.max(...this.weeklyData.map(d => d.steps), 1)
    },
  },
  methods: {
    hasAnyReward(goal) {
      return (goal.str > 0 || goal.def > 0 || goal.luk > 0 || goal.gold > 0 || goal.mana > 0)
    },
    barHeight(steps) {
      return Math.max(4, Math.round((steps / this.maxSteps) * 100))
    },
    formatSteps(n) {
      if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
      return n
    },
    rankClass(rank) {
      if (rank === 1) return 'rank-gold'
      if (rank === 2) return 'rank-silver'
      if (rank === 3) return 'rank-bronze'
      return ''
    },
    rankMedal(rank) {
      return ['🥇', '🥈', '🥉'][rank - 1]
    },
    async authorize() {
      this.authLoading = true
      try {
        const { data } = await getFitbitAuthUrl()
        window.location.href = data.authorize_url
      } catch (e) {
        this.showToast('Failed to get authorization URL', 'error')
      } finally {
        this.authLoading = false
      }
    },
    async handleCallback(code) {
      try {
        await fitbitCallback(code)
        this.connected = true
        this.showToast('Fitbit linked successfully! ⌚', 'success')
        await this.loadData()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to link Fitbit', 'error')
      }
    },
    async syncAndRefresh() {
      this.syncing = true
      try {
        await syncFitbitSteps()
        await this.loadData()
        this.showToast('Steps synced! 🥾', 'success')
      } catch (e) {
        if (e.response?.status === 401) {
          this.showToast('Fitbit session expired. Please reconnect.', 'error')
          this.connected = false
        } else {
          this.showToast(e.response?.data?.detail || 'Sync failed', 'error')
        }
      } finally {
        this.syncing = false
      }
    },
    async claimReward(rewardType) {
      this.claiming = true
      try {
        const { data } = await claimStepReward(rewardType)
        this.showToast(data.message, 'success')
        await this.loadGoals()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to claim reward', 'error')
      } finally {
        this.claiming = false
      }
    },
    async loadSteps() {
      try {
        const { data } = await getMyFitbitSteps(30)
        this.steps = data
      } catch (e) { console.error(e) }
    },
    async loadLeaderboard() {
      try {
        const { data } = await getFitbitLeaderboard()
        this.leaderboard = data
      } catch (e) { console.error(e) }
    },
    async loadGoals() {
      try {
        const { data } = await getStepGoals()
        this.goals = data
      } catch (e) { console.error(e) }
    },
    async loadData() {
      await Promise.all([this.loadSteps(), this.loadLeaderboard(), this.loadGoals()])
    },
    async disconnect() {
      if (!confirm('Disconnect your Fitbit account?')) return
      try {
        await disconnectFitbit()
        this.connected = false
        this.steps = []
        this.leaderboard = []
        this.showToast('Fitbit disconnected', 'success')
      } catch (e) {
        this.showToast('Failed to disconnect', 'error')
      }
    },
  },
  async mounted() {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    this.myId = user.user_id || user.id

    const code = this.$route.query.code
    if (code) {
      this.$router.replace({ path: '/staff/fitbit', query: {} })
      await this.handleCallback(code)
      this.loading = false
      return
    }

    try {
      const { data } = await getFitbitStatus()
      this.connected = data.connected
      if (this.connected) {
        await this.loadData()
      }
    } catch (e) {
      console.error(e)
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped>
/* ── RPG Header Frame ─────────────────────────── */
.rpg-header-frame {
  position: relative;
  padding: 28px 24px 24px;
  margin-bottom: 20px;
  border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.9), rgba(26,26,46,0.95));
  border: 2px solid rgba(212,164,76,0.5);
  box-shadow:
    0 0 20px rgba(212,164,76,0.15),
    inset 0 0 30px rgba(0,0,0,0.3);
  overflow: visible;
}
.rpg-header-frame::before {
  content: '';
  position: absolute;
  inset: 4px;
  border-radius: 12px;
  border: 1px solid rgba(212,164,76,0.15);
  pointer-events: none;
}
.rpg-corner {
  position: absolute; width: 20px; height: 20px;
  border-color: #d4a44c; border-style: solid;
}
.rpg-corner--tl { top: -2px; left: -2px; border-width: 3px 0 0 3px; border-radius: 4px 0 0 0; }
.rpg-corner--tr { top: -2px; right: -2px; border-width: 3px 3px 0 0; border-radius: 0 4px 0 0; }
.rpg-corner--bl { bottom: -2px; left: -2px; border-width: 0 0 3px 3px; border-radius: 0 0 0 4px; }
.rpg-corner--br { bottom: -2px; right: -2px; border-width: 0 3px 3px 0; border-radius: 0 0 4px 0; }

.fit-back {
  display: inline-block; margin-bottom: 12px;
  color: #8b7355; text-decoration: none; font-weight: 700; font-size: 13px;
}
.fit-back:hover { color: #d4a44c; }

.rpg-header-inner { text-align: center; }
.rpg-header-icon {
  font-size: 48px; margin-bottom: 8px;
  filter: drop-shadow(0 4px 12px rgba(212,164,76,0.4));
}
.rpg-header-title {
  font-family: 'Cinzel', serif;
  font-size: 22px; font-weight: 900;
  color: #d4a44c;
  text-shadow: 0 2px 12px rgba(212,164,76,0.3);
  margin: 0 0 4px;
}
.rpg-header-sub {
  color: #8b7355; font-size: 13px; margin: 0;
  font-style: italic;
}

/* ── Loading ──────────────────────────────────── */
.loading-state { text-align: center; padding: 60px 16px; color: #8b7355; }
.loading-spinner {
  width: 40px; height: 40px; border-radius: 50%; margin: 0 auto 16px;
  border: 4px solid rgba(212,164,76,0.2); border-top-color: #d4a44c;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Connect ──────────────────────────────────── */
.connect-section { display: flex; justify-content: center; padding: 20px 0; }
.connect-card {
  text-align: center; padding: 48px 32px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3); width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.connect-icon { font-size: 64px; margin-bottom: 16px; filter: drop-shadow(0 4px 12px rgba(212,164,76,0.3)); }
.connect-title {
  font-family: 'Cinzel', serif; font-size: 22px; font-weight: 800;
  color: #d4a44c; margin-bottom: 8px;
}
.connect-desc { color: #8b7355; font-size: 14px; margin-bottom: 24px; line-height: 1.5; }
.connect-btn {
  padding: 14px 32px; border-radius: 10px; font-size: 15px; font-weight: 800;
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
  border: 2px solid #d4a44c; cursor: pointer; transition: all 0.25s;
  box-shadow: 0 4px 20px rgba(212,164,76,0.3);
}
.connect-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d4a44c, #ffd700);
  box-shadow: 0 8px 32px rgba(212,164,76,0.4); transform: translateY(-2px);
}
.connect-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* ── Today ────────────────────────────────────── */
.steps-content { display: flex; flex-direction: column; gap: 16px; }

.today-card {
  padding: 24px 20px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3);
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
.today-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.today-label { font-family: 'Cinzel', serif; font-weight: 700; font-size: 15px; color: #d4a44c; }
.sync-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700;
  background: rgba(212,164,76,0.15); color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.3); cursor: pointer; transition: all 0.2s;
}
.sync-btn:hover:not(:disabled) { background: rgba(212,164,76,0.25); }
.sync-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.today-steps { text-align: center; margin: 16px 0 20px; }
.steps-number {
  font-family: 'Cinzel', serif; font-size: 48px; font-weight: 900;
  color: #d4a44c; text-shadow: 0 2px 16px rgba(212,164,76,0.4);
  letter-spacing: -1px;
}
.steps-unit { font-size: 16px; color: #8b7355; font-weight: 700; margin-left: 6px; }

/* Progress bar */
.progress-track {
  position: relative; height: 14px; border-radius: 7px;
  background: rgba(26,26,46,0.8); overflow: hidden;
  border: 1px solid rgba(212,164,76,0.15);
}
.progress-fill {
  height: 100%; border-radius: 7px; transition: width 0.6s ease;
  background: linear-gradient(90deg, #b8860b, #d4a44c, #ffd700);
  box-shadow: 0 0 12px rgba(212,164,76,0.4);
}
.progress-label {
  display: flex; justify-content: space-between; margin-top: 8px;
  font-size: 12px; color: #8b7355; font-weight: 600;
}

/* ── Daily Quest ──────────────────────────────── */
.quests-card {
  padding: 24px 20px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3);
}
.section-title {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 700;
  color: #d4a44c; margin-bottom: 4px;
}
.section-sub { font-size: 12px; color: #8b7355; margin-bottom: 16px; }

.quest-row {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 12px;
  background: rgba(26,26,46,0.5);
  border: 1px solid rgba(212,164,76,0.08);
  transition: all 0.2s;
}
.quest-row--ready {
  border-color: rgba(212,164,76,0.4);
  background: rgba(212,164,76,0.08);
  box-shadow: 0 0 12px rgba(212,164,76,0.1);
}
.quest-row--done { opacity: 0.6; }
.quest-icon { font-size: 22px; flex-shrink: 0; }
.quest-info { flex: 1; min-width: 0; }
.quest-name { font-weight: 700; font-size: 14px; color: #e8d5b7; margin-bottom: 4px; }
.quest-reward { display: flex; gap: 6px; flex-wrap: wrap; }
.reward-tag {
  display: inline-block; padding: 2px 8px; border-radius: 6px;
  font-size: 11px; font-weight: 700;
}
.reward-str { background: rgba(231,76,60,0.15); color: #e74c3c; border: 1px solid rgba(231,76,60,0.2); }
.reward-def { background: rgba(52,152,219,0.15); color: #3498db; border: 1px solid rgba(52,152,219,0.2); }
.reward-luk { background: rgba(155,89,182,0.15); color: #9b59b6; border: 1px solid rgba(155,89,182,0.2); }
.reward-gold { background: rgba(212,164,76,0.15); color: #d4a44c; border: 1px solid rgba(212,164,76,0.2); }
.reward-mana { background: rgba(46,204,113,0.15); color: #2ecc71; border: 1px solid rgba(46,204,113,0.2); }
.reward-none { background: rgba(127,140,141,0.15); color: #7f8c8d; border: 1px solid rgba(127,140,141,0.2); }

.claim-btn {
  padding: 8px 18px; border-radius: 8px; font-size: 12px; font-weight: 800;
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
  border: 2px solid #d4a44c; cursor: pointer; transition: all 0.25s;
  box-shadow: 0 2px 12px rgba(212,164,76,0.3);
  animation: glow-pulse 2s ease-in-out infinite;
}
.claim-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d4a44c, #ffd700);
  transform: translateY(-1px);
}
.claim-btn:disabled { opacity: 0.5; cursor: not-allowed; animation: none; }
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 2px 12px rgba(212,164,76,0.3); }
  50% { box-shadow: 0 2px 20px rgba(212,164,76,0.6); }
}

.claimed-label { font-size: 12px; color: #27ae60; font-weight: 700; flex-shrink: 0; }
.locked-label { font-size: 11px; color: #8b7355; font-weight: 600; flex-shrink: 0; }

/* ── Monthly Quest ────────────────────────────── */
.monthly-card {
  padding: 24px 20px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3);
}
.monthly-progress-wrap { margin-bottom: 16px; }
.monthly-bar-track {
  height: 12px; border-radius: 6px;
  background: rgba(26,26,46,0.8); overflow: hidden;
  border: 1px solid rgba(212,164,76,0.15);
}
.monthly-bar-fill {
  height: 100%; border-radius: 6px; transition: width 0.6s ease;
  background: linear-gradient(90deg, #2ecc71, #27ae60);
  box-shadow: 0 0 10px rgba(46,204,113,0.3);
}
.monthly-stats {
  display: flex; justify-content: space-between; margin-top: 6px;
  font-size: 12px; color: #8b7355; font-weight: 600;
}
.monthly-reward-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; border-radius: 12px;
  background: rgba(26,26,46,0.5);
  border: 1px solid rgba(212,164,76,0.08);
  transition: all 0.2s;
}

/* ── Weekly Chart ─────────────────────────────── */
.chart-card {
  padding: 24px 20px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3);
}
.bar-chart { display: flex; gap: 8px; align-items: flex-end; height: 160px; margin-bottom: 16px; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; }
.bar-value { font-size: 10px; font-weight: 700; color: #8b7355; }
.bar-track {
  flex: 1; width: 100%; border-radius: 6px 6px 4px 4px;
  background: rgba(26,26,46,0.6); display: flex; align-items: flex-end;
  overflow: hidden;
}
.bar-fill {
  width: 100%; border-radius: 4px 4px 0 0; transition: height 0.6s ease;
  background: linear-gradient(180deg, #d4a44c, #b8860b);
}
.bar-fill--today {
  background: linear-gradient(180deg, #ffd700, #d4a44c);
  box-shadow: 0 0 10px rgba(255,215,0,0.3);
}
.bar-label { font-size: 11px; font-weight: 700; color: #8b7355; }
.bar-label--today { color: #ffd700; }

.weekly-total {
  text-align: center; padding: 10px; border-radius: 8px;
  background: rgba(212,164,76,0.08); border: 1px solid rgba(212,164,76,0.15);
  font-size: 13px; color: #8b7355; font-weight: 600;
}
.weekly-total strong { color: #d4a44c; }

/* ── Leaderboard ──────────────────────────────── */
.leaderboard-card {
  padding: 24px 20px; border-radius: 16px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.3);
}
.empty-lb { text-align: center; padding: 24px; color: #8b7355; font-size: 14px; }

.lb-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.lb-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 10px;
  background: rgba(26,26,46,0.5); border: 1px solid rgba(212,164,76,0.08);
  transition: all 0.2s;
}
.lb-row--me {
  background: rgba(212,164,76,0.1);
  border-color: rgba(212,164,76,0.3);
  box-shadow: 0 0 12px rgba(212,164,76,0.08);
}
.lb-rank { font-size: 18px; font-weight: 800; min-width: 32px; text-align: center; color: #8b7355; }
.rank-gold { color: #ffd700; text-shadow: 0 0 8px rgba(255,215,0,0.4); }
.rank-silver { color: #c0c0c0; text-shadow: 0 0 6px rgba(192,192,192,0.3); }
.rank-bronze { color: #cd7f32; text-shadow: 0 0 6px rgba(205,127,50,0.3); }

.lb-avatar { flex-shrink: 0; }
.lb-avatar-img {
  width: 40px; height: 40px; border-radius: 10px; object-fit: cover;
  border: 2px solid rgba(212,164,76,0.3);
}
.lb-avatar-fallback {
  width: 40px; height: 40px; border-radius: 10px;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 16px; color: #1c1208;
}
.lb-info { flex: 1; min-width: 0; }
.lb-name { font-weight: 700; font-size: 14px; color: #e8d5b7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lb-pos { font-size: 11px; color: #8b7355; }
.lb-steps { font-weight: 800; font-size: 15px; color: #d4a44c; flex-shrink: 0; }

/* ── Disconnect ───────────────────────────────── */
.disconnect-wrap { text-align: center; padding: 8px 0 24px; }
.disconnect-btn {
  padding: 8px 20px; border-radius: 8px; font-size: 12px; font-weight: 700;
  background: rgba(192,57,43,0.1); color: #e74c3c;
  border: 1px solid rgba(192,57,43,0.2); cursor: pointer; transition: all 0.2s;
}
.disconnect-btn:hover { background: rgba(192,57,43,0.2); }
</style>
