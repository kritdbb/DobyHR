<template>
  <div class="checkin-page">
    <div class="checkin-header">
      <h1 class="checkin-title">🗡️ Daily Quest</h1>
      <p class="checkin-sub">Report to the guild to begin your quest</p>
    </div>

    <!-- DEF Grace Info -->
    <div v-if="defGrace && defGrace.totalDef > 0 && !alreadyCheckedIn" class="def-grace-card">
      <div class="def-grace-row">
        <span class="def-stat">🛡️ DEF: <strong>{{ defGrace.totalDef }}</strong></span>
        <span class="def-grace-value">สายได้ <strong>{{ formatGrace(defGrace.graceSeconds) }}</strong></span>
      </div>
      <div class="def-grace-hint">
        เวลาเข้างานปกติ {{ defGrace.workStartFormatted }}
        → ยืดเป็น {{ defGrace.effectiveStart }}
      </div>
    </div>

    <!-- Distance Display -->
    <div v-if="!alreadyCheckedIn" class="distance-section">
      <div v-if="distLoading" class="distance-badge distance-badge--loading">
        <div class="spinner"></div>
        Scouting the area...
      </div>
      <div v-else-if="distance !== null"
        :class="['distance-badge', distance <= maxRadius ? 'distance-badge--ok' : 'distance-badge--far']">
        <span class="distance-icon">🧭</span>
        You are <strong>{{ distance.toLocaleString() }}m</strong> from the guild
        <div class="distance-hint">
          {{ distance <= maxRadius ? '✅ Within quest range' : '📡 Remote — will create Remote Quest' }}
        </div>
      </div>
      <div v-else-if="distError" class="distance-badge distance-badge--error">
        {{ distError }}
      </div>
    </div>

    <!-- Already Checked In -->
    <div v-if="alreadyCheckedIn" class="already-done-card">
      <div class="already-done-icon">⚔️</div>
      <div class="already-done-text">
        Check-In at <strong>{{ checkedInTime }}</strong>
      </div>
      <div class="already-done-status">
        Status: {{ checkedInStatus }}
      </div>
    </div>

    <!-- Expired -->
    <div v-else-if="isExpired" class="expired-section">
      <button class="checkin-btn checkin-btn--disabled" disabled>
        <span style="font-size: 48px;">⏳</span>
        <span class="checkin-btn-label">Quest Expired</span>
      </button>
      <p class="expired-hint">Quest posted at {{ formattedStartTime }} — deadline has passed</p>
    </div>

    <!-- Check In / Remote Work Button -->
    <div v-else>
      <button 
        @click="handleCheckIn" 
        :disabled="loading"
        :class="['checkin-btn', isRemote ? 'checkin-btn--remote' : '']">
        <div v-if="loading" class="spinner spinner--lg"></div>
        <span v-else style="font-size: 48px;">⚔️</span>
        <span class="checkin-btn-label">{{ loading ? 'Processing...' : buttonLabel }}</span>
      </button>
    </div>

    <!-- Status Message -->
    <div v-if="statusMessage" :class="['status-msg', statusType === 'error' ? 'status-msg--error' : 'status-msg--success']">
      {{ statusType === 'success' ? '⚔️ ' : '💀 ' }}{{ statusMessage }}
    </div>
  </div>
</template>

<script>
import { checkIn, getCompany, getTodayCheckInStatus } from '../../services/api'
import api from '../../services/api'

