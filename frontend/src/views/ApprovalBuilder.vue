<template>
  <div>
    <div class="page-header">
      <h2>Approval Lines</h2>
      <p>Configure approval workflows for employees</p>
    </div>

    <div style="display: grid; grid-template-columns: 340px 1fr; gap: 24px;">
      <!-- Left: Employee Selector -->
      <div class="card" style="align-self: flex-start;">
        <div class="card-title" style="margin-bottom: 16px;">Select Employee</div>
        <input v-model="userSearch" class="form-input" placeholder="🔍 Search..." style="margin-bottom: 16px;"
          @input="debouncedUserSearch" />
        <div style="max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px;">
          <div v-for="user in users" :key="user.id" @click="selectUser(user)"
            :class="['nav-item', { active: selectedUser?.id === user.id }]"
            style="padding: 10px 12px;">
            <div class="avatar" style="width: 32px; height: 32px; font-size: 12px;">
              <img v-if="user.image" :src="user.image" :alt="user.name" />
              <span v-else>{{ user.name.charAt(0) }}</span>
            </div>
            <div>
              <div style="font-size: 13px; font-weight: 600;">{{ user.name }} {{ user.surname }}</div>
              <div style="font-size: 11px; color: #64748b;">{{ user.department || 'No department' }}</div>
            </div>
            <span v-if="userFlowMap[user.id]" style="margin-left: auto; color: #4ade80; font-size: 12px;">✓</span>
          </div>
          <div v-if="users.length === 0" style="padding: 20px; text-align: center; color: #64748b; font-size: 13px;">
            No employees found
          </div>
        </div>
      </div>

      <!-- Right: Approval Flow Builder -->
      <div>
        <div v-if="!selectedUser" class="card">
          <div class="empty-state">
            <span class="icon">👈</span>
            <h3>Select an employee</h3>
            <p>Choose an employee from the list to configure their approval line</p>
          </div>
        </div>

        <div v-else>
          <div class="card" style="margin-bottom: 24px;">
            <div class="card-header">
              <div>
                <span class="card-title">Approval Flow for {{ selectedUser.name }} {{ selectedUser.surname }}</span>
                <p style="font-size: 13px; color: #64748b; margin-top: 4px;">{{ selectedUser.department || '' }} · {{ selectedUser.position || '' }}</p>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <div v-if="!existingFlowId && patterns.length > 0" style="position: relative;">
                  <select v-model="selectedPatternId" class="form-input" style="font-size: 12px; padding: 6px 10px; width: 200px;">
                    <option value="">📋 Apply Pattern...</option>
                    <option v-for="p in patterns" :key="p.id" :value="p.id">{{ p.name }}</option>
                  </select>
                  <button v-if="selectedPatternId" class="btn btn-secondary btn-sm" @click="applyPattern" style="margin-left: 4px;">Apply</button>
                </div>
                <button v-if="existingFlowId" class="btn btn-danger btn-sm" @click="handleDeleteFlow">🗑️ Delete</button>
                <button class="btn btn-success" @click="handleSaveFlow" :disabled="saving">
                  {{ saving ? 'Saving...' : '💾 Save Flow' }}
                </button>
              </div>
            </div>

            <!-- Approval Steps Timeline -->
            <div class="approval-timeline" v-if="steps.length > 0">
              <div v-for="(step, idx) in steps" :key="idx" class="step-card">
                <div class="step-header">
                  <span class="step-number">Level {{ idx + 1 }}</span>
                  <button class="btn btn-danger btn-sm" @click="removeStep(idx)" v-if="steps.length > 1">✕ Remove</button>
                </div>

                <!-- Approvers -->
                <div class="approver-chips">
                  <div v-for="(approver, aIdx) in step.approvers" :key="aIdx" class="approver-chip">
                    <span>{{ approver.name }} {{ approver.surname }}</span>
                    <span class="remove-btn" @click="removeApprover(idx, aIdx)">✕</span>
                  </div>
                </div>

                <!-- Add Approver -->
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                  <select v-model="step.newApproverId" class="form-input" style="flex: 1;">
                    <option value="">-- Select Approver --</option>
                    <option v-for="u in availableApprovers(idx)" :key="u.id" :value="u.id">
                      {{ u.name }} {{ u.surname }} ({{ u.department || '-' }})
                    </option>
                  </select>
                  <button class="btn btn-secondary btn-sm" @click="addApprover(idx)" :disabled="!step.newApproverId">
                    + Add
                  </button>
                </div>

                <!-- Condition Toggle (only show if more than 1 approver) -->
                <div v-if="step.approvers.length > 1" class="condition-toggle">
                  <span style="font-size: 13px; color: #94a3b8;">Condition:</span>
                  <div class="toggle-wrapper">
                    <button
                      :class="['toggle-option', step.condition_type === 'AND' ? 'active-and' : '']"
                      @click="step.condition_type = 'AND'">
                      AND (ทุกคน)
                    </button>
                    <button
                      :class="['toggle-option', step.condition_type === 'OR' ? 'active-or' : '']"
                      @click="step.condition_type = 'OR'">
                      OR (คนใดคนหนึ่ง)
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Empty Steps State -->
            <div v-else style="padding: 24px; text-align: center; color: #64748b;">
              <p style="margin-bottom: 12px;">No approval steps configured</p>
            </div>

            <!-- Add Step Button -->
            <button class="btn btn-secondary" @click="addStep" style="width: 100%; justify-content: center; margin-top: 8px;">
              ➕ Add Approval Level
            </button>
          </div>

          <!-- Flow Preview -->
          <div v-if="steps.length > 0" class="card">
            <div class="card-title" style="margin-bottom: 16px;">📋 Flow Preview</div>
            <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 12px;">
              <template v-for="(step, idx) in steps" :key="idx">
                <div style="background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.15); border-radius: 10px; padding: 12px 16px; text-align: center;">
                  <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Level {{ idx + 1 }}</div>
                  <div style="font-size: 13px; color: #e2e8f0;">
                    <span v-for="(a, aIdx) in step.approvers" :key="aIdx">
                      {{ a.name }} {{ a.surname }}
                      <span v-if="aIdx < step.approvers.length - 1">
                        <span :class="['badge', step.condition_type === 'AND' ? 'badge-and' : 'badge-or']"
                          style="margin: 0 4px; font-size: 10px;">
                          {{ step.condition_type }}
                        </span>
                      </span>
                    </span>
                  </div>
                </div>
                <span v-if="idx < steps.length - 1" style="color: #f97316; font-size: 18px;">→</span>
              </template>
              <div style="background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.2); border-radius: 10px; padding: 12px 16px; text-align: center;">
                <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">Result</div>
                <div style="font-size: 13px; color: #4ade80; font-weight: 600;">✅ Approved</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getUsers, getApprovalFlows, getApprovalFlowByUser,
  createApprovalFlow, updateApprovalFlow, deleteApprovalFlow,
  getApprovalPatterns,
} from '../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      users: [],
      allUsers: [],
      selectedUser: null,
      steps: [],
      existingFlowId: null,
      userFlowMap: {},
      userSearch: '',
      saving: false,
      searchTimer: null,
      patterns: [],
      selectedPatternId: '',
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      try {
        const [usersRes, flowsRes, patternsRes] = await Promise.all([
          getUsers(), getApprovalFlows(), getApprovalPatterns()
        ])
        this.allUsers = usersRes.data
        this.users = [...this.allUsers]
        this.patterns = patternsRes.data
        // Build user->flow map
        this.userFlowMap = {}
        for (const flow of flowsRes.data) {
          this.userFlowMap[flow.target_user_id] = flow.id
        }
      } catch (e) {
        console.error(e)
      }
    },
    debouncedUserSearch() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        const q = this.userSearch.toLowerCase()
        this.users = this.allUsers.filter(u =>
          u.name.toLowerCase().includes(q) || u.surname.toLowerCase().includes(q)
        )
      }, 200)
    },
    async selectUser(user) {
      this.selectedUser = user
      this.existingFlowId = null
      this.steps = []
      this.selectedPatternId = ''

      try {
        const { data } = await getApprovalFlowByUser(user.id)
        this.existingFlowId = data.id
        // Build steps from response
        this.steps = data.steps.map(s => ({
          condition_type: s.condition_type,
          approvers: s.approvers.map(a => ({
            id: a.approver_id,
            name: a.approver_name || '',
            surname: a.approver_surname || '',
          })),
          newApproverId: '',
        }))
      } catch (e) {
        // No flow exists — that's fine
        this.steps = []
      }
    },
    addStep() {
      this.steps.push({
        condition_type: 'AND',
        approvers: [],
        newApproverId: '',
      })
    },
    removeStep(idx) {
      this.steps.splice(idx, 1)
    },
    availableApprovers(stepIdx) {
      // Exclude selected user + already added approvers in this step
      const usedInStep = new Set(this.steps[stepIdx].approvers.map(a => a.id))
      return this.allUsers.filter(u =>
        u.id !== this.selectedUser.id && !usedInStep.has(u.id)
      )
    },
    addApprover(stepIdx) {
      const step = this.steps[stepIdx]
      const userId = parseInt(step.newApproverId)
      const user = this.allUsers.find(u => u.id === userId)
      if (user) {
        step.approvers.push({
          id: user.id,
          name: user.name,
          surname: user.surname,
        })
        step.newApproverId = ''
      }
    },
    removeApprover(stepIdx, approverIdx) {
      this.steps[stepIdx].approvers.splice(approverIdx, 1)
    },
    applyPattern() {
      const pattern = this.patterns.find(p => p.id === parseInt(this.selectedPatternId))
      if (!pattern) return
      this.steps = pattern.steps.map(s => ({
        condition_type: s.condition_type,
        approvers: s.approvers.map(a => ({
          id: a.approver_id,
          name: a.approver_name || '',
          surname: a.approver_surname || '',
        })),
        newApproverId: '',
      }))
      this.selectedPatternId = ''
      this.showToast(`Pattern "${pattern.name}" applied! You can customize before saving.`)
    },
    async handleSaveFlow() {
      // Validate
      const validSteps = this.steps.filter(s => s.approvers.length > 0)
      if (validSteps.length === 0) {
        this.showToast('Please add at least one approval level with approvers', 'error')
        return
      }

      this.saving = true
      try {
        const payload = {
          name: `Approval for ${this.selectedUser.name} ${this.selectedUser.surname}`,
          steps: validSteps.map((s, idx) => ({
            step_order: idx + 1,
            condition_type: s.condition_type,
            approver_ids: s.approvers.map(a => a.id),
          })),
        }

        if (this.existingFlowId) {
          await updateApprovalFlow(this.existingFlowId, payload)
          this.showToast('Approval flow updated!')
        } else {
          payload.target_user_id = this.selectedUser.id
          const { data } = await createApprovalFlow(payload)
          this.existingFlowId = data.id
          this.userFlowMap[this.selectedUser.id] = data.id
          this.showToast('Approval flow created!')
        }
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to save flow', 'error')
      } finally {
        this.saving = false
      }
    },
    async handleDeleteFlow() {
      if (!this.existingFlowId) return
      try {
        await deleteApprovalFlow(this.existingFlowId)
        delete this.userFlowMap[this.selectedUser.id]
        this.existingFlowId = null
        this.steps = []
        this.showToast('Approval flow deleted')
      } catch (e) {
        this.showToast('Failed to delete flow', 'error')
      }
    },
  },
}
</script>
