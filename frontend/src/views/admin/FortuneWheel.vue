<template>
  <div>
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2>🎡 Fortune Wheel Maker</h2>
        <p>Create fortune wheels with rewards</p>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-secondary" @click="newWheel" v-if="currentWheel">+ New</button>
        <button class="btn btn-primary" @click="saveWheel" :disabled="saving || !wheelName.trim()">
          {{ saving ? 'Saving...' : (currentWheel ? '💾 Update' : '💾 Save') }}
        </button>
      </div>
    </div>

    <!-- Saved Wheels List -->
    <div v-if="savedWheels.length > 0" class="fw-saved-bar">
      <span class="fw-saved-label">📜 Saved:</span>
      <button v-for="w in savedWheels" :key="w.id"
        class="fw-saved-chip" :class="{ active: currentWheel && currentWheel.id === w.id }"
        @click="loadWheel(w)">
        {{ w.name }}
        <span class="fw-chip-badge" :class="w.is_active ? 'on' : 'off'">{{ w.is_active ? '✅' : '⏸️' }}</span>
      </button>
    </div>

    <div class="fw-layout">
      <!-- Left: Config Panel -->
      <div class="fw-config card">
        <div class="fw-name-section">
          <label class="fw-label">Wheel Name</label>
          <input type="text" v-model="wheelName" class="fw-name-input" placeholder="e.g. Lucky Spin..." />
        </div>

        <h3 class="fw-config-title">⚙️ Segments</h3>
        <div class="fw-segments">
          <div v-for="(seg, i) in segments" :key="seg._uid || i" class="fw-seg-row"
            draggable="true"
            :class="{ 'drag-over': dragOverIndex === i, 'dragging': dragIndex === i }"
            @dragstart="onDragStart(i, $event)"
            @dragover.prevent="onDragOver(i)"
            @dragleave="onDragLeave"
            @drop="onDrop(i)"
            @dragend="onDragEnd">
            <div class="fw-drag-handle" title="Drag to reorder">⠿</div>
            <input type="color" v-model="seg.color" class="fw-color-picker" />
            <div class="fw-seg-fields">
              <input type="text" v-model="seg.label" class="fw-seg-input" placeholder="Label..." />
              <div class="fw-seg-reward-row">
                <select v-model="seg.reward_type" class="fw-reward-select">
                  <option value="nothing">Nothing</option>
                  <option value="gold">💰 Gold</option>
                  <option value="mana">✨ Mana</option>
                  <option value="str">⚔️ STR</option>
                  <option value="def">🛡️ DEF</option>
                  <option value="luk">🍀 LUK</option>
                </select>
                <input v-if="seg.reward_type !== 'nothing'" type="number" v-model.number="seg.reward_amount" min="0" class="fw-reward-amount" placeholder="Amt" />
                <div class="fw-weight-wrap">
                  <label class="fw-weight-label">W</label>
                  <input type="number" v-model.number="seg.weight" min="1" max="100" class="fw-weight-input" />
                </div>
              </div>
            </div>
            <button class="fw-seg-remove" @click="removeSegment(i)" :disabled="segments.length <= 2">✕</button>
          </div>
        </div>
        <button class="fw-add-btn" @click="addSegment" :disabled="segments.length >= 12">+ Add Segment</button>

        <!-- Spin Settings -->
        <div class="fw-settings-section">
          <h3 class="fw-config-title">🌀 Spin Settings</h3>
          <div class="fw-setting-row">
            <label>Min Rotations</label>
            <input type="number" v-model.number="spinMin" min="1" max="20" class="fw-setting-input" />
          </div>
          <div class="fw-setting-row">
            <label>Max Rotations</label>
            <input type="number" v-model.number="spinMax" min="1" max="20" class="fw-setting-input" />
          </div>
        </div>

        <!-- Publish Settings -->
        <div class="fw-settings-section">
          <h3 class="fw-config-title">🔮 Magic Shop Settings</h3>
          <div class="fw-setting-row">
            <label>Pay with</label>
            <select v-model="currency" class="fw-setting-select">
              <option value="gold">💰 Gold</option>
              <option value="mana">✨ Mana</option>
            </select>
          </div>
          <div class="fw-setting-row">
            <label>Price</label>
            <input type="number" v-model.number="price" min="0" class="fw-setting-input" />
          </div>
          <div class="fw-setting-row">
            <label>Status</label>
            <label class="fw-toggle">
              <input type="checkbox" v-model="isActive" />
              <span class="fw-toggle-slider"></span>
              <span class="fw-toggle-text">{{ isActive ? 'Active' : 'Inactive' }}</span>
            </label>
          </div>
        </div>

        <!-- Probability Info -->
        <div class="fw-info">
          <div class="fw-info-row" v-for="(seg, i) in segments" :key="'p'+i">
            <span class="fw-info-seg">
              <span class="fw-info-dot" :style="{ background: seg.color }"></span>
              {{ seg.label || '(empty)' }}
            </span>
            <span class="fw-info-val">{{ segmentProbability(i) }}%</span>
          </div>
        </div>

        <button v-if="currentWheel" class="fw-delete-btn" @click="deleteCurrentWheel">🗑️ Delete Wheel</button>
      </div>

      <!-- Right: Wheel Preview -->
      <div class="fw-preview card">
        <!-- Epic Wheel Frame -->
        <div class="fw-epic-frame">
          <!-- Ornamental corners -->
          <div class="fw-corner fw-corner-tl">◆</div>
          <div class="fw-corner fw-corner-tr">◆</div>
          <div class="fw-corner fw-corner-bl">◆</div>
          <div class="fw-corner fw-corner-br">◆</div>

          <div class="fw-wheel-container">
            <!-- Outer glow ring -->
            <div class="fw-outer-glow" :class="{ spinning: spinning, won: result && !spinning }"></div>

            <!-- Pointer -->
            <div class="fw-pointer-wrap">
              <div class="fw-pointer">
                <svg width="36" height="44" viewBox="0 0 36 44">
                  <defs>
                    <linearGradient id="ptrGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="#ffd700"/>
                      <stop offset="50%" stop-color="#d4a44c"/>
                      <stop offset="100%" stop-color="#8b6914"/>
                    </linearGradient>
                    <filter id="ptrGlow">
                      <feGaussianBlur stdDeviation="2" result="blur"/>
                      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                  </defs>
                  <polygon points="18,44 4,8 18,16 32,8" fill="url(#ptrGrad)" stroke="#8b6914" stroke-width="1.5" filter="url(#ptrGlow)"/>
                  <circle cx="18" cy="10" r="5" fill="#ffd700" stroke="#8b6914" stroke-width="1"/>
                </svg>
              </div>
            </div>

            <!-- Wheel Canvas -->
            <canvas
              ref="wheelCanvas"
              :width="wheelSize"
              :height="wheelSize"
              class="fw-canvas"
              :style="wheelStyle"
            ></canvas>

            <!-- Center Hub -->
            <div class="fw-center-hub" :class="{ spinning: spinning }">
              <div class="fw-hub-inner">⚜</div>
            </div>
          </div>
        </div>

        <button class="fw-spin-btn" :class="{ active: !spinning }" @click="spin" :disabled="spinning">
          <span class="fw-spin-btn-text">{{ spinning ? '🌀 SPINNING...' : '⚔️ SPIN THE WHEEL' }}</span>
        </button>

        <!-- Result -->
        <transition name="result-fade">
          <div v-if="result && !spinning" class="fw-result">
            <div class="fw-result-glow"></div>
            <div class="fw-result-content">
              <div class="fw-result-title">VICTORY!</div>
              <div class="fw-result-label">{{ result }}</div>
              <div class="fw-result-sparks">✦ ✧ ✦</div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { getFortuneWheels, createFortuneWheel, updateFortuneWheel, deleteFortuneWheel as apiDeleteWheel } from '../../services/api'

