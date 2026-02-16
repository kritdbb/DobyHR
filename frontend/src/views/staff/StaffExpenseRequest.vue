<template>
  <div class="staff-page">
    <h1 class="page-title">💰 Expense Request</h1>
    <p class="page-sub">Submit your expense claims</p>

    <!-- Type Picker -->
    <div v-if="!selectedType" class="type-picker">
      <button class="type-card" :style="{ backgroundImage: 'url(/icons/generalexpense.png)' }" @click="selectedType = 'general'">
        <span class="type-label">General Expense</span>
        <span class="type-desc">Bills, receipts &amp; invoices</span>
      </button>
      <button class="type-card" :style="{ backgroundImage: 'url(/icons/travelexpense.png)' }" @click="selectedType = 'travel'">
        <span class="type-label">Travel Expense</span>
        <span class="type-desc">Mileage &amp; transport costs</span>
      </button>
      <button class="type-card" :style="{ backgroundImage: 'url(/icons/centerexpense.png)' }" @click="selectedType = 'center'">
        <span class="type-label">Center Expense</span>
        <span class="type-desc">Shared company costs</span>
      </button>
    </div>

    <!-- General Expense Form -->
    <div v-if="selectedType === 'general'" class="form-section">
      <button class="back-btn" @click="selectedType = null">← Back</button>
      <h2 class="section-title">📄 General Expense</h2>

      <div class="form-group">
        <label>Upload Receipt (Image or PDF)</label>
        <div class="file-drop" @click="$refs.generalFile.click()" @dragover.prevent @drop.prevent="onDropGeneral">
          <input ref="generalFile" type="file" accept="image/*,.pdf" style="display:none" @change="onGeneralFileChange" />
          <div v-if="!generalForm.file" class="drop-text">
            <span class="drop-icon">📎</span>
            <span>Tap or drag to upload</span>
          </div>
          <div v-else class="file-preview">
            <img v-if="generalForm.filePreview && !generalForm.isPdf" :src="generalForm.filePreview" class="preview-img" @click.stop="openPreview(generalForm.filePreview, 'image')" />
            <div v-else class="pdf-badge" @click.stop="openPreview(generalForm.file, 'pdf')">
              📄 {{ generalForm.file.name }}
              <span class="preview-hint">tap to preview</span>
            </div>
            <button class="remove-btn" @click.stop="removeGeneralFile">✕</button>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label>Expense Date</label>
        <input v-model="generalForm.date" type="date" class="form-input" />
      </div>

      <div class="form-group">
        <label>Description</label>
        <input v-model="generalForm.description" type="text" class="form-input" placeholder="What is this expense for?" />
      </div>

      <div class="form-group">
        <label>Amount (฿)</label>
        <input v-model.number="generalForm.amount" type="number" class="form-input" placeholder="0.00" />
      </div>

      <button class="submit-btn" :disabled="submitting || !canSubmitGeneral" @click="submitGeneral">
        {{ submitting ? 'Submitting...' : '📤 Submit Request' }}
      </button>
    </div>

    <!-- Center Expense Form (same layout as general) -->
    <div v-if="selectedType === 'center'" class="form-section">
      <button class="back-btn" @click="selectedType = null">← Back</button>
      <h2 class="section-title">🏢 Center Expense</h2>
      <div class="center-notice">ℹ️ ค่าใช้จ่ายส่วนกลาง — ไม่ต้องผ่านการอนุมัติ</div>

      <div class="form-group">
        <label>Date</label>
        <input v-model="centerForm.date" type="date" class="form-input" />
      </div>

      <div class="form-group">
        <label>📸 Receipt / Invoice</label>
        <div
          class="file-drop"
          @click="$refs.centerFile.click()"
          @dragover.prevent
          @drop.prevent="onDropCenter"
        >
          <template v-if="centerForm.file">
            <img v-if="!centerForm.isPdf" :src="centerForm.filePreview" class="file-preview" @click.stop="openPreview(centerForm.filePreview, 'image')" />
            <div v-else class="pdf-badge" @click.stop="openPreview(centerForm.file, 'pdf')">
              📎 {{ centerForm.file.name }}
              <span class="preview-hint">tap to preview</span>
            </div>
            <button class="remove-btn" @click.stop="removeCenterFile">✕</button>
          </template>
          <template v-else>
            <div class="drop-text">📤 Tap or drop file here</div>
          </template>
        </div>
        <input ref="centerFile" type="file" accept="image/*,.pdf" style="display:none" @change="onCenterFileChange" />
      </div>

      <div class="form-group">
        <label>Description</label>
        <input v-model="centerForm.description" type="text" class="form-input" placeholder="What is this expense for?" />
      </div>

      <div class="form-group">
        <label>Amount (฿)</label>
        <input v-model.number="centerForm.amount" type="number" class="form-input" placeholder="0.00" />
      </div>

      <button class="submit-btn" :disabled="submitting || !canSubmitCenter" @click="submitCenter">
        {{ submitting ? 'Submitting...' : '📤 Submit Center Expense' }}
      </button>
    </div>

    <!-- Travel Expense Form -->
    <div v-if="selectedType === 'travel'" class="form-section">
      <button class="back-btn" @click="selectedType = null">← Back</button>
      <h2 class="section-title">🚗 Travel Expense</h2>

      <div class="form-group">
        <label>Travel Date</label>
        <input v-model="travelForm.date" type="date" class="form-input" />
      </div>

      <div class="form-group">
        <label>Description</label>
        <input v-model="travelForm.description" type="text" class="form-input" placeholder="Where & why? e.g. ไปพบลูกค้า จ.ชลบุรี" />
      </div>

      <div class="form-group">
        <label>Vehicle Type</label>
        <div class="vehicle-picker">
          <button :class="['vehicle-btn', travelForm.vehicleType === 'CAR' ? 'active' : '']" @click="travelForm.vehicleType = 'CAR'">
            🚗 Car (฿10/km)
          </button>
          <button :class="['vehicle-btn', travelForm.vehicleType === 'MOTORCYCLE' ? 'active' : '']" @click="travelForm.vehicleType = 'MOTORCYCLE'">
            🏍️ Motorcycle (฿5/km)
          </button>
        </div>
      </div>

      <div class="two-col">
        <div class="form-group">
          <label>KM Outbound</label>
          <input v-model.number="travelForm.kmOut" type="number" class="form-input" placeholder="0" />
        </div>
        <div class="form-group">
          <label>KM Return</label>
          <input v-model.number="travelForm.kmReturn" type="number" class="form-input" placeholder="0" />
        </div>
      </div>

      <div class="cost-summary">
        <div class="cost-row"><span>Travel Cost</span><span>฿{{ travelCost.toLocaleString() }}</span></div>
      </div>

      <!-- Outbound / Return images -->
      <div class="two-col">
        <div class="form-group">
          <label>📸 Outbound Photo</label>
          <div class="file-drop small" @click="$refs.outImg.click()">
            <input ref="outImg" type="file" accept="image/*" style="display:none" @change="onOutboundImg" />
            <div v-if="!travelForm.outboundPreview" class="drop-text"><span>📎 Upload</span></div>
            <div v-else class="file-preview">
              <img :src="travelForm.outboundPreview" class="preview-img" @click.stop="openPreview(travelForm.outboundPreview, 'image')" />
              <button class="remove-btn" @click.stop="travelForm.outboundFile=null;travelForm.outboundPreview=null">✕</button>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label>📸 Return Photo</label>
          <div class="file-drop small" @click="$refs.retImg.click()">
            <input ref="retImg" type="file" accept="image/*" style="display:none" @change="onReturnImg" />
            <div v-if="!travelForm.returnPreview" class="drop-text"><span>📎 Upload</span></div>
            <div v-else class="file-preview">
              <img :src="travelForm.returnPreview" class="preview-img" @click.stop="openPreview(travelForm.returnPreview, 'image')" />
              <button class="remove-btn" @click.stop="travelForm.returnFile=null;travelForm.returnPreview=null">✕</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Other costs -->
      <h3 class="sub-title">Other Costs (Tolls, etc.)</h3>
      <div class="form-group">
        <label>Other Cost Amount (฿)</label>
        <input v-model.number="travelForm.otherCost" type="number" class="form-input" placeholder="0.00" />
      </div>
      <div class="form-group">
        <label>Upload Receipts (multiple)</label>
        <div class="file-drop" @click="$refs.otherFiles.click()">
          <input ref="otherFiles" type="file" accept="image/*,.pdf" multiple style="display:none" @change="onOtherFiles" />
          <div v-if="travelForm.otherFiles.length === 0" class="drop-text"><span class="drop-icon">📎</span><span>Tap to upload receipts</span></div>
          <div v-else class="multi-preview">
            <div v-for="(f, i) in travelForm.otherPreviews" :key="i" class="mini-thumb">
              <img :src="f" class="preview-img" @click.stop="openPreview(f, 'image')" />
              <button class="remove-btn mini" @click.stop="removeOtherFile(i)">✕</button>
            </div>
            <div class="add-more" @click.stop="$refs.otherFiles.click()">+</div>
          </div>
        </div>
      </div>

      <div class="cost-summary total">
        <div class="cost-row"><span>Travel Cost</span><span>฿{{ travelCost.toLocaleString() }}</span></div>
        <div class="cost-row"><span>Other Cost</span><span>฿{{ (travelForm.otherCost || 0).toLocaleString() }}</span></div>
        <div class="cost-row grand"><span>Grand Total</span><span>฿{{ grandTotal.toLocaleString() }}</span></div>
      </div>

      <button class="submit-btn" :disabled="submitting || !canSubmitTravel" @click="submitTravel">
        {{ submitting ? 'Submitting...' : '📤 Submit Request' }}
      </button>
    </div>

    <!-- My Expense History -->
    <div v-if="!selectedType" class="history-section">
      <h2 class="section-title">📋 My Requests</h2>
      <div v-if="myExpenses.length === 0" class="empty-state">
        <div class="empty-icon">💰</div>
        <p class="empty-text">No expense requests yet</p>
      </div>
      <div v-for="exp in myExpenses" :key="exp.id" class="history-card">
        <div class="history-icon-wrap">
          <img :src="'/icons/' + (exp.expense_type === 'GENERAL' ? 'generalexpense' : exp.expense_type === 'CENTER' ? 'centerexpense' : 'travelexpense') + '.png'" class="history-icon-img" />
        </div>
        <div class="history-content">
          <div class="history-header">
            <span class="history-type">{{ exp.expense_type }}</span>
            <span :class="'status-badge ' + exp.status.toLowerCase()">{{ exp.status }}</span>
          </div>
          <div class="history-details">
            <span>{{ exp.expense_type === 'TRAVEL' ? exp.travel_date : exp.expense_date }}</span>
            <span class="history-amount">฿{{ (exp.expense_type === 'TRAVEL' ? exp.total_amount : exp.amount).toLocaleString() }}</span>
          </div>
          <div v-if="exp.description" class="history-desc">{{ exp.description }}</div>
          <div v-if="exp.status === 'PENDING'" class="history-progress">
            Approval: {{ exp.current_step }}/{{ exp.total_steps }}
          </div>
        </div>
      </div>
    </div>

    <!-- Full-screen Preview Modal -->
    <teleport to="body">
      <div v-if="previewModal.show" class="preview-overlay" @click="closePreview">
        <div class="preview-toolbar">
          <button v-if="previewModal.type === 'image'" class="preview-btn" @click.stop="zoomIn">🔍+</button>
          <button v-if="previewModal.type === 'image'" class="preview-btn" @click.stop="zoomOut">🔍−</button>
          <button v-if="previewModal.type === 'image'" class="preview-btn" @click.stop="resetZoom">↺</button>
          <button class="preview-btn close" @click.stop="closePreview">✕</button>
        </div>
        <div class="preview-body" @click.stop>
          <!-- Image preview with zoom -->
          <div v-if="previewModal.type === 'image'" class="image-container"
            @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd"
            @wheel.prevent="onWheel">
            <img :src="previewModal.src" class="preview-full-img"
              :style="{ transform: `scale(${previewModal.zoom}) translate(${previewModal.panX}px, ${previewModal.panY}px)` }" />
          </div>
          <!-- PDF preview -->
          <iframe v-else-if="previewModal.type === 'pdf'" :src="previewModal.src" class="preview-pdf-frame" />
        </div>
      </div>
    </teleport>
  </div>
