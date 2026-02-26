<template>
  <div class="hof-page">
    <!-- Background image overlay -->
    <div class="hof-bg"></div>
    <div class="hof-vignette"></div>

    <!-- Header -->
    <div class="hof-header">
      <div class="hof-emblem">⚔️</div>
      <h1 class="hof-title">REVIVAL RECORDS</h1>
      <div class="hof-divider">
        <span class="div-line"></span>
        <span class="div-gem">💀</span>
        <span class="div-line"></span>
      </div>
      <p class="hof-tagline">Those who defied death, and those who pulled them back</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="hof-loading">
      <div class="skull-pulse">💀</div>
      <p>Summoning the records...</p>
    </div>

    <!-- Empty -->
    <div v-else-if="records.length === 0" class="hof-empty">
      <div class="empty-skull">☠️</div>
      <p class="empty-text">No souls have been revived yet</p>
      <p class="empty-sub">The halls remain silent...</p>
    </div>

    <!-- Records -->
    <div v-else class="hof-records">
      <div v-for="(r, idx) in records" :key="r.id" class="hof-card" :class="{'hof-card-legendary': idx === 0}">
        <!-- Corner ornaments -->
        <div class="corner-tl"></div>
        <div class="corner-tr"></div>
        <div class="corner-bl"></div>
        <div class="corner-br"></div>

        <!-- Rank flame -->
        <div class="card-rank" :class="'rank-' + Math.min(idx+1, 4)">
          <span v-if="idx === 0" class="rank-icon">👑</span>
          <span v-else-if="idx === 1" class="rank-icon">⚔️</span>
          <span v-else-if="idx === 2" class="rank-icon">🛡️</span>
          <span v-else class="rank-num">#{{ idx + 1 }}</span>
        </div>

        <!-- Revived hero -->
        <div class="card-hero">
          <div class="hero-frame" :class="{'hero-legendary': idx === 0}">
            <img v-if="r.revived_user.image" :src="r.revived_user.image" class="hero-img" />
            <span v-else class="hero-letter">{{ r.revived_user.name.charAt(0) }}</span>
          </div>
          <div class="hero-info">
            <div class="hero-name">{{ r.revived_user.name }}</div>
            <div class="hero-status">
              <span class="status-revived">REVIVED</span>
              <span class="status-dot">✦</span>
              <span class="status-date">{{ formatDate(r.date) }}</span>
            </div>
          </div>
        </div>

        <!-- Separator -->
        <div class="card-sep">
          <span class="sep-line"></span>
          <span class="sep-icon">🙏</span>
          <span class="sep-line"></span>
        </div>

        <!-- Rescuers -->
        <div class="card-rescuers">
          <div class="rescuers-title">HEROES WHO ANSWERED THE CALL</div>
          <div class="rescuers-grid">
            <div v-for="(rc, ri) in r.rescuers" :key="ri" class="rescuer-badge">
              <div class="rescuer-portrait">
                <img v-if="rc.image" :src="rc.image" class="rescuer-img" />
                <span v-else class="rescuer-letter">{{ rc.name.charAt(0) }}</span>
              </div>
              <span class="rescuer-name">{{ rc.name }}</span>
            </div>
          </div>
        </div>

        <!-- Gold footer -->
        <div v-if="r.gold_given > 0" class="card-gold">
          <span class="gold-icon">💰</span>
          <span class="gold-amount">+{{ r.gold_given }} Gold Restored</span>
        </div>
      </div>
    </div>

    <!-- Back -->
    <router-link to="/staff/services" class="hof-back">
      <span>⬅ Return to Guild</span>
    </router-link>
  </div>
</template>

<script>
import api from '../../services/api'

