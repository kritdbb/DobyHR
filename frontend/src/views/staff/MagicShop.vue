<template>
  <div class="staff-page">
    <div class="ms-header">
      <router-link to="/staff/services" class="ms-back">← Back</router-link>
      <h1 class="page-title">🔮 Magic Shop</h1>
      <p class="page-sub">Spend your Gold on mystic arts</p>
      <div class="ms-gold">💰 {{ myCoins }} Gold &nbsp; ✨ {{ myMana }} Mana</div>
    </div>

    <!-- ═══ Section 1: Scroll Emporium ═══ -->
    <div class="ms-section">
      <div class="ms-section-header">
        <span class="ms-section-icon">📜</span>
        <div>
          <h2 class="ms-section-title">Scroll Emporium</h2>
          <p class="ms-section-sub">Enhance your stats permanently</p>
        </div>
      </div>
      <div class="magic-grid">
        <div class="magic-card scroll-card luk">
          <div class="magic-icon">🍀</div>
          <div class="magic-name">Scroll of Luck</div>
          <div class="magic-desc">Permanently gain +1 LUK</div>
          <div class="magic-cost">Cost: 💰 1</div>
          <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_luck')">
            {{ buying === 'scroll_of_luck' ? 'Learning...' : 'Buy Scroll' }}
          </button>
          <div v-if="lastResult && lastResult.item === 'Scroll of Luck'" class="magic-result win">
            🍀 LUK is now {{ lastResult.new_value }}!
          </div>
        </div>

        <div class="magic-card scroll-card str">
          <div class="magic-icon">⚔️</div>
          <div class="magic-name">Scroll of Strength</div>
          <div class="magic-desc">Permanently gain +1 STR</div>
          <div class="magic-cost">Cost: 💰 1</div>
          <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_strength')">
            {{ buying === 'scroll_of_strength' ? 'Learning...' : 'Buy Scroll' }}
          </button>
          <div v-if="lastResult && lastResult.item === 'Scroll of Strength'" class="magic-result win">
            ⚔️ STR is now {{ lastResult.new_value }}!
          </div>
        </div>

        <div class="magic-card scroll-card def">
          <div class="magic-icon">🛡️</div>
          <div class="magic-name">Scroll of Defense</div>
          <div class="magic-desc">Permanently gain +1 DEF</div>
          <div class="magic-cost">Cost: 💰 1</div>
          <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_defense')">
            {{ buying === 'scroll_of_defense' ? 'Learning...' : 'Buy Scroll' }}
          </button>
          <div v-if="lastResult && lastResult.item === 'Scroll of Defense'" class="magic-result win">
            🛡️ DEF is now {{ lastResult.new_value }}!
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Section 2: Custom Workshop ═══ -->
    <div class="ms-section">
      <div class="ms-section-header">
        <span class="ms-section-icon">⚗️</span>
        <div>
          <h2 class="ms-section-title">Custom Workshop</h2>
          <p class="ms-section-sub">Craft your own identity</p>
        </div>
      </div>
      <div class="magic-grid">
        <div class="magic-card scroll-card title">
          <div class="magic-icon">📜</div>
          <div class="magic-name">Title Scroll</div>
          <div class="magic-desc">Write your own status (70 chars)</div>
          <div class="magic-cost">Cost: 💰 1</div>
          <div class="title-input-wrap">
            <input
              v-model="titleText"
              type="text"
              maxlength="70"
              placeholder="Enter your status..."
              class="title-input"
              :disabled="buying"
            />
            <span class="title-counter">{{ titleText.length }}/70</span>
          </div>
          <button class="magic-buy title-btn" :disabled="buying || myCoins < 1 || !titleText.trim()" @click="buyTitle">
            {{ buying === 'title_scroll' ? 'Writing...' : '📜 Set Status' }}
          </button>
          <div v-if="currentStatus" class="title-current">💬 {{ currentStatus }}</div>
          <div v-if="lastResult && lastResult.item === 'Title Scroll'" class="magic-result win">
            ✨ Status updated!
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Section 3: Lucky Zone ═══ -->
    <div class="ms-section" v-if="fortuneWheels.length > 0">
      <div class="ms-section-header">
        <span class="ms-section-icon">🎰</span>
        <div>
          <h2 class="ms-section-title">Lucky Zone</h2>
          <p class="ms-section-sub">Test your fate with fortune wheels</p>
        </div>
      </div>
      <div class="magic-grid">
        <div v-for="fw in fortuneWheels" :key="'fw-' + fw.id" class="magic-card fw-card">
          <div class="magic-icon">🎡</div>
          <div class="magic-name">{{ fw.name }}</div>
          <div class="magic-desc">Spin the wheel for a chance to win prizes!</div>
          <div class="magic-cost">Cost: {{ fw.currency === 'gold' ? '💰' : '✨' }} {{ fw.price }} {{ fw.currency === 'gold' ? 'Gold' : 'Mana' }}</div>
          <button class="magic-buy fw-buy-btn" :disabled="buying || (fw.currency === 'gold' ? myCoins < fw.price : myMana < fw.price)" @click="openWheelPopup(fw)">
            🎡 Spin!
          </button>
        </div>
      </div>
    </div>

    <!-- Fortune Wheel Spin Popup Overlay -->
    <div v-if="showWheelPopup" class="fw-overlay">
      <div class="fw-popup">
        <button class="fw-popup-close" @click="closeWheelPopup" :disabled="fwSpinning">✕</button>
        <div class="fw-popup-title">🎡 {{ activeWheel?.name || 'Fortune Wheel' }}</div>
        <div class="fw-popup-subtitle">{{ activeWheel?.currency === 'gold' ? '💰' : '✨' }} {{ activeWheel?.price }} {{ activeWheel?.currency === 'gold' ? 'Gold' : 'Mana' }}</div>

        <div class="fw-popup-wheel-container">
          <div class="fw-popup-glow" :class="{ spinning: fwSpinning, won: fwResult && !fwSpinning }"></div>
          <div class="fw-popup-pointer">
            <svg width="30" height="38" viewBox="0 0 36 44">
              <polygon points="18,44 4,8 18,16 32,8" fill="#ffd700" stroke="#8b6914" stroke-width="1.5"/>
              <circle cx="18" cy="10" r="5" fill="#ffd700" stroke="#8b6914" stroke-width="1"/>
            </svg>
          </div>
          <canvas ref="fwCanvas" :width="fwSize" :height="fwSize" class="fw-popup-canvas" :style="fwWheelStyle"></canvas>
          <div class="fw-popup-hub">⚜</div>
        </div>

        <button v-if="!fwSpinning && !fwResult" class="fw-popup-spin-btn" @click="spinFortuneWheel" :disabled="fwSpinning">
          ⚔️ SPIN!
        </button>

        <transition name="result-fade">
          <div v-if="fwResult && !fwSpinning" class="fw-popup-result">
            <div class="fw-popup-result-title">{{ fwResult.message }}</div>
            <div class="fw-popup-result-sparks">✦ ✧ ✦</div>
            <button class="fw-popup-done-btn" @click="closeWheelPopup">Continue</button>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { buyMagicItem, getActiveFortuneWheels, spinFortuneWheel } from '../../services/api'

