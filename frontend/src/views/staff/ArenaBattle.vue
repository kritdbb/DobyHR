<template>
  <div class="staff-page arena-page">
    <div class="arena-header">
      <router-link to="/staff/home" class="arena-back">← Back</router-link>
      <h1 class="arena-title">⚔️ A R E N A ⚔️</h1>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Preparing the arena...</p>
    </div>

    <!-- Scheduled (not yet 12:00) -->
    <div v-else-if="battle && battle.status === 'scheduled'" class="arena-waiting">
      <div class="fighters-row">
        <div class="char-card player-a"
          :style="bgStyle(battle.player_a)">
          <!-- Player A card -->
          <div class="person-portrait">
            <img v-if="getArtifactImage(battle.player_a.circle_artifact)"
              :src="getArtifactImage(battle.player_a.circle_artifact)" class="person-artifact-ring-img" />
            <div v-else-if="battle.player_a.circle_artifact" class="person-artifact-ring"
              :style="{ borderColor: getArtifactColor(battle.player_a.circle_artifact), boxShadow: '0 0 14px ' + getArtifactColor(battle.player_a.circle_artifact) + '66' }"></div>
            <img v-if="battle.player_a.image" :src="battle.player_a.image" class="person-img" />
            <div v-else class="person-placeholder">{{ (battle.player_a.name || '?').charAt(0) }}</div>
            <span class="person-role-tag" :class="battle.player_a.role">{{ battle.player_a.role }}</span>
          </div>
          <div class="person-name">{{ battle.player_a.name }}</div>
          <div class="person-surname">{{ battle.player_a.surname }}</div>
          <div class="person-position">〈 {{ battle.player_a.position || 'Adventurer' }} 〉</div>
          <div v-if="battle.player_a.status_text" class="person-status">"{{ battle.player_a.status_text }}"</div>
          <div class="person-badges" v-if="battle.player_a.badges && battle.player_a.badges.length">
            <div v-for="b in battle.player_a.badges.slice(0, 5)" :key="b.id" class="pb-circle" :title="b.name">
              <img v-if="b.image" :src="b.image" class="pb-img" />
              <span v-else>🏅</span>
            </div>
            <span v-if="battle.player_a.badges.length > 5" class="pb-more">+{{ battle.player_a.badges.length - 5 }}</span>
          </div>
          <div v-else class="person-no-badges">No badges yet</div>
          <div class="person-currency">
            <span class="cur gold">💰 {{ battle.player_a.coins }}</span>
            <span class="cur mana">✨ {{ battle.player_a.angel_coins }}</span>
          </div>
        </div>

        <div class="vs-badge">VS</div>

        <div class="char-card player-b"
          :style="bgStyle(battle.player_b)">
          <!-- Player B card -->
          <div class="person-portrait">
            <img v-if="getArtifactImage(battle.player_b.circle_artifact)"
              :src="getArtifactImage(battle.player_b.circle_artifact)" class="person-artifact-ring-img" />
            <div v-else-if="battle.player_b.circle_artifact" class="person-artifact-ring"
              :style="{ borderColor: getArtifactColor(battle.player_b.circle_artifact), boxShadow: '0 0 14px ' + getArtifactColor(battle.player_b.circle_artifact) + '66' }"></div>
            <img v-if="battle.player_b.image" :src="battle.player_b.image" class="person-img" />
            <div v-else class="person-placeholder">{{ (battle.player_b.name || '?').charAt(0) }}</div>
            <span class="person-role-tag" :class="battle.player_b.role">{{ battle.player_b.role }}</span>
          </div>
          <div class="person-name">{{ battle.player_b.name }}</div>
          <div class="person-surname">{{ battle.player_b.surname }}</div>
          <div class="person-position">〈 {{ battle.player_b.position || 'Adventurer' }} 〉</div>
          <div v-if="battle.player_b.status_text" class="person-status">"{{ battle.player_b.status_text }}"</div>
          <div class="person-badges" v-if="battle.player_b.badges && battle.player_b.badges.length">
            <div v-for="b in battle.player_b.badges.slice(0, 5)" :key="b.id" class="pb-circle" :title="b.name">
              <img v-if="b.image" :src="b.image" class="pb-img" />
              <span v-else>🏅</span>
            </div>
            <span v-if="battle.player_b.badges.length > 5" class="pb-more">+{{ battle.player_b.badges.length - 5 }}</span>
          </div>
          <div v-else class="person-no-badges">No badges yet</div>
          <div class="person-currency">
            <span class="cur gold">💰 {{ battle.player_b.coins }}</span>
            <span class="cur mana">✨ {{ battle.player_b.angel_coins }}</span>
          </div>
        </div>
      </div>
      <div class="waiting-msg">
        <span class="waiting-icon">⏰</span>
        <span>Battle Time: <strong>{{ formatScheduledTime(battle.scheduled_time) }}</strong></span>
      </div>
    </div>

    <!-- Resolved — show battle replay -->
    <div v-else-if="battle && battle.status === 'resolved'" class="arena-battle">
      <!-- Countdown Overlay -->
      <div class="countdown-overlay" v-if="countdownText" :key="countdownText">
        <span class="countdown-number" :class="{ 'countdown-fight': countdownText === 'FIGHT!' }">{{ countdownText }}</span>
      </div>
      <!-- Ambient Particles Container -->
      <div class="ambient-particles" id="ambientParticles"></div>
      <!-- Confetti Container -->
      <div class="confetti-container" id="confettiContainer" v-if="battleDone"></div>
      <div class="fighters-row">
        <div class="char-card player-a" :id="'cardA'"
          :class="{ dead: battleDone && battle.winner_id !== battle.player_a.id, 'winner-glow': battleDone && battle.winner_id === battle.player_a.id, 'active-turn': activeSide === 'A', 'card-intro-left': battleStarted }"
          :style="bgStyle(battle.player_a)">
          <!-- Hit flash overlay -->
          <div class="hit-flash" :id="'flashA'"></div>
          <!-- Floating effects container -->
          <div class="fx-container" :id="'fxA'"></div>
          <!-- Player A card -->
          <div class="person-portrait">
            <img v-if="getArtifactImage(battle.player_a.circle_artifact)"
              :src="getArtifactImage(battle.player_a.circle_artifact)" class="person-artifact-ring-img" />
            <div v-else-if="battle.player_a.circle_artifact" class="person-artifact-ring"
              :style="{ borderColor: getArtifactColor(battle.player_a.circle_artifact), boxShadow: '0 0 14px ' + getArtifactColor(battle.player_a.circle_artifact) + '66' }"></div>
            <img v-if="battle.player_a.image" :src="battle.player_a.image" class="person-img" />
            <div v-else class="person-placeholder">{{ (battle.player_a.name || '?').charAt(0) }}</div>
            <span class="person-role-tag" :class="battle.player_a.role">{{ battle.player_a.role }}</span>
          </div>
          <div class="person-name">{{ battle.player_a.name }}</div>
          <div class="person-surname">{{ battle.player_a.surname }}</div>
          <div class="person-position">〈 {{ battle.player_a.position || 'Adventurer' }} 〉</div>
          <div v-if="battle.player_a.status_text" class="person-status">"{{ battle.player_a.status_text }}"</div>
          <div class="person-stats">
            <span class="ps str">⚔️ {{ battle.player_a.str }}</span>
            <span class="ps def">🛡️ {{ battle.player_a.def }}</span>
            <span class="ps luk">🍀 {{ battle.player_a.luk }}</span>
          </div>
          <!-- Hit & Combo Counter -->
          <div class="hit-counter" v-if="hitsA > 0">🗡️ {{ hitsA }} <span v-if="comboA >= 2" class="combo-badge">{{ comboA }}x COMBO</span></div>
          <div class="person-badges" v-if="battle.player_a.badges && battle.player_a.badges.length">
            <div v-for="b in battle.player_a.badges.slice(0, 5)" :key="b.id" class="pb-circle" :title="b.name">
              <img v-if="b.image" :src="b.image" class="pb-img" />
              <span v-else>🏅</span>
            </div>
            <span v-if="battle.player_a.badges.length > 5" class="pb-more">+{{ battle.player_a.badges.length - 5 }}</span>
          </div>
          <div v-else class="person-no-badges">No badges yet</div>
          <div class="person-currency">
            <span class="cur gold">💰 {{ battle.player_a.coins }}</span>
            <span class="cur mana">✨ {{ battle.player_a.angel_coins }}</span>
          </div>
          <!-- HP bar -->
          <div class="hp-section">
            <div class="hp-bar-wrap"><div class="hp-bar hp-a" :class="{ critical: hpA/hpAMax < 0.25 }" :style="{ width: (hpA/hpAMax*100)+'%' }"></div></div>
            <div class="hp-text hp-text-a">♥ {{ hpA }} / {{ hpAMax }}</div>
          </div>
        </div>

        <div class="vs-badge" v-if="!battleStarted">VS</div>

        <div class="char-card player-b" :id="'cardB'"
          :class="{ dead: battleDone && battle.winner_id !== battle.player_b.id, 'winner-glow': battleDone && battle.winner_id === battle.player_b.id, 'active-turn': activeSide === 'B', 'card-intro-right': battleStarted }"
          :style="bgStyle(battle.player_b)">
          <!-- Hit flash overlay -->
          <div class="hit-flash" :id="'flashB'"></div>
          <!-- Floating effects container -->
          <div class="fx-container" :id="'fxB'"></div>
          <!-- Player B card -->
          <div class="person-portrait">
            <img v-if="getArtifactImage(battle.player_b.circle_artifact)"
              :src="getArtifactImage(battle.player_b.circle_artifact)" class="person-artifact-ring-img" />
            <div v-else-if="battle.player_b.circle_artifact" class="person-artifact-ring"
              :style="{ borderColor: getArtifactColor(battle.player_b.circle_artifact), boxShadow: '0 0 14px ' + getArtifactColor(battle.player_b.circle_artifact) + '66' }"></div>
            <img v-if="battle.player_b.image" :src="battle.player_b.image" class="person-img" />
            <div v-else class="person-placeholder">{{ (battle.player_b.name || '?').charAt(0) }}</div>
            <span class="person-role-tag" :class="battle.player_b.role">{{ battle.player_b.role }}</span>
          </div>
          <div class="person-name">{{ battle.player_b.name }}</div>
          <div class="person-surname">{{ battle.player_b.surname }}</div>
          <div class="person-position">〈 {{ battle.player_b.position || 'Adventurer' }} 〉</div>
          <div v-if="battle.player_b.status_text" class="person-status">"{{ battle.player_b.status_text }}"</div>
          <div class="person-stats">
            <span class="ps str">⚔️ {{ battle.player_b.str }}</span>
            <span class="ps def">🛡️ {{ battle.player_b.def }}</span>
            <span class="ps luk">🍀 {{ battle.player_b.luk }}</span>
          </div>
          <!-- Hit & Combo Counter -->
          <div class="hit-counter" v-if="hitsB > 0">🗡️ {{ hitsB }} <span v-if="comboB >= 2" class="combo-badge">{{ comboB }}x COMBO</span></div>
          <div class="person-badges" v-if="battle.player_b.badges && battle.player_b.badges.length">
            <div v-for="b in battle.player_b.badges.slice(0, 5)" :key="b.id" class="pb-circle" :title="b.name">
              <img v-if="b.image" :src="b.image" class="pb-img" />
              <span v-else>🏅</span>
            </div>
            <span v-if="battle.player_b.badges.length > 5" class="pb-more">+{{ battle.player_b.badges.length - 5 }}</span>
          </div>
          <div v-else class="person-no-badges">No badges yet</div>
          <div class="person-currency">
            <span class="cur gold">💰 {{ battle.player_b.coins }}</span>
            <span class="cur mana">✨ {{ battle.player_b.angel_coins }}</span>
          </div>
          <!-- HP bar -->
          <div class="hp-section">
            <div class="hp-bar-wrap"><div class="hp-bar hp-b" :class="{ critical: hpB/hpBMax < 0.25 }" :style="{ width: (hpB/hpBMax*100)+'%' }"></div></div>
            <div class="hp-text hp-text-b">♥ {{ hpB }} / {{ hpBMax }}</div>
          </div>
        </div>
      </div>

      <div class="battle-log" ref="logRef">
        <template v-for="(entry, i) in logEntries" :key="i">
          <!-- Two-column row -->
          <div v-if="entry.type === 'row'" class="log-grid">
            <div class="log-cell cell-a" :class="entry.leftCls" v-html="entry.left"></div>
            <div class="log-cell cell-b" :class="entry.rightCls" v-html="entry.right"></div>
          </div>
          <!-- Centered row (turn header, winner) -->
          <div v-else class="log-center" :class="entry.cls" v-html="entry.html"></div>
        </template>
      </div>

      <div class="arena-controls" v-if="!battleStarted">
        <button class="btn-fight" @click="playBattle">⚔️ FIGHT !</button>
      </div>

      <div class="arena-controls" v-if="battleDone">
        <div class="reward-info">
          <span class="reward-winner">🏆 {{ winnerName }} ได้รับ +{{ battle.winner_gold||0 }} Gold</span>
          <span class="reward-loser">{{ loserName }} เสีย {{ battle.loser_gold||0 }} Gold</span>
        </div>
      </div>

      <div class="speed-bar" v-if="battleStarted && !battleDone">
        <span>⏱️</span>
        <button class="speed-btn" :class="{ active: speed === 800 }" @click="speed=800">🐢</button>
        <button class="speed-btn" :class="{ active: speed === 400 }" @click="speed=400">⚡</button>
        <button class="speed-btn" :class="{ active: speed === 150 }" @click="speed=150">🔥</button>
      </div>
    </div>

    <div v-else class="no-battle">
      <p>ไม่พบข้อมูลการต่อสู้</p>
      <router-link to="/staff/home" class="btn-back">← กลับหน้าหลัก</router-link>
    </div>
  </div>
