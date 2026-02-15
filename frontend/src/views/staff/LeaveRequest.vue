<template>
  <div class="staff-page">
    <h1 class="page-title">📋 Leave Request</h1>
    
    <!-- Quota Cards -->
    <div class="quota-grid">
      <div v-if="quota.sick" class="quota-card" style="background-image: url('/icons/leave_sick.png')">
        <div class="quota-type">sick</div>
        <div class="quota-value">{{ quota.sick.total - quota.sick.used }}</div>
        <div class="quota-label">remaining</div>
      </div>
      <div v-if="quota.business" class="quota-card" style="background-image: url('/icons/leave_business.png')">
        <div class="quota-type">business</div>
        <div class="quota-value">{{ quota.business.total - quota.business.used }}</div>
        <div class="quota-label">remaining</div>
      </div>
      <div v-if="quota.vacation" class="quota-card" style="background-image: url('/icons/leave_vacation.png')">
        <div class="quota-type">vacation</div>
        <div class="quota-value">{{ quota.vacation.total - quota.vacation.used }}</div>
        <div class="quota-label">remaining</div>
      </div>
    </div>

    <!-- New Request Button -->
    <button @click="showModal = true" class="new-request-btn">
      📜 New Request
    </button>
    
    <!-- History -->
    <div class="section chronicles-section">
      <h2 class="section-title">📋 Chronicles</h2>
      <div v-if="history.length === 0" class="empty-state">
        <div class="empty-icon">🏨</div>
        <p class="empty-text">No rest history found</p>
      </div>
      <div v-else class="history-list">
        <div v-for="req in history" :key="req.id"
          class="history-card"
          :class="{
            'history-card--pending': req.status === 'pending',
            'history-card--approved': req.status === 'approved',
            'history-card--rejected': req.status === 'rejected'
          }">
          <div class="history-top">
            <div>
              <div class="history-type">{{ req.leave_type }}</div>
              <div class="history-dates">{{ formatDate(req.start_date) }} - {{ formatDate(req.end_date) }}</div>
            </div>
            <span :class="['status-pill', 'status-pill--' + req.status]">{{ req.status }}</span>
          </div>
          <p class="history-reason" v-if="req.reason">{{ req.reason }}</p>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h2 class="modal-title">📜 Request Rest</h2>
          <button @click="showModal = false" class="modal-close">✕</button>
        </div>
        
        <form @submit.prevent="submitRequest" class="modal-form">
          <div class="form-group">
            <label class="form-label">Type</label>
            <select v-model="form.leave_type" class="form-input">
              <option value="sick">🤒 Sick Rest</option>
              <option value="business">💼 Guild Business</option>
              <option value="vacation">🌴 Vacation</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Start Date</label>
              <input v-model="form.start_date" type="date" required class="form-input">
            </div>
            <div class="form-group">
              <label class="form-label">End Date</label>
              <input v-model="form.end_date" type="date" required class="form-input">
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Reason</label>
            <textarea v-model="form.reason" rows="3" class="form-input form-textarea" placeholder="Optional reason..."></textarea>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="showModal = false" class="modal-btn modal-btn--cancel">Cancel</button>
            <button type="submit" class="modal-btn modal-btn--submit" :disabled="submitting">
              {{ submitting ? '⏳ Submitting...' : '📜 Submit' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { getLeaveQuota, getMyLeaves, requestLeave } from '../../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      quota: {},
      history: [],
      showModal: false,
      submitting: false,
      form: { leave_type: 'sick', start_date: '', end_date: '', reason: '' }
    }
  },
  async mounted() { this.refreshData() },
  methods: {
    async refreshData() {
      try {
        const [qRes, hRes] = await Promise.all([getLeaveQuota(), getMyLeaves()])
        this.quota = qRes.data
        this.history = hRes.data
      } catch (e) { console.error(e) }
    },
    async submitRequest() {
      this.submitting = true
      try {
        await requestLeave(this.form)
        this.showModal = false
        this.form = { leave_type: 'sick', start_date: '', end_date: '', reason: '' }
        this.showToast('Rest request submitted! ⚔️')
        await this.refreshData()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Error submitting request', 'error')
      } finally { this.submitting = false }
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-GB') : '' }
  }
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 20px;
}