const DEFAULT_COLORS = [
  '#c0392b', '#2980b9', '#27ae60', '#d4a44c', '#8e44ad',
  '#16a085', '#d35400', '#2c3e50', '#e74c3c', '#3498db',
  '#1abc9c', '#e67e22',
]

export default {
  name: 'FortuneWheel',
  inject: ['showToast'],
  data() {
    return {
      wheelName: 'Lucky Spin',
      segments: [
        { label: 'Gold +10', color: '#d4a44c', weight: 30, reward_type: 'gold', reward_amount: 10, _uid: 1 },
        { label: 'Mana +5', color: '#2980b9', weight: 25, reward_type: 'mana', reward_amount: 5, _uid: 2 },
        { label: 'STR +1', color: '#c0392b', weight: 15, reward_type: 'str', reward_amount: 1, _uid: 3 },
        { label: 'DEF +1', color: '#27ae60', weight: 15, reward_type: 'def', reward_amount: 1, _uid: 4 },
        { label: 'LUK +1', color: '#8e44ad', weight: 10, reward_type: 'luk', reward_amount: 1, _uid: 5 },
        { label: 'Nothing', color: '#2c3e50', weight: 5, reward_type: 'nothing', reward_amount: 0, _uid: 6 },
      ],
      uidCounter: 7,
      spinMin: 3,
      spinMax: 7,
      currency: 'gold',
      price: 50,
      isActive: false,
      wheelSize: 420,
      currentRotation: 0,
      spinning: false,
      spinDuration: 0,
      result: null,
      saving: false,
      savedWheels: [],
      currentWheel: null,
      useTransition: false,
      // Drag & Drop
      dragIndex: null,
      dragOverIndex: null,
    }
  },
  computed: {
    wheelStyle() {
      return {
        transform: `rotate(${this.currentRotation}deg)`,
        transition: this.useTransition
          ? `transform ${this.spinDuration}s cubic-bezier(0.15, 0.60, 0.07, 1.0)`
          : 'none',
      }
    },
  },
  mounted() {
    this.drawWheel()
    this.loadSavedWheels()
  },
  watch: {
    segments: {
      handler() { this.$nextTick(() => this.drawWheel()) },
      deep: true,
    },
  },
  methods: {
    addSegment() {
      if (this.segments.length >= 12) return
      const ci = this.segments.length % DEFAULT_COLORS.length
      this.segments.push({ label: `Prize ${this.segments.length + 1}`, color: DEFAULT_COLORS[ci], weight: 10, reward_type: 'nothing', reward_amount: 0, _uid: this.uidCounter++ })
    },
    removeSegment(i) {
      if (this.segments.length <= 2) return
      this.segments.splice(i, 1)
    },

    // ── Drag & Drop ──
    onDragStart(i, e) {
      this.dragIndex = i
      e.dataTransfer.effectAllowed = 'move'
    },
    onDragOver(i) {
      if (this.dragIndex === null || this.dragIndex === i) return
      this.dragOverIndex = i
    },
    onDragLeave() {
      this.dragOverIndex = null
    },
    onDrop(i) {
      if (this.dragIndex === null || this.dragIndex === i) return
      const moved = this.segments.splice(this.dragIndex, 1)[0]
      this.segments.splice(i, 0, moved)
      this.dragIndex = null
      this.dragOverIndex = null
    },
    onDragEnd() {
      this.dragIndex = null
      this.dragOverIndex = null
    },
    segmentProbability(i) {
      const total = this.segments.reduce((s, seg) => s + (seg.weight || 1), 0)
      return ((this.segments[i].weight || 1) / total * 100).toFixed(1)
    },

    drawWheel() {
      const canvas = this.$refs.wheelCanvas
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      const cx = this.wheelSize / 2
      const cy = this.wheelSize / 2
      const r = this.wheelSize / 2 - 12

      ctx.clearRect(0, 0, this.wheelSize, this.wheelSize)

      const total = this.segments.reduce((s, seg) => s + (seg.weight || 1), 0)
      let startAngle = 0

      this.segments.forEach((seg, idx) => {
        const sliceAngle = ((seg.weight || 1) / total) * 2 * Math.PI

        // Gradient fill for each segment
        const midAngle = startAngle + sliceAngle / 2
        const gx = cx + r * 0.5 * Math.cos(midAngle)
        const gy = cy + r * 0.5 * Math.sin(midAngle)
        const grad = ctx.createRadialGradient(cx, cy, 30, gx, gy, r)
        const baseColor = seg.color
        grad.addColorStop(0, this.lightenColor(baseColor, 30))
        grad.addColorStop(0.6, baseColor)
        grad.addColorStop(1, this.darkenColor(baseColor, 30))

        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, r, startAngle, startAngle + sliceAngle)
        ctx.closePath()
        ctx.fillStyle = grad
        ctx.fill()

        // Segment border (dark line)
        ctx.strokeStyle = 'rgba(0,0,0,0.6)'
        ctx.lineWidth = 2
        ctx.stroke()

        // Inner highlight line
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.lineTo(cx + r * Math.cos(startAngle), cy + r * Math.sin(startAngle))
        ctx.strokeStyle = 'rgba(255,215,0,0.15)'
        ctx.lineWidth = 1
        ctx.stroke()

        // Label with shadow
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(startAngle + sliceAngle / 2)
        ctx.textAlign = 'right'
        ctx.fillStyle = '#fff'
        const fontSize = Math.max(11, Math.min(14, 160 / this.segments.length))
        ctx.font = `bold ${fontSize}px 'Inter', sans-serif`
        ctx.shadowColor = 'rgba(0,0,0,0.8)'
        ctx.shadowBlur = 4
        ctx.shadowOffsetX = 1
        ctx.shadowOffsetY = 1
        const labelText = seg.label || ''
        const maxLen = Math.floor(r * 0.5 / 7)
        ctx.fillText(labelText.length > maxLen ? labelText.substring(0, maxLen) + '…' : labelText, r - 22, 5)
        ctx.shadowBlur = 0
        ctx.restore()

        startAngle += sliceAngle
      })

      // Outer ring (ornate golden border)
      for (let ring = 0; ring < 3; ring++) {
        ctx.beginPath()
        ctx.arc(cx, cy, r + 4 + ring * 3, 0, 2 * Math.PI)
        ctx.strokeStyle = ring === 1 ? '#ffd700' : '#8b6914'
        ctx.lineWidth = ring === 1 ? 3 : 2
        ctx.stroke()
      }

      // Decorative metal studs around the rim
      const studCount = this.segments.length * 4
      for (let i = 0; i < studCount; i++) {
        const angle = (i / studCount) * 2 * Math.PI
        const dx = cx + (r + 7) * Math.cos(angle)
        const dy = cy + (r + 7) * Math.sin(angle)
        ctx.beginPath()
        ctx.arc(dx, dy, 2.5, 0, 2 * Math.PI)
        const studGrad = ctx.createRadialGradient(dx - 1, dy - 1, 0, dx, dy, 3)
        studGrad.addColorStop(0, '#ffd700')
        studGrad.addColorStop(1, '#8b6914')
        ctx.fillStyle = studGrad
        ctx.fill()
      }

      // Inner dark ring  
      ctx.beginPath()
      ctx.arc(cx, cy, 34, 0, 2 * Math.PI)
      ctx.strokeStyle = '#ffd700'
      ctx.lineWidth = 2
      ctx.stroke()
    },

    lightenColor(hex, percent) {
      const num = parseInt(hex.replace('#', ''), 16)
      const r = Math.min(255, (num >> 16) + Math.round(255 * percent / 100))
      const g = Math.min(255, ((num >> 8) & 0x00FF) + Math.round(255 * percent / 100))
      const b = Math.min(255, (num & 0x0000FF) + Math.round(255 * percent / 100))
      return `rgb(${r},${g},${b})`
    },
    darkenColor(hex, percent) {
      const num = parseInt(hex.replace('#', ''), 16)
      const r = Math.max(0, (num >> 16) - Math.round(255 * percent / 100))
      const g = Math.max(0, ((num >> 8) & 0x00FF) - Math.round(255 * percent / 100))
      const b = Math.max(0, (num & 0x0000FF) - Math.round(255 * percent / 100))
      return `rgb(${r},${g},${b})`
    },

    // ── SPIN (counter-clockwise, correct alignment) ──
    spin() {
      if (this.spinning) return
      this.result = null
      this.spinning = true
      this.useTransition = false

      // Weighted random pick
      const total = this.segments.reduce((s, seg) => s + (seg.weight || 1), 0)
      let rand = Math.random() * total
      let winnerIndex = 0
      for (let i = 0; i < this.segments.length; i++) {
        rand -= (this.segments[i].weight || 1)
        if (rand <= 0) { winnerIndex = i; break }
      }

      // Calculate segment center angle in canvas degrees
      // Canvas 0° = 3 o'clock, segments drawn clockwise
      let cumAngle = 0
      for (let i = 0; i < winnerIndex; i++) {
        cumAngle += ((this.segments[i].weight || 1) / total) * 360
      }
      const segSize = ((this.segments[winnerIndex].weight || 1) / total) * 360
      const segCenter = cumAngle + segSize / 2
      // Add jitter within segment (±35% of segment size)
      const jitter = (Math.random() - 0.5) * segSize * 0.7

      // Pointer is at the top = 270° in canvas coords.
      // After CSS rotate(R deg), the canvas angle at the pointer is: ((270 - R) % 360 + 360) % 360
      // We want this to equal (segCenter + jitter).
      // For counter-clockwise spin: total CCW angle = fullSpins * 360 + remainder
      // CSS new rotation = baseRotation - totalCCW
      const baseRotation = this.currentRotation % 360
      const targetAngle = segCenter + jitter
      const remainder = (((targetAngle - 270 + baseRotation) % 360) + 360) % 360
      const fullSpins = this.spinMin + Math.floor(Math.random() * (this.spinMax - this.spinMin + 1))
      const totalCCW = fullSpins * 360 + remainder
      const finalRotation = this.currentRotation - totalCCW

      // Reset transition then apply  
      this.currentRotation = this.currentRotation // force same value
      void this.$refs.wheelCanvas?.offsetHeight

      this.spinDuration = 4 + Math.random() * 2.5

      this.$nextTick(() => {
        this.useTransition = true
        this.currentRotation = finalRotation

        setTimeout(() => {
          this.spinning = false
          this.useTransition = false
          this.result = this.segments[winnerIndex].label || 'Unknown'
          this.showToast(`🎡 Result: ${this.result}`)
        }, this.spinDuration * 1000 + 400)
      })
    },

    // ── CRUD ──
    async loadSavedWheels() {
      try {
        const { data } = await getFortuneWheels()
        this.savedWheels = data
      } catch (e) { console.error('Failed to load wheels', e) }
    },
    loadWheel(w) {
      this.currentWheel = w
      this.wheelName = w.name
      this.segments = w.segments.map(s => ({ ...s, _uid: this.uidCounter++ }))
      this.spinMin = w.spin_min
      this.spinMax = w.spin_max
      this.currency = w.currency
      this.price = w.price
      this.isActive = w.is_active
      this.result = null
    },
    newWheel() {
      this.currentWheel = null
      this.wheelName = 'Lucky Spin'
      this.segments = [
        { label: 'Gold +10', color: '#d4a44c', weight: 30, reward_type: 'gold', reward_amount: 10, _uid: this.uidCounter++ },
        { label: 'Nothing', color: '#2c3e50', weight: 70, reward_type: 'nothing', reward_amount: 0, _uid: this.uidCounter++ },
      ]
      this.spinMin = 3; this.spinMax = 7
      this.currency = 'gold'; this.price = 50; this.isActive = false; this.result = null
    },
    async saveWheel() {
      if (!this.wheelName.trim()) return
      this.saving = true
      const payload = {
        name: this.wheelName, segments: this.segments,
        spin_min: this.spinMin, spin_max: this.spinMax,
        currency: this.currency, price: this.price, is_active: this.isActive,
      }
      try {
        if (this.currentWheel) {
          const { data } = await updateFortuneWheel(this.currentWheel.id, payload)
          this.currentWheel = data
          this.showToast('💾 Wheel updated!')
        } else {
          const { data } = await createFortuneWheel(payload)
          this.currentWheel = data
          this.showToast('💾 Wheel created!')
        }
        await this.loadSavedWheels()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to save', 'error')
      } finally { this.saving = false }
    },
    async deleteCurrentWheel() {
      if (!this.currentWheel || !confirm(`Delete "${this.currentWheel.name}"?`)) return
      try {
        await apiDeleteWheel(this.currentWheel.id)
        this.showToast('🗑️ Wheel deleted')
        this.newWheel()
        await this.loadSavedWheels()
      } catch (e) { this.showToast('Failed to delete', 'error') }
    },
  },
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════
   FORTUNE WHEEL — Dark Fantasy Theme (Diablo/Hearthstone)
   ═══════════════════════════════════════════════════════ */

