<template>
  <div class="admin-page">
    <h1 class="page-title">💎 Artifact Shop</h1>
    <p class="page-sub">Create and manage circle artifacts</p>

    <!-- Create / Edit Form -->
    <div class="form-card">
      <h3 class="form-title">{{ editingId ? '✏️ Edit Artifact' : '➕ New Artifact' }}</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>Name</label>
          <input v-model="form.name" placeholder="Artifact name" />
        </div>
        <div class="form-group">
          <label>Price (Mana)</label>
          <input v-model.number="form.price" type="number" min="1" />
        </div>
        <div class="form-group">
          <label>Rarity</label>
          <select v-model="form.rarity">
            <option value="common">Common</option>
            <option value="uncommon">Uncommon</option>
            <option value="rare">Rare</option>
            <option value="epic">Epic</option>
            <option value="legendary">Legendary</option>
            <option value="mythic">Mythic</option>
          </select>
        </div>
        <div class="form-group">
          <label>Effect</label>
          <select v-model="form.effect">
            <option value="pulse">💫 Pulse (Scale)</option>
            <option value="spin">🔄 Spin (Rotate)</option>
            <option value="glow">🌟 Glow (Brightness)</option>
            <option value="bounce">⬆️ Bounce (Up/Down)</option>
            <option value="shake">💥 Shake (Vibrate)</option>
            <option value="rainbow">🌈 Rainbow (Color Shift)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Color</label>
          <input v-model="form.color" type="color" class="color-input" />
        </div>
        <div class="form-group">
          <label>Image</label>
          <label class="file-label">
            📂 {{ form.file ? form.file.name : 'Choose image...' }}
            <input type="file" accept="image/*" @change="onFileChange" class="file-input" />
          </label>
        </div>
      </div>

      <!-- Preview -->
      <div class="preview-section">
        <div class="preview-label">Preview</div>
        <div class="preview-ring" :class="'effect-' + form.effect" :style="{ borderColor: form.color, boxShadow: '0 0 16px ' + form.color + '55' }">
          <img v-if="previewUrl" :src="previewUrl" class="preview-img" />
          <div v-else class="preview-inner" :style="{ background: 'radial-gradient(circle, ' + form.color + '33, transparent)' }"></div>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-save" @click="save" :disabled="saving || !form.name.trim()">
          {{ saving ? 'Saving...' : (editingId ? 'Update' : 'Create') }}
        </button>
        <button v-if="editingId" class="btn-cancel" @click="resetForm">Cancel</button>
      </div>
    </div>

    <!-- Artifact List -->
    <div class="list-section">
      <h3 class="list-title">📋 All Artifacts ({{ artifacts.length }})</h3>
      <div class="artifact-grid">
        <div v-for="a in artifacts" :key="a.id" class="art-card" :class="{ inactive: !a.active }">
          <div class="art-ring" :class="'effect-' + (a.effect || 'pulse')" :style="{ borderColor: a.color, boxShadow: '0 0 12px ' + a.color + '44' }">
            <img v-if="a.image" :src="a.image" class="art-img" />
            <div v-else class="art-inner" :style="{ background: 'radial-gradient(circle, ' + a.color + '33, transparent)' }"></div>
          </div>
          <div class="art-name">{{ a.name }}</div>
          <div class="art-meta">
            <span class="art-rarity" :class="a.rarity">{{ a.rarity }}</span>
            <span class="art-effect">{{ {pulse:'💫',spin:'🔄',glow:'🌟',bounce:'⬆️',shake:'💥',rainbow:'🌈'}[a.effect] || '💫' }}</span>
            <span class="art-price">✨{{ a.price }}</span>
          </div>
          <div class="art-equipped" v-if="a.equipped_count">👤 {{ a.equipped_count }} equipped</div>
          <div class="art-actions">
            <button class="btn-edit" @click="startEdit(a)">✏️</button>
            <button class="btn-toggle" :class="{ deactivate: a.active }" @click="toggleActive(a)">
              {{ a.active ? '🚫' : '✅' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { adminListArtifacts, adminCreateArtifact, adminUpdateArtifact, adminDeleteArtifact } from '../../services/api'

export default {
  name: 'ArtifactShop',
  data() {
    return {
      artifacts: [],
      form: { name: '', price: 5, rarity: 'common', effect: 'pulse', color: '#d4a44c', file: null },
      editingId: null,
      saving: false,
      previewUrl: null,
    }
  },
  mounted() {
    this.loadArtifacts()
  },
  methods: {
    async loadArtifacts() {
      try {
        const { data } = await adminListArtifacts()
        this.artifacts = data
      } catch (e) { console.error(e) }
    },
    onFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      this.form.file = file
      this.previewUrl = URL.createObjectURL(file)
    },
    resetForm() {
      this.form = { name: '', price: 5, rarity: 'common', effect: 'pulse', color: '#d4a44c', file: null }
      this.editingId = null
      this.previewUrl = null
    },
    startEdit(a) {
      this.editingId = a.id
      this.form = { name: a.name, price: a.price, rarity: a.rarity, effect: a.effect || 'pulse', color: a.color, file: null }
      this.previewUrl = a.image || null
    },
    async save() {
      if (!this.form.name.trim()) return
      this.saving = true
      try {
        const fd = new FormData()
        fd.append('name', this.form.name)
        fd.append('price', this.form.price)
        fd.append('rarity', this.form.rarity)
        fd.append('color', this.form.color)
        fd.append('effect', this.form.effect)
        if (this.form.file) fd.append('file', this.form.file)

        if (this.editingId) {
          await adminUpdateArtifact(this.editingId, fd)
        } else {
          await adminCreateArtifact(fd)
        }
        this.resetForm()
        await this.loadArtifacts()
      } catch (e) {
        const detail = e.response?.data?.detail
        alert(typeof detail === 'object' ? JSON.stringify(detail) : (detail || 'Save failed'))
      } finally { this.saving = false }
    },
    async toggleActive(a) {
      try {
        await adminDeleteArtifact(a.id)
        await this.loadArtifacts()
      } catch (e) { alert('Failed to toggle') }
    },
  },
}
</script>

<style scoped>
.admin-page { padding: 24px 20px; }
.page-title {
  font-family: 'Cinzel', serif; font-size: 24px; font-weight: 800;
  color: #d4a44c; text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub { color: #8b7355; font-size: 13px; font-style: italic; margin-bottom: 20px; }

/* Form Card */
.form-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 1px solid rgba(212,164,76,0.2); border-radius: 14px;
  padding: 20px; margin-bottom: 24px;
}
.form-title {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 700;
  color: #e8d5b7; margin: 0 0 14px;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.form-group label { display: block; font-size: 11px; font-weight: 700; color: #8b7355; margin-bottom: 4px; }
.form-group input, .form-group select {
  width: 100%; padding: 8px 10px; border-radius: 8px;
  border: 1px solid rgba(212,164,76,0.2); background: rgba(0,0,0,0.3);
  color: #e8d5b7; font-size: 13px; box-sizing: border-box;
}
.form-group select { appearance: auto; }
.color-input { height: 36px; padding: 2px; cursor: pointer; }
.file-label {
  display: block; padding: 8px 10px; border-radius: 8px;
  border: 2px dashed rgba(212,164,76,0.2); color: #8b7355;
  font-size: 12px; cursor: pointer; text-align: center;
  transition: all 0.2s; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.file-label:hover { border-color: rgba(212,164,76,0.4); }
.file-input { display: none; }

/* Preview */
.preview-section { display: flex; flex-direction: column; align-items: center; margin-bottom: 16px; }
.preview-label { font-size: 11px; color: #8b7355; margin-bottom: 8px; }
.preview-ring {
  width: 100px; height: 100px; border-radius: 50%;
  border: 3px solid; display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.preview-ring.effect-pulse { animation: artPulse 3s ease-in-out infinite; }
.preview-ring.effect-spin { animation: artSpin 6s linear infinite; }
.preview-ring.effect-glow { animation: artGlow 2s ease-in-out infinite; }
.preview-ring.effect-bounce { animation: artBounce 2s ease-in-out infinite; }
.preview-ring.effect-shake { animation: artShake 0.6s ease-in-out infinite; }
.preview-ring.effect-rainbow { animation: artRainbow 4s linear infinite; }
@keyframes artPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }
@keyframes artSpin { from{transform:rotate(0)} to{transform:rotate(360deg)} }
@keyframes artGlow { 0%,100%{filter:brightness(1) drop-shadow(0 0 4px currentColor)} 50%{filter:brightness(1.4) drop-shadow(0 0 16px currentColor)} }
@keyframes artBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
@keyframes artShake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-3px) rotate(-2deg)} 75%{transform:translateX(3px) rotate(2deg)} }
@keyframes artRainbow { from{filter:hue-rotate(0deg)} to{filter:hue-rotate(360deg)} }
.preview-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.preview-inner { width: 60px; height: 60px; border-radius: 50%; }

.form-actions { display: flex; gap: 10px; justify-content: center; }
.btn-save {
  padding: 10px 28px; border-radius: 8px; border: none;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; font-weight: 800; font-size: 14px; cursor: pointer;
  transition: all 0.2s;
}
.btn-save:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(212,164,76,0.3); }
.btn-save:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-cancel {
  padding: 10px 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05); color: #8b7355; font-weight: 700; cursor: pointer;
}