export default {
  name: 'MagicShop',
  data() {
    return {
      myCoins: 0,
      buying: null,
      lastResult: null,
      titleText: '',
      currentStatus: '',
      // Fortune Wheels
      fortuneWheels: [],
      myMana: 0,
      showWheelPopup: false,
      activeWheel: null,
      fwSpinning: false,
      fwResult: null,
      fwSize: 340,
      fwRotation: 0,
      fwUseTransition: false,
      fwSpinDuration: 0,
    }
  },
  computed: {
    fwWheelStyle() {
      return {
        transform: `rotate(${this.fwRotation}deg)`,
        transition: this.fwUseTransition
          ? `transform ${this.fwSpinDuration}s cubic-bezier(0.15, 0.60, 0.07, 1.0)`
          : 'none',
      }
    },
  },
  mounted() {
    this.refreshCoins()
    this.loadFortuneWheels()
  },
  methods: {
    async refreshCoins() {
      try {
        const { data } = await import('../../services/api').then(m => m.default.get('/api/users/me'))
        this.myCoins = data.coins || 0
        this.myMana = data.angel_coins || 0
        this.currentStatus = data.status_text || ''
      } catch (e) { /* ignore */ }
    },


    async buy(itemType) {
      if (this.myCoins < 1) return
      this.buying = itemType
      this.lastResult = null
      try {
        const { data } = await buyMagicItem(itemType)
        this.lastResult = data
        this.myCoins = data.coins
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        alert(msg)
      } finally {
        this.buying = null
      }
    },

    async buyTitle() {
      if (!this.titleText.trim() || this.myCoins < 1 || this.buying) return
      this.buying = 'title_scroll'
      this.lastResult = null
      try {
        const { data } = await buyMagicItem('title_scroll', { status_text: this.titleText.trim() })
        this.lastResult = data
        this.myCoins = data.coins
        this.currentStatus = data.status_text
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        user.status_text = data.status_text
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        alert(msg)
      } finally {
        this.buying = null
      }
    },

    // ── Fortune Wheel ──
    async loadFortuneWheels() {
      try {
        const { data } = await getActiveFortuneWheels()
        this.fortuneWheels = data
      } catch (e) { console.error('Failed to load fortune wheels', e) }
    },

    openWheelPopup(fw) {
      this.activeWheel = fw
      this.fwResult = null
      this.fwSpinning = false
      this.fwRotation = 0
      this.fwUseTransition = false
      this.showWheelPopup = true
      this.$nextTick(() => this.drawFwWheel())
    },

    closeWheelPopup() {
      if (this.fwSpinning) return
      this.showWheelPopup = false
      this.activeWheel = null
      this.fwResult = null
    },

    drawFwWheel() {
      const canvas = this.$refs.fwCanvas
      if (!canvas || !this.activeWheel) return
      const ctx = canvas.getContext('2d')
      const size = this.fwSize
      const cx = size / 2, cy = size / 2, r = size / 2 - 10
      const segments = this.activeWheel.segments
      const total = segments.reduce((s, seg) => s + (seg.weight || 1), 0)
      let startAngle = 0

      ctx.clearRect(0, 0, size, size)

      segments.forEach(seg => {
        const sliceAngle = ((seg.weight || 1) / total) * 2 * Math.PI
        const midAngle = startAngle + sliceAngle / 2
        const gx = cx + r * 0.5 * Math.cos(midAngle)
        const gy = cy + r * 0.5 * Math.sin(midAngle)
        const grad = ctx.createRadialGradient(cx, cy, 25, gx, gy, r)
        grad.addColorStop(0, this.lightenHex(seg.color, 30))
        grad.addColorStop(0.6, seg.color)
        grad.addColorStop(1, this.darkenHex(seg.color, 30))

        ctx.beginPath(); ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, r, startAngle, startAngle + sliceAngle)
        ctx.closePath(); ctx.fillStyle = grad; ctx.fill()
        ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 2; ctx.stroke()

        // Label
        ctx.save(); ctx.translate(cx, cy)
        ctx.rotate(startAngle + sliceAngle / 2)
        ctx.textAlign = 'right'; ctx.fillStyle = '#fff'
        ctx.font = `bold ${Math.max(10, Math.min(13, 120 / segments.length))}px Inter, sans-serif`
        ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 3
        const label = seg.label || ''
        ctx.fillText(label.length > 12 ? label.substring(0, 12) + '…' : label, r - 16, 4)
        ctx.shadowBlur = 0; ctx.restore()
        startAngle += sliceAngle
      })

      // Outer rings
      for (let ring = 0; ring < 2; ring++) {
        ctx.beginPath(); ctx.arc(cx, cy, r + 3 + ring * 3, 0, 2 * Math.PI)
        ctx.strokeStyle = ring === 0 ? '#ffd700' : '#8b6914'
        ctx.lineWidth = ring === 0 ? 3 : 2; ctx.stroke()
      }
      ctx.beginPath(); ctx.arc(cx, cy, 28, 0, 2 * Math.PI)
      ctx.strokeStyle = '#ffd700'; ctx.lineWidth = 2; ctx.stroke()
    },

    async spinFortuneWheel() {
      if (this.fwSpinning || !this.activeWheel) return
      this.fwSpinning = true
      this.fwResult = null
      this.fwUseTransition = false

      try {
        const { data } = await spinFortuneWheel(this.activeWheel.id)
        this.myCoins = data.coins
        this.myMana = data.angel_coins
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins; user.angel_coins = data.angel_coins
        localStorage.setItem('user', JSON.stringify(user))

        const winnerIndex = data.segment_index
        const segments = this.activeWheel.segments
        const total = segments.reduce((s, seg) => s + (seg.weight || 1), 0)

        let cumAngle = 0
        for (let i = 0; i < winnerIndex; i++) {
          cumAngle += ((segments[i].weight || 1) / total) * 360
        }
        const segSize = ((segments[winnerIndex].weight || 1) / total) * 360
        const segCenter = cumAngle + segSize / 2
        const jitter = (Math.random() - 0.5) * segSize * 0.6

        const baseRotation = this.fwRotation % 360
        const targetAngle = segCenter + jitter
        const remainder = (((targetAngle - 270 + baseRotation) % 360) + 360) % 360
        const fullSpins = data.rotations || 5
        const totalCCW = fullSpins * 360 + remainder

        void this.$refs.fwCanvas?.offsetHeight
        this.fwSpinDuration = 4 + Math.random() * 2

        this.$nextTick(() => {
          this.fwUseTransition = true
          this.fwRotation = this.fwRotation - totalCCW

          setTimeout(() => {
            this.fwSpinning = false
            this.fwUseTransition = false
            this.fwResult = data
          }, this.fwSpinDuration * 1000 + 400)
        })
      } catch (e) {
        this.fwSpinning = false
        alert(e.response?.data?.detail || 'Spin failed')
      }
    },

    lightenHex(hex, pct) {
      const n = parseInt(hex.replace('#', ''), 16)
      const r = Math.min(255, (n >> 16) + Math.round(255 * pct / 100))
      const g = Math.min(255, ((n >> 8) & 0xFF) + Math.round(255 * pct / 100))
      const b = Math.min(255, (n & 0xFF) + Math.round(255 * pct / 100))
      return `rgb(${r},${g},${b})`
    },
    darkenHex(hex, pct) {
      const n = parseInt(hex.replace('#', ''), 16)
      const r = Math.max(0, (n >> 16) - Math.round(255 * pct / 100))
      const g = Math.max(0, ((n >> 8) & 0xFF) - Math.round(255 * pct / 100))
      const b = Math.max(0, (n & 0xFF) - Math.round(255 * pct / 100))
      return `rgb(${r},${g},${b})`
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 16px 0; }

.ms-header { margin-bottom: 20px; }
.ms-back {
  display: inline-block; margin-bottom: 8px;
  color: #b8860b; font-weight: 700; font-size: 13px;
  text-decoration: none; opacity: 0.8;
}
.ms-back:hover { opacity: 1; }
.page-title {
  font-family: 'Cinzel', serif;
  font-size: 24px; font-weight: 800; color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub {
  color: #8b7355; font-size: 13px; font-weight: 600;
  font-style: italic; margin-bottom: 8px;
}
.ms-gold {
  display: inline-block;
  background: linear-gradient(135deg, rgba(212,164,76,0.15), rgba(184,134,11,0.1));
  border: 1px solid rgba(212,164,76,0.3);
  border-radius: 8px; padding: 6px 14px;
  font-size: 16px; font-weight: 800; color: #d4a44c;
}

/* Grid */
.magic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

/* Card */
.magic-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 20px 14px 16px;
  display: flex; flex-direction: column; align-items: center;
  text-align: center;
  transition: all 0.2s;
}
.magic-card:hover {
  border-color: rgba(212,164,76,0.35);
  box-shadow: 0 6px 24px rgba(212,164,76,0.08);
}

.scroll-card.luk { border-color: rgba(46,204,113,0.25); }
.scroll-card.str { border-color: rgba(231,76,60,0.25); }
.scroll-card.def { border-color: rgba(52,152,219,0.25); }
.scroll-card.title { border-color: rgba(241,196,15,0.3); grid-column: 1 / -1; }

.magic-icon {
  font-size: 36px; margin-bottom: 8px;
  filter: drop-shadow(0 2px 6px rgba(212,164,76,0.3));
}
.magic-name {
  font-family: 'Cinzel', serif;
  font-size: 14px; font-weight: 700; color: #e8d5b7;
  margin-bottom: 6px;
}
.magic-desc {
  font-size: 11px; color: #8b7355; font-weight: 600;
  margin-bottom: 10px; line-height: 1.4;
}
.magic-cost {
  font-size: 12px; font-weight: 700; color: #d4a44c;
  margin-bottom: 10px;
}

.magic-buy {
  width: 100%; padding: 8px 0;
  border: none; border-radius: 8px;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; font-weight: 800; font-size: 13px;
  cursor: pointer; transition: all 0.2s;
}
.magic-buy:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(212,164,76,0.3);
}
.magic-buy:disabled {
  opacity: 0.4; cursor: not-allowed;
}