export default {
  data() {
    return {
      loading: false,
      statusMessage: '',
      statusType: '',
      distance: null,
      distLoading: true,
      distError: '',
      maxRadius: 200,
      companyLat: null,
      companyLon: null,
      alreadyCheckedIn: false,
      checkedInTime: '',
      checkedInStatus: '',
      isExpired: false,
      workStartTime: null,
      formattedStartTime: '',
      defGrace: null,
    }
  },
  computed: {
    isRemote() {
      return this.distance !== null && this.distance > this.maxRadius
    },
    buttonLabel() {
      return this.isRemote ? 'REMOTE QUEST' : 'ACCEPT QUEST'
    },
  },
  inject: ['showToast'],
  async mounted() {
    await this.checkTodayStatus()
    if (!this.alreadyCheckedIn) {
      await this.loadDefGrace()
      await this.checkExpired()
      await this.calcDistance()
    }
  },
  methods: {
    async checkTodayStatus() {
      try {
        const { data } = await getTodayCheckInStatus()
        if (data.checked_in) {
          this.alreadyCheckedIn = true
          this.checkedInTime = data.time
          this.checkedInStatus = data.status
        }
      } catch (e) {
        console.error('Failed to check today status', e)
      }
    },
    async loadDefGrace() {
      try {
        const [companyRes, meRes, statsRes] = await Promise.all([
          getCompany(),
          api.get('/api/users/me'),
          api.get('/api/badges/stats/me')
        ])
        const company = companyRes.data
        const me = meRes.data
        const stats = statsRes.data
        const defGracePerPoint = company.def_grace_seconds || 0
        if (defGracePerPoint <= 0) return

        // Use total_def from stats endpoint (base_def + badge DEF, calculated server-side)
        const fullDef = stats.total_def || 10
        const graceSeconds = fullDef * defGracePerPoint

        // Work start time
        const startTime = me.work_start_time || '09:00'
        const parts = startTime.split(':')
        const startH = parseInt(parts[0]), startM = parseInt(parts[1] || 0)
        const workStartFormatted = `${String(startH).padStart(2,'0')}:${String(startM).padStart(2,'0')}`

        // Calculate effective start with grace
        const totalStartSec = startH * 3600 + startM * 60 + graceSeconds
        const effH = Math.floor(totalStartSec / 3600)
        const effM = Math.floor((totalStartSec % 3600) / 60)
        const effS = totalStartSec % 60
        const effectiveStart = effS > 0
          ? `${String(effH).padStart(2,'0')}:${String(effM).padStart(2,'0')}:${String(effS).padStart(2,'0')}`
          : `${String(effH).padStart(2,'0')}:${String(effM).padStart(2,'0')}`

        this.defGrace = {
          totalDef: fullDef,
          graceSeconds,
          workStartFormatted,
          effectiveStart
        }
      } catch (e) {
        console.error('Failed to load DEF grace', e)
      }
    },
    formatGrace(seconds) {
      if (seconds >= 60) {
        const min = Math.floor(seconds / 60)
        const sec = seconds % 60
        return sec > 0 ? `${min} นาที ${sec} วินาที` : `${min} นาที`
      }
      return `${seconds} วินาที`
    },
    async checkExpired() {
      try {
        const { data: me } = await api.get('/api/users/me')
        if (me.work_start_time) {
          this.workStartTime = me.work_start_time
          const parts = me.work_start_time.split(':')
          const startH = parseInt(parts[0]), startM = parseInt(parts[1])
          this.formattedStartTime = `${String(startH).padStart(2, '0')}:${String(startM).padStart(2, '0')}`
          
          const now = new Date()
          const utc = now.getTime() + now.getTimezoneOffset() * 60000
          const local = new Date(utc + 7 * 3600000)
          const nowMin = local.getHours() * 60 + local.getMinutes()
          const startMin = startH * 60 + startM
          
          if (nowMin - startMin > 60) {
            this.isExpired = true
          }
        }
      } catch (e) {
        console.error('Failed to check work time', e)
      }
    },
    async calcDistance() {
      this.distLoading = true
      this.distError = ''
      try {
        const { data: company } = await getCompany()
        if (!company.latitude || !company.longitude) {
          this.distError = 'Guild location not set'
          this.distLoading = false
          return
        }
        this.companyLat = company.latitude
        this.companyLon = company.longitude

        if (!navigator.geolocation) {
          this.distError = 'Compass not supported'
          this.distLoading = false
          return
        }

        // Phase 1: Try fast location (WiFi/cell, cached OK) — 3s timeout
        const fastPos = await this.getPosition({ enableHighAccuracy: false, timeout: 3000, maximumAge: 60000 })
          .catch(() => null)

        if (fastPos) {
          this.distance = Math.round(this.haversine(fastPos.coords.latitude, fastPos.coords.longitude, this.companyLat, this.companyLon))
          this.distLoading = false

          // Phase 2: Refine with GPS in background (silent upgrade)
          this.getPosition({ enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 })
            .then(pos => {
              this.distance = Math.round(this.haversine(pos.coords.latitude, pos.coords.longitude, this.companyLat, this.companyLon))
            })
            .catch(() => { /* keep fast result */ })
          return
        }

        // Fallback: high accuracy only (if fast failed)
        const pos = await this.getPosition({ enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 })
        this.distance = Math.round(this.haversine(pos.coords.latitude, pos.coords.longitude, this.companyLat, this.companyLon))
        this.distLoading = false
      } catch (e) {
        this.distError = e.code === 1 ? 'Location access denied' : 'Could not determine location — please enable Location Services'
        this.distLoading = false
      }
    },
    getPosition(options) {
      return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, options)
      })
    },
    haversine(lat1, lon1, lat2, lon2) {
      const R = 6371000, toRad = (d) => (d * Math.PI) / 180
      const dLat = toRad(lat2 - lat1), dLon = toRad(lon2 - lon1)
      const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
      return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    },
    handleCheckIn() {
      this.loading = true
      this.statusMessage = ''
      if (!navigator.geolocation) {
        this.statusMessage = "Compass is not supported by your device."
        this.statusType = 'error'
        this.loading = false
        return
      }
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords
            const { data } = await checkIn(latitude, longitude)
            if (data.work_request_created) {
              this.statusMessage = `📋 Special Mission created! Awaiting guild approval. Distance: ${data.distance}m`
              this.statusType = 'success'
            } else if (data.remote_request_created) {
              this.statusMessage = `📡 Remote Quest created! Awaiting guild approval. Distance: ${data.distance}m`
              this.statusType = 'success'
            } else {
              this.statusMessage = `Quest Accepted! Status: ${data.status}, Distance: ${data.distance}m${data.coin_change ? ` (${data.coin_change > 0 ? '+' : ''}${data.coin_change} gold)` : ''}`
              this.statusType = 'success'
            }
            this.alreadyCheckedIn = true
            const ts = new Date(data.timestamp)
            const utc = ts.getTime() + ts.getTimezoneOffset() * 60000
            const local = new Date(utc + 7 * 3600000)
            this.checkedInTime = `${String(local.getHours()).padStart(2, '0')}:${String(local.getMinutes()).padStart(2, '0')}`
            this.checkedInStatus = data.status
          } catch (e) {
            this.statusMessage = e.response?.data?.detail || "Quest failed"
            this.statusType = 'error'
          } finally { this.loading = false }
        },
        () => { this.statusMessage = "Unable to locate adventurer"; this.statusType = 'error'; this.loading = false },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
      )
    }
  }
}
</script>

