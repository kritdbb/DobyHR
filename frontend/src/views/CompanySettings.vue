<template>
  <div>
    <div class="page-header">
      <h2>⚙️ Kingdom Settings</h2>
      <p>Manage your kingdom's configuration</p>
    </div>

    <div class="card" style="max-width: 720px;">
      <div class="card-header">
        <span class="card-title">Kingdom Information</span>
        <button class="btn btn-primary" @click="saveCompany" :disabled="saving">
          {{ saving ? 'Saving...' : '💾 Save' }}
        </button>
      </div>

      <!-- Logo Upload -->
      <div class="form-group" style="display: flex; align-items: flex-start; gap: 24px;">
        <div>
          <label>Kingdom Crest</label>
          <div class="logo-upload-area" @click="$refs.logoInput.click()">
            <img v-if="form.logo" :src="form.logo" alt="Logo" />
            <div v-else class="upload-placeholder">
              <span class="icon">📷</span>
              <span>Upload Crest</span>
            </div>
          </div>
          <input ref="logoInput" type="file" accept="image/*" @change="handleLogoUpload" style="display: none;" />
        </div>
        <div style="flex: 1;">
          <div class="form-group">
            <label>Kingdom Name</label>
            <input v-model="form.name" class="form-input" placeholder="Enter kingdom name" />
          </div>
          <div class="form-group">
            <label>Tax ID (13 digits)</label>
            <input v-model="form.tax_id" class="form-input" placeholder="0000000000000" maxlength="13"
              @input="form.tax_id = form.tax_id.replace(/\D/g, '')" />
          </div>
        </div>
      </div>

      <!-- Location -->
      <div class="form-row">
        <div class="form-group">
          <label>Latitude</label>
          <input v-model.number="form.latitude" class="form-input" type="number" step="any"
            placeholder="e.g. 13.7563" />
        </div>
        <div class="form-group">
          <label>Longitude</label>
          <input v-model.number="form.longitude" class="form-input" type="number" step="any"
            placeholder="e.g. 100.5018" />
        </div>
      </div>

      <!-- Coin Configuration -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">💰 Gold Configuration</span>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>On-Time Reward (Gold)</label>
          <input v-model.number="form.coin_on_time" class="form-input" type="number" placeholder="e.g. 1" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Gold awarded for timely quest arrival.</p>
        </div>
        <div class="form-group">
          <label>Late Penalty (Gold)</label>
          <input v-model.number="form.coin_late_penalty" class="form-input" type="number" placeholder="e.g. 20" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Gold deducted for late arrival.</p>
        </div>
        <div class="form-group">
          <label>Absent Penalty (Gold)</label>
          <input v-model.number="form.coin_absent_penalty" class="form-input" type="number" placeholder="e.g. 20" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Gold deducted for skipping a quest day.</p>
        </div>
      </div>

      <!-- Auto Coin Giver -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">💰 Automatic Gold Giver</span>
      </div>
      <p class="section-desc">Automatically grant gold to all adventurers on selected days at 00:01</p>
      <div class="form-row">
        <div class="form-group" style="flex: 2;">
          <label>Days</label>
          <div class="day-picker">
            <button v-for="d in allDays" :key="d.code"
              :class="['day-chip', autoCoinDays.includes(d.code) && 'day-chip--active']"
              @click="toggleDay('coin', d.code)">
              {{ d.label }}
            </button>
          </div>
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Amount per person</label>
          <input v-model.number="form.auto_coin_amount" class="form-input" type="number" placeholder="e.g. 5" min="0" />
        </div>
      </div>

      <!-- Auto Mana Giver -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">🔮 Automatic Mana Giver</span>
      </div>
      <p class="section-desc">Automatically grant Mana to all adventurers on selected days at 00:01</p>
      <div class="form-row">
        <div class="form-group" style="flex: 2;">
          <label>Days</label>
          <div class="day-picker">
            <button v-for="d in allDays" :key="d.code"
              :class="['day-chip', autoAngelDays.includes(d.code) && 'day-chip--active']"
              @click="toggleDay('angel', d.code)">
              {{ d.label }}
            </button>
          </div>
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Amount per person</label>
          <input v-model.number="form.auto_angel_amount" class="form-input" type="number" placeholder="e.g. 3" min="0" />
        </div>
      </div>

      <!-- Lucky Draw -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">🎰 Lucky Draw (LUK-weighted)</span>
      </div>
      <p class="section-desc">Randomly award gold to one lucky adventurer at 12:30 daily. Higher LUK = more tickets!</p>
      <div class="form-row">
        <div class="form-group" style="flex: 2;">
          <label>Draw Days</label>
          <div class="day-picker">
            <button v-for="d in allDays" :key="d.code"
              :class="['day-chip', luckyDrawDays.includes(d.code) && 'day-chip--active']"
              @click="toggleDay('lucky', d.code)">
              {{ d.label }}
            </button>
          </div>
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Gold Prize</label>
          <input v-model.number="form.lucky_draw_amount" class="form-input" type="number" placeholder="e.g. 10" min="0" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getCompany, updateCompany, uploadCompanyLogo } from '../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      form: {
        name: '',
        tax_id: '',
        logo: null,
        latitude: null,
        longitude: null,
        coin_on_time: 1,
        coin_late_penalty: 20,
        coin_absent_penalty: 20,
        auto_coin_amount: 0,
        auto_angel_amount: 0,
      },
      autoCoinDays: [],
      autoAngelDays: [],
      luckyDrawDays: [],
      allDays: [
        { code: 'mon', label: 'Mon' },
        { code: 'tue', label: 'Tue' },
        { code: 'wed', label: 'Wed' },
        { code: 'thu', label: 'Thu' },
        { code: 'fri', label: 'Fri' },
        { code: 'sat', label: 'Sat' },
        { code: 'sun', label: 'Sun' },
      ],
      saving: false,
    }
  },
  async mounted() {
    await this.loadCompany()
  },
  methods: {
    toggleDay(type, code) {
      let arr
      if (type === 'coin') arr = this.autoCoinDays
      else if (type === 'angel') arr = this.autoAngelDays
      else arr = this.luckyDrawDays
      const idx = arr.indexOf(code)
      if (idx >= 0) arr.splice(idx, 1)
      else arr.push(code)
    },
    async loadCompany() {
      try {
        const { data } = await getCompany()
        this.form = {
          name: data.name || '',
          tax_id: data.tax_id || '',
          logo: data.logo || null,
          latitude: data.latitude,
          longitude: data.longitude,
          coin_on_time: data.coin_on_time,
          coin_late_penalty: data.coin_late_penalty,
          coin_absent_penalty: data.coin_absent_penalty,
          auto_coin_amount: data.auto_coin_amount || 0,
          auto_angel_amount: data.auto_angel_amount || 0,
          lucky_draw_amount: data.lucky_draw_amount || 0,
        }
        this.autoCoinDays = data.auto_coin_day ? data.auto_coin_day.split(',').map(d => d.trim().toLowerCase()) : []
        this.autoAngelDays = data.auto_angel_day ? data.auto_angel_day.split(',').map(d => d.trim().toLowerCase()) : []
        this.luckyDrawDays = data.lucky_draw_day ? data.lucky_draw_day.split(',').map(d => d.trim().toLowerCase()) : []
      } catch (e) {
        console.error('Failed to load company', e)
      }
    },
    async saveCompany() {
      this.saving = true
      try {
        await updateCompany({
          name: this.form.name,
          tax_id: this.form.tax_id,
          latitude: this.form.latitude,
          longitude: this.form.longitude,
          coin_on_time: this.form.coin_on_time,
          coin_late_penalty: this.form.coin_late_penalty,
          coin_absent_penalty: this.form.coin_absent_penalty,
          auto_coin_day: this.autoCoinDays.join(','),
          auto_coin_amount: this.form.auto_coin_amount,
          auto_angel_day: this.autoAngelDays.join(','),
          auto_angel_amount: this.form.auto_angel_amount,
          lucky_draw_day: this.luckyDrawDays.join(','),
          lucky_draw_amount: this.form.lucky_draw_amount,
        })
        this.showToast('Kingdom settings updated!')
      } catch (e) {
        this.showToast('Failed to update settings', 'error')
      } finally {
        this.saving = false
      }
    },
    async handleLogoUpload(event) {
      const file = event.target.files[0]
      if (!file) return
      try {
        const { data } = await uploadCompanyLogo(file)
        this.form.logo = data.logo
        this.showToast('Crest uploaded successfully!')
      } catch (e) {
        this.showToast('Failed to upload crest', 'error')
      }
    },
  },
}
</script>

<style scoped>
.section-desc {
  font-size: 13px;
  color: #8b7355;
  font-weight: 500;
  margin-bottom: 12px;
  margin-top: -4px;
}

.day-picker {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.day-chip {
  padding: 8px 14px;
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  background: rgba(44,24,16,0.6);
  color: #8b7355;
  cursor: pointer;
  transition: all 0.2s;
}
.day-chip:hover {
  border-color: rgba(212,164,76,0.3);
  background: rgba(212,164,76,0.06);
}
.day-chip--active {
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208;
  border-color: transparent;
}
</style>