export default {
  data() {
    return { records: [], loading: true }
  },
  async mounted() {
    try {
      const { data } = await api.get('/api/users/rescue/records')
      this.records = data
    } catch (e) {
      this.records = []
    } finally {
      this.loading = false
    }
  },
  methods: {
    formatDate(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      const day = d.getDate()
      const months = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']
      return `${day} ${months[d.getMonth()]} ${d.getFullYear() + 543}`
    },
  },
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&display=swap');

/* ─── Page & Background ─── */
.hof-page {
  position: relative;
  min-height: 100vh;
  padding: 0 0 32px;
  overflow: hidden;
}
.hof-bg {
  position: fixed;
  inset: 0;
  background: url('/icons/revive_record.webp') center center / cover no-repeat;
  opacity: 0.06;
  pointer-events: none;
  z-index: 0;
}
.hof-vignette {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 30%, rgba(10,6,2,0.7) 100%);
  pointer-events: none;
  z-index: 0;
}

/* ─── Header ─── */
.hof-header {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 32px 20px 20px;
}
.hof-emblem {
  font-size: 36px;
  margin-bottom: 4px;
  filter: drop-shadow(0 0 12px rgba(212,164,76,0.4));
}
.hof-title {
  font-family: 'Cinzel', serif;
  font-size: 26px;
  font-weight: 900;
  letter-spacing: 4px;
  background: linear-gradient(180deg, #f5d98a 0%, #c9952c 40%, #8b6914 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
}
.hof-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 12px 0 8px;
}
.div-line {
  display: block;
  width: 60px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #8b6914, transparent);
}
.div-gem { font-size: 16px; opacity: 0.6; }
.hof-tagline {
  font-size: 11px;
  color: #6b5a40;
  font-style: italic;
  letter-spacing: 1px;
}

/* ─── Loading ─── */
.hof-loading {
  position: relative; z-index: 1;
  text-align: center;
  padding: 60px 0;
  color: #6b5a40;
}
.skull-pulse {
  font-size: 40px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* ─── Empty ─── */
.hof-empty {
  position: relative; z-index: 1;
  text-align: center;
  padding: 60px 20px;
}
.empty-skull { font-size: 48px; opacity: 0.3; margin-bottom: 12px; }
.empty-text { color: #6b5a40; font-size: 15px; }
.empty-sub { color: #4a3d2a; font-size: 12px; font-style: italic; margin-top: 4px; }

/* ─── Records ─── */
.hof-records {
  position: relative; z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0 4px;
}

/* ─── Card ─── */
.hof-card {
  position: relative;
  background: linear-gradient(160deg, rgba(30,20,10,0.95) 0%, rgba(20,12,6,0.98) 100%);
  border: 1px solid rgba(139,105,20,0.2);
  border-radius: 4px;
  padding: 24px 20px 18px;
  overflow: hidden;
}
.hof-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url('/icons/revive_record.webp') center center / 200px no-repeat;
  opacity: 0.03;
  pointer-events: none;
}
.hof-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 5%, rgba(139,105,20,0.4) 50%, transparent 95%);
}

