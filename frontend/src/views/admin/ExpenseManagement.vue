<template>
  <div>
    <div class="page-header">
      <div>
        <h2>💰 Expense Management</h2>
        <p>Review, confirm, and manage expense requests</p>
      </div>
    </div>

    <!-- View Toggle -->
    <div class="tab-bar">
      <button :class="['tab', viewMode === 'manage' ? 'active' : '']" @click="viewMode = 'manage'; loadData()">
        📋 Manage
      </button>
      <button :class="['tab', viewMode === 'report' ? 'active' : '']" @click="viewMode = 'report'; loadReport()">
        📊 Report
      </button>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- MANAGE VIEW (original table style)     -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="viewMode === 'manage'">
      <div class="tab-bar sub-tabs">
        <button :class="['tab', activeTab === 'pending' ? 'active' : '']" @click="activeTab = 'pending'; loadData()">
          📋 Pending / Approved
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
              <th>Adventurer</th><th>Type</th><th>Date</th><th>Description</th><th>Amount</th><th>Status</th><th>Files</th><th>Action</th>
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
                  <div v-if="exp.outbound_image" class="thumb" @click="openViewer(exp.outbound_image)"><img :src="apiBase + exp.outbound_image" /></div>
                  <div v-if="exp.return_image" class="thumb" @click="openViewer(exp.return_image)"><img :src="apiBase + exp.return_image" /></div>
                  <div v-for="att in exp.attachments" :key="att.id" class="thumb" @click="openViewer(att.file_path)"><img :src="apiBase + att.file_path" /></div>
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
    </template>

    <!-- ═══════════════════════════════════════ -->
    <!-- REPORT VIEW (per-user cards)           -->
    <!-- ═══════════════════════════════════════ -->
    <template v-if="viewMode === 'report'">
      <!-- Date Filter -->
      <div class="report-filter">
        <div class="filter-group">
          <label>📅 From</label>
          <input v-model="filterFrom" type="date" class="form-input" @change="loadReport" />
        </div>
        <div class="filter-group">
          <label>📅 To</label>
          <input v-model="filterTo" type="date" class="form-input" @change="loadReport" />
        </div>
      </div>

      <div v-if="reportLoading" class="loading">Loading...</div>

      <template v-else>
        <!-- Grand Total Banner -->
        <div class="grand-total-banner">
          <div class="gt-title">📊 Company Expense Summary</div>
          <div class="gt-row">
            <div class="gt-item">
              <span class="gt-label">📄 General</span>
              <span class="gt-val general">฿{{ grandTotal.general.toLocaleString() }}</span>
            </div>
            <div class="gt-item">
              <span class="gt-label">🚗 Travel</span>
              <span class="gt-val travel">฿{{ grandTotal.travel.toLocaleString() }}</span>
            </div>
            <div class="gt-item">
              <span class="gt-label">🏢 Center</span>
              <span class="gt-val center">฿{{ grandTotal.center.toLocaleString() }}</span>
            </div>
            <div class="gt-sep"></div>
            <div class="gt-item">
              <span class="gt-label">💰 Grand Total</span>
              <span class="gt-val total">฿{{ grandTotal.all.toLocaleString() }}</span>
            </div>
          </div>
        </div>

        <!-- Per-user cards -->
        <div v-if="userCards.length === 0" class="empty-state">
          <p>No expense records found for this period.</p>
        </div>

        <div v-for="uc in userCards" :key="uc.user_id" class="user-card">
          <div class="uc-header" @click="uc.expanded = !uc.expanded">
            <div class="uc-user">
              <div class="uc-avatar">
                <img v-if="uc.image" :src="uc.image" />
                <span v-else>{{ (uc.name || '?').charAt(0) }}</span>
              </div>
              <div class="uc-info">
                <div class="uc-name">{{ uc.name }}</div>
                <div class="uc-count">{{ uc.items.length }} items</div>
              </div>
            </div>
            <div class="uc-summary">
              <span v-if="uc.generalTotal > 0" class="uc-stat general">📄 ฿{{ uc.generalTotal.toLocaleString() }}</span>
              <span v-if="uc.travelTotal > 0" class="uc-stat travel">🚗 ฿{{ uc.travelTotal.toLocaleString() }}</span>
              <span v-if="uc.centerTotal > 0" class="uc-stat center">🏢 ฿{{ uc.centerTotal.toLocaleString() }}</span>
              <span class="uc-stat total">💰 ฿{{ uc.total.toLocaleString() }}</span>
            </div>
            <span class="uc-chevron" :class="{ open: uc.expanded }">▾</span>
          </div>
          <div v-if="uc.expanded" class="uc-body">
            <table class="uc-table">
              <thead>
                <tr>
                  <th>Type</th><th>Date</th><th>Description</th><th>Amount</th><th>Status</th><th>Files</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="exp in uc.items" :key="exp.id">
                  <td>
                    <span class="type-badge" :class="exp.expense_type.toLowerCase()">
                      {{ exp.expense_type === 'GENERAL' ? '📄' : exp.expense_type === 'CENTER' ? '🏢' : '🚗' }} {{ exp.expense_type }}
                    </span>
                  </td>
                  <td>{{ exp.expense_type === 'TRAVEL' ? exp.travel_date : exp.expense_date }}</td>
                  <td>{{ exp.description || (exp.expense_type === 'TRAVEL' ? `${exp.vehicle_type} ${exp.km_outbound}+${exp.km_return}km` : '-') }}</td>
                  <td>฿{{ getExpAmount(exp).toLocaleString() }}</td>
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
                      <div v-if="exp.outbound_image" class="thumb" @click="openViewer(exp.outbound_image)"><img :src="apiBase + exp.outbound_image" /></div>
                      <div v-if="exp.return_image" class="thumb" @click="openViewer(exp.return_image)"><img :src="apiBase + exp.return_image" /></div>
                      <div v-for="att in exp.attachments" :key="att.id" class="thumb" @click="openViewer(att.file_path)"><img :src="apiBase + att.file_path" /></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </template>

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
      viewMode: 'manage',
      // Manage view
      activeTab: 'pending',
      loading: true,
      expenses: [],
      editingId: null,
      editForm: { amount: 0, description: '', other_cost: 0 },
      // Report view
      reportLoading: false,
      filterFrom: '',
      filterTo: '',
      allExpenses: [],
      userCards: [],
      grandTotal: { general: 0, travel: 0, center: 0, all: 0 },
      // Shared
      viewerOpen: false,
      viewerSrc: '',
      apiBase: import.meta.env.VITE_API_URL || '',
    }
  },
  async mounted() {
    // Default date filter: start of current month to today
    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    this.filterFrom = `${y}-${m}-01`
    this.filterTo = now.toISOString().slice(0, 10)
    await this.loadData()
  },
  methods: {
    // ── Manage View ──
    async loadData() {
      this.loading = true
      try {
        let statusFilter = null
        if (this.activeTab === 'confirmed') statusFilter = 'CONFIRMED'
        else if (this.activeTab === 'rejected') statusFilter = 'REJECTED'
        const res = await getAllExpenses(statusFilter)
        let data = res.data || []
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
      try { await confirmExpense(id, this.editForm); this.editingId = null; await this.loadData() }
      catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },
    async doConfirm(id) {
      try { await confirmExpense(id, null); await this.loadData() }
      catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },
    async doReject(id) {
      try { await adminRejectExpense(id); await this.loadData() }
      catch (e) { alert(e.response?.data?.detail || 'Failed') }
    },

    // ── Report View ──
    async loadReport() {
      this.reportLoading = true
      try {
        const res = await getAllExpenses()
        let data = res.data || []

        // Filter out REJECTED
        data = data.filter(e => e.status !== 'REJECTED')

        // Date filter
        if (this.filterFrom) {
          data = data.filter(e => {
            const d = e.expense_type === 'TRAVEL' ? e.travel_date : e.expense_date
            return d && d >= this.filterFrom
          })
        }
        if (this.filterTo) {
          data = data.filter(e => {
            const d = e.expense_type === 'TRAVEL' ? e.travel_date : e.expense_date
            return d && d <= this.filterTo
          })
        }

        // Group by user
        const groups = {}
        for (const exp of data) {
          const key = exp.user_id
          if (!groups[key]) {
            groups[key] = {
              user_id: exp.user_id,
              name: exp.user_name,
              image: null,
              items: [],
              generalTotal: 0,
              travelTotal: 0,
              centerTotal: 0,
              total: 0,
              expanded: false,
            }
          }
          groups[key].items.push(exp)
          const amt = this.getExpAmount(exp)
          if (exp.expense_type === 'GENERAL') groups[key].generalTotal += amt
          else if (exp.expense_type === 'TRAVEL') groups[key].travelTotal += amt
          else if (exp.expense_type === 'CENTER') groups[key].centerTotal += amt
          groups[key].total += amt
        }

        // Sort by total descending
        this.userCards = Object.values(groups).sort((a, b) => b.total - a.total)

        // Grand totals
        this.grandTotal = {
          general: this.userCards.reduce((s, u) => s + u.generalTotal, 0),
          travel: this.userCards.reduce((s, u) => s + u.travelTotal, 0),
          center: this.userCards.reduce((s, u) => s + u.centerTotal, 0),
          all: this.userCards.reduce((s, u) => s + u.total, 0),
        }
      } catch (e) { console.error(e) }
      finally { this.reportLoading = false }
    },

    getExpAmount(exp) {
      return exp.expense_type === 'TRAVEL' ? (exp.total_amount || 0) : (exp.amount || 0)
    },

    // ── Shared ──
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
.sub-tabs { margin-bottom: 16px; }
.tab {
  padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 700;
  border: 1px solid rgba(212,164,76,0.2); background: rgba(26,26,46,0.4);
  color: #8b7355; cursor: pointer; transition: all 0.2s;
}
.tab.active { background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208; border-color: #d4a44c; }

/* ── Table (Manage View) ── */
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

/* ── Report View ── */
.report-filter {
  display: flex; gap: 12px; margin-bottom: 20px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(17,10,30,0.6), rgba(30,14,10,0.4));
  border: 1px solid rgba(212,164,76,0.12);
  border-radius: 12px;
  align-items: flex-end;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 11px; font-weight: 700; color: #8b7355; }
.filter-group .form-input { font-size: 13px; padding: 8px 12px; }

/* Grand Total Banner */
.grand-total-banner {
  background: linear-gradient(135deg, rgba(17,10,30,0.7), rgba(30,14,10,0.5));
  border: 1px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 18px 22px;
  margin-bottom: 20px;
}
.gt-title {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 700; color: #d4a44c;
  margin-bottom: 14px;
}
.gt-row {
  display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
}
.gt-item { display: flex; flex-direction: column; gap: 2px; }
.gt-label { font-size: 11px; font-weight: 600; color: #8b7355; }
.gt-val { font-size: 18px; font-weight: 800; }
.gt-val.general { color: #3498db; }
.gt-val.travel { color: #2ecc71; }
.gt-val.center { color: #9b59b6; }
.gt-val.total { color: #d4a44c; }
.gt-sep {
  width: 1px; height: 36px;
  background: rgba(212,164,76,0.2);
}

/* User Cards */
.user-card {
  background: linear-gradient(135deg, rgba(17,10,30,0.5), rgba(30,14,10,0.35));
  border: 1px solid rgba(212,164,76,0.1);
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.user-card:hover { border-color: rgba(212,164,76,0.25); }

.uc-header {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 18px;
  cursor: pointer;
  transition: background 0.15s;
}
.uc-header:hover { background: rgba(212,164,76,0.04); }

.uc-user { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.uc-avatar {
  width: 38px; height: 38px; border-radius: 50%; overflow: hidden; flex-shrink: 0;
  border: 2px solid rgba(212,164,76,0.2); background: rgba(212,164,76,0.1);
  display: flex; align-items: center; justify-content: center;
}
.uc-avatar img { width: 100%; height: 100%; object-fit: cover; }
.uc-avatar span { color: #d4a44c; font-weight: 800; font-size: 16px; }

.uc-name { font-size: 14px; font-weight: 700; color: #e8d5b7; }
.uc-count { font-size: 11px; color: #8b7355; }

.uc-summary { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.uc-stat { font-size: 12px; font-weight: 700; white-space: nowrap; }
.uc-stat.general { color: #3498db; }
.uc-stat.travel { color: #2ecc71; }
.uc-stat.center { color: #9b59b6; }
.uc-stat.total { color: #d4a44c; font-size: 14px; }

.uc-chevron {
  font-size: 16px; color: #8b7355;
  transition: transform 0.2s;
}
.uc-chevron.open { transform: rotate(180deg); }

.uc-body {
  border-top: 1px solid rgba(212,164,76,0.08);
  padding: 0 18px 14px;
}
.uc-table { margin-top: 10px; }
.uc-table th { font-size: 11px; padding: 8px 10px; }
.uc-table td { font-size: 12px; padding: 8px 10px; }

.empty-state {
  text-align: center; padding: 50px 20px;
  color: #8b7355; font-size: 14px;
}

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
