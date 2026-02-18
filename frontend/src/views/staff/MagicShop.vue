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
      <div class="scroll-row">
        <div class="scroll-item" v-for="s in scrollTypes" :key="s.type"
          :style="{ backgroundImage: 'linear-gradient(rgba(17,10,30,0.55), rgba(17,10,30,0.8)), url(' + s.bg + ')', backgroundSize: 'cover', backgroundPosition: 'center' }">
          <div class="scroll-icon">{{ s.icon }}</div>
          <div class="scroll-name">{{ s.name }}</div>
          <div class="scroll-desc">+1 {{ s.stat }}</div>
          <div class="scroll-cost">💰 20</div>
          <button class="magic-buy" :disabled="buying || myCoins < 20" @click="confirmScroll(s)">
            {{ buying === s.type ? 'Learning...' : 'Buy' }}
          </button>
          <div v-if="lastResult && lastResult.item === s.name" class="magic-result win">
            {{ s.icon }} {{ s.stat }} → {{ lastResult.new_value }}!
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
        <div v-for="fw in fortuneWheels" :key="'fw-' + fw.id" class="magic-card fw-card"
          :style="fw.icon_image ? { backgroundImage: 'url(' + apiBase + fw.icon_image + ')', backgroundSize: 'cover', backgroundPosition: 'center' } : {}">
          <div v-if="!fw.icon_image" class="magic-icon">🎡</div>
          <div class="magic-name">{{ fw.name }}</div>
          <div class="magic-desc">Spin the wheel for a chance to win prizes!</div>
          <div class="magic-cost">Cost: {{ fw.currency === 'gold' ? '💰' : '✨' }} {{ fw.price }} {{ fw.currency === 'gold' ? 'Gold' : 'Mana' }}</div>
          <button class="magic-buy fw-buy-btn" :disabled="buying || (fw.currency === 'gold' ? myCoins < fw.price : myMana < fw.price)" @click="openWheelPopup(fw)">
            🎡 Spin!
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Section 4: Cosmetics ═══ -->
    <div class="ms-section">
      <div class="ms-section-header">
        <span class="ms-section-icon">🎨</span>
        <div>
          <h2 class="ms-section-title">Cosmetics</h2>
          <p class="ms-section-sub">Customize your appearance in Town People</p>
        </div>
      </div>

      <!-- ██ DEMO CARD ██ -->
      <div class="demo-card-wrap">
        <div class="demo-card" :style="demoBgStyle">
          <div class="person-portrait">
            <img v-if="demoArtifactImg" :src="demoArtifactImg" class="demo-artifact-ring-img" :class="'effect-' + demoArtifactEffect" />
            <div v-else-if="demoArtifact" class="demo-artifact-ring-css" :class="'effect-' + demoArtifactEffect" :style="{ borderColor: demoArtifactColor, boxShadow: '0 0 18px ' + demoArtifactColor + '66' }"></div>
            <img v-if="myImage" :src="myImage" class="person-img" />
            <div v-else class="person-placeholder">{{ (myName || '?').charAt(0) }}</div>
            <span class="person-role-tag" :class="myRole">{{ myRole }}</span>
          </div>
          <div class="person-name">{{ myName.split(' ')[0] || '' }}</div>
          <div class="person-surname">{{ myName.split(' ').slice(1).join(' ') || '' }}</div>
          <div class="person-position">{{ myPosition }}</div>
          <div v-if="demoStatus" class="person-status">"{{ demoStatus }}"</div>
          <div class="person-stats">
            <span class="ps str">⚔️ {{ myStats.str }}</span>
            <span class="ps def">🛡️ {{ myStats.def }}</span>
            <span class="ps luk">🍀 {{ myStats.luk }}</span>
          </div>
          <div class="person-badges" v-if="myBadges.length">
            <div v-for="b in myBadges.slice(0,5)" :key="b.id" class="pb-circle" :title="b.name">
              <img v-if="b.image" :src="b.image" class="pb-img" />
              <span v-else>🏅</span>
            </div>
          </div>
          <div class="person-currency">
            <span class="cur gold">💰 {{ myCoins }}</span>
            <span class="cur mana">✨ {{ myMana }}</span>
          </div>
        </div>
        <div class="demo-label">👆 Live Preview</div>
      </div>

      <!-- Row: Title Scroll + Background -->
      <div class="cosm-row">
        <div class="cosm-panel">
          <div class="cosm-sub-header">📜 Title Scroll <span class="cosm-price">✨ 2 Mana</span></div>
          <div class="cosm-panel-body">
            <div class="title-input-wrap">
              <input v-model="titleText" type="text" maxlength="70" placeholder="Enter your status..." class="title-input" :disabled="buying" />
              <span class="title-counter">{{ titleText.length }}/70</span>
            </div>
            <button class="magic-buy cosm-buy" :disabled="buying || myMana < 2 || !titleText.trim()" @click="confirmBuyTitle">
              {{ buying === 'title_scroll' ? 'Writing...' : '📜 Set Status (✨2)' }}
            </button>
            <div v-if="currentStatus" class="title-current">💬 Current: "{{ currentStatus }}"</div>
            <div v-if="lastResult && lastResult.item === 'Title Scroll'" class="magic-result win">✨ Status updated!</div>
          </div>
        </div>
        <div class="cosm-panel">
          <div class="cosm-sub-header">🖼️ Background <span class="cosm-price">✨ 2 Mana / change</span></div>
          <div class="cosm-panel-body">
            <label class="cosm-file-label">
              📂 Choose Image
              <input type="file" accept="image/*" class="cosm-file-input" @change="onBgFileChange" :disabled="buyingCosmetic" />
            </label>
            <button v-if="bgFile" class="magic-buy cosm-buy" :disabled="buyingCosmetic || myMana < 2" @click="confirmUploadBackground">
              {{ buyingCosmetic === 'bg' ? 'Uploading...' : '🖼️ Set Background (✨2)' }}
            </button>
            <div v-if="currentBg && !bgFile" class="title-current">✓ Background active</div>
            <div v-if="bgResult" class="magic-result win">✨ Background updated!</div>
          </div>
        </div>
      </div>

      <!-- Circle Artifacts -->
      <div class="cosm-sub-header" style="margin-top:18px;">💎 Artifacts <span class="cosm-price">Tap to preview → Buy to equip</span></div>
      <div v-if="artifactCatalog.length" class="artifact-grid">
        <div v-for="a in artifactCatalog" :key="a.id"
          class="artifact-card" :class="[a.rarity, { equipped: equippedArtifact === String(a.id), previewing: previewArtifact === String(a.id) }]"
          :style="{ '--art-color': a.color }"
          @click="previewArtifactOnDemo(a)">
          <div class="artifact-ring" :class="'effect-' + (a.effect || 'pulse')" :style="{ borderColor: a.color, boxShadow: '0 0 12px ' + a.color + '44' }">
            <img v-if="a.image" :src="a.image" class="artifact-img" />
            <div v-else class="artifact-inner" :style="{ background: 'radial-gradient(circle, ' + a.color + '33, transparent)' }"></div>
          </div>
          <div class="artifact-name">{{ a.name }}</div>
          <div class="artifact-rarity">{{ a.rarity }}</div>
          <div class="artifact-effect-tag">{{ {pulse:'💫 Pulse',spin:'🔄 Spin',glow:'🌟 Glow',bounce:'⬆️ Bounce',shake:'💥 Shake',rainbow:'🌈 Rainbow'}[a.effect] || '💫 Pulse' }}</div>
          <div v-if="equippedArtifact === String(a.id)" class="artifact-equipped-badge">✦ Equipped</div>
          <button v-else class="artifact-buy-btn" :disabled="buyingCosmetic || myMana < a.price"
            @click.stop="confirmBuyArtifact(a)">
            {{ buyingCosmetic === String(a.id) ? 'Equipping...' : '✨ ' + a.price + ' Mana' }}
          </button>
        </div>
      </div>
      <div v-else class="cosm-loading">Loading artifacts...</div>
    </div>

    <!-- ═══ Confirm Popup ═══ -->
    <div v-if="confirmPopup" class="confirm-overlay" @click.self="confirmPopup = null">
      <div class="confirm-box">
        <div class="confirm-icon">{{ confirmPopup.icon }}</div>
        <div class="confirm-title">{{ confirmPopup.title }}</div>
        <div class="confirm-desc">{{ confirmPopup.desc }}</div>
        <div class="confirm-cost">{{ confirmPopup.costLabel }}</div>
        <div class="confirm-actions">
          <button class="confirm-cancel" @click="confirmPopup = null">Cancel</button>
          <button class="confirm-ok" @click="confirmPopup.action()">{{ confirmPopup.okText || 'Confirm' }}</button>
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
import { buyMagicItem, getActiveFortuneWheels, spinFortuneWheel, getArtifactCatalog, uploadMagicBackground } from '../../services/api'

