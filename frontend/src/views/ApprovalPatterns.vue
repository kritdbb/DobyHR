<template>
  <div>
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2>📋 Approval Patterns</h2>
        <p>Create reusable approval templates</p>
      </div>
      <button class="btn btn-primary" @click="openCreateModal">➕ New Pattern</button>
    </div>

    <div v-if="patterns.length > 0" style="display: flex; flex-direction: column; gap: 16px;">
      <div v-for="pattern in patterns" :key="pattern.id" class="card">
        <div class="card-header" style="margin-bottom: 16px;">
          <div>
            <span class="card-title">{{ pattern.name }}</span>
            <p style="font-size: 12px; color: #8b7355; margin-top: 4px;">
              {{ pattern.steps.length }} level{{ pattern.steps.length !== 1 ? 's' : '' }}
            </p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" @click="openEditModal(pattern)">✏️ Edit</button>
            <button class="btn btn-danger btn-sm" @click="confirmDelete(pattern)">🗑️</button>
          </div>
        </div>
        <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
          <template v-for="(step, idx) in pattern.steps" :key="step.id">
            <div style="background: rgba(41,128,185,0.06); border: 1px solid rgba(41,128,185,0.12); border-radius: 8px; padding: 10px 14px; text-align: center;">
              <div style="font-size: 10px; color: #8b7355; margin-bottom: 3px; font-weight: 700; text-transform: uppercase;">Level {{ idx + 1 }}</div>
              <div style="font-size: 12px; color: #e8d5b7;">
                <span v-for="(a, aIdx) in step.approvers" :key="a.id">
                  {{ a.approver_name }} {{ a.approver_surname }}
                  <span v-if="aIdx < step.approvers.length - 1"
                    :style="{ color: step.condition_type === 'AND' ? '#2980b9' : '#d4a44c', fontWeight: 700, fontSize: '10px' }">
                    {{ step.condition_type }}
                  </span>
                </span>
              </div>
            </div>
            <span v-if="idx < pattern.steps.length - 1" style="color: #d4a44c; font-size: 16px;">→</span>
          </template>
          <div style="background: rgba(39,174,96,0.08); border: 1px solid rgba(39,174,96,0.15); border-radius: 8px; padding: 10px 14px; text-align: center;">
            <div style="font-size: 10px; color: #8b7355; margin-bottom: 3px; font-weight: 700;">RESULT</div>
            <div style="font-size: 12px; color: #27ae60; font-weight: 600;">✅ Approved</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="card">
      <div class="empty-state">
        <span class="icon">📋</span>
        <h3>No patterns yet</h3>
        <p>Create a reusable approval pattern template</p>
        <button class="btn btn-primary" @click="openCreateModal">➕ New Pattern</button>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal-content" style="max-width: 640px; max-height: 85vh; overflow-y: auto;">
        <h3>{{ editingId ? 'Edit Pattern' : 'Create Pattern' }}</h3>
        <div class="form-group">
          <label>Pattern Name</label>
          <input v-model="form.name" class="form-input" placeholder="e.g. Royal Guard Team" />
        </div>
        <div style="margin-top: 16px;">
          <div v-for="(step, idx) in form.steps" :key="idx"
            style="background: rgba(41,128,185,0.04); border: 1px solid rgba(41,128,185,0.1); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <span style="font-size: 13px; font-weight: 700; color: #2980b9;">Level {{ idx + 1 }}</span>
              <button v-if="form.steps.length > 1" class="btn btn-danger btn-sm" @click="form.steps.splice(idx, 1)" style="padding: 2px 10px; font-size: 11px;">✕</button>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;">
              <div v-for="(approver, aIdx) in step.approvers" :key="aIdx"
                style="background: rgba(212,164,76,0.08); border: 1px solid rgba(212,164,76,0.15); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #e8d5b7; display: flex; align-items: center; gap: 6px;">
                <span>{{ approver.name }} {{ approver.surname }}</span>
                <span @click="step.approvers.splice(aIdx, 1)" style="cursor: pointer; color: #c0392b; font-weight: 700;">✕</span>
              </div>
            </div>
            <div style="display: flex; gap: 8px;">
              <select v-model="step.newApproverId" class="form-input" style="flex: 1; font-size: 13px;">
                <option value="">-- Select Approver --</option>
                <option v-for="u in availableApprovers(idx)" :key="u.id" :value="u.id">
                  {{ u.name }} {{ u.surname }} ({{ u.department || '-' }})
                </option>
              </select>
              <button class="btn btn-secondary btn-sm" @click="addApprover(idx)" :disabled="!step.newApproverId">+ Add</button>
            </div>
            <div v-if="step.approvers.length > 1" style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
              <span style="font-size: 12px; color: #8b7355;">Condition:</span>
              <button :class="['toggle-option', step.condition_type === 'AND' ? 'active-and' : '']"
                @click="step.condition_type = 'AND'" style="padding: 3px 10px; font-size: 11px; border-radius: 6px;">AND</button>
              <button :class="['toggle-option', step.condition_type === 'OR' ? 'active-or' : '']"
                @click="step.condition_type = 'OR'" style="padding: 3px 10px; font-size: 11px; border-radius: 6px;">OR</button>
            </div>
          </div>
          <button class="btn btn-secondary" @click="addStep" style="width: 100%; justify-content: center;">
            ➕ Add Level
          </button>
        </div>
        <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(212,164,76,0.1);">
          <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
          <button class="btn btn-primary" @click="handleSave" :disabled="saving">
            {{ saving ? 'Saving...' : '💾 Save Pattern' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-content" style="max-width: 400px;">
        <h3>Delete Pattern</h3>
        <p style="color: #8b7355; margin-bottom: 24px;">
          Are you sure you want to delete <strong style="color: #e8d5b7;">{{ patternToDelete?.name }}</strong>?
        </p>
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="showDeleteModal = false">Cancel</button>
          <button class="btn btn-danger" @click="handleDelete">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getUsers, getApprovalPatterns, createApprovalPattern,
  updateApprovalPattern, deleteApprovalPattern,
} from '../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      patterns: [],
      allUsers: [],
      showModal: false,
      editingId: null,
      saving: false,
      form: { name: '', steps: [] },
      showDeleteModal: false,
      patternToDelete: null,
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [patternsRes, usersRes] = await Promise.all([getApprovalPatterns(), getUsers()])
        this.patterns = patternsRes.data
        this.allUsers = usersRes.data
      } catch (e) {
        console.error(e)
      }
    },
    openCreateModal() {
      this.editingId = null
      this.form = { name: '', steps: [{ condition_type: 'AND', approvers: [], newApproverId: '' }] }
      this.showModal = true
    },
    openEditModal(pattern) {
      this.editingId = pattern.id
      this.form = {
        name: pattern.name,
        steps: pattern.steps.map(s => ({
          condition_type: s.condition_type,
          approvers: s.approvers.map(a => ({ id: a.approver_id, name: a.approver_name || '', surname: a.approver_surname || '' })),
          newApproverId: '',
        })),
      }
      this.showModal = true
    },
    addStep() {
      this.form.steps.push({ condition_type: 'AND', approvers: [], newApproverId: '' })
    },
    availableApprovers(stepIdx) {
      const usedInStep = new Set(this.form.steps[stepIdx].approvers.map(a => a.id))
      return this.allUsers.filter(u => !usedInStep.has(u.id))
    },
    addApprover(stepIdx) {
      const step = this.form.steps[stepIdx]
      const userId = parseInt(step.newApproverId)
      const user = this.allUsers.find(u => u.id === userId)
      if (user) {
        step.approvers.push({ id: user.id, name: user.name, surname: user.surname })
        step.newApproverId = ''
      }
    },
    async handleSave() {
      if (!this.form.name.trim()) { this.showToast('Pattern name is required', 'error'); return }
      const validSteps = this.form.steps.filter(s => s.approvers.length > 0)
      if (validSteps.length === 0) { this.showToast('Add at least one level with approvers', 'error'); return }
      this.saving = true
      try {
        const payload = {
          name: this.form.name,
          steps: validSteps.map((s, idx) => ({ step_order: idx + 1, condition_type: s.condition_type, approver_ids: s.approvers.map(a => a.id) })),
        }
        if (this.editingId) { await updateApprovalPattern(this.editingId, payload); this.showToast('Pattern updated!') }
        else { await createApprovalPattern(payload); this.showToast('Pattern created!') }
        this.showModal = false
        await this.loadData()
      } catch (e) { this.showToast(e.response?.data?.detail || 'Failed to save', 'error') }
      finally { this.saving = false }
    },
    confirmDelete(pattern) { this.patternToDelete = pattern; this.showDeleteModal = true },
    async handleDelete() {
      try {
        await deleteApprovalPattern(this.patternToDelete.id)
        this.showToast('Pattern deleted')
        this.showDeleteModal = false
        await this.loadData()
      } catch (e) { this.showToast('Failed to delete pattern', 'error') }
    },
  },
}
</script>

<style scoped>
.toggle-option {
  background: rgba(44,24,16,0.6);
  border: 1px solid rgba(212,164,76,0.15);
  color: #8b7355;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.2s;
}
.toggle-option:hover { border-color: rgba(212,164,76,0.3); }
.active-and { background: rgba(41,128,185,0.1); border-color: #2980b9; color: #2980b9; }
.active-or { background: rgba(212,164,76,0.1); border-color: #d4a44c; color: #d4a44c; }
</style>
