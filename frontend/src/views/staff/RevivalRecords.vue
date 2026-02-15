<template>
  <div class="hall-page">
    <div class="hall-header">
      <div class="hall-glow"></div>
      <h1 class="hall-title">⚔️ Revival Records</h1>
      <p class="hall-sub">Hall of Fame — ผู้กล้าที่รวมพลังชุบชีวิตเพื่อน</p>
    </div>

    <div v-if="loading" class="hall-loading">
      <div class="loading-spin"></div>
      <p>กำลังโหลดบันทึกการชุบชีวิต...</p>
    </div>

    <div v-else-if="records.length === 0" class="hall-empty">
      <div class="empty-icon">📜</div>
      <p>ยังไม่มีบันทึกการชุบชีวิต</p>
      <p class="empty-sub">เมื่อมีใครถูกชุบชีวิตสำเร็จ จะปรากฏที่นี่!</p>
    </div>

    <div v-else class="records-list">
      <div v-for="(r, idx) in records" :key="r.id" class="record-card" :class="{'record-first': idx === 0}">
        <!-- Rank badge -->
        <div class="record-rank" :class="'rank-' + (idx < 3 ? idx+1 : 'normal')">
          <span v-if="idx === 0">👑</span>
          <span v-else-if="idx === 1">🥈</span>
          <span v-else-if="idx === 2">🥉</span>
          <span v-else>#{{ idx + 1 }}</span>
        </div>

        <!-- Revived user (center) -->
        <div class="record-revived">
          <div class="revived-portrait" :class="{'portrait-first': idx === 0}">
            <img v-if="r.revived_user.image" :src="r.revived_user.image" class="revived-img" />
            <span v-else class="revived-fb">{{ r.revived_user.name.charAt(0) }}</span>
            <div class="revived-aura"></div>
          </div>
          <div class="revived-info">
            <div class="revived-name">{{ r.revived_user.name }}</div>
            <div class="revived-label">ได้รับการชุบชีวิต ✨</div>
            <div class="revived-date">{{ formatDate(r.date) }}</div>
          </div>
        </div>

        <!-- Rescuers -->
        <div class="record-rescuers">
          <div class="rescuers-label">🙏 ผู้กล้าที่ร่วมชุบชีวิต</div>
          <div class="rescuers-row">
            <div v-for="(rc, ri) in r.rescuers" :key="ri" class="rescuer-chip">
              <img v-if="rc.image" :src="rc.image" class="rescuer-img" />
              <span v-else class="rescuer-fb">{{ rc.name.charAt(0) }}</span>
              <span class="rescuer-name">{{ rc.name }}</span>
            </div>
          </div>
        </div>

        <!-- Gold given -->
        <div v-if="r.gold_given > 0" class="record-gold">💰 +{{ r.gold_given }} Gold</div>
      </div>
    </div>

    <router-link to="/staff/services" class="back-btn">← Back to Guild Services</router-link>
  </div>
</template>

<script>
import api from '../../services/api'

export default {
  data() {
    return {
      records: [],
      loading: true,
    }
  },
  async mounted() {
    await this.loadRecords()
  },
  methods: {
    async loadRecords() {
      this.loading = true
      try {
        const { data } = await api.get('/api/users/rescue/records')
        this.records = data
      } catch (e) {
        console.error('Failed to load revival records', e)
        this.records = []
      } finally {
        this.loading = false
      }
    },
    formatDate(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      const day = d.getDate()
      const months = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']
      const month = months[d.getMonth()]
      const year = d.getFullYear() + 543
      const h = d.getHours().toString().padStart(2, '0')
      const m = d.getMinutes().toString().padStart(2, '0')
      return `${day} ${month} ${year} เวลา ${h}:${m}`
    },
  },
}
</script>

<style scoped>
.hall-page {
  padding: 20px 0 32px;
  min-height: 100vh;
}