.fw-layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 24px;
  margin-top: 20px;
  align-items: start;
}
@media (max-width: 960px) { .fw-layout { grid-template-columns: 1fr; } }

/* ── Saved wheels bar ── */
.fw-saved-bar {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-top: 12px; padding: 10px 14px;
  background: rgba(139,105,20,0.06);
  border: 1px solid rgba(212,164,76,0.12);
  border-radius: 12px;
}
.fw-saved-label { font-size: 12px; color: #8b7355; font-weight: 700; }
.fw-saved-chip {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(212,164,76,0.15);
  color: #e8d5b7; padding: 6px 14px;
  border-radius: 20px; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; gap: 6px;
}
.fw-saved-chip:hover { border-color: #d4a44c; background: rgba(212,164,76,0.1); }
.fw-saved-chip.active { border-color: #d4a44c; background: rgba(212,164,76,0.15); color: #d4a44c; }

/* ── Config Panel ── */
.fw-name-section { margin-bottom: 16px; }
.fw-label { font-size: 11px; color: #8b7355; font-weight: 700; margin-bottom: 4px; display: block; }
.fw-name-input {
  width: 100%; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.2); border-radius: 10px;
  padding: 10px 14px; color: #d4a44c;
  font-size: 16px; font-weight: 700; font-family: 'Cinzel', serif;
}
.fw-name-input:focus { outline: none; border-color: #d4a44c; box-shadow: 0 0 0 2px rgba(212,164,76,0.15); }

.fw-config-title { font-family: 'Cinzel', serif; font-size: 14px; color: #d4a44c; margin-bottom: 12px; }
.fw-segments { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.fw-seg-row {
  display: flex; align-items: flex-start; gap: 8px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(212,164,76,0.1);
  border-radius: 10px; padding: 8px 10px;
}
.fw-seg-fields { flex: 1; min-width: 0; }
.fw-drag-handle {
  display: flex; align-items: center; justify-content: center;
  width: 20px; height: 32px; cursor: grab;
  color: #5a4a30; font-size: 16px; flex-shrink: 0;
  user-select: none; transition: color 0.2s;
}
.fw-drag-handle:active { cursor: grabbing; color: #d4a44c; }
.fw-seg-row.dragging { opacity: 0.4; }
.fw-seg-row.drag-over { border-color: #d4a44c; box-shadow: 0 0 8px rgba(212,164,76,0.3); }
.fw-color-picker {
  width: 32px; height: 32px; border: 2px solid rgba(212,164,76,0.3);
  border-radius: 8px; padding: 0; cursor: pointer; background: transparent; flex-shrink: 0;
  -webkit-appearance: none;
}
.fw-color-picker::-webkit-color-swatch-wrapper { padding: 2px; }
.fw-color-picker::-webkit-color-swatch { border: none; border-radius: 4px; }

.fw-seg-input {
  width: 100%; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.12); border-radius: 6px;
  padding: 5px 8px; color: #e8d5b7; font-size: 13px; font-weight: 600; margin-bottom: 4px;
}
.fw-seg-input:focus { outline: none; border-color: #d4a44c; }

.fw-seg-reward-row { display: flex; gap: 4px; align-items: center; }
.fw-reward-select {
  flex: 1; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.12); border-radius: 6px;
  padding: 4px 6px; color: #e8d5b7; font-size: 11px;
}
.fw-reward-amount {
  width: 50px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.12); border-radius: 6px;
  padding: 4px; color: #2ecc71; font-size: 12px; font-weight: 700; text-align: center;
}
.fw-weight-wrap { display: flex; align-items: center; gap: 2px; }
.fw-weight-label { font-size: 9px; color: #8b7355; font-weight: 700; }
.fw-weight-input {
  width: 40px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.12); border-radius: 6px;
  padding: 4px; color: #d4a44c; font-size: 12px; font-weight: 700; text-align: center;
}
.fw-seg-remove {
  background: rgba(231,76,60,0.1); border: 1px solid rgba(231,76,60,0.2);
  color: #e74c3c; width: 28px; height: 28px; border-radius: 8px;
  cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.2s;
}
.fw-seg-remove:hover { background: rgba(231,76,60,0.2); }
.fw-seg-remove:disabled { opacity: 0.3; cursor: not-allowed; }

.fw-add-btn {
  width: 100%; padding: 8px; background: rgba(212,164,76,0.08);
  border: 2px dashed rgba(212,164,76,0.25); border-radius: 10px;
  color: #d4a44c; font-weight: 700; font-size: 13px; cursor: pointer; transition: all 0.2s;
}
.fw-add-btn:hover { background: rgba(212,164,76,0.15); border-color: rgba(212,164,76,0.4); }
.fw-add-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Settings ── */
.fw-settings-section { margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(212,164,76,0.12); }
.fw-setting-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.fw-setting-row > label { font-size: 12px; color: #8b7355; font-weight: 600; }
.fw-setting-input {
  width: 80px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.15); border-radius: 8px;
  padding: 6px 10px; color: #d4a44c; font-size: 14px; font-weight: 700; text-align: center;
}
.fw-setting-input:focus { outline: none; border-color: #d4a44c; }
.fw-setting-select {
  width: 180px; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(212,164,76,0.15); border-radius: 8px;
  padding: 6px 10px; color: #e8d5b7; font-size: 12px; font-weight: 600;
}

/* Toggle */
.fw-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none; }
.fw-toggle input { display: none; }
.fw-toggle-slider {
  width: 38px; height: 20px; background: rgba(255,255,255,0.1);
  border-radius: 10px; position: relative; transition: background 0.3s;
}
.fw-toggle-slider::after {
  content: ''; width: 16px; height: 16px; background: #8b7355;
  border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: all 0.3s;
}
.fw-toggle input:checked + .fw-toggle-slider { background: rgba(46,204,113,0.3); }
.fw-toggle input:checked + .fw-toggle-slider::after { left: 20px; background: #2ecc71; }
.fw-toggle-text { font-size: 12px; color: #8b7355; font-weight: 600; }

/* Probability */
.fw-info { margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(212,164,76,0.12); }
.fw-info-row { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; font-size: 11px; color: #8b7355; }
.fw-info-val { font-weight: 700; color: #d4a44c; }
.fw-info-seg { display: flex; align-items: center; gap: 6px; }
.fw-info-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.fw-delete-btn {
  width: 100%; margin-top: 16px; padding: 8px;
  background: rgba(231,76,60,0.08); border: 1px solid rgba(231,76,60,0.2);
  border-radius: 10px; color: #e74c3c; font-weight: 700; font-size: 12px;
  cursor: pointer; transition: all 0.2s;
}
.fw-delete-btn:hover { background: rgba(231,76,60,0.15); }


/* ═══════════════════════════════════════════════════════
   EPIC WHEEL — Dark Fantasy Visual
   ═══════════════════════════════════════════════════════ */

.fw-preview {
  display: flex; flex-direction: column; align-items: center;
  padding: 40px 32px;
  position: sticky; top: 20px;
  background: radial-gradient(ellipse at center, rgba(26,26,46,0.95), rgba(15,10,8,0.98));
  border: 2px solid rgba(139,105,20,0.4);
  overflow: hidden;
}

/* Ornamental frame */
.fw-epic-frame {
  position: relative;
  padding: 20px;
}
.fw-corner {
  position: absolute;
  font-size: 20px;
  color: #8b6914;
  text-shadow: 0 0 8px rgba(255,215,0,0.3);
  z-index: 5;
}
.fw-corner-tl { top: -4px; left: -4px; }
.fw-corner-tr { top: -4px; right: -4px; }
.fw-corner-bl { bottom: -4px; left: -4px; }
.fw-corner-br { bottom: -4px; right: -4px; }

.fw-wheel-container {
  position: relative;
  display: inline-block;
}

/* Outer glow ring */
.fw-outer-glow {
  position: absolute;
  top: -15px; left: -15px; right: -15px; bottom: -15px;
  border-radius: 50%;
  border: 2px solid rgba(255,215,0,0.15);
  box-shadow: 
    0 0 30px rgba(255,215,0,0.05),
    inset 0 0 30px rgba(255,215,0,0.03);
  transition: all 0.5s;
}
.fw-outer-glow.spinning {
  border-color: rgba(255,215,0,0.4);
  box-shadow: 
    0 0 40px rgba(255,215,0,0.15),
    0 0 80px rgba(255,215,0,0.08),
    inset 0 0 40px rgba(255,215,0,0.05);
  animation: pulseGlow 0.6s ease-in-out infinite alternate;
}
.fw-outer-glow.won {
  border-color: rgba(255,215,0,0.6);
  box-shadow: 
    0 0 60px rgba(255,215,0,0.25),
    0 0 120px rgba(255,215,0,0.1),
    inset 0 0 40px rgba(255,215,0,0.08);
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 40px rgba(255,215,0,0.15), 0 0 80px rgba(255,215,0,0.08); }
  100% { box-shadow: 0 0 60px rgba(255,215,0,0.25), 0 0 100px rgba(255,215,0,0.12); }
}

/* Pointer */
.fw-pointer-wrap {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.7));
}

/* Canvas */
.fw-canvas {
  display: block;
  border-radius: 50%;
  box-shadow:
    0 0 0 4px rgba(139,105,20,0.5),
    0 0 40px rgba(0,0,0,0.6),
    0 0 80px rgba(0,0,0,0.3),
    inset 0 0 60px rgba(0,0,0,0.2);
}

/* Center Hub */
.fw-center-hub {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 60px; height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #ffd700, #8b6914, #4a3600);
  border: 3px solid #ffd700;
  box-shadow:
    0 0 15px rgba(255,215,0,0.3),
    inset 0 0 10px rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 10;
  pointer-events: none;
  transition: box-shadow 0.3s;
}
.fw-center-hub.spinning {
  box-shadow:
    0 0 25px rgba(255,215,0,0.5),
    0 0 50px rgba(255,215,0,0.2),
    inset 0 0 10px rgba(0,0,0,0.4);
}
.fw-hub-inner {
  font-size: 24px;
  color: #1a0a00;
  text-shadow: 0 1px 2px rgba(255,215,0,0.5);
}

/* ── SPIN BUTTON ── */
.fw-spin-btn {
  margin-top: 32px;
  padding: 16px 56px;
  background: linear-gradient(180deg, #5a3a0a 0%, #2c1a00 50%, #1a0e00 100%);
  border: 2px solid #8b6914;
  color: #ffd700;
  border-radius: 8px;
  font-size: 16px; font-weight: 900;
  font-family: 'Cinzel', serif;
  cursor: pointer;
  letter-spacing: 3px;
  text-transform: uppercase;
  box-shadow:
    0 4px 20px rgba(0,0,0,0.5),
    inset 0 1px 0 rgba(255,215,0,0.2);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}
.fw-spin-btn.active:hover {
  border-color: #ffd700;
  box-shadow:
    0 4px 30px rgba(255,215,0,0.2),
    0 8px 40px rgba(0,0,0,0.4),
    inset 0 1px 0 rgba(255,215,0,0.3);
  transform: translateY(-2px);
}
.fw-spin-btn.active::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,215,0,0.1), transparent);
  animation: shimmer 3s ease-in-out infinite;
}
.fw-spin-btn:active { transform: translateY(0); }
.fw-spin-btn:disabled {
  opacity: 0.6; cursor: not-allowed; transform: none;
  border-color: #5a3a0a;
}

@keyframes shimmer {
  0% { left: -100%; }
  50% { left: 100%; }
  100% { left: 100%; }
}

/* ── RESULT ── */
.fw-result {
  margin-top: 28px;
  text-align: center;
  position: relative;
  padding: 20px 40px;
  animation: resultSlam 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.fw-result-glow {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(ellipse, rgba(255,215,0,0.1), transparent 70%);
  border-radius: 12px;
}
.fw-result-content { position: relative; z-index: 1; }
.fw-result-title {
  font-family: 'Cinzel', serif;
  font-size: 12px; font-weight: 700;
  color: #8b6914; letter-spacing: 6px;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.fw-result-label {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 900;
  color: #ffd700;
  text-shadow:
    0 0 20px rgba(255,215,0,0.4),
    0 2px 4px rgba(0,0,0,0.6);
}
.fw-result-sparks {
  font-size: 14px;
  color: #8b6914;
  margin-top: 8px;
  letter-spacing: 8px;
  animation: sparkle 1.5s ease-in-out infinite;
}

@keyframes resultSlam {
  0% { transform: scale(2) rotate(-5deg); opacity: 0; }
  60% { transform: scale(0.95) rotate(1deg); }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}
@keyframes sparkle {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.result-fade-enter-active { animation: resultSlam 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); }
.result-fade-leave-active { opacity: 0; transition: opacity 0.2s; }
</style>
