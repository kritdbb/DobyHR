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

      <!-- Step Goal: Daily -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">🥾 Daily Step Goal</span>
      </div>
      <p class="section-desc">Set a daily walking target and rewards for reaching it (resets daily at midnight)</p>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>Target Steps</label>
          <input v-model.number="form.step_daily_target" class="form-input" type="number" placeholder="e.g. 5000" min="0" />
        </div>
      </div>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>STR</label>
          <input v-model.number="form.step_daily_str" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>DEF</label>
          <input v-model.number="form.step_daily_def" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>LUK</label>
          <input v-model.number="form.step_daily_luk" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Gold</label>
          <input v-model.number="form.step_daily_gold" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Mana</label>
          <input v-model.number="form.step_daily_mana" class="form-input" type="number" min="0" />
        </div>
      </div>

      <!-- Step Goal: Daily Tier 2 -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">🥾 Daily Step Goal — Tier 2</span>
      </div>
      <p class="section-desc">Second milestone on the same bar. Set target to 0 to disable.</p>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>Target Steps</label>
          <input v-model.number="form.step_daily2_target" class="form-input" type="number" placeholder="e.g. 10000" min="0" />
        </div>
      </div>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>STR</label>
          <input v-model.number="form.step_daily2_str" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>DEF</label>
          <input v-model.number="form.step_daily2_def" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>LUK</label>
          <input v-model.number="form.step_daily2_luk" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Gold</label>
          <input v-model.number="form.step_daily2_gold" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Mana</label>
          <input v-model.number="form.step_daily2_mana" class="form-input" type="number" min="0" />
        </div>
      </div>

      <!-- Step Goal: Monthly -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">🗓️ Monthly Step Goal</span>
      </div>
      <p class="section-desc">Monthly walking target (set target to 0 to disable)</p>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>Target Steps</label>
          <input v-model.number="form.step_monthly_target" class="form-input" type="number" placeholder="e.g. 75000" min="0" />
        </div>
      </div>
      <div class="form-row">
        <div class="form-group" style="flex: 1;">
          <label>STR</label>
          <input v-model.number="form.step_monthly_str" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>DEF</label>
          <input v-model.number="form.step_monthly_def" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>LUK</label>
          <input v-model.number="form.step_monthly_luk" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Gold</label>
          <input v-model.number="form.step_monthly_gold" class="form-input" type="number" min="0" />
        </div>
        <div class="form-group" style="flex: 1;">
          <label>Mana</label>
          <input v-model.number="form.step_monthly_mana" class="form-input" type="number" min="0" />
        </div>
      </div>

      <!-- Rescue (Revival Pool) -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">💖 Revival Pool (Rescue)</span>
      </div>
      <p class="section-desc">When a guild member's Gold drops below 0, they are considered "dead". Fellow members can contribute Mana to revive them.</p>
      <div class="form-row">
        <div class="form-group">
          <label>Mana Cost per Person</label>
          <input v-model.number="form.rescue_cost_per_person" class="form-input" type="number" placeholder="1" min="1" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Mana each rescuer must spend.</p>
        </div>
        <div class="form-group">
          <label>Required People</label>
          <input v-model.number="form.rescue_required_people" class="form-input" type="number" placeholder="3" min="1" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">How many people must contribute to revive.</p>
        </div>
        <div class="form-group">
          <label>Gold on Revive</label>
          <input v-model.number="form.rescue_gold_on_revive" class="form-input" type="number" placeholder="0" min="0" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Gold given to the revived member (0 = reset to zero).</p>
        </div>
      </div>

      <!-- CCTV Face Recognition -->
      <div class="card-header" style="margin-top: 24px; border-top: 1px solid rgba(212,164,76,0.1); padding-top: 24px;">
        <span class="card-title">📹 CCTV Face Recognition</span>
      </div>
      <p class="section-desc">Configure RTSP cameras for automatic face check-in.</p>
      <div style="margin-bottom: 16px;">
        <label style="font-size: 13px; font-weight: 600; color: #8b7355;">RTSP Cameras</label>
        <div v-for="(cam, idx) in rtspCameras" :key="idx" style="margin-top: 10px; padding: 12px; background: rgba(26,20,15,0.3); border-radius: 8px; border: 1px solid rgba(212,164,76,0.1);">
          <div style="display: flex; gap: 8px; align-items: center;">
            <span style="font-size: 12px; color: #d4a44c; font-weight: 600; min-width: 24px;">{{ idx + 1 }}.</span>
            <input v-model="cam.url" class="form-input" placeholder="rtsp://192.168.1.10:554/stream" style="flex: 1;" />
            <button v-if="testingCamera !== idx" @click="startTest(idx)" class="btn btn-primary" style="padding: 6px 14px; font-size: 12px; white-space: nowrap;" :disabled="!cam.url">
              ▶ Test
            </button>
            <button v-else @click="stopTest()" class="btn btn-secondary" style="padding: 6px 14px; font-size: 12px; white-space: nowrap; background: rgba(231,76,60,0.15); color: #e74c3c; border-color: rgba(231,76,60,0.3);">
              ■ Stop
            </button>
            <button @click="removeCamera(idx)" class="btn btn-secondary" style="padding: 6px 10px; font-size: 12px;">✕</button>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px; padding-left: 32px;">
            <input v-model="cam.username" class="form-input" placeholder="Username" style="flex: 1; font-size: 12px; padding: 6px 10px;" />
            <input v-model="cam.password" class="form-input" type="password" placeholder="Password" style="flex: 1; font-size: 12px; padding: 6px 10px;" />
          </div>
          <!-- MJPEG Stream preview -->
          <div v-if="testingCamera === idx" style="margin-top: 10px; border-radius: 6px; overflow: hidden; border: 1px solid rgba(212,164,76,0.2); position: relative;">
            <div style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.6); color: #e74c3c; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; display: flex; align-items: center; gap: 5px; z-index: 1;">
              <span style="width: 6px; height: 6px; background: #e74c3c; border-radius: 50%; display: inline-block; animation: blink 1s infinite;"></span> LIVE
            </div>
            <img :src="streamUrl" style="width: 100%; display: block; background: #111;" @error="onStreamError" />
          </div>
        </div>
        <button @click="rtspCameras.push({ url: '', username: '', password: '' })" class="btn btn-secondary" style="margin-top: 8px; font-size: 12px; padding: 5px 12px;">
          + Add Camera
        </button>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Confidence Threshold</label>
          <input v-model.number="form.face_confidence_threshold" class="form-input" type="number" step="0.01" min="0" max="1" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Min similarity score (0.0–1.0). Default: 0.5</p>
        </div>
        <div class="form-group">
          <label>Consecutive Frames</label>
          <input v-model.number="form.face_min_consecutive_frames" class="form-input" type="number" min="1" />
          <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">Frames face must be visible. Default: 20</p>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Min Face Height (px)</label>
          <input v-model.number="form.face_min_face_height" class="form-input" type="number" min="10" />
        </div>
        <div class="form-group">
          <label>Active Start Time</label>
          <input v-model="form.face_start_time" class="form-input" type="time" />
        </div>
        <div class="form-group">
          <label>Active End Time</label>
          <input v-model="form.face_end_time" class="form-input" type="time" />
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
        step_daily_target: 5000,
        step_daily_str: 0,
        step_daily_def: 0,
        step_daily_luk: 0,
        step_daily_gold: 0,
        step_daily_mana: 0,
        step_daily2_target: 0,
        step_daily2_str: 0,
        step_daily2_def: 0,
        step_daily2_luk: 0,
        step_daily2_gold: 0,
        step_daily2_mana: 0,
        step_monthly_target: 75000,
        step_monthly_str: 0,
        step_monthly_def: 0,
        step_monthly_luk: 0,
        step_monthly_gold: 1,
        step_monthly_mana: 0,
        rescue_cost_per_person: 1,
        rescue_required_people: 3,
        rescue_gold_on_revive: 0,
        face_confidence_threshold: 0.5,
        face_min_consecutive_frames: 20,
        face_min_face_height: 50,
        face_start_time: '06:00',
        face_end_time: '10:30',
      },
      rtspCameras: [],
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
      testingCamera: null,
      streamUrl: '',
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
          step_daily_target: data.step_daily_target ?? 5000,
          step_daily_str: data.step_daily_str ?? 0,
          step_daily_def: data.step_daily_def ?? 0,
          step_daily_luk: data.step_daily_luk ?? 0,
          step_daily_gold: data.step_daily_gold ?? 0,
          step_daily_mana: data.step_daily_mana ?? 0,
          step_daily2_target: data.step_daily2_target ?? 0,
          step_daily2_str: data.step_daily2_str ?? 0,
          step_daily2_def: data.step_daily2_def ?? 0,
          step_daily2_luk: data.step_daily2_luk ?? 0,
          step_daily2_gold: data.step_daily2_gold ?? 0,
          step_daily2_mana: data.step_daily2_mana ?? 0,
          step_monthly_target: data.step_monthly_target ?? 75000,
          step_monthly_str: data.step_monthly_str ?? 0,
          step_monthly_def: data.step_monthly_def ?? 0,
          step_monthly_luk: data.step_monthly_luk ?? 0,
          step_monthly_gold: data.step_monthly_gold ?? 1,
          step_monthly_mana: data.step_monthly_mana ?? 0,
          rescue_cost_per_person: data.rescue_cost_per_person ?? 1,
          rescue_required_people: data.rescue_required_people ?? 3,
          rescue_gold_on_revive: data.rescue_gold_on_revive ?? 0,
          face_confidence_threshold: data.face_confidence_threshold ?? 0.5,
          face_min_consecutive_frames: data.face_min_consecutive_frames ?? 20,
          face_min_face_height: data.face_min_face_height ?? 50,
          face_start_time: data.face_start_time || '06:00',
          face_end_time: data.face_end_time || '10:30',
        }
        // RTSP cameras
        try {
          const parsed = data.face_rtsp_urls ? JSON.parse(data.face_rtsp_urls) : []
          // Backwards compat: convert old string array to object array
          this.rtspCameras = parsed.map(item =>
            typeof item === 'string'
              ? { url: item, username: '', password: '' }
              : { url: item.url || '', username: item.username || '', password: item.password || '' }
          )
        } catch { this.rtspCameras = [] }
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
          step_daily_target: this.form.step_daily_target,
          step_daily_str: this.form.step_daily_str,
          step_daily_def: this.form.step_daily_def,
          step_daily_luk: this.form.step_daily_luk,
          step_daily_gold: this.form.step_daily_gold,
          step_daily_mana: this.form.step_daily_mana,
          step_daily2_target: this.form.step_daily2_target,
          step_daily2_str: this.form.step_daily2_str,
          step_daily2_def: this.form.step_daily2_def,
          step_daily2_luk: this.form.step_daily2_luk,
          step_daily2_gold: this.form.step_daily2_gold,
          step_daily2_mana: this.form.step_daily2_mana,
          step_monthly_target: this.form.step_monthly_target,
          step_monthly_str: this.form.step_monthly_str,
          step_monthly_def: this.form.step_monthly_def,
          step_monthly_luk: this.form.step_monthly_luk,
          step_monthly_gold: this.form.step_monthly_gold,
          step_monthly_mana: this.form.step_monthly_mana,
          rescue_cost_per_person: this.form.rescue_cost_per_person,
          rescue_required_people: this.form.rescue_required_people,
          rescue_gold_on_revive: this.form.rescue_gold_on_revive,
          face_rtsp_urls: JSON.stringify(this.rtspCameras.filter(c => c.url.trim())),
          face_confidence_threshold: this.form.face_confidence_threshold,
          face_min_consecutive_frames: this.form.face_min_consecutive_frames,
          face_min_face_height: this.form.face_min_face_height,
          face_start_time: this.form.face_start_time,
          face_end_time: this.form.face_end_time,
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
    startTest(idx) {
      const cam = this.rtspCameras[idx]
      if (!cam || !cam.url) return
      // Build full RTSP URL with credentials
      let fullUrl = cam.url
      if (cam.username && cam.url.startsWith('rtsp://')) {
        const cred = cam.password ? `${cam.username}:${cam.password}` : cam.username
        fullUrl = 'rtsp://' + cred + '@' + cam.url.slice(7)
      }
      const token = localStorage.getItem('token')
      const base = import.meta.env.VITE_API_URL || ''
      this.streamUrl = `${base}/api/face/test-stream?rtsp_url=${encodeURIComponent(fullUrl)}&token=${encodeURIComponent(token)}`
      this.testingCamera = idx
    },
    stopTest() {
      this.streamUrl = ''
      this.testingCamera = null
    },
    removeCamera(idx) {
      if (this.testingCamera === idx) this.stopTest()
      this.rtspCameras.splice(idx, 1)
    },
    onStreamError() {
      this.showToast('Stream connection failed', 'error')
      this.stopTest()
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

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
