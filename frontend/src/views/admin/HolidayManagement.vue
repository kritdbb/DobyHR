<template>
  <div class="admin-page">
    <h1 class="page-title">🎌 Holiday Calendar</h1>
    <p class="page-sub">จัดการวันหยุดราชการ — วันหยุดจะไม่ถูกหักแต้ม</p>

    <!-- Add Holiday -->
    <div class="add-section">
      <div class="add-row">
        <input type="date" v-model="newDate" class="input-field date-input" />
        <input type="text" v-model="newName" placeholder="ชื่อวันหยุด เช่น วันสงกรานต์" class="input-field name-input" />
        <button @click="addHoliday" :disabled="!newDate || !newName || adding" class="btn-add">
          {{ adding ? '...' : '+ เพิ่มวันหยุด' }}
        </button>
      </div>
    </div>

    <!-- Year Filter -->
    <div class="year-row">
      <button @click="changeYear(-1)" class="year-btn">‹</button>
      <span class="year-label">{{ year }}</span>
      <button @click="changeYear(1)" class="year-btn">›</button>
    </div>

    <!-- Holiday List -->
    <div v-if="loading" class="loading-state">⏳ Loading...</div>
    <div v-else-if="holidays.length === 0" class="empty-state">
      <div class="empty-icon">🎌</div>
      <p class="empty-text">ยังไม่มีวันหยุดในปี {{ year }}</p>
    </div>
    <div v-else class="holiday-list">
      <div v-for="h in holidays" :key="h.id" class="holiday-card">
        <div class="holiday-info">
          <div class="holiday-date">📅 {{ formatDate(h.date) }}</div>
          <div class="holiday-name">{{ h.name }}</div>
        </div>
        <button @click="deleteHoliday(h.id, h.name)" class="btn-delete" title="ลบวันหยุด">🗑️</button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../services/api'

export default {
  name: 'HolidayManagement',
  inject: ['showToast'],
  data() {
    return {
      holidays: [],
      loading: true,
      adding: false,
      newDate: '',
      newName: '',
      year: new Date().getFullYear(),
    }
  },
  async mounted() {
    await this.loadHolidays()
  },
  methods: {
    async loadHolidays() {
      this.loading = true
      try {
        const { data } = await api.get(`/api/holidays?year=${this.year}`)
        this.holidays = data
      } catch (e) {
        console.error(e)
        this.holidays = []
      } finally {
        this.loading = false
      }
    },
    async addHoliday() {
      if (!this.newDate || !this.newName) return
      this.adding = true
      try {
        await api.post('/api/holidays', { date: this.newDate, name: this.newName })
        this.showToast(`เพิ่มวันหยุด "${this.newName}" สำเร็จ 🎌`)
        this.newDate = ''
        this.newName = ''
        await this.loadHolidays()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'เพิ่มไม่สำเร็จ', 'error')
      } finally {
        this.adding = false
      }
    },
    async deleteHoliday(id, name) {
      if (!confirm(`ลบวันหยุด "${name}" ?`)) return
      try {
        await api.delete(`/api/holidays/${id}`)
        this.showToast(`ลบวันหยุด "${name}" แล้ว`)
        await this.loadHolidays()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'ลบไม่สำเร็จ', 'error')
      }
    },
    changeYear(delta) {
      this.year += delta
      this.loadHolidays()
    },
    formatDate(d) {
      if (!d) return ''
      const dt = new Date(d + 'T00:00:00')
      return dt.toLocaleDateString('th-TH', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' })
    },
  },
}
</script>

<style scoped>
.admin-page { max-width: 700px; margin: 0 auto; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; margin-bottom: 24px; font-style: italic; }

/* Add Section */
.add-section {
  background: rgba(44,24,16,0.6);
  border: 2px solid rgba(212,164,76,0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}
.add-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.input-field {
  padding: 10px 14px; border-radius: 8px;
  border: 1px solid rgba(212,164,76,0.25);
  background: rgba(0,0,0,0.3); color: #e8d5b7;
  font-size: 14px; font-weight: 600;
}
.input-field::placeholder { color: #8b7355; }
.date-input { width: 170px; }
.name-input { flex: 1; min-width: 180px; }
.btn-add {
  padding: 10px 20px; border-radius: 8px;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; font-weight: 700; font-size: 14px;
  border: none; cursor: pointer; white-space: nowrap;
  transition: all 0.2s;
}
.btn-add:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(212,164,76,0.3); }
.btn-add:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* Year Filter */
.year-row {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; margin-bottom: 16px;
}
.year-btn {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(212,164,76,0.1); border: 1px solid rgba(212,164,76,0.2);
  color: #d4a44c; font-size: 18px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.year-btn:hover { background: rgba(212,164,76,0.2); }
.year-label { font-size: 20px; font-weight: 800; color: #d4a44c; font-family: 'Cinzel', serif; }

/* Holiday List */
.holiday-list { display: flex; flex-direction: column; gap: 8px; }
.holiday-card {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(44,24,16,0.5);
  border: 1px solid rgba(212,164,76,0.15);
  border-left: 4px solid #d4a44c;
  border-radius: 10px; padding: 14px 16px;
  transition: all 0.2s;
}
.holiday-card:hover { border-color: rgba(212,164,76,0.3); background: rgba(44,24,16,0.7); }
.holiday-info { flex: 1; }
.holiday-date { font-size: 13px; color: #d4a44c; font-weight: 700; margin-bottom: 2px; }
.holiday-name { font-size: 15px; color: #e8d5b7; font-weight: 600; }
.btn-delete {
  width: 36px; height: 36px; border-radius: 8px;
  background: rgba(231,76,60,0.1); border: 1px solid rgba(231,76,60,0.2);
  font-size: 16px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.btn-delete:hover { background: rgba(231,76,60,0.2); border-color: rgba(231,76,60,0.4); }

/* Empty / Loading */
.empty-state {
  padding: 40px 16px; text-align: center; border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 40px; margin-bottom: 10px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }
.loading-state { text-align: center; padding: 48px 0; color: #8b7355; font-weight: 600; }
</style>