</template>

<script>
import api, { getArtifactCatalog } from '../../services/api'

const ARTIFACT_COLORS = {
  artifact_01: '#ffd700', artifact_02: '#a8d8ea', artifact_03: '#2ecc71', artifact_04: '#e74c3c',
  artifact_05: '#3498db', artifact_06: '#9b59b6', artifact_07: '#cd7f32', artifact_08: '#00a86b',
  artifact_09: '#2c3e50', artifact_10: '#f39c12', artifact_11: '#e67e22', artifact_12: '#f1c40f',
  artifact_13: '#bdc3c7', artifact_14: '#c0392b', artifact_15: '#1abc9c', artifact_16: '#8e44ad',
  artifact_17: '#d4a44c', artifact_18: '#ecf0f1', artifact_19: '#7b241c', artifact_20: '#ff6b6b',
}
const ARTIFACT_IDS = Object.keys(ARTIFACT_COLORS)

export default {
  name: 'ArenaBattle',
  data() {
    return {
      loading: true,
      battle: null,
      battleStarted: false,
      battleDone: false,
      logEntries: [],
      hpA: 0,
      hpB: 0,
      hpAMax: 100,
      hpBMax: 100,
      speed: 400,
      winnerName: '',
      loserName: '',
      apiBase: import.meta.env.VITE_API_URL || '',
      artifactCatalog: [],
      // Enhancement: countdown, active turn, hit/combo tracking
      countdownText: '',
      activeSide: '',
      hitsA: 0,
      hitsB: 0,
      comboA: 0,
      comboB: 0,
      lastAttacker: '',
      currentCombo: 0,
      ambientInterval: null,
      // Battle sounds
      sounds: {
        strike: new Audio('/sound/strike.mp3'),
        crit: new Audio('/sound/Critical.mp3'),
        dodge: new Audio('/sound/Dodge.mp3'),
        doubleStrike: new Audio('/sound/doubleStrike.mp3'),
        victory: new Audio('/sound/Victory.mp3'),
      },
    }
  },
  beforeUnmount() {
    this.stopAmbientParticles()
  },
  async mounted() {
    try {
      const [res, catRes] = await Promise.all([
        api.get(`/api/pvp/battle/${this.$route.params.id}`),
        getArtifactCatalog().catch(() => ({ data: [] })),
      ])
      this.battle = res.data
      this.artifactCatalog = catRes.data || []
      if (this.battle && this.battle.player_a && this.battle.player_a.str !== undefined) {
        this.hpAMax = this.calcHP(this.battle.player_a.str, this.battle.player_a.def, this.battle.player_a.luk)
        this.hpBMax = this.calcHP(this.battle.player_b.str, this.battle.player_b.def, this.battle.player_b.luk)
        this.hpA = this.hpAMax
        this.hpB = this.hpBMax
      }
    } catch (e) {
      console.error('Failed to load battle:', e)
    } finally {
      this.loading = false
    }
    // Auto-start battle if already resolved (no need to click FIGHT)
    if (this.battle && this.battle.status === 'resolved' && this.battle.battle_log) {
      setTimeout(() => this.playBattle(), 800)
    }
  },
  methods: {
    calcHP(s, d, l) { return s * 2 + d * 4 + l * 2 + 50 },
    sleep(ms) { return new Promise(r => setTimeout(r, ms)) },

    bgStyle(player) {
      if (!player.magic_background) return {}
      return {
        backgroundImage: `linear-gradient(rgba(17,10,30,0.6), rgba(17,10,30,0.8)), url(${this.apiBase}${player.magic_background})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    },
    hasArtifactImage(id) { return ARTIFACT_IDS.includes(id) },
    getArtifactColor(id) { return ARTIFACT_COLORS[id] || '#d4a44c' },
    getArtifactImage(artifactId) {
      if (!artifactId || !this.artifactCatalog.length) return null
      const a = this.artifactCatalog.find(x => String(x.id) === String(artifactId))
      return a ? a.image : null
    },
    formatScheduledTime(iso) {
      if (!iso) return '??:??'
      // scheduled_time is stored as naive Bangkok time (UTC+7),
      // append timezone offset so Date parses it correctly
      const isoWithTz = iso.includes('+') || iso.includes('Z') ? iso : iso + '+07:00'
      const d = new Date(isoWithTz)
      return d.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Bangkok' })
    },

    addCenterLog(html, cls = '') {
      this.logEntries.push({ type: 'center', html, cls })
      this.$nextTick(() => {
        if (this.$refs.logRef) this.$refs.logRef.scrollTop = this.$refs.logRef.scrollHeight
      })
    },
    addBattleRow(left, leftCls, right, rightCls) {
      this.logEntries.push({ type: 'row', left, leftCls, right, rightCls })
      this.$nextTick(() => {
        if (this.$refs.logRef) this.$refs.logRef.scrollTop = this.$refs.logRef.scrollHeight
      })
    },
    shakeCard(id) {
      const el = document.getElementById(id)
      if (!el) return
      el.classList.remove('shake-hit')
      void el.offsetWidth
      el.classList.add('shake-hit')
    },

    playSound(name) {
      const snd = this.sounds[name]
      if (!snd) return
      const clone = snd.cloneNode()
      clone.volume = 0.5
      clone.play().catch(() => {})
    },

    // ─── RO-Style Visual FX ──────────────────────────
    spawnFloatingText(containerId, text, cssClass) {
      const container = document.getElementById(containerId)
      if (!container) return
      const el = document.createElement('div')
      el.className = `fx-float ${cssClass}`
      el.textContent = text
      el.style.left = `${20 + Math.random() * 60}%`
      container.appendChild(el)
      setTimeout(() => el.remove(), 1500)
    },

    spawnSlash(containerId, isCrit) {
      const container = document.getElementById(containerId)
      if (!container) return
      const slash = document.createElement('div')
      slash.className = isCrit ? 'fx-slash fx-slash-crit' : 'fx-slash'
      // Random angle for variety
      const angle = -30 + Math.random() * 60
      slash.style.transform = `rotate(${angle}deg)`
      container.appendChild(slash)
      setTimeout(() => slash.remove(), 600)
      // Second slash for crits (X pattern)
      if (isCrit) {
        const slash2 = document.createElement('div')
        slash2.className = 'fx-slash fx-slash-crit'
        slash2.style.transform = `rotate(${angle + 90}deg)`
        slash2.style.animationDelay = '0.05s'
        container.appendChild(slash2)
        setTimeout(() => slash2.remove(), 650)
      }
    },

    spawnSparks(containerId, count, color) {
      const container = document.getElementById(containerId)
      if (!container) return
      for (let i = 0; i < count; i++) {
        const spark = document.createElement('div')
        spark.className = 'fx-spark'
        spark.style.left = `${40 + Math.random() * 20}%`
        spark.style.top = `${30 + Math.random() * 30}%`
        const angle = Math.random() * 360
        const dist = 30 + Math.random() * 50
        spark.style.setProperty('--sx', `${Math.cos(angle * Math.PI / 180) * dist}px`)
        spark.style.setProperty('--sy', `${Math.sin(angle * Math.PI / 180) * dist}px`)
        spark.style.background = color || '#ffd700'
        spark.style.animationDelay = `${Math.random() * 0.1}s`
        container.appendChild(spark)
        setTimeout(() => spark.remove(), 800)
      }
    },

    spawnImpactRing(containerId, color) {
      const container = document.getElementById(containerId)
      if (!container) return
      const ring = document.createElement('div')
      ring.className = 'fx-impact-ring'
      ring.style.borderColor = color || 'rgba(255,215,0,0.6)'
      container.appendChild(ring)
      setTimeout(() => ring.remove(), 700)
    },

    flashCard(flashId, color) {
      const el = document.getElementById(flashId)
      if (!el) return
      el.style.background = color
      el.classList.remove('flash-active')
      void el.offsetWidth
      el.classList.add('flash-active')
      setTimeout(() => el.classList.remove('flash-active'), 500)
    },

    screenShake(intensity) {
      const page = document.querySelector('.arena-battle')
      if (!page) return
      page.classList.remove('screen-shake', 'screen-shake-heavy')
      void page.offsetWidth
      page.classList.add(intensity === 'heavy' ? 'screen-shake-heavy' : 'screen-shake')
      setTimeout(() => page.classList.remove('screen-shake', 'screen-shake-heavy'), 400)
    },

    screenFlash() {
      const flash = document.createElement('div')
      flash.className = 'fx-screen-flash'
      document.querySelector('.arena-battle')?.appendChild(flash)
      setTimeout(() => flash.remove(), 400)
    },

    spawnDodgeGhost(cardId) {
      const card = document.getElementById(cardId)
      if (!card) return
      card.classList.remove('dodge-ghost')
      void card.offsetWidth
      card.classList.add('dodge-ghost')
      setTimeout(() => card.classList.remove('dodge-ghost'), 600)
    },

    // ─── Countdown Intro ──────────────────────────
    async playCountdown() {
      const steps = ['3', '2', '1', 'FIGHT!']
      for (const text of steps) {
        this.countdownText = text
        await this.sleep(text === 'FIGHT!' ? 600 : 500)
      }
      this.countdownText = ''
    },

    // ─── Ambient Particles ──────────────────────────
    startAmbientParticles() {
      const container = document.getElementById('ambientParticles')
      if (!container) return
      this.ambientInterval = setInterval(() => {
        if (this.battleDone) { this.stopAmbientParticles(); return }
        const p = document.createElement('div')
        p.className = 'ambient-dot'
        p.style.left = Math.random() * 100 + '%'
        p.style.animationDuration = (3 + Math.random() * 4) + 's'
        p.style.animationDelay = Math.random() * 0.5 + 's'
        p.style.width = p.style.height = (2 + Math.random() * 3) + 'px'
        p.style.opacity = 0.2 + Math.random() * 0.5
        container.appendChild(p)
        setTimeout(() => p.remove(), 7000)
      }, 200)
    },
    stopAmbientParticles() {
      if (this.ambientInterval) { clearInterval(this.ambientInterval); this.ambientInterval = null }
    },

    // ─── Confetti / Fireworks ──────────────────────────
    spawnConfetti() {
      const container = document.getElementById('confettiContainer')
      if (!container) return
      const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f7dc6f', '#bb8fce', '#85c1e9', '#f0b27a']
      for (let i = 0; i < 60; i++) {
        const c = document.createElement('div')
        c.className = 'confetti-piece'
        c.style.left = Math.random() * 100 + '%'
        c.style.background = colors[Math.floor(Math.random() * colors.length)]
        c.style.animationDuration = (2 + Math.random() * 2) + 's'
        c.style.animationDelay = Math.random() * 0.8 + 's'
        c.style.setProperty('--drift', (Math.random() * 200 - 100) + 'px')
        c.style.setProperty('--spin', (Math.random() * 720 - 360) + 'deg')
        c.style.width = (4 + Math.random() * 6) + 'px'
        c.style.height = (4 + Math.random() * 6) + 'px'
        container.appendChild(c)
        setTimeout(() => c.remove(), 5000)
      }
    },

    // ─── Track Combos ──────────────────────────
    trackCombo(side) {
      if (this.lastAttacker === side) {
        this.currentCombo++
      } else {
        this.currentCombo = 1
        this.lastAttacker = side
      }
      if (side === 'A') { this.comboA = this.currentCombo; this.comboB = 0 }
      else { this.comboB = this.currentCombo; this.comboA = 0 }
      // Combo FX
      if (this.currentCombo >= 3) {
        const fx = side === 'A' ? 'fxA' : 'fxB'
        this.spawnFloatingText(fx, `${this.currentCombo}x COMBO!`, 'fx-combo-label')
      }
    },

    async playBattle() {
      if (!this.battle || !this.battle.battle_log) return
      this.battleStarted = true

      // ─── Cinematic Intro ───
      await this.playCountdown()
      this.startAmbientParticles()

      const events = this.battle.battle_log

      for (const ev of events) {
        if (ev.type === 'turn') {
          this.activeSide = ''
          this.addCenterLog(`── TURN ${ev.turn} ──`, 'turn-header')
          await this.sleep(this.speed * 0.4)
          continue
        }

        if (ev.type === 'winner') {
          this.activeSide = ''
          this.stopAmbientParticles()
          const nameA = this.battle.player_a.name
          const nameB = this.battle.player_b.name
          const wName = ev.side === 'A' ? nameA : nameB
          this.winnerName = wName
          this.loserName = ev.side === 'A' ? nameB : nameA
          const winFx = ev.side === 'A' ? 'fxA' : 'fxB'
          this.spawnSparks(winFx, 15, '#ffd700')
          this.spawnImpactRing(winFx, 'rgba(255,215,0,0.8)')
          this.screenFlash()
          this.playSound('victory')
          this.addCenterLog(`🏆 ${wName} WINS!`, 'winner-log')
          this.battleDone = true
          // Victory confetti
          this.$nextTick(() => {
            this.spawnConfetti()
            // Extra burst after a short delay
            setTimeout(() => this.spawnConfetti(), 800)
          })
          await this.sleep(500)
          continue
        }

        if (ev.type === 'attack') {
          // Active turn glow
          this.activeSide = ev.side

          const defCard = ev.side === 'A' ? 'cardB' : 'cardA'
          const defFx = ev.side === 'A' ? 'fxB' : 'fxA'
          const defFlash = ev.side === 'A' ? 'flashB' : 'flashA'

          // Build attacker HTML and defender HTML
          let atkHtml = ''
          let defHtml = ''
          let atkCls = ''
          let defCls = ''

          if (ev.dodge) {
            // ══ DODGE ══
            this.playSound('dodge')
            this.spawnDodgeGhost(defCard)
            this.spawnFloatingText(defFx, 'MISS', 'fx-miss')
            atkHtml = `<span class="log-icon">⚔️</span><span class="log-miss-text">MISS</span>`
            defHtml = `<span class="log-icon">🍀</span><span class="log-dodge-text">หลบได้!</span>`
            atkCls = 'miss-cell'
            defCls = 'dodge-cell'
          } else {
            // ══ HIT ══ — Track hits & combos
            if (ev.side === 'A') this.hitsA++
            else this.hitsB++
            this.trackCombo(ev.side)

            this.shakeCard(defCard)
            this.spawnSlash(defFx, ev.crit)
            this.spawnSparks(defFx, ev.crit ? 12 : 6, ev.crit ? '#ffeb3b' : '#ff6b35')

            // Build tags
            let tags = ''
            if (ev.crit) tags += ' <span class="log-tag tag-crit">🎯 CRIT</span>'
            if (ev.lucky) tags += ' <span class="log-tag tag-lucky">🍀 x2</span>'
            if (ev.block) tags += ' <span class="log-tag tag-block">🛡️ BLOCK</span>'

            atkHtml = `<span class="log-icon">⚔️</span><span class="log-dmg${ev.crit ? ' crit' : ''}">${ev.dmg}</span>${tags}`
            defHtml = `<span class="log-hp-loss">HP ▼ ${ev.dmg}</span>${ev.block ? ' <span class="log-tag tag-block">🛡️</span>' : ''}`
            atkCls = ev.crit ? 'atk-cell crit-cell' : (ev.lucky ? 'atk-cell lucky-cell' : 'atk-cell')
            defCls = ev.block ? 'hp-cell block-cell' : 'hp-cell'

            // Visual FX
            if (ev.crit) {
              this.playSound('crit')
              this.flashCard(defFlash, 'rgba(255,235,59,0.5)')
              this.screenFlash()
              this.screenShake('heavy')
              this.spawnImpactRing(defFx, 'rgba(255,235,59,0.7)')
              this.spawnFloatingText(defFx, `-${ev.dmg}`, 'fx-dmg fx-crit-dmg')
              setTimeout(() => this.spawnFloatingText(defFx, 'CRITICAL!', 'fx-crit-label'), 100)
            } else {
              this.playSound('strike')
              this.flashCard(defFlash, ev.block ? 'rgba(52,152,219,0.4)' : 'rgba(255,60,60,0.3)')
              this.screenShake(ev.block ? 'normal' : 'normal')
              this.spawnFloatingText(defFx, `-${ev.dmg}`, 'fx-dmg')
            }

            if (ev.block) {
              setTimeout(() => this.spawnFloatingText(defFx, 'BLOCKED!', 'fx-block-label'), 80)
            }

            if (ev.lucky) {
              setTimeout(() => {
                this.playSound('doubleStrike')
                this.spawnSlash(defFx, false)
                this.spawnSparks(defFx, 8, '#ce93d8')
                this.spawnImpactRing(defFx, 'rgba(206,147,216,0.6)')
                this.spawnFloatingText(defFx, 'DOUBLE STRIKE!', 'fx-lucky-label')
              }, 180)
              // Second slash for double strike
              setTimeout(() => {
                this.spawnSlash(defFx, false)
              }, 350)
            }
          }

          // Place in correct columns: A attacks → left=atk, right=def | B attacks → left=def, right=atk
          if (ev.side === 'A') {
            this.addBattleRow(atkHtml, atkCls, defHtml, defCls)
          } else {
            this.addBattleRow(defHtml, defCls, atkHtml, atkCls)
          }

          this.hpA = ev.aHP
          this.hpB = ev.bHP

          await this.sleep(this.speed)
        }
      }
    },
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Noto+Sans+Thai:wght@400;600;700&display=swap');

.arena-page {
  max-width: 500px;
  margin: 0 auto;
  padding: 16px;
}
.arena-header {
  text-align: center;
  margin-bottom: 20px;
}
.arena-back {
  color: #8b7355;
  text-decoration: none;
  font-size: 13px;
  display: inline-block;
  margin-bottom: 8px;
}
.arena-title {
  font-family: 'Cinzel', serif;
  font-size: 24px;
  font-weight: 900;
  background: linear-gradient(135deg, #d4a44c, #f7d774, #d4a44c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 4px;
  filter: drop-shadow(0 0 8px rgba(212,164,76,0.3));
}
.loading-state {
  text-align: center;
  padding: 60px 0;
  color: #8b7355;
}
.loading-spinner {
  width: 40px; height: 40px;
  border: 3px solid rgba(212,164,76,0.2);
  border-top-color: #d4a44c;
  border-radius: 50%;
  margin: 0 auto 12px;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Fighters Row ── */
.fighters-row {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 14px;
  position: relative;
}

/* ── Character Card (TownPeople style) ── */
.char-card {
  flex: 1;
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 16px 10px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  overflow: visible;
  transition: all 0.3s;
  background-size: cover;
  background-position: center;
}
.char-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: 14px 14px 0 0;
  z-index: 2;
}
.char-card.player-a::before { background: linear-gradient(90deg, transparent, #4a9eff, transparent); }
.char-card.player-b::before { background: linear-gradient(90deg, transparent, #ff4a6a, transparent); }
.char-card.shake-hit {
  animation: shake-hit 0.4s ease-in-out;
}

/* ── Portrait (TownPeople style) ── */
.person-portrait {
  position: relative; margin-bottom: 8px;
  width: 74px; height: 74px;
  display: flex; align-items: center; justify-content: center;
}
.person-artifact-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 74px; height: 74px; border-radius: 50%;
  border: 3px solid; pointer-events: none; overflow: hidden;
  z-index: 0;
  animation: artifactGlow 3s ease-in-out infinite;
}
.person-artifact-ring-img {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 74px; height: 74px; border-radius: 50%;
  object-fit: cover; pointer-events: none; overflow: hidden;
  aspect-ratio: 1 / 1; z-index: 0;
  animation: artifactGlow 3s ease-in-out infinite;
}
@keyframes artifactGlow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.06); }
}
.person-img {
  width: 52px; height: 52px; border-radius: 50%;
  object-fit: cover; border: 2px solid rgba(212,164,76,0.3);
  position: relative; z-index: 1;
}
.person-placeholder {
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 1;
  font-size: 20px; font-weight: 800; color: #1c1208;
}
.person-role-tag {
  position: absolute; bottom: -4px; left: 50%; transform: translateX(-50%);
  font-size: 8px; font-weight: 800; padding: 1px 5px;
  border-radius: 6px; text-transform: uppercase;
  white-space: nowrap; z-index: 2;
}
.person-role-tag.god { background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208; }
.person-role-tag.gm { background: linear-gradient(135deg, #2980b9, #3498db); color: #fff; }
.person-role-tag.player { background: linear-gradient(135deg, #27ae60, #2ecc71); color: #fff; }
.person-role-tag.manager { background: linear-gradient(135deg, #2980b9, #3498db); color: #fff; }

/* ── Name & Position ── */
.person-name {
  font-family: 'Cinzel', serif;
  font-size: 13px; font-weight: 700; color: #e8d5b7;
  text-align: center; margin-bottom: 0; line-height: 1.3;
}
.player-a .person-name { color: #7ec8ff; }
.player-b .person-name { color: #ff8fa3; }
.person-surname {
  font-family: 'Cinzel', serif;
  font-size: 11px; font-weight: 600; color: #c4b08a;
  text-align: center; margin-bottom: 2px; line-height: 1.3;
}
.person-position {
  font-size: 10px; color: #8b7355; font-weight: 600;
  margin-bottom: 4px; text-align: center; font-style: italic;
}
.person-status {
  font-size: 9px; color: #e74c3c; font-style: italic;
  font-weight: 600; margin-bottom: 6px; text-align: center;
  word-break: break-word; line-height: 1.3;
}

/* ── Stats ── */
.person-stats {
  display: flex; gap: 4px; margin-bottom: 6px;
}
.ps {
  font-size: 9px; font-weight: 700; padding: 2px 5px;
  border-radius: 6px; display: flex; align-items: center; gap: 1px;
}
.ps.str { background: rgba(231,76,60,0.12); color: #e74c3c; }
.ps.def { background: rgba(52,152,219,0.12); color: #3498db; }
.ps.luk { background: rgba(46,204,113,0.12); color: #2ecc71; }

/* ── Badges ── */
.person-badges {
  display: flex; gap: 3px; align-items: center;
  margin-bottom: 6px; flex-wrap: wrap; justify-content: center;
}
.pb-circle {
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(212,164,76,0.1); border: 1px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; font-size: 10px;
}
.pb-img { width: 100%; height: 100%; object-fit: cover; }
.pb-more { font-size: 9px; color: #b8860b; font-weight: 700; }
.person-no-badges {
  font-size: 9px; color: #6b5a3e; font-style: italic;
  margin-bottom: 6px;
}

/* ── Currency ── */
.person-currency {
  display: flex; gap: 8px; margin-bottom: 4px;
}
.cur {
  font-size: 10px; font-weight: 700;
}
.cur.gold { color: #d4a44c; }
.cur.mana { color: #a78bfa; }

/* ── HP Bar ── */
.hp-section { margin-top: 6px; width: 100%; padding: 0 4px; }
.hp-bar-wrap {
  width: 100%; height: 12px;
  background: rgba(0,0,0,0.4);
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.06);
}
.hp-bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}
.hp-a { background: linear-gradient(90deg, #1565c0, #42a5f5); }
.hp-b { background: linear-gradient(90deg, #c62828, #ef5350); }
.hp-bar.critical { background: linear-gradient(90deg, #ff6f00, #ff9800) !important; animation: hp-pulse 0.6s infinite; }
.hp-bar::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.15), transparent);
  border-radius: 6px 6px 0 0;
}
.hp-text { font-size: 10px; font-weight: 700; margin-top: 2px; }
.hp-text-a { color: #90caf9; }
.hp-text-b { color: #ef9a9a; }

/* ── VS badge ── */
.vs-badge {
  position: absolute;
  left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  width: 44px; height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d4a44c, #f0c040);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Cinzel', serif;
  font-size: 15px;
  font-weight: 900;
  color: #1a0e2e;
  box-shadow: 0 0 20px rgba(212,164,76,0.3);
}

/* ── Battle Log (Two-Column Grid) ── */
.battle-log {
  background: linear-gradient(180deg, rgba(10,10,20,0.85), rgba(5,5,15,0.9));
  border: 1px solid rgba(212,164,76,0.08);
  border-radius: 12px;
  padding: 6px;
  height: 200px;
  overflow-y: auto;
  margin-bottom: 12px;
  scroll-behavior: smooth;
}
.battle-log::-webkit-scrollbar { width: 3px; }
.battle-log::-webkit-scrollbar-thumb { background: rgba(212,164,76,0.15); border-radius: 2px; }

/* Grid row: always 2 equal columns */
.log-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3px;
  margin-bottom: 3px;
  animation: log-in 0.25s ease-out;
}

/* Each cell */
.log-cell {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  padding: 4px 6px;
  border-radius: 6px;
  line-height: 1.3;
  min-height: 24px;
}

/* Attacker cell — prominent */
.log-cell.atk-cell {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
}
.log-cell.cell-a.atk-cell { border-color: rgba(33,150,243,0.25); background: rgba(33,150,243,0.08); }
.log-cell.cell-b.atk-cell { border-color: rgba(244,67,54,0.25); background: rgba(244,67,54,0.08); }

/* Crit / Lucky overrides */
.log-cell.crit-cell {
  border-color: rgba(255,235,59,0.35) !important;
  background: rgba(255,235,59,0.08) !important;
}
.log-cell.lucky-cell {
  border-color: rgba(206,147,216,0.3) !important;
  background: rgba(206,147,216,0.08) !important;
}

/* HP loss cell — subtle */
.log-cell.hp-cell {
  justify-content: center;
  background: rgba(255,60,60,0.04);
  border: 1px solid rgba(255,60,60,0.1);
}

/* Dodge / Miss cells */
.log-cell.miss-cell {
  justify-content: center;
  background: rgba(100,100,120,0.06);
  border: 1px solid rgba(100,100,120,0.12);
  color: #777;
}
.log-cell.dodge-cell {
  background: rgba(129,199,132,0.06);
  border: 1px solid rgba(129,199,132,0.15);
}

/* Inner elements */
.log-icon { font-size: 12px; flex-shrink: 0; }
.log-dmg {
  font-weight: 900; font-size: 14px; color: #ff5555;
  font-family: 'Cinzel', serif;
}
.log-dmg.crit {
  font-size: 16px; color: #ffd700;
  text-shadow: 0 0 6px rgba(255,215,0,0.4);
}
.log-hp-loss {
  font-size: 11px; font-weight: 700; color: #ef5350;
  opacity: 0.8;
}
.log-miss-text {
  font-size: 11px; font-weight: 700; color: #888;
  letter-spacing: 1px;
}
.log-dodge-text {
  font-size: 11px; font-weight: 700; color: #81c784;
}
.log-tag {
  font-size: 8px; font-weight: 800;
  padding: 1px 4px; border-radius: 3px;
  letter-spacing: 0.5px;
}
.log-tag.tag-crit {
  background: rgba(255,235,59,0.15); color: #ffeb3b;
}
.log-tag.tag-lucky {
  background: rgba(206,147,216,0.15); color: #ce93d8;
}

/* Centered rows (turn header, winner) */
.log-center {
  text-align: center;
  animation: log-in 0.25s ease-out;
}
.log-center.turn-header {
  color: #d4a44c;
  font-weight: 700;
  font-size: 10px;
  font-family: 'Cinzel', serif;
  letter-spacing: 2px;
  padding: 3px 0;
  margin: 4px 0 2px;
  background: linear-gradient(90deg, transparent, rgba(212,164,76,0.08), transparent);
}
.log-center.winner-log {
  color: #ffd700;
  font-size: 15px;
  font-family: 'Cinzel', serif;
  font-weight: 900;
  padding: 10px;
  margin-top: 6px;
  background: linear-gradient(90deg, transparent, rgba(255,215,0,0.1), transparent);
  letter-spacing: 2px;
  border: 1px solid rgba(255,215,0,0.15);
  border-radius: 8px;
}

/* ── Controls ── */
.arena-controls { text-align: center; margin-top: 12px; }
.btn-fight {
  padding: 12px 32px;
  border: 1px solid rgba(212,164,76,0.3);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(212,164,76,0.15), rgba(212,164,76,0.05));
  color: #d4a44c;
  font-family: 'Cinzel', serif;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  letter-spacing: 2px;
  transition: all 0.3s;
}
.btn-fight:hover {
  background: linear-gradient(135deg, rgba(212,164,76,0.3), rgba(212,164,76,0.1));
  box-shadow: 0 0 25px rgba(212,164,76,0.15);
}

.speed-bar {
  display: flex;
  justify-content: center;
  gap: 4px;
  align-items: center;
  margin-top: 10px;
}
.speed-bar span { font-size: 11px; color: #5a4a3a; margin-right: 4px; }
.speed-btn {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid rgba(212,164,76,0.12);
  background: rgba(212,164,76,0.04);
  color: #8b7355;
  cursor: pointer;
}
.speed-btn.active { background: rgba(212,164,76,0.15); color: #d4a44c; border-color: rgba(212,164,76,0.3); }

/* ── Reward info ── */
.reward-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: rgba(212,164,76,0.06);
  border: 1px solid rgba(212,164,76,0.12);
  border-radius: 10px;
  margin-top: 8px;
}
.reward-winner { color: #ffd700; font-weight: 700; font-size: 14px; }
.reward-loser { color: #8b7355; font-size: 12px; }

/* ── Waiting ── */
.arena-waiting { text-align: center; }
.waiting-msg {
  margin-top: 20px;
  padding: 16px;
  background: rgba(212,164,76,0.06);
  border: 1px solid rgba(212,164,76,0.12);
  border-radius: 12px;
  color: #d4a44c;
  font-size: 18px;
  font-family: 'Cinzel', serif;
  letter-spacing: 2px;
}
.waiting-icon { font-size: 24px; margin-right: 8px; }

/* ── Countdown Overlay ── */
.countdown-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  pointer-events: none;
}
.countdown-number {
  font-family: 'Cinzel', serif;
  font-size: 60px;
  font-weight: 900;
  color: #ffd700;
  text-shadow:
    0 0 20px rgba(255,215,0,0.6),
    0 0 40px rgba(255,215,0,0.3),
    0 4px 8px rgba(0,0,0,0.8);
  animation: countdownPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
.countdown-fight {
  font-size: 48px !important;
  color: #ff4444 !important;
  text-shadow:
    0 0 20px rgba(255,68,68,0.6),
    0 0 40px rgba(255,68,68,0.3),
    0 4px 8px rgba(0,0,0,0.8) !important;
  letter-spacing: 6px;
  animation: countdownFightPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards !important;
}
@keyframes countdownPop {
  0% { opacity: 0; transform: scale(3) rotate(-5deg); }
  40% { opacity: 1; transform: scale(0.9) rotate(1deg); }
  60% { transform: scale(1.05) rotate(0deg); }
  100% { opacity: 0.85; transform: scale(1); }
}
@keyframes countdownFightPop {
  0% { opacity: 0; transform: scale(0.2) rotate(-10deg); }
  30% { opacity: 1; transform: scale(1.4) rotate(2deg); }
  50% { transform: scale(1.1) rotate(-1deg); }
  100% { opacity: 0; transform: scale(0.8) translateY(-30px); }
}

/* ── Card Intro Slide ── */
.card-intro-left {
  animation: slideInLeft 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
.card-intro-right {
  animation: slideInRight 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes slideInLeft {
  0% { opacity: 0; transform: translateX(-40px) scale(0.9); }
  100% { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes slideInRight {
  0% { opacity: 0; transform: translateX(40px) scale(0.9); }
  100% { opacity: 1; transform: translateX(0) scale(1); }
}

/* ── Active Turn Glow ── */
.char-card.active-turn {
  transition: box-shadow 0.3s, border-color 0.3s;
}
.char-card.player-a.active-turn {
  border-color: rgba(74,158,255,0.5);
  box-shadow: 0 0 18px rgba(74,158,255,0.25), inset 0 0 12px rgba(74,158,255,0.06);
}
.char-card.player-b.active-turn {
  border-color: rgba(255,74,106,0.5);
  box-shadow: 0 0 18px rgba(255,74,106,0.25), inset 0 0 12px rgba(255,74,106,0.06);
}

/* ── Hit Counter & Combo ── */
.hit-counter {
  font-size: 9px;
  font-weight: 700;
  color: #c4b08a;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.combo-badge {
  font-size: 8px;
  font-weight: 900;
  padding: 1px 5px;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(255,107,107,0.2), rgba(255,107,107,0.1));
  color: #ff6b6b;
  border: 1px solid rgba(255,107,107,0.3);
  animation: comboPulse 0.6s ease-in-out;
}
@keyframes comboPulse {
  0% { transform: scale(0.5); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

/* ── HP Bar Shimmer ── */
.hp-bar::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  animation: hpShimmer 3s ease-in-out infinite;
  z-index: 1;
}
@keyframes hpShimmer {
  0% { left: -100%; }
  50% { left: 150%; }
  100% { left: 150%; }
}

/* ── Ambient Particles ── */
.ambient-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 5;
  overflow: hidden;
}

/* ── Confetti Container ── */
.confetti-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 40;
  overflow: hidden;
}

/* ── Enhanced Dead Card Transition ── */
.char-card.dead {
  filter: grayscale(0.8) brightness(0.5);
  transition: filter 1.2s ease-in-out, transform 0.8s ease;
  transform: scale(0.97);
}

/* ── Enhanced Winner Glow ── */
.char-card.winner-glow {
  border-color: rgba(255,215,0,0.4);
  box-shadow: 0 0 30px rgba(255,215,0,0.15), 0 0 60px rgba(255,215,0,0.08);
  animation: winnerPulseGlow 2s ease-in-out infinite;
}
@keyframes winnerPulseGlow {
  0%, 100% { box-shadow: 0 0 30px rgba(255,215,0,0.15), 0 0 60px rgba(255,215,0,0.08); }
  50% { box-shadow: 0 0 40px rgba(255,215,0,0.25), 0 0 80px rgba(255,215,0,0.12); }
}

/* ── No battle ── */
.no-battle { text-align: center; padding: 60px 0; color: #8b7355; }
.btn-back {
  display: inline-block;
  margin-top: 12px;
  padding: 8px 20px;
  border: 1px solid rgba(212,164,76,0.2);
  border-radius: 8px;
  color: #d4a44c;
  text-decoration: none;
}

</style>

<!-- UNSCOPED: dynamically created FX elements need global CSS (scoped won't work with document.createElement) -->
<style>
/* ══════════════════════════════════════════════════
   RO-STYLE BATTLE EFFECTS (UNSCOPED for dynamic DOM)
   ══════════════════════════════════════════════════ */

/* ── Hit Flash Overlay ── */
.hit-flash {
  position: absolute;
  inset: 0;
  border-radius: 14px;
  pointer-events: none;
  z-index: 20;
  opacity: 0;
}
.hit-flash.flash-active {
  animation: flashFade 0.5s ease-out forwards;
}

/* ── FX Container ── */
.fx-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 25;
  overflow: visible;
}

/* ── Slash Effect (RO sword swing) ── */
.fx-slash {
  position: absolute;
  top: 15%; left: 10%;
  width: 80%; height: 70%;
  pointer-events: none;
  z-index: 26;
  background: linear-gradient(
    135deg,
    transparent 40%,
    rgba(255,255,255,0.9) 48%,
    rgba(200,220,255,0.7) 50%,
    rgba(255,255,255,0.9) 52%,
    transparent 60%
  );
  animation: slashIn 0.35s ease-out forwards;
  mix-blend-mode: screen;
}
.fx-slash-crit {
  background: linear-gradient(
    135deg,
    transparent 35%,
    rgba(255,235,59,0.95) 46%,
    rgba(255,200,0,1) 50%,
    rgba(255,235,59,0.95) 54%,
    transparent 65%
  );
  filter: drop-shadow(0 0 8px rgba(255,215,0,0.8));
}

/* ── Spark Particles ── */
.fx-spark {
  position: absolute;
  width: 4px; height: 4px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 28;
  box-shadow: 0 0 6px 2px currentColor;
  animation: sparkBurst 0.6s ease-out forwards;
}

/* ── Impact Ring (expanding circle) ── */
.fx-impact-ring {
  position: absolute;
  top: 50%; left: 50%;
  width: 20px; height: 20px;
  transform: translate(-50%, -50%);
  border: 3px solid;
  border-radius: 50%;
  pointer-events: none;
  z-index: 27;
  animation: impactExpand 0.6s ease-out forwards;
}

/* ── Screen Flash (full card white flash on crit) ── */
.fx-screen-flash {
  position: fixed;
  inset: 0;
  background: rgba(255,255,255,0.3);
  pointer-events: none;
  z-index: 100;
  animation: screenFlashFade 0.35s ease-out forwards;
}

/* ── Dodge Ghost Afterimage ── */
.char-card.dodge-ghost {
  animation: dodgeGhost 0.5s ease-out !important;
}

/* ── Floating Text ── */
.fx-float {
  position: absolute;
  top: 25%;
  font-weight: 900;
  white-space: nowrap;
  pointer-events: none;
  text-shadow: 0 2px 10px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.5);
  z-index: 30;
}

/* ── Damage Numbers ── */
.fx-dmg {
  font-size: 26px;
  color: #ff3333;
  font-family: 'Cinzel', serif;
  animation: dmgPop 1.2s ease-out forwards;
  filter: drop-shadow(0 0 4px rgba(255,50,50,0.6));
}
.fx-crit-dmg {
  font-size: 38px !important;
  color: #ffd700 !important;
  filter: drop-shadow(0 0 12px rgba(255,215,0,0.8)) drop-shadow(0 0 24px rgba(255,200,0,0.4)) !important;
  animation: critDmgPop 1.4s ease-out forwards !important;
}

/* ── MISS (dodge) ── */
.fx-miss {
  font-size: 22px;
  color: #a0d8ef;
  font-family: 'Cinzel', serif;
  letter-spacing: 4px;
  animation: missPop 1s ease-out forwards;
  filter: drop-shadow(0 0 6px rgba(160,216,239,0.5));
}

/* ── CRITICAL label ── */
.fx-crit-label {
  font-size: 16px;
  color: #ffeb3b;
  font-family: 'Cinzel', serif;
  letter-spacing: 4px;
  top: 12%;
  animation: critLabelPop 1.2s ease-out forwards;
  filter: drop-shadow(0 0 10px rgba(255,235,59,0.7));
}

/* ── DOUBLE STRIKE label ── */
.fx-lucky-label {
  font-size: 14px;
  color: #e1bee7;
  font-family: 'Cinzel', serif;
  letter-spacing: 3px;
  top: 50%;
  animation: luckyPop 1.2s ease-out forwards;
  filter: drop-shadow(0 0 8px rgba(206,147,216,0.6));
}

/* ── BLOCK styles ── */
.log-tag.tag-block {
  background: rgba(52,152,219,0.15); color: #3498db;
}
.block-cell {
  background: rgba(52,152,219,0.06) !important;
}
.fx-block-label {
  font-size: 12px;
  color: #85c1e9;
  font-family: 'Cinzel', serif;
  letter-spacing: 2px;
  top: 35%;
  animation: blockPop 1.2s ease-out forwards;
  filter: drop-shadow(0 0 6px rgba(52,152,219,0.5));
}
@keyframes blockPop {
  0% { opacity: 0; transform: translateY(0) scale(0.5); }
  15% { opacity: 1; transform: translateY(-5px) scale(1.1); }
  100% { opacity: 0; transform: translateY(-30px) scale(0.8); }
}
/* ── Screen Shake ── */
.arena-battle.screen-shake {
  animation: screenShake 0.3s ease-in-out;
}
.arena-battle.screen-shake-heavy {
  animation: screenShakeHeavy 0.45s ease-in-out;
}

/* ══════════════════════════════════════════════════
   KEYFRAMES
   ══════════════════════════════════════════════════ */

@keyframes shake-hit {
  0%,100% { transform: translateX(0) rotate(0); }
  10% { transform: translateX(-8px) rotate(-2deg); filter: brightness(2.5); }
  25% { transform: translateX(8px) rotate(2deg); filter: brightness(1.5); }
  40% { transform: translateX(-5px) rotate(-1deg); }
  55% { transform: translateX(4px) rotate(0.5deg); }
  70% { transform: translateX(-2px); }
  85% { transform: translateX(1px); }
}

@keyframes slashIn {
  0% { opacity: 0; clip-path: inset(0 100% 0 0); }
  30% { opacity: 1; clip-path: inset(0 0 0 0); }
  100% { opacity: 0; clip-path: inset(0 0 0 0); }
}

@keyframes sparkBurst {
  0% { opacity: 1; transform: translate(0, 0) scale(1); }
  100% { opacity: 0; transform: translate(var(--sx), var(--sy)) scale(0); }
}

@keyframes impactExpand {
  0% { width: 10px; height: 10px; opacity: 1; }
  100% { width: 120px; height: 120px; opacity: 0; transform: translate(-50%, -50%); }
}

@keyframes screenFlashFade {
  0% { opacity: 1; }
  100% { opacity: 0; }
}

@keyframes flashFade {
  0% { opacity: 0.8; }
  100% { opacity: 0; }
}

@keyframes dodgeGhost {
  0% { transform: translateX(0); opacity: 1; }
  20% { transform: translateX(20px); opacity: 0.3; filter: blur(2px) brightness(1.5); }
  40% { transform: translateX(-15px); opacity: 0.5; }
  60% { transform: translateX(8px); opacity: 0.7; }
  100% { transform: translateX(0); opacity: 1; filter: none; }
}

@keyframes dmgPop {
  0% { opacity: 0; transform: translateY(10px) scale(0.3); }
  15% { opacity: 1; transform: translateY(-5px) scale(1.3); }
  30% { transform: translateY(-15px) scale(1); }
  100% { opacity: 0; transform: translateY(-70px) scale(0.7); }
}

@keyframes critDmgPop {
  0% { opacity: 0; transform: translateY(10px) scale(0.2); }
  10% { opacity: 1; transform: translateY(0) scale(1.8); }
  20% { transform: translateY(-5px) scale(1.4); }
  35% { transform: translateY(-15px) scale(1.6); }
  50% { transform: translateY(-25px) scale(1.3); }
  100% { opacity: 0; transform: translateY(-90px) scale(0.6); }
}

@keyframes missPop {
  0% { opacity: 0; transform: translateY(0) scale(0.5); }
  20% { opacity: 1; transform: translateY(-10px) scale(1.2); }
  40% { transform: translateY(-20px) scale(1); }
  100% { opacity: 0; transform: translateY(-55px) scale(0.8); }
}

@keyframes critLabelPop {
  0% { opacity: 0; transform: translateY(5px) scale(0.3); letter-spacing: 1px; }
  15% { opacity: 1; transform: translateY(-8px) scale(1.5); letter-spacing: 6px; }
  30% { transform: translateY(-12px) scale(1.1); letter-spacing: 4px; }
  100% { opacity: 0; transform: translateY(-50px) scale(0.8); }
}

@keyframes luckyPop {
  0% { opacity: 0; transform: translateY(5px) scale(0.5); }
  20% { opacity: 1; transform: translateY(-5px) scale(1.2); }
  100% { opacity: 0; transform: translateY(-45px) scale(0.7); }
}

@keyframes screenShake {
  0%, 100% { transform: translate(0, 0); }
  10% { transform: translate(-3px, -2px); }
  20% { transform: translate(4px, 1px); }
  30% { transform: translate(-2px, 3px); }
  40% { transform: translate(3px, -1px); }
  50% { transform: translate(-1px, 2px); }
}

@keyframes screenShakeHeavy {
  0%, 100% { transform: translate(0, 0) rotate(0); }
  8% { transform: translate(-8px, -4px) rotate(-0.5deg); }
  16% { transform: translate(7px, 3px) rotate(0.5deg); }
  24% { transform: translate(-6px, 5px) rotate(-0.3deg); }
  32% { transform: translate(5px, -3px) rotate(0.3deg); }
  40% { transform: translate(-4px, 2px); }
  50% { transform: translate(3px, -2px); }
  60% { transform: translate(-2px, 1px); }
  75% { transform: translate(1px, -1px); }
}

@keyframes hp-pulse {
  0%,100% { opacity: 1; }
  50% { opacity: 0.6; }
}
@keyframes log-in {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

/* ── Ambient Floating Particles ── */
.ambient-dot {
  position: absolute;
  bottom: -5px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,215,0,0.8), rgba(212,164,76,0.3));
  pointer-events: none;
  animation: ambientFloat linear forwards;
  box-shadow: 0 0 4px rgba(255,215,0,0.3);
}
@keyframes ambientFloat {
  0% { transform: translateY(0) translateX(0); opacity: 0; }
  10% { opacity: 0.6; }
  90% { opacity: 0.2; }
  100% { transform: translateY(-350px) translateX(var(--drift, 20px)); opacity: 0; }
}

/* ── Confetti Pieces ── */
.confetti-piece {
  position: absolute;
  top: -10px;
  border-radius: 2px;
  pointer-events: none;
  animation: confettiFall ease-out forwards;
  opacity: 0;
}
@keyframes confettiFall {
  0% { opacity: 0; transform: translateY(-20px) translateX(0) rotate(0deg); }
  10% { opacity: 1; }
  100% { opacity: 0; transform: translateY(400px) translateX(var(--drift, 0px)) rotate(var(--spin, 360deg)); }
}

/* ── Combo Label FX ── */
.fx-combo-label {
  font-size: 14px;
  color: #ff6b6b;
  font-family: 'Cinzel', serif;
  letter-spacing: 3px;
  top: 60%;
  animation: comboBurst 1.4s ease-out forwards;
  filter: drop-shadow(0 0 8px rgba(255,107,107,0.6));
}
@keyframes comboBurst {
  0% { opacity: 0; transform: translateY(5px) scale(0.3); }
  15% { opacity: 1; transform: translateY(-5px) scale(1.4); }
  30% { transform: translateY(-10px) scale(1.1); }
  100% { opacity: 0; transform: translateY(-45px) scale(0.7); }
}
</style>