<style scoped>
.checkin-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
}

.checkin-header { margin-bottom: 24px; }
.checkin-title {
  font-family: 'Cinzel', serif;
  font-size: 28px;
  font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
}
.checkin-sub { color: #8b7355; font-weight: 600; margin-top: 4px; }

/* DEF Grace Info */
.def-grace-card {
  background: linear-gradient(135deg, rgba(52,152,219,0.08), rgba(41,128,185,0.04));
  border: 1.5px solid rgba(52,152,219,0.25);
  border-radius: 10px;
  padding: 12px 20px;
  margin-bottom: 18px;
  max-width: 340px;
}
.def-grace-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.def-stat { color: #3498db; font-size: 14px; font-weight: 700; }
.def-grace-value { color: #2ecc71; font-size: 13px; font-weight: 600; }
.def-grace-hint {
  font-size: 11px;
  color: #8b7355;
  margin-top: 6px;
  text-align: center;
  font-weight: 500;
}

/* Distance */
.distance-section { margin-bottom: 28px; }
.distance-badge {
  display: inline-flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 14px 28px; border-radius: 10px; font-weight: 700; font-size: 14px;
  border: 2px solid;
}
.distance-badge--loading { background: rgba(26,26,46,0.6); color: #8b7355; border-color: rgba(212,164,76,0.15); }
.distance-badge--ok { background: rgba(39,174,96,0.1); color: #27ae60; border-color: rgba(39,174,96,0.3); }
.distance-badge--far { background: rgba(212,164,76,0.1); color: #d4a44c; border-color: rgba(212,164,76,0.3); }
.distance-badge--error { background: rgba(192,57,43,0.1); color: #e74c3c; border-color: rgba(192,57,43,0.3); }
.distance-icon { font-size: 20px; }
.distance-hint { font-size: 12px; font-weight: 600; margin-top: 2px; }

/* Already Done */
.already-done-card {
  background: linear-gradient(135deg, rgba(39,174,96,0.15), rgba(46,204,113,0.1));
  border: 2px solid rgba(39,174,96,0.3);
  border-radius: 16px;
  padding: 32px 48px;
  margin-bottom: 20px;
}
.already-done-icon { font-size: 48px; margin-bottom: 8px; }
.already-done-text { font-size: 16px; font-weight: 700; color: #27ae60; }
.already-done-status {
  font-size: 13px; font-weight: 600; color: #2ecc71;
  margin-top: 6px; text-transform: capitalize;
}

/* Expired */
.expired-section { text-align: center; }
.expired-hint { font-size: 13px; color: #8b7355; font-weight: 600; margin-top: 12px; }

/* Button */
.checkin-btn {
  width: 180px; height: 180px; border-radius: 50%;
  border: 3px solid #d4a44c; cursor: pointer;
  background: linear-gradient(135deg, #2c1810, #1a1a2e);
  color: #d4a44c; font-weight: 900; font-size: 16px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  box-shadow: 0 0 30px rgba(212,164,76,0.2), inset 0 0 20px rgba(212,164,76,0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.checkin-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 50px rgba(212,164,76,0.3), inset 0 0 30px rgba(212,164,76,0.1);
  border-color: #ffd700;
}
.checkin-btn:active:not(:disabled) { transform: scale(0.97); }
.checkin-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.checkin-btn--remote {
  border-color: #9b59b6;
  box-shadow: 0 0 30px rgba(155,89,182,0.2), inset 0 0 20px rgba(155,89,182,0.05);
  color: #c39bd3;
}
.checkin-btn--remote:hover:not(:disabled) {
  box-shadow: 0 0 50px rgba(155,89,182,0.3);
  border-color: #c39bd3;
}

.checkin-btn--disabled {
  width: 180px; height: 180px; border-radius: 50%;
  border: 3px solid rgba(139,115,85,0.3); cursor: not-allowed;
  background: linear-gradient(135deg, #2c1810, #1a1a2e);
  color: #8b7355; font-weight: 900; font-size: 14px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  box-shadow: none; opacity: 0.5;
}

.checkin-btn-label { letter-spacing: 1px; font-family: 'Cinzel', serif; font-size: 13px; }

/* Status */
.status-msg {
  margin-top: 20px; padding: 14px 24px; border-radius: 10px;
  font-weight: 700; font-size: 14px; max-width: 400px;
  border: 2px solid;
}
.status-msg--success { background: rgba(39,174,96,0.1); color: #27ae60; border-color: rgba(39,174,96,0.3); }
.status-msg--error { background: rgba(192,57,43,0.1); color: #e74c3c; border-color: rgba(192,57,43,0.3); }

/* Spinner */
.spinner {
  width: 20px; height: 20px; border: 3px solid rgba(212,164,76,0.3);
  border-top-color: #d4a44c; border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
.spinner--lg { width: 40px; height: 40px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