</template>

<script>
import { createGeneralExpense, createTravelExpense, createCenterExpense, getMyExpenses } from '../../services/api'

export default {
  name: 'StaffExpenseRequest',
  inject: ['showToast'],
  data() {
    return {
      selectedType: null,
      submitting: false,
      myExpenses: [],
      generalForm: {
        file: null,
        filePreview: null,
        isPdf: false,
        date: new Date().toISOString().slice(0, 10),
        description: '',
        amount: null,
      },
      travelForm: {
        date: new Date().toISOString().slice(0, 10),
        description: '',
        vehicleType: 'CAR',
        kmOut: null,
        kmReturn: null,
        otherCost: 0,
        outboundFile: null,
        outboundPreview: null,
        returnFile: null,
        returnPreview: null,
        otherFiles: [],
        otherPreviews: [],
      },
      centerForm: {
        file: null,
        filePreview: null,
        isPdf: false,
        date: new Date().toISOString().slice(0, 10),
        description: '',
        amount: null,
      },
      previewModal: {
        show: false,
        type: 'image',
        src: null,
        zoom: 1,
        panX: 0,
        panY: 0,
        lastDist: 0,
        lastPan: { x: 0, y: 0 },
        isPanning: false,
      },
    }
  },
  computed: {
    travelCost() {
      const rate = this.travelForm.vehicleType === 'CAR' ? 10 : 5
      return ((this.travelForm.kmOut || 0) + (this.travelForm.kmReturn || 0)) * rate
    },
    grandTotal() {
      return this.travelCost + (this.travelForm.otherCost || 0)
    },
    canSubmitGeneral() {
      return this.generalForm.file && this.generalForm.date && this.generalForm.description && this.generalForm.amount > 0
    },
    canSubmitTravel() {
      return this.travelForm.date && this.travelForm.outboundFile && this.travelForm.returnFile && (this.travelForm.kmOut > 0 || this.travelForm.kmReturn > 0)
    },
    canSubmitCenter() {
      return this.centerForm.file && this.centerForm.date && this.centerForm.description && this.centerForm.amount > 0
    },
  },
  async mounted() {
    await this.loadHistory()
  },
  methods: {
    async loadHistory() {
      try {
        const res = await getMyExpenses()
        this.myExpenses = res.data || []
      } catch (e) { console.error(e) }
    },

    // General file handlers
    onGeneralFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      this.setGeneralFile(file)
    },
    onDropGeneral(e) {
      const file = e.dataTransfer.files[0]
      if (file) this.setGeneralFile(file)
    },
    setGeneralFile(file) {
      this.generalForm.file = file
      this.generalForm.isPdf = file.type === 'application/pdf'
      if (!this.generalForm.isPdf) {
        const reader = new FileReader()
        reader.onload = (e) => { this.generalForm.filePreview = e.target.result }
        reader.readAsDataURL(file)
      } else {
        this.generalForm.filePreview = null
      }
    },
    removeGeneralFile() {
      this.generalForm.file = null
      this.generalForm.filePreview = null
      this.generalForm.isPdf = false
    },

    // Travel image handlers
    onOutboundImg(e) {
      const file = e.target.files[0]
      if (!file) return
      this.travelForm.outboundFile = file
      const reader = new FileReader()
      reader.onload = (ev) => { this.travelForm.outboundPreview = ev.target.result }
      reader.readAsDataURL(file)
    },
    onReturnImg(e) {
      const file = e.target.files[0]
      if (!file) return
      this.travelForm.returnFile = file
      const reader = new FileReader()
      reader.onload = (ev) => { this.travelForm.returnPreview = ev.target.result }
      reader.readAsDataURL(file)
    },
    onOtherFiles(e) {
      for (const file of e.target.files) {
        this.travelForm.otherFiles.push(file)
        const reader = new FileReader()
        reader.onload = (ev) => { this.travelForm.otherPreviews.push(ev.target.result) }
        reader.readAsDataURL(file)
      }
    },
    removeOtherFile(i) {
      this.travelForm.otherFiles.splice(i, 1)
      this.travelForm.otherPreviews.splice(i, 1)
    },

    // Submissions
    async submitGeneral() {
      this.submitting = true
      try {
        const fd = new FormData()
        fd.append('expense_date', this.generalForm.date)
        fd.append('description', this.generalForm.description)
        fd.append('amount', this.generalForm.amount)
        fd.append('file', this.generalForm.file)
        await createGeneralExpense(fd)
        this.showToast('Expense submitted! ✅', 'success')
        this.resetGeneral()
        this.selectedType = null
        await this.loadHistory()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to submit', 'error')
      } finally {
        this.submitting = false
      }
    },
    async submitTravel() {
      this.submitting = true
      try {
        const fd = new FormData()
        fd.append('travel_date', this.travelForm.date)
        fd.append('vehicle_type', this.travelForm.vehicleType)
        fd.append('km_outbound', this.travelForm.kmOut)
        fd.append('km_return', this.travelForm.kmReturn)
        fd.append('description', this.travelForm.description || '')
        fd.append('other_cost', this.travelForm.otherCost || 0)
        fd.append('outbound_image', this.travelForm.outboundFile)
        fd.append('return_image', this.travelForm.returnFile)
        this.travelForm.otherFiles.forEach(f => fd.append('other_files', f))
        await createTravelExpense(fd)
        this.showToast('Travel expense submitted! ✅', 'success')
        this.resetTravel()
        this.selectedType = null
        await this.loadHistory()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to submit', 'error')
      } finally {
        this.submitting = false
      }
    },
    resetGeneral() {
      this.generalForm = { file: null, filePreview: null, isPdf: false, date: new Date().toISOString().slice(0, 10), description: '', amount: null }
    },
    resetTravel() {
      this.travelForm = { date: new Date().toISOString().slice(0, 10), description: '', vehicleType: 'CAR', kmOut: null, kmReturn: null, otherCost: 0, outboundFile: null, outboundPreview: null, returnFile: null, returnPreview: null, otherFiles: [], otherPreviews: [] }
    },

    // Center file handlers
    onCenterFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      this.setCenterFile(file)
    },
    onDropCenter(e) {
      const file = e.dataTransfer.files[0]
      if (file) this.setCenterFile(file)
    },
    setCenterFile(file) {
      this.centerForm.file = file
      this.centerForm.isPdf = file.type === 'application/pdf'
      if (!this.centerForm.isPdf) {
        const reader = new FileReader()
        reader.onload = (e) => { this.centerForm.filePreview = e.target.result }
        reader.readAsDataURL(file)
      } else {
        this.centerForm.filePreview = null
      }
    },
    removeCenterFile() {
      this.centerForm.file = null
      this.centerForm.filePreview = null
      this.centerForm.isPdf = false
    },
    async submitCenter() {
      this.submitting = true
      try {
        const fd = new FormData()
        fd.append('expense_date', this.centerForm.date)
        fd.append('description', this.centerForm.description)
        fd.append('amount', this.centerForm.amount)
        fd.append('file', this.centerForm.file)
        await createCenterExpense(fd)
        this.showToast('ระบบได้รับรายการของคุณแล้ว กรุณาอย่าส่งซ้ำ', 'success')
        this.resetCenter()
        this.selectedType = null
        await this.loadHistory()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to submit', 'error')
      } finally {
        this.submitting = false
      }
    },
    resetCenter() {
      this.centerForm = { file: null, filePreview: null, isPdf: false, date: new Date().toISOString().slice(0, 10), description: '', amount: null }
    },

    // Preview modal
    openPreview(src, type) {
      if (type === 'pdf' && src instanceof File) {
        this.previewModal.src = URL.createObjectURL(src)
      } else {
        this.previewModal.src = src
      }
      this.previewModal.type = type
      this.previewModal.zoom = 1
      this.previewModal.panX = 0
      this.previewModal.panY = 0
      this.previewModal.show = true
      document.body.style.overflow = 'hidden'
    },
    closePreview() {
      if (this.previewModal.type === 'pdf' && this.previewModal.src) {
        URL.revokeObjectURL(this.previewModal.src)
      }
      this.previewModal.show = false
      this.previewModal.src = null
      document.body.style.overflow = ''
    },
    zoomIn() { this.previewModal.zoom = Math.min(this.previewModal.zoom + 0.3, 5) },
    zoomOut() { this.previewModal.zoom = Math.max(this.previewModal.zoom - 0.3, 0.5) },
    resetZoom() { this.previewModal.zoom = 1; this.previewModal.panX = 0; this.previewModal.panY = 0 },
    onWheel(e) {
      if (e.deltaY < 0) this.zoomIn()
      else this.zoomOut()
    },
    onTouchStart(e) {
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        this.previewModal.lastDist = Math.sqrt(dx * dx + dy * dy)
      } else if (e.touches.length === 1 && this.previewModal.zoom > 1) {
        this.previewModal.isPanning = true
        this.previewModal.lastPan = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      }
    },
    onTouchMove(e) {
      if (e.touches.length === 2) {
        e.preventDefault()
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        const dist = Math.sqrt(dx * dx + dy * dy)
        const scale = dist / this.previewModal.lastDist
        this.previewModal.zoom = Math.min(Math.max(this.previewModal.zoom * scale, 0.5), 5)
        this.previewModal.lastDist = dist
      } else if (e.touches.length === 1 && this.previewModal.isPanning) {
        e.preventDefault()
        const dx = e.touches[0].clientX - this.previewModal.lastPan.x
        const dy = e.touches[0].clientY - this.previewModal.lastPan.y
        this.previewModal.panX += dx / this.previewModal.zoom
        this.previewModal.panY += dy / this.previewModal.zoom
        this.previewModal.lastPan = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      }
    },
    onTouchEnd() {
      this.previewModal.isPanning = false
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }
.page-title { font-family: 'Cinzel', serif; font-size: 26px; font-weight: 800; color: #d4a44c; text-shadow: 0 2px 8px rgba(212,164,76,0.2); margin-bottom: 4px; }
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; margin-bottom: 24px; font-style: italic; }
.center-notice { padding: 10px 14px; border-radius: 10px; background: rgba(52,152,219,0.1); border: 1px solid rgba(52,152,219,0.2); color: #3498db; font-size: 13px; font-weight: 600; margin-bottom: 16px; }

/* Type Picker */
.type-picker { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin-bottom: 24px; }
.type-card {
  display: flex; flex-direction: column; align-items: center; justify-content: flex-end;
  padding: 10px 8px 12px; aspect-ratio: 1 / 1;
  border-radius: 14px; border: 2px solid rgba(212,164,76,0.2);
  background-color: rgba(26,26,46,0.5);
  background-size: cover; background-repeat: no-repeat; background-position: center;
  color: #e8d5b7; cursor: pointer; transition: all 0.2s;
  overflow: hidden;
}
.type-card:hover { border-color: #d4a44c; transform: translateY(-3px); box-shadow: 0 8px 28px rgba(212,164,76,0.15); }
.type-label { font-family: 'Cinzel', serif; font-weight: 700; font-size: 13px; margin-bottom: 2px; text-shadow: 0 1px 6px rgba(0,0,0,0.8), 0 0 12px rgba(0,0,0,0.6); }
.type-desc { font-size: 10px; color: #c8b090; text-shadow: 0 1px 5px rgba(0,0,0,0.8), 0 0 10px rgba(0,0,0,0.6); }

/* Form */
.form-section { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.back-btn { background: none; border: none; color: #d4a44c; font-weight: 700; font-size: 14px; cursor: pointer; margin-bottom: 16px; padding: 0; }
.section-title { font-family: 'Cinzel', serif; font-size: 20px; color: #e8d5b7; margin-bottom: 18px; }
.sub-title { font-family: 'Cinzel', serif; font-size: 15px; color: #d4a44c; margin: 18px 0 10px; }

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 700; color: #d4a44c; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 12px 14px; border-radius: 10px; border: 1px solid rgba(212,164,76,0.3);
  background: rgba(26,26,46,0.6); color: #e8d5b7; font-size: 14px; box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: #d4a44c; }

/* File Drop */
.file-drop {
  border: 2px dashed rgba(212,164,76,0.3); border-radius: 12px; padding: 24px;
  text-align: center; cursor: pointer; transition: border-color 0.2s; min-height: 80px;
  display: flex; align-items: center; justify-content: center;
}
.file-drop.small { padding: 14px; min-height: 60px; }
.file-drop:hover { border-color: #d4a44c; }
.drop-text { color: #8b7355; font-size: 13px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.drop-icon { font-size: 24px; }
.file-preview { position: relative; display: inline-block; }
.preview-img { max-height: 120px; border-radius: 8px; object-fit: cover; }
.pdf-badge { background: rgba(212,164,76,0.15); border-radius: 8px; padding: 10px 16px; color: #d4a44c; font-weight: 700; font-size: 13px; }
.remove-btn { position: absolute; top: -6px; right: -6px; width: 22px; height: 22px; border-radius: 50%; background: #c0392b; color: #fff; border: 2px solid rgba(44,24,16,0.9); font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.remove-btn.mini { width: 18px; height: 18px; font-size: 9px; top: -4px; right: -4px; }

/* Multi Preview */
.multi-preview { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.mini-thumb { position: relative; }
.mini-thumb .preview-img { width: 60px; height: 60px; object-fit: cover; border-radius: 6px; }
.add-more { width: 60px; height: 60px; border-radius: 6px; border: 2px dashed rgba(212,164,76,0.3); display: flex; align-items: center; justify-content: center; color: #d4a44c; font-size: 24px; cursor: pointer; }

/* Vehicle Picker */
.vehicle-picker { display: flex; gap: 10px; }
.vehicle-btn {
  flex: 1; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 700;
  border: 2px solid rgba(212,164,76,0.2); background: rgba(26,26,46,0.6); color: #8b7355; cursor: pointer; transition: all 0.2s;
}
.vehicle-btn.active { border-color: #d4a44c; color: #e8d5b7; background: rgba(212,164,76,0.15); }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

/* Cost Summary */
.cost-summary { background: rgba(26,26,46,0.6); border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; border: 1px solid rgba(212,164,76,0.15); }
.cost-summary.total { border-color: rgba(212,164,76,0.4); }
.cost-row { display: flex; justify-content: space-between; font-size: 14px; color: #e8d5b7; padding: 4px 0; }
.cost-row.grand { font-weight: 800; font-size: 16px; color: #d4a44c; border-top: 1px solid rgba(212,164,76,0.2); padding-top: 8px; margin-top: 4px; }

/* Submit */
.submit-btn {
  width: 100%; padding: 14px; border-radius: 12px; font-size: 15px; font-weight: 800;
  border: none; cursor: pointer; color: #1c1208;
  background: linear-gradient(135deg, #d4a44c, #b8860b);
  box-shadow: 0 4px 15px rgba(212,164,76,0.25); transition: all 0.2s;
}
.submit-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(212,164,76,0.35); }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* History */
.history-section { margin-top: 28px; }
.empty-state { text-align: center; padding: 32px 0; }
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-text { color: #8b7355; font-weight: 600; }

.history-card {
  display: flex; align-items: stretch;
  background: rgba(26,26,46,0.7); border: 1px solid rgba(212,164,76,0.15); border-radius: 12px;
  margin-bottom: 10px; overflow: hidden;
}
.history-icon-wrap {
  width: 60px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(212,164,76,0.06);
}
.history-icon-img { width: 100%; height: 100%; object-fit: cover; }
.history-content { flex: 1; padding: 12px 14px; }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.history-type { font-weight: 700; font-size: 13px; color: #e8d5b7; }
.history-details { display: flex; justify-content: space-between; font-size: 13px; color: #8b7355; }
.history-amount { font-weight: 800; color: #d4a44c; }
.history-desc { font-size: 12px; color: #8b7355; margin-top: 4px; }
.history-progress { font-size: 12px; color: #e67e22; margin-top: 4px; font-weight: 700; }

.status-badge {
  font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 6px; text-transform: uppercase;
}
.status-badge.pending { background: rgba(230,126,34,0.2); color: #e67e22; }
.status-badge.all_approved { background: rgba(46,204,113,0.2); color: #2ecc71; }
.status-badge.confirmed { background: rgba(52,152,219,0.2); color: #3498db; }
.status-badge.rejected { background: rgba(192,57,43,0.2); color: #c0392b; }

/* Preview Hint */
.preview-hint { display: block; font-size: 10px; color: #8b7355; font-weight: 400; margin-top: 2px; }
.preview-img { cursor: zoom-in; }

/* Preview Overlay */
.preview-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,0.92); backdrop-filter: blur(8px);
  display: flex; flex-direction: column;
  animation: fadeIn 0.2s ease;
}
.preview-toolbar {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 12px 16px; flex-shrink: 0;
}
.preview-btn {
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(212,164,76,0.2); border: 1px solid rgba(212,164,76,0.4);
  color: #d4a44c; font-size: 16px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.preview-btn:hover { background: rgba(212,164,76,0.35); }
.preview-btn.close { background: rgba(192,57,43,0.3); border-color: rgba(192,57,43,0.5); color: #fff; font-size: 18px; }
.preview-body {
  flex: 1; display: flex; align-items: center; justify-content: center;
  overflow: hidden; padding: 0 16px 16px;
}
.image-container {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; touch-action: none;
}
.preview-full-img {
  max-width: 100%; max-height: 100%; object-fit: contain;
  transition: transform 0.1s ease;
  user-select: none; -webkit-user-drag: none;
}
.preview-pdf-frame {
  width: 100%; height: 100%; border: none; border-radius: 8px;
  background: #fff;
}
</style>