/* Header */
.hall-header {
  text-align: center;
  margin-bottom: 28px;
  position: relative;
}
.hall-glow {
  position: absolute;
  top: -30px; left: 50%; transform: translateX(-50%);
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(212,164,76,0.15) 0%, transparent 70%);
  pointer-events: none;
}
.hall-title {
  font-family: 'Cinzel', serif;
  font-size: 28px;
  font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 12px rgba(212,164,76,0.3);
  position: relative;
}
.hall-sub {
  color: #8b7355;
  font-size: 13px;
  font-style: italic;
  margin-top: 4px;
}

/* Loading */
.hall-loading {
  text-align: center;
  padding: 60px 0;
  color: #8b7355;
}
.loading-spin {
  width: 40px; height: 40px;
  border: 3px solid rgba(212,164,76,0.2);
  border-top-color: #d4a44c;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Empty */
.hall-empty {
  text-align: center;
  padding: 60px 20px;
  color: #8b7355;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}
.empty-sub {
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.7;
}

/* Records */
.records-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.record-card {
  background: linear-gradient(135deg, rgba(44,24,16,0.9), rgba(30,18,10,0.95));
  border: 1px solid rgba(212,164,76,0.15);
  border-radius: 16px;
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}
.record-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, rgba(212,164,76,0.4), transparent);
}
.record-first {
  border-color: rgba(212,164,76,0.4);
  box-shadow: 0 0 30px rgba(212,164,76,0.1);
}
.record-first::before {
  height: 4px;
  background: linear-gradient(90deg, transparent, #d4a44c, transparent);
}

/* Rank */
.record-rank {
  position: absolute;
  top: 12px; right: 16px;
  font-size: 22px;
}
.rank-normal {
  font-size: 14px;
  color: #8b7355;
  font-weight: 700;
}

/* Revived user */
.record-revived {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.revived-portrait {
  position: relative;
  width: 56px; height: 56px;
  flex-shrink: 0;
}
.portrait-first .revived-aura {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid rgba(212,164,76,0.3);
  animation: pulse-aura 2s ease-in-out infinite;
}
@keyframes pulse-aura {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.08); }
}
.revived-img {
  width: 56px; height: 56px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(212,164,76,0.3);
}
.revived-fb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px; height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #8b6914);
  color: #fff;
  font-size: 22px;
  font-weight: 800;
}
.revived-info { flex: 1; }
.revived-name {
  font-family: 'Cinzel', serif;
  font-size: 17px;
  font-weight: 700;
  color: #e8d5b7;
}
.revived-label {
  font-size: 12px;
  color: #d4a44c;
  font-weight: 600;
  margin-top: 2px;
}
.revived-date {
  font-size: 11px;
  color: #6b5a40;
  margin-top: 2px;
}

/* Rescuers */
.record-rescuers {
  margin-top: 4px;
}
.rescuers-label {
  font-size: 11px;
  color: #8b7355;
  font-weight: 700;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.rescuers-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.rescuer-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px 6px 6px;
  border-radius: 20px;
  background: rgba(212,164,76,0.08);
  border: 1px solid rgba(212,164,76,0.15);
  transition: all 0.2s;
}
.rescuer-chip:hover {
  border-color: rgba(212,164,76,0.3);
  background: rgba(212,164,76,0.12);
}
.rescuer-img {
  width: 28px; height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(212,164,76,0.2);
}
.rescuer-fb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b3a1e, #4a2e15);
  color: #d4a44c;
  font-size: 12px;
  font-weight: 800;
}
.rescuer-name {
  font-size: 13px;
  font-weight: 600;
  color: #c4a97d;
}

/* Gold */
.record-gold {
  margin-top: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #f1c40f;
  text-align: right;
}

/* Back button */
.back-btn {
  display: block;
  text-align: center;
  margin-top: 28px;
  padding: 12px;
  color: #8b7355;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid rgba(212,164,76,0.15);
  border-radius: 10px;
  transition: all 0.2s;
}
.back-btn:hover {
  border-color: rgba(212,164,76,0.3);
  color: #d4a44c;
}
</style>