/* Artifact Grid */
.list-section { margin-bottom: 20px; }
.list-title {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 700;
  color: #e8d5b7; margin: 0 0 14px;
}
.artifact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
@media (min-width: 600px) { .artifact-grid { grid-template-columns: repeat(4, 1fr); } }
@media (min-width: 900px) { .artifact-grid { grid-template-columns: repeat(5, 1fr); } }

.art-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px 10px; border-radius: 12px;
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 1px solid rgba(212,164,76,0.15); transition: all 0.2s; position: relative;
}
.art-card.inactive { opacity: 0.4; filter: grayscale(0.5); }
.art-card:hover { border-color: rgba(212,164,76,0.3); }

.art-ring {
  width: 72px; height: 72px; border-radius: 50%;
  border: 3px solid; display: flex; align-items: center; justify-content: center;
  overflow: hidden; margin-bottom: 6px;
}
.art-ring.effect-pulse { animation: artPulse 3s ease-in-out infinite; }
.art-ring.effect-spin { animation: artSpin 6s linear infinite; }
.art-ring.effect-glow { animation: artGlow 2s ease-in-out infinite; }
.art-ring.effect-bounce { animation: artBounce 2s ease-in-out infinite; }
.art-ring.effect-shake { animation: artShake 0.6s ease-in-out infinite; }
.art-ring.effect-rainbow { animation: artRainbow 4s linear infinite; }
.art-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.art-inner { width: 40px; height: 40px; border-radius: 50%; }