.magic-result {
  margin-top: 10px; padding: 6px 10px;
  border-radius: 8px; font-size: 12px; font-weight: 700;
  animation: fadeIn 0.3s ease;
}
.magic-result.win {
  background: rgba(46,204,113,0.1); color: #2ecc71;
  border: 1px solid rgba(46,204,113,0.2);
}

/* Title Scroll Input */
.title-input-wrap {
  width: 100%; position: relative; margin-bottom: 8px;
}
.title-input {
  width: 100%; padding: 8px 10px; border-radius: 8px;
  border: 1px solid rgba(241,196,15,0.3);
  background: rgba(0,0,0,0.3); color: #e8d5b7;
  font-size: 13px; font-weight: 600;
  outline: none; box-sizing: border-box;
}
.title-input:focus {
  border-color: rgba(241,196,15,0.6);
  box-shadow: 0 0 10px rgba(241,196,15,0.1);
}
.title-input::placeholder { color: #6b5a3e; }
.title-counter {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  font-size: 10px; color: #6b5a3e; font-weight: 700;
}
.title-btn {
  background: linear-gradient(135deg, #d4a017, #f1c40f) !important;
  color: #1c1208 !important;
}
.title-current {
  margin-top: 8px; font-size: 11px; color: #f1c40f;
  font-style: italic; font-weight: 600;
  word-break: break-word;
}

/* ── Section Headers ── */
.ms-section {
  margin-bottom: 28px;
}
.ms-section-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(212,164,76,0.12);
}
.ms-section-icon {
  font-size: 28px;
  filter: drop-shadow(0 2px 6px rgba(212,164,76,0.3));
}
.ms-section-title {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 800; color: #d4a44c;
  margin: 0;
  text-shadow: 0 1px 4px rgba(212,164,76,0.15);
}
.ms-section-sub {
  font-size: 11px; color: #8b7355; font-weight: 600;
  font-style: italic; margin: 2px 0 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Fortune Wheel Card ── */
.fw-card { border-color: rgba(255,215,0,0.25); }
.fw-card:hover { border-color: rgba(255,215,0,0.5); box-shadow: 0 4px 20px rgba(255,215,0,0.08); }
.fw-buy-btn {
  background: linear-gradient(135deg, #8b6914, #d4a44c) !important;
  color: #fff !important;
}

/* ── Fortune Wheel Popup ── */
.fw-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.9);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}
.fw-popup {
  background: linear-gradient(145deg, #1a0a2e, #0f0a08, #1a0a2e);
  border: 3px solid rgba(255,215,0,0.4);
  border-radius: 24px;
  padding: 32px 28px;
  text-align: center;
  max-width: 420px; width: 95%;
  position: relative;
  box-shadow:
    0 0 60px rgba(255,215,0,0.1),
    0 0 120px rgba(0,0,0,0.5),
    inset 0 0 40px rgba(255,215,0,0.03);
}
.fw-popup-close {
  position: absolute; top: 12px; right: 16px;
  background: none; border: none; color: #8b7355;
  font-size: 20px; cursor: pointer;
}
.fw-popup-close:hover { color: #d4a44c; }
.fw-popup-close:disabled { opacity: 0.3; cursor: not-allowed; }
.fw-popup-title {
  font-family: 'Cinzel', serif;
  font-size: 20px; font-weight: 800;
  color: #ffd700;
  text-shadow: 0 0 20px rgba(255,215,0,0.3);
  margin-bottom: 4px;
}
.fw-popup-subtitle {
  font-size: 13px; color: #8b7355; font-weight: 600;
  margin-bottom: 20px;
}
.fw-popup-wheel-container {
  position: relative;
  display: inline-block;
  margin: 0 auto;
}
.fw-popup-glow {
  position: absolute;
  top: -12px; left: -12px; right: -12px; bottom: -12px;
  border-radius: 50%;
  border: 2px solid rgba(255,215,0,0.1);
  transition: all 0.5s;
}
.fw-popup-glow.spinning {
  border-color: rgba(255,215,0,0.4);
  box-shadow: 0 0 40px rgba(255,215,0,0.15), 0 0 80px rgba(255,215,0,0.08);
  animation: fwPulse 0.6s ease-in-out infinite alternate;
}
.fw-popup-glow.won {
  border-color: rgba(255,215,0,0.6);
  box-shadow: 0 0 60px rgba(255,215,0,0.25);
}
@keyframes fwPulse {
  0% { box-shadow: 0 0 40px rgba(255,215,0,0.15); }
  100% { box-shadow: 0 0 60px rgba(255,215,0,0.25); }
}
.fw-popup-pointer {
  position: absolute; top: -18px; left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  filter: drop-shadow(0 3px 6px rgba(0,0,0,0.7));
}
.fw-popup-canvas {
  display: block; border-radius: 50%;
  box-shadow:
    0 0 0 3px rgba(139,105,20,0.5),
    0 0 30px rgba(0,0,0,0.5);
}
.fw-popup-hub {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 50px; height: 50px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #ffd700, #8b6914, #4a3600);
  border: 3px solid #ffd700;
  box-shadow: 0 0 12px rgba(255,215,0,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #1a0a00;
  z-index: 10; pointer-events: none;
}
.fw-popup-spin-btn {
  margin-top: 24px;
  padding: 14px 48px;
  background: linear-gradient(180deg, #5a3a0a 0%, #2c1a00 50%, #1a0e00 100%);
  border: 2px solid #8b6914;
  color: #ffd700;
  border-radius: 8px;
  font-size: 16px; font-weight: 900;
  font-family: 'Cinzel', serif;
  cursor: pointer; letter-spacing: 2px;
  text-transform: uppercase;
  transition: all 0.3s;
}
.fw-popup-spin-btn:hover {
  border-color: #ffd700;
  box-shadow: 0 4px 30px rgba(255,215,0,0.2);
  transform: translateY(-2px);
}
.fw-popup-spin-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.fw-popup-result {
  margin-top: 20px;
  animation: fwResultSlam 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.fw-popup-result-title {
  font-family: 'Cinzel', serif;
  font-size: 22px; font-weight: 900;
  color: #ffd700;
  text-shadow: 0 0 20px rgba(255,215,0,0.4);
  margin-bottom: 8px;
}
.fw-popup-result-sparks {
  font-size: 14px; color: #8b6914;
  letter-spacing: 6px; margin-bottom: 16px;
  animation: fwSparkle 1.5s ease-in-out infinite;
}
.fw-popup-done-btn {
  padding: 10px 32px;
  background: linear-gradient(135deg, #8b6914, #d4a44c);
  border: none; border-radius: 10px;
  color: #fff; font-weight: 800; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
}
.fw-popup-done-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(212,164,76,0.3);
}
@keyframes fwResultSlam {
  0% { transform: scale(2) rotate(-5deg); opacity: 0; }
  60% { transform: scale(0.95) rotate(1deg); }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}
@keyframes fwSparkle {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.result-fade-enter-active { animation: fwResultSlam 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }
.result-fade-leave-active { opacity: 0; transition: opacity 0.2s; }
</style>
