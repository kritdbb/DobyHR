<template>
  <div>
    <div class="page-header">
      <div>
        <h2>💰 Expense Management</h2>
        <p>Review, confirm, and manage expense requests</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button :class="['tab', activeTab === 'pending' ? 'active' : '']" @click="activeTab = 'pending'; loadData()">
        📋 Pending / All Approved
      </button>
      <button :class="['tab', activeTab === 'confirmed' ? 'active' : '']" @click="activeTab = 'confirmed'; loadData()">
        ✅ Confirmed
      </button>
      <button :class="['tab', activeTab === 'rejected' ? 'active' : '']" @click="activeTab = 'rejected'; loadData()">
        ❌ Rejected
      </button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else class="card" style="overflow: visible;">
      <table>
        <thead>
          <tr>
            <th>Adventurer</th>
            <th>Type</th>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Files</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="expenses.length === 0">
            <td colspan="8" style="text-align: center; color: #8b7355; padding: 24px;">No records found</td>
          </tr>
          <tr v-for="exp in expenses" :key="exp.id">
            <td>{{ exp.user_name }}</td>
            <td>
              <span class="type-badge" :class="exp.expense_type.toLowerCase()">
                {{ exp.expense_type === 'GENERAL' ? '📄' : exp.expense_type === 'CENTER' ? '🏢' : '🚗' }} {{ exp.expense_type }}
              </span>
            </td>
            <td>{{ exp.expense_type === 'TRAVEL' ? exp.travel_date : exp.expense_date }}</td>
            <td>
              <template v-if="editingId === exp.id">
                <input v-model="editForm.description" class="form-input" style="width: 100%; font-size: 12px;" />
              </template>
              <template v-else>
                {{ exp.description || (exp.expense_type === 'TRAVEL' ? `${exp.vehicle_type} ${exp.km_outbound}+${exp.km_return}km` : '-') }}
              </template>
            </td>
            <td>
              <template v-if="editingId === exp.id">
                <input v-model.number="editForm.amount" type="number" class="form-input" style="width: 80px; font-size: 12px;" />
              </template>
              <template v-else>
                ฿{{ (exp.expense_type === 'TRAVEL' ? exp.total_amount : exp.amount).toLocaleString() }}
              </template>
            </td>
            <td>
              <span class="status-badge" :class="exp.status.toLowerCase()">
                <template v-if="exp.status === 'PENDING'">{{ exp.current_step }}/{{ exp.total_steps }}</template>
                <template v-else>{{ exp.status }}</template>
              </span>
            </td>
            <td>
              <div class="file-thumbs">
                <div v-if="exp.file_path" class="thumb" @click="openViewer(exp.file_path)">
                  <img v-if="!isPdf(exp.file_path)" :src="apiBase + exp.file_path" />
                  <span v-else class="pdf-icon">PDF</span>
                </div>
                <div v-if="exp.outbound_image" class="thumb" @click="openViewer(exp.outbound_image)">
                  <img :src="apiBase + exp.outbound_image" />
                </div>
                <div v-if="exp.return_image" class="thumb" @click="openViewer(exp.return_image)">
                  <img :src="apiBase + exp.return_image" />
                </div>
                <div v-for="att in exp.attachments" :key="att.id" class="thumb" @click="openViewer(att.file_path)">
                  <img :src="apiBase + att.file_path" />
                </div>
              </div>
            </td>
            <td>
              <template v-if="exp.status === 'ALL_APPROVED'">
                <div class="action-btns">
                  <button v-if="editingId !== exp.id" class="btn btn-sm btn-outline" @click="startEdit(exp)">✏️ Edit</button>
                  <button v-if="editingId === exp.id" class="btn btn-sm btn-primary" @click="saveAndConfirm(exp.id)">💾 Save & Confirm</button>
                  <button v-if="editingId === exp.id" class="btn btn-sm btn-outline" @click="editingId = null">Cancel</button>
                  <button v-if="editingId !== exp.id" class="btn btn-sm btn-success" @click="doConfirm(exp.id)">✅ Confirm</button>
                  <button class="btn btn-sm btn-danger" @click="doReject(exp.id)">❌ Reject</button>
                </div>
              </template>
              <template v-else-if="exp.status === 'PENDING'">
                <span style="color: #e67e22; font-size: 12px; font-weight: 700;">Awaiting approval</span>
              </template>
              <template v-else>
                <span style="color: #8b7355; font-size: 12px;">—</span>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Fullscreen Viewer -->
    <div v-if="viewerOpen" class="viewer-overlay" @click="viewerOpen = false">
      <button class="viewer-close" @click="viewerOpen = false">✕</button>
      <div class="viewer-content" @click.stop>
        <img v-if="!isPdf(viewerSrc)" :src="apiBase + viewerSrc" class="viewer-img" />
        <iframe v-else :src="apiBase + viewerSrc" class="viewer-pdf"></iframe>
      </div>
    </div>
  </div>