/* Legendary card (1st) */
.hof-card-legendary {
  border-color: rgba(212,164,76,0.35);
  box-shadow:
    0 0 20px rgba(212,164,76,0.08),
    inset 0 0 40px rgba(212,164,76,0.03);
}
.hof-card-legendary::after {
  height: 3px;
  background: linear-gradient(90deg, transparent, #d4a44c, transparent);
}

/* Corner ornaments */
.corner-tl, .corner-tr, .corner-bl, .corner-br {
  position: absolute;
  width: 16px; height: 16px;
  border-color: rgba(139,105,20,0.3);
  border-style: solid;
}
.corner-tl { top: 4px; left: 4px; border-width: 1px 0 0 1px; }
.corner-tr { top: 4px; right: 4px; border-width: 1px 1px 0 0; }
.corner-bl { bottom: 4px; left: 4px; border-width: 0 0 1px 1px; }
.corner-br { bottom: 4px; right: 4px; border-width: 0 1px 1px 0; }
.hof-card-legendary .corner-tl,
.hof-card-legendary .corner-tr,
.hof-card-legendary .corner-bl,
.hof-card-legendary .corner-br {
  border-color: rgba(212,164,76,0.5);
  width: 20px; height: 20px;
}

/* ─── Rank ─── */
.card-rank {
  position: absolute;
  top: 8px; right: 12px;
  z-index: 2;
}
.rank-icon { font-size: 20px; }
.rank-1 .rank-icon { font-size: 24px; filter: drop-shadow(0 0 8px rgba(255,215,0,0.5)); }
.rank-num {
  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 700;
  color: #5a4a30;
}

/* ─── Hero (revived user) ─── */
.card-hero {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
}
.hero-frame {
  position: relative;
  width: 60px; height: 60px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  border: 2px solid rgba(139,105,20,0.3);
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
}
.hero-legendary {
  border-color: rgba(212,164,76,0.5);
  box-shadow: 0 0 16px rgba(212,164,76,0.15), 0 0 6px rgba(0,0,0,0.6);
  animation: frame-glow 3s ease-in-out infinite;
}
@keyframes frame-glow {
  0%, 100% { box-shadow: 0 0 16px rgba(212,164,76,0.1); }
  50% { box-shadow: 0 0 24px rgba(212,164,76,0.25); }
}
.hero-img {
  width: 100%; height: 100%;
  object-fit: cover;
}
.hero-letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #2c180e, #1a0f08);
  color: #d4a44c;
  font-family: 'Cinzel', serif;
  font-size: 24px;
  font-weight: 900;
}
.hero-info { flex: 1; min-width: 0; }
.hero-name {
  font-family: 'Cinzel', serif;
  font-size: 18px;
  font-weight: 700;
  color: #e8d5b7;
  line-height: 1.2;
}
.hero-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.status-revived {
  font-family: 'Cinzel', serif;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #4ade80;
  text-shadow: 0 0 8px rgba(74,222,128,0.3);
}
.status-dot { font-size: 6px; color: #5a4a30; }
.status-date { font-size: 11px; color: #5a4a30; }

/* ─── Separator ─── */
.card-sep {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 14px 0;
  position: relative;
  z-index: 1;
}
.sep-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139,105,20,0.2), transparent);
}
.sep-icon { font-size: 14px; opacity: 0.5; }

/* ─── Rescuers ─── */
.card-rescuers { position: relative; z-index: 1; }
.rescuers-title {
  font-family: 'Cinzel', serif;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #6b5a40;
  text-align: center;
  margin-bottom: 10px;
}
.rescuers-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.rescuer-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 64px;
}
.rescuer-portrait {
  width: 40px; height: 40px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(139,105,20,0.25);
  box-shadow: 0 2px 6px rgba(0,0,0,0.4);
}
.rescuer-img {
  width: 100%; height: 100%;
  object-fit: cover;
}
.rescuer-letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #1e140a, #140c06);
  color: #8b7355;
  font-family: 'Cinzel', serif;
  font-size: 16px;
  font-weight: 700;
}
.rescuer-name {
  font-size: 10px;
  font-weight: 600;
  color: #8b7355;
  text-align: center;
  line-height: 1.2;
  max-width: 80px;
}

/* ─── Gold ─── */
.card-gold {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid rgba(139,105,20,0.1);
  position: relative;
  z-index: 1;
}
.gold-icon { font-size: 14px; }
.gold-amount {
  font-family: 'Cinzel', serif;
  font-size: 12px;
  font-weight: 700;
  color: #d4a44c;
  letter-spacing: 1px;
}

/* ─── Back ─── */
.hof-back {
  display: block;
  text-align: center;
  margin: 28px 4px 0;
  padding: 14px;
  color: #5a4a30;
  font-family: 'Cinzel', serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 1px;
  text-decoration: none;
  border: 1px solid rgba(139,105,20,0.15);
  border-radius: 4px;
  background: rgba(20,12,6,0.6);
  transition: all 0.3s;
  position: relative;
  z-index: 1;
}
.hof-back:hover {
  border-color: rgba(212,164,76,0.3);
  color: #d4a44c;
  background: rgba(30,18,10,0.8);
}
</style>