.art-name { font-size: 11px; font-weight: 700; color: #e8d5b7; text-align: center; line-height: 1.3; margin-bottom: 4px; }
.art-meta { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; flex-wrap: wrap; justify-content: center; }
.art-rarity {
  font-size: 9px; font-weight: 800; text-transform: uppercase;
  padding: 1px 6px; border-radius: 4px;
}
.art-rarity.common { color: #bdc3c7; background: rgba(189,195,199,0.1); }
.art-rarity.uncommon { color: #2ecc71; background: rgba(46,204,113,0.1); }
.art-rarity.rare { color: #3498db; background: rgba(52,152,219,0.1); }
.art-rarity.epic { color: #9b59b6; background: rgba(155,89,182,0.1); }
.art-rarity.legendary { color: #f39c12; background: rgba(243,156,18,0.1); }
.art-rarity.mythic { color: #e74c3c; background: rgba(231,76,60,0.15); }
.art-effect { font-size: 12px; }
.art-price { font-size: 11px; font-weight: 700; color: #c39bd3; }
.art-equipped { font-size: 10px; color: #8b7355; margin-bottom: 6px; }

.art-actions { display: flex; gap: 6px; margin-top: 4px; }
.btn-edit, .btn-toggle {
  padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(212,164,76,0.2);
  background: rgba(0,0,0,0.3); cursor: pointer; font-size: 12px;
  transition: all 0.15s;
}
.btn-edit:hover { border-color: rgba(212,164,76,0.5); background: rgba(212,164,76,0.1); }
.btn-toggle.deactivate:hover { border-color: rgba(231,76,60,0.5); background: rgba(231,76,60,0.1); }
</style>