</template>

<script>
import { getAllExpenses, confirmExpense, adminRejectExpense } from '../../services/api'

export default {
  name: 'ExpenseManagement',
  data() {
    return {
      activeTab: 'pending',
      loading: true,
      expenses: [],
      editingId: null,
      editForm: { amount: 0, description: '', other_cost: 0 },
      viewerOpen: false,
      viewerSrc: '',
      apiBase: import.meta.env.VITE_API_URL || '',
    }
  },
  async mounted() { await this.loadData() },
  methods: {
    async loadData() {
      this.loading = true
      try {
        let statusFilter = null
        if (this.activeTab === 'confirmed') statusFilter = 'CONFIRMED'
        else if (this.activeTab === 'rejected') statusFilter = 'REJECTED'

        const res = await getAllExpenses(statusFilter)
        let data = res.data || []
        // For pending tab, show PENDING + ALL_APPROVED
        if (this.activeTab === 'pending') {
          data = data.filter(e => e.status === 'PENDING' || e.status === 'ALL_APPROVED')
        }
        this.expenses = data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    startEdit(exp) {
      this.editingId = exp.id
      this.editForm = {
        amount: exp.expense_type === 'TRAVEL' ? exp.total_amount : exp.amount,
        description: exp.description || '',
        other_cost: exp.other_cost || 0,
      }
    },
    async saveAndConfirm(id) {
      try {
        await confirmExpense(id, this.editForm)
        this.editingId = null
        await this.loadData()
      } catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },
    async doConfirm(id) {
      try {
        await confirmExpense(id, null)
        await this.loadData()
      } catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },
    async doReject(id) {
      try {
        await adminRejectExpense(id)
        await this.loadData()
      } catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },
    openViewer(src) { this.viewerSrc = src; this.viewerOpen = true },
    isPdf(path) { return path && path.toLowerCase().endsWith('.pdf') },
  },
}
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h2 { font-family: 'Cinzel', serif; color: #d4a44c; margin: 0 0 4px; }
.page-header p { color: #8b7355; margin: 0; font-size: 14px; }

.tab-bar { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 700;
  border: 1px solid rgba(212,164,76,0.2); background: rgba(26,26,46,0.4);
  color: #8b7355; cursor: pointer; transition: all 0.2s;
}
.tab.active { background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208; border-color: #d4a44c; }

table { width: 100%; border-collapse: collapse; }
th { text-align: left; font-size: 12px; color: #d4a44c; padding: 10px 12px; border-bottom: 1px solid rgba(212,164,76,0.15); }
td { padding: 10px 12px; font-size: 13px; color: #e8d5b7; border-bottom: 1px solid rgba(212,164,76,0.08); vertical-align: middle; }

.type-badge { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 6px; white-space: nowrap; }
.type-badge.general { background: rgba(52,152,219,0.15); color: #3498db; }
.type-badge.travel { background: rgba(46,204,113,0.15); color: #2ecc71; }
.type-badge.center { background: rgba(155,89,182,0.15); color: #9b59b6; }

.status-badge {
  font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; white-space: nowrap;
}
.status-badge.pending { background: rgba(230,126,34,0.2); color: #e67e22; }
.status-badge.all_approved { background: rgba(46,204,113,0.2); color: #2ecc71; }
.status-badge.confirmed { background: rgba(52,152,219,0.2); color: #3498db; }
.status-badge.rejected { background: rgba(192,57,43,0.2); color: #c0392b; }

.file-thumbs { display: flex; gap: 4px; flex-wrap: wrap; }
.thumb { width: 40px; height: 40px; border-radius: 4px; overflow: hidden; cursor: pointer; border: 1px solid rgba(212,164,76,0.2); }
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.pdf-icon { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: rgba(212,164,76,0.1); font-size: 9px; font-weight: 800; color: #d4a44c; }

.action-btns { display: flex; gap: 4px; flex-wrap: wrap; }
.btn-sm { padding: 5px 10px; font-size: 11px; border-radius: 6px; }
.btn-success { background: #27ae60; color: #fff; border: none; cursor: pointer; }
.btn-danger { background: rgba(192,57,43,0.2); color: #c0392b; border: 1px solid rgba(192,57,43,0.3); cursor: pointer; }

/* Viewer */
.viewer-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.92); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.viewer-close { position: absolute; top: 16px; right: 16px; background: rgba(255,255,255,0.2); border: none; color: #fff; font-size: 20px; width: 36px; height: 36px; border-radius: 50%; cursor: pointer; z-index: 10000; }
.viewer-content { max-width: 90vw; max-height: 90vh; overflow: auto; }
.viewer-img { max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; }
.viewer-pdf { width: 90vw; height: 90vh; border: none; border-radius: 8px; }
</style>