/* Quota Grid */
.quota-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
.quota-card {
  padding: 14px 8px; border-radius: 10px; text-align: center;
  background-color: rgba(44,24,16,0.8);
  background-size: cover; background-position: center;
  border: 2px solid rgba(212,164,76,0.2);
  display: flex; flex-direction: column; justify-content: flex-end;
  min-height: 120px; overflow: hidden;
}
.quota-type { font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; color: #fff; font-weight: 800; margin-bottom: 4px; text-shadow: 0 1px 6px rgba(0,0,0,0.9); }
.quota-value { font-size: 28px; font-weight: 800; color: #fff; text-shadow: 0 2px 8px rgba(0,0,0,0.9); }
.quota-label { font-size: 10px; color: #fff; font-weight: 700; text-shadow: 0 1px 4px rgba(0,0,0,0.9); }

/* New Request */
.new-request-btn {
  width: 100%; padding: 14px 0; border-radius: 10px;
  font-family: 'Cinzel', serif;
  font-size: 15px; font-weight: 700; color: #1c1208;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  border: 2px solid #d4a44c;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(212,164,76,0.2);
  transition: all 0.15s;
  margin-bottom: 28px;
}
.new-request-btn:active { transform: scale(0.98); }

/* Section */
.section-title {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 800; color: #d4a44c; margin-bottom: 14px;
}
.chronicles-section {
  padding: 20px 16px; border-radius: 14px;
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.88)),
    url('/icons/leave_chronicles.png') center / cover no-repeat;
  border: 2px solid rgba(212,164,76,0.2);
}

/* History */
.history-list { display: flex; flex-direction: column; gap: 10px; }
.history-card {
  padding: 14px 16px; border-radius: 10px; border-left: 4px solid;
  background: rgba(26,26,46,0.6);
  backdrop-filter: blur(4px);
  border-color: rgba(212,164,76,0.2);
}
.history-card--pending { border-color: #d4a44c; }
.history-card--approved { border-color: #27ae60; }
.history-card--rejected { border-color: #c0392b; }
.history-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
.history-type { font-weight: 700; font-size: 14px; color: #e8d5b7; text-transform: capitalize; }
.history-dates { font-size: 12px; color: #8b7355; font-family: monospace; }
.history-reason { font-size: 13px; color: #8b7355; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.status-pill {
  padding: 2px 12px; border-radius: 6px;
  font-size: 10px; font-weight: 800; text-transform: uppercase;
  border: 1px solid;
}
.status-pill--pending { background: rgba(212,164,76,0.1); color: #d4a44c; border-color: rgba(212,164,76,0.3); }
.status-pill--approved { background: rgba(39,174,96,0.1); color: #27ae60; border-color: rgba(39,174,96,0.3); }
.status-pill--rejected { background: rgba(192,57,43,0.1); color: #e74c3c; border-color: rgba(192,57,43,0.3); }

/* Empty */
.empty-state {
  text-align: center; padding: 36px 16px; border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  display: flex; align-items: flex-end; justify-content: center;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(6px);
  padding: 0;
}
@media (min-width: 640px) {
  .modal-overlay { align-items: center; padding: 24px; }
}
.modal-card {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 2px solid #d4a44c;
  width: 100%; max-width: 420px;
  border-radius: 16px 16px 0 0; padding: 28px 24px;
  box-shadow: 0 -8px 32px rgba(0,0,0,0.3);
  animation: slideUp 0.3s ease-out;
}
@media (min-width: 640px) {
  .modal-card { border-radius: 16px; animation: none; }
}
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.modal-title { font-family: 'Cinzel', serif; font-size: 20px; font-weight: 800; color: #d4a44c; }
.modal-close {
  font-size: 18px; font-weight: 700; color: #8b7355;
  background: none; border: none; cursor: pointer; padding: 4px 8px;
}

.modal-form { display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; }
.form-label { font-size: 11px; font-weight: 800; text-transform: uppercase; color: #d4a44c; margin-bottom: 6px; }
.form-input {
  width: 100%; height: 46px; padding: 0 14px;
  border-radius: 8px; border: 2px solid rgba(212,164,76,0.2);
  font-size: 14px; font-weight: 500; color: #e8d5b7;
  background: rgba(26,26,46,0.8); outline: none;
  transition: border-color 0.2s; box-sizing: border-box;
}
.form-input:focus { border-color: #d4a44c; }
.form-textarea { height: auto; padding: 12px 14px; resize: none; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-input option { background: #1a1a2e; color: #e8d5b7; }

.modal-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }
.modal-btn {
  padding: 13px 0; border-radius: 8px; font-weight: 700;
  font-size: 14px; border: 2px solid transparent; cursor: pointer; transition: all 0.15s;
}
.modal-btn:active { transform: scale(0.97); }
.modal-btn--cancel { color: #8b7355; background: transparent; border-color: rgba(139,115,85,0.2); }
.modal-btn--submit {
  color: #1c1208;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  border-color: #d4a44c;
  box-shadow: 0 4px 16px rgba(212,164,76,0.2);
}
.modal-btn--submit:disabled { opacity: 0.6; cursor: not-allowed; }

@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
</style>