export default {
  name: 'MagicShop',
  data() {
    return {
      myCoins: 0,
      buying: null,
      lastResult: null,
      apiBase: import.meta.env.VITE_API_URL || '',
      titleText: '',
      currentStatus: '',
      // Scroll Emporium
      scrollTypes: [
        { type: 'scroll_of_luck', name: 'Scroll of Luck', stat: 'LUK', icon: '🍀', bg: '/icons/scroll_luck.png' },
        { type: 'scroll_of_strength', name: 'Scroll of Strength', stat: 'STR', icon: '⚔️', bg: '/icons/scroll_strength.png' },
        { type: 'scroll_of_defense', name: 'Scroll of Defense', stat: 'DEF', icon: '🛡️', bg: '/icons/scroll_defense.png' },
      ],
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
      // Cosmetics
      artifactCatalog: [],
      equippedArtifact: '',
      previewArtifact: null,
      buyingCosmetic: null,
      bgFile: null,
      bgPreviewUrl: null,
      bgResult: false,
      currentBg: '',
      // User profile for demo card
      myImage: '',
      myName: '',
      myPosition: '',
      myRole: 'staff',
      myStats: { str: 10, def: 10, luk: 10 },
      myBadges: [],
      // Confirmation popup
      confirmPopup: null,
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
    demoStatus() {
      return this.titleText.trim() || this.currentStatus || ''
    },
    demoBgStyle() {
      const url = this.bgPreviewUrl || (this.currentBg ? this.apiBase + this.currentBg : null)
      if (!url) return {}
      return {
        backgroundImage: `linear-gradient(rgba(17,10,30,0.65), rgba(17,10,30,0.8)), url(${url})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }
    },
    demoArtifact() {
      return this.previewArtifact || this.equippedArtifact || null
    },
    demoArtifactColor() {
      const a = this.artifactCatalog.find(x => String(x.id) === this.demoArtifact)
      return a ? a.color : '#d4a44c'
    },
    demoArtifactImg() {
      const a = this.artifactCatalog.find(x => String(x.id) === this.demoArtifact)
      return a ? a.image : null
    },
    demoArtifactEffect() {
      const a = this.artifactCatalog.find(x => String(x.id) === this.demoArtifact)
      return a ? (a.effect || 'pulse') : 'pulse'
    },
  },
  mounted() {
    this.refreshCoins()
    this.loadFortuneWheels()
    this.loadArtifactCatalog()
  },
  methods: {
    async refreshCoins() {
      try {
        const { data } = await import('../../services/api').then(m => m.default.get('/api/users/me'))
        this.myCoins = data.coins || 0
        this.myMana = data.angel_coins || 0
        this.currentStatus = data.status_text || ''
        this.equippedArtifact = data.circle_artifact || ''
        this.currentBg = data.magic_background || ''
        this.myImage = data.image || ''
        this.myName = `${data.name || ''} ${data.surname || ''}`.trim()
        this.myPosition = data.position || 'Adventurer'
        this.myRole = data.role || 'staff'
      } catch (e) { /* ignore */ }
      // Load badges & stats from town-people
      try {
        const { data: people } = await import('../../services/api').then(m => m.default.get('/api/badges/town-people'))
        const me = people.find(p => p.name === (this.myName.split(' ')[0] || ''))
        if (me) {
          this.myStats = { str: me.stats.total_str, def: me.stats.total_def, luk: me.stats.total_luk }
          this.myBadges = me.badges || []
        }
      } catch (e) { /* ignore */ }
    },

    // ── Scroll Emporium ──
    confirmScroll(s) {
      this.confirmPopup = {
        icon: s.icon,
        title: `Buy ${s.name}?`,
        desc: `Permanently gain +1 ${s.stat}`,
        costLabel: '💰 20 Gold',
        okText: 'Buy',
        action: () => { this.confirmPopup = null; this.buy(s.type) },
      }
    },
    async buy(itemType) {
      if (this.myCoins < 20) return
      this.buying = itemType
      this.lastResult = null
      try {
        const { data } = await buyMagicItem(itemType)
        this.lastResult = data
        this.myCoins = data.coins
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        localStorage.setItem('user', JSON.stringify(user))
        // Refresh stats
        this.refreshCoins()
      } catch (e) {
        alert(e.response?.data?.detail || 'Purchase failed')
      } finally { this.buying = null }
    },

    // ── Title Scroll ──
    confirmBuyTitle() {
      this.confirmPopup = {
        icon: '📜',
        title: 'Set Title Scroll?',
        desc: `Status: "${this.titleText.trim()}"`,
        costLabel: '✨ 2 Mana',
        okText: 'Set Status',
        action: () => { this.confirmPopup = null; this.buyTitle() },
      }
    },
    async buyTitle() {
      if (!this.titleText.trim() || this.myMana < 2 || this.buying) return
      this.buying = 'title_scroll'
      this.lastResult = null
      try {
        const { data } = await buyMagicItem('title_scroll', { status_text: this.titleText.trim() })
        this.lastResult = data
        this.myMana = data.angel_coins
        this.currentStatus = data.status_text
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.angel_coins = data.angel_coins
        user.status_text = data.status_text
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        alert(e.response?.data?.detail || 'Purchase failed')
      } finally { this.buying = null }
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

    // ── Cosmetics ──
    async loadArtifactCatalog() {
      try {
        const { data } = await getArtifactCatalog()
        this.artifactCatalog = data
      } catch (e) { console.error('Failed to load artifact catalog', e) }
    },

    previewArtifactOnDemo(a) {
      const sid = String(a.id)
      this.previewArtifact = (this.previewArtifact === sid) ? null : sid
    },

    confirmBuyArtifact(a) {
      this.previewArtifact = String(a.id)
      this.confirmPopup = {
        icon: '💎',
        title: `Equip ${a.name}?`,
        desc: `${a.rarity} artifact (${a.effect === 'spin' ? '🔄 Spin' : '💫 Pulse'})`,
        costLabel: `✨ ${a.price} Mana`,
        okText: 'Equip',
        action: () => { this.confirmPopup = null; this.buyArtifact(a) },
      }
    },
    async buyArtifact(artifact) {
      if (this.buyingCosmetic) return
      this.buyingCosmetic = String(artifact.id)
      try {
        const { data } = await buyMagicItem('circle_artifact', { artifact_id: String(artifact.id) })
        this.myMana = data.angel_coins
        this.equippedArtifact = data.artifact_id
        this.previewArtifact = null
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.angel_coins = data.angel_coins
        user.circle_artifact = data.artifact_id
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        alert(e.response?.data?.detail || 'Purchase failed')
      } finally { this.buyingCosmetic = null }
    },

    onBgFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      this.bgFile = file
      this.bgPreviewUrl = URL.createObjectURL(file)
      this.bgResult = false
    },

    confirmUploadBackground() {
      this.confirmPopup = {
        icon: '🖼️',
        title: 'Set Magic Background?',
        desc: 'Upload selected image as card background',
        costLabel: '✨ 2 Mana',
        okText: 'Upload',
        action: () => { this.confirmPopup = null; this.uploadBackground() },
      }
    },
    async uploadBackground() {
      if (!this.bgFile || this.buyingCosmetic) return
      this.buyingCosmetic = 'bg'
      try {
        const fd = new FormData()
        fd.append('file', this.bgFile)
        const { data } = await uploadMagicBackground(fd)
        this.myMana = data.angel_coins
        this.currentBg = data.magic_background
        this.bgResult = true
        this.bgFile = null
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.angel_coins = data.angel_coins
        user.magic_background = data.magic_background
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        alert(e.response?.data?.detail || 'Upload failed')
      } finally { this.buyingCosmetic = null }
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

.scroll-card {
  background-size: cover; background-position: center;
  justify-content: flex-end; min-height: 180px; overflow: hidden;
}
.scroll-card .magic-name, .scroll-card .magic-desc, .scroll-card .magic-cost {
  text-shadow: 0 1px 6px rgba(0,0,0,0.9), 0 0 14px rgba(0,0,0,0.7);
  position: relative; z-index: 1;
}
.scroll-card .magic-buy, .scroll-card .magic-result {
  position: relative; z-index: 1;
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
.fw-card { border-color: rgba(255,215,0,0.25); position: relative; overflow: hidden; justify-content: flex-end; min-height: 200px; }
.fw-card:hover { border-color: rgba(255,215,0,0.5); box-shadow: 0 4px 20px rgba(255,215,0,0.08); }
.fw-card .magic-name, .fw-card .magic-desc, .fw-card .magic-cost {
  text-shadow: 0 1px 6px rgba(0,0,0,0.8), 0 0 12px rgba(0,0,0,0.6);
  position: relative; z-index: 1;
}
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

/* ── Scroll Row ── */
.scroll-row {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
}
.scroll-item {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 6px 10px; border-radius: 12px;
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 1px solid rgba(212,164,76,0.15);
}
.scroll-icon { font-size: 28px; margin-bottom: 4px; }
.scroll-name { font-family: 'Cinzel', serif; font-size: 10px; font-weight: 700; color: #e8d5b7; text-align: center; }
.scroll-desc { font-size: 10px; color: #8b7355; margin-bottom: 4px; }
.scroll-cost { font-size: 11px; font-weight: 700; color: #d4a44c; margin-bottom: 6px; }

/* ── Demo Card ── */
.demo-card-wrap {
  display: flex; flex-direction: column; align-items: center; margin-bottom: 16px;
}
.demo-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px; padding: 18px 14px 14px;
  display: flex; flex-direction: column; align-items: center;
  width: 180px; background-size: cover; background-position: center;
  transition: background-image 0.3s;
}
.demo-label {
  font-size: 11px; font-weight: 700; color: #8b7355; margin-top: 6px;
  font-style: italic; letter-spacing: 0.5px;
}

/* Demo card reuses Town People classes */
.demo-card .person-portrait {
  position: relative; margin-bottom: 10px;
  width: 90px; height: 90px;
  display: flex; align-items: center; justify-content: center;
  overflow: visible;
}
.demo-card .person-img {
  width: 56px; height: 56px; border-radius: 50%;
  object-fit: cover; border: 2px solid rgba(212,164,76,0.3);
  position: relative; z-index: 1;
}
.demo-card .person-placeholder {
  width: 56px; height: 56px; border-radius: 50%;
  background: rgba(212,164,76,0.15); display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700; color: #8b7355;
  border: 2px solid rgba(212,164,76,0.3); position: relative; z-index: 1;
}
.demo-card .person-role-tag {
  position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%);
  font-size: 8px; font-weight: 800; text-transform: uppercase;
  padding: 2px 8px; border-radius: 4px; z-index: 2;
  background: #2c1810; color: #d4a44c; border: 1px solid rgba(212,164,76,0.3);
}
.demo-card .person-name { font-family: 'Cinzel', serif; font-size: 14px; font-weight: 700; color: #e8d5b7; margin-top: 4px; }
.demo-card .person-surname { font-family: 'Cinzel', serif; font-size: 12px; color: #c4a882; }
.demo-card .person-position { font-size: 9px; font-weight: 600; color: #8b7355; text-transform: uppercase; letter-spacing: 1px; margin: 2px 0; }
.demo-card .person-status { font-size: 10px; font-weight: 700; color: #e74c3c; font-style: italic; margin-bottom: 4px; }
.demo-card .person-stats { display: flex; gap: 8px; margin: 6px 0; }
.demo-card .ps { font-size: 10px; font-weight: 700; }
.demo-card .ps.str { color: #e74c3c; }
.demo-card .ps.def { color: #3498db; }
.demo-card .ps.luk { color: #2ecc71; }
.demo-card .person-badges { display: flex; gap: 4px; margin-bottom: 6px; }
.demo-card .pb-circle { width: 22px; height: 22px; border-radius: 50%; overflow: hidden; }
.demo-card .pb-img { width: 100%; height: 100%; object-fit: cover; }
.demo-card .person-currency { display: flex; gap: 10px; }
.demo-card .cur { font-size: 10px; font-weight: 700; }
.demo-card .cur.gold { color: #d4a44c; }
.demo-card .cur.mana { color: #9b59b6; }

/* Artifact ring on demo card */
.demo-artifact-ring-img {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 90px; height: 90px; border-radius: 50%;
  object-fit: cover; pointer-events: none; overflow: hidden;
  aspect-ratio: 1 / 1;
}
.demo-artifact-ring-css {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 90px; height: 90px; border-radius: 50%;
  border: 3px solid; pointer-events: none; overflow: hidden;
}
.demo-artifact-ring-img.effect-pulse,
.demo-artifact-ring-css.effect-pulse {
  animation: demoArtifactPulse 3s ease-in-out infinite;
}
.demo-artifact-ring-img.effect-spin,
.demo-artifact-ring-css.effect-spin {
  animation: demoArtifactSpin 6s linear infinite;
}
.demo-artifact-ring-img.effect-glow,
.demo-artifact-ring-css.effect-glow {
  animation: demoArtifactGlow 2s ease-in-out infinite;
}
.demo-artifact-ring-img.effect-bounce,
.demo-artifact-ring-css.effect-bounce {
  animation: demoArtifactBounce 2s ease-in-out infinite;
}
.demo-artifact-ring-img.effect-shake,
.demo-artifact-ring-css.effect-shake {
  animation: demoArtifactShake 0.6s ease-in-out infinite;
}
.demo-artifact-ring-img.effect-rainbow,
.demo-artifact-ring-css.effect-rainbow {
  animation: demoArtifactRainbow 4s linear infinite;
}
@keyframes demoArtifactPulse {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.06); }
}
@keyframes demoArtifactSpin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}
@keyframes demoArtifactGlow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%); filter: brightness(1); }
  50% { opacity: 1; transform: translate(-50%, -50%); filter: brightness(1.4) drop-shadow(0 0 16px currentColor); }
}
@keyframes demoArtifactBounce {
  0%, 100% { transform: translate(-50%, -50%); }
  50% { transform: translate(-50%, calc(-50% - 8px)); }
}
@keyframes demoArtifactShake {
  0%, 100% { transform: translate(-50%, -50%); }
  25% { transform: translate(calc(-50% - 3px), -50%) rotate(-2deg); }
  75% { transform: translate(calc(-50% + 3px), -50%) rotate(2deg); }
}
@keyframes demoArtifactRainbow {
  from { transform: translate(-50%, -50%); filter: hue-rotate(0deg); }
  to { transform: translate(-50%, -50%); filter: hue-rotate(360deg); }
}

/* ── Cosmetics Section ── */
.cosm-sub-header {
  font-family: 'Cinzel', serif;
  font-size: 13px; font-weight: 700; color: #c39bd3;
  margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.cosm-price {
  font-family: 'Inter', sans-serif;
  font-size: 11px; font-weight: 600; color: #9b59b6;
  background: rgba(155,89,182,0.1); padding: 2px 8px;
  border-radius: 8px; border: 1px solid rgba(155,89,182,0.2);
}

.cosm-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  margin-bottom: 16px;
}
@media (max-width: 440px) {
  .cosm-row { grid-template-columns: 1fr; }
}
.cosm-panel {
  background: linear-gradient(145deg, rgba(44,24,16,0.5), rgba(26,26,46,0.6));
  border: 1px solid rgba(155,89,182,0.15); border-radius: 12px;
  padding: 12px; display: flex; flex-direction: column;
}
.cosm-panel-body {
  display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1;
}
.cosm-file-label {
  display: inline-block; padding: 8px 16px; border-radius: 8px;
  border: 2px dashed rgba(155,89,182,0.3); color: #c39bd3;
  font-size: 13px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; margin-bottom: 8px;
}
.cosm-file-label:hover { border-color: rgba(155,89,182,0.6); background: rgba(155,89,182,0.08); }
.cosm-file-input { display: none; }
.cosm-buy {
  background: linear-gradient(135deg, #7b2d8e, #9b59b6) !important;
  color: #fff !important; border: 1px solid rgba(155,89,182,0.4) !important;
}
.cosm-loading { font-size: 12px; color: #8b7355; font-style: italic; text-align: center; padding: 20px; }

/* Artifact Grid */
.artifact-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}
.artifact-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px 10px; border-radius: 12px;
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid var(--art-color, rgba(212,164,76,0.15));
  transition: all 0.2s; cursor: pointer; position: relative;
}
.artifact-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px color-mix(in srgb, var(--art-color) 20%, transparent);
}
.artifact-card.equipped {
  border-width: 2px; border-style: solid;
  box-shadow: 0 0 20px color-mix(in srgb, var(--art-color) 25%, transparent);
}
.artifact-card.previewing {
  border-width: 3px;
  box-shadow: 0 0 24px color-mix(in srgb, var(--art-color) 40%, transparent);
  transform: translateY(-3px);
}
.artifact-ring {
  width: 84px; height: 84px; border-radius: 50%;
  border: 3px solid; display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px; position: relative; overflow: hidden;
}
.artifact-ring.effect-pulse { animation: artifactPulse 3s ease-in-out infinite; }
.artifact-ring.effect-spin { animation: artifactSpin 6s linear infinite; }
.artifact-ring.effect-glow { animation: artifactGlow 2s ease-in-out infinite; }
.artifact-ring.effect-bounce { animation: artifactBounce 2s ease-in-out infinite; }
.artifact-ring.effect-shake { animation: artifactShake 0.6s ease-in-out infinite; }
.artifact-ring.effect-rainbow { animation: artifactRainbow 4s linear infinite; }
@keyframes artifactPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.06); }
}
@keyframes artifactSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes artifactGlow {
  0%, 100% { filter: brightness(1) drop-shadow(0 0 4px currentColor); }
  50% { filter: brightness(1.4) drop-shadow(0 0 16px currentColor); }
}
@keyframes artifactBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes artifactShake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-3px) rotate(-2deg); }
  75% { transform: translateX(3px) rotate(2deg); }
}
@keyframes artifactRainbow {
  from { filter: hue-rotate(0deg); }
  to { filter: hue-rotate(360deg); }
}
.artifact-inner { width: 50px; height: 50px; border-radius: 50%; }
.artifact-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; aspect-ratio: 1 / 1; }
.artifact-effect-tag {
  font-size: 9px; font-weight: 700; color: #8b7355;
  margin-bottom: 4px;
}
.artifact-name {
  font-family: 'Cinzel', serif;
  font-size: 10px; font-weight: 700; color: #e8d5b7;
  text-align: center; line-height: 1.3; margin-bottom: 2px;
}
.artifact-rarity {
  font-size: 9px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.5px; margin-bottom: 6px; padding: 1px 6px; border-radius: 4px;
}
.artifact-card.common .artifact-rarity { color: #bdc3c7; background: rgba(189,195,199,0.1); }
.artifact-card.uncommon .artifact-rarity { color: #2ecc71; background: rgba(46,204,113,0.1); }
.artifact-card.rare .artifact-rarity { color: #3498db; background: rgba(52,152,219,0.1); }
.artifact-card.epic .artifact-rarity { color: #9b59b6; background: rgba(155,89,182,0.1); }
.artifact-card.legendary .artifact-rarity { color: #f39c12; background: rgba(243,156,18,0.1); }
.artifact-card.mythic .artifact-rarity { color: #e74c3c; background: rgba(231,76,60,0.15); }

.artifact-equipped-badge {
  font-size: 10px; font-weight: 800; color: #2ecc71;
  background: rgba(46,204,113,0.12); border: 1px solid rgba(46,204,113,0.3);
  padding: 3px 10px; border-radius: 6px;
}
.artifact-buy-btn {
  font-size: 10px; font-weight: 800; color: #c39bd3;
  background: rgba(155,89,182,0.1); border: 1px solid rgba(155,89,182,0.3);
  padding: 4px 10px; border-radius: 6px; cursor: pointer; transition: all 0.15s;
}
.artifact-buy-btn:hover:not(:disabled) {
  background: rgba(155,89,182,0.2); box-shadow: 0 0 8px rgba(155,89,182,0.15);
}
.artifact-buy-btn:disabled { opacity: 0.4; cursor: not-allowed; }

@media (min-width: 540px) {
  .artifact-grid { grid-template-columns: repeat(4, 1fr); }
}

/* ── Confirm Popup ── */
.confirm-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.7); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.confirm-box {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 2px solid rgba(212,164,76,0.3); border-radius: 16px;
  padding: 28px 24px; text-align: center; max-width: 300px; width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
}
.confirm-icon { font-size: 42px; margin-bottom: 8px; }
.confirm-title {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 700;
  color: #e8d5b7; margin-bottom: 4px;
}
.confirm-desc { font-size: 12px; color: #8b7355; margin-bottom: 8px; }
.confirm-cost {
  font-size: 14px; font-weight: 800; color: #d4a44c; margin-bottom: 16px;
}
.confirm-actions { display: flex; gap: 10px; justify-content: center; }
.confirm-cancel {
  padding: 8px 20px; border-radius: 8px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
  color: #8b7355; font-weight: 700; font-size: 13px; cursor: pointer;
}
.confirm-ok {
  padding: 8px 20px; border-radius: 8px;
  background: linear-gradient(135deg, #8b6914, #d4a44c);
  border: none; color: #fff; font-weight: 800; font-size: 13px; cursor: pointer;
  transition: all 0.2s;
}
.confirm-ok:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(212,164,76,0.3); }
</style>
