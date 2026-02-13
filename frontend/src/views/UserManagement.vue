<template>
  <div>
    <div class="page-header" style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h2>🛡️ Guild Roster</h2>
        <p>Manage guild members</p>
      </div>
      <router-link to="/users/create" class="btn btn-primary">
        ➕ Recruit Member
      </router-link>
    </div>

    <!-- Search -->
    <div class="card" style="margin-bottom: 24px; padding: 16px 20px;">
      <div style="display: flex; gap: 12px;">
        <input v-model="search" class="form-input" placeholder="🔍 Search by name..." style="flex: 1;"
          @input="debouncedSearch" />
        <select v-model="filterDepartment" class="form-input" style="width: 200px;" @change="loadUsers">
          <option value="">All Guilds</option>
          <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
        </select>
      </div>
    </div>

    <!-- Users Table -->
    <div class="card" v-if="users.length > 0">
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th style="width: 60px;"></th>
              <th>Name</th>
              <th>Guild</th>
              <th>Rank</th>
              <th>Gold</th>
              <th>Mana</th>
              <th style="width: 200px;">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <div class="avatar">
                  <img v-if="user.image" :src="user.image" :alt="user.name" />
                  <span v-else>{{ user.name.charAt(0) }}</span>
                </div>
              </td>
              <td>
                <strong style="color: #e8d5b7;">{{ user.name }} {{ user.surname }}</strong>
              </td>
              <td>{{ user.department || '-' }}</td>
              <td>{{ user.position || '-' }}</td>
              <td><span style="color: #d4a44c; font-weight: 800;">{{ user.coins || 0 }} 💰</span></td>
              <td><span style="color: #9b59b6; font-weight: 800;">{{ user.angel_coins || 0 }} 🔮</span></td>
              <td>
                <div style="display: flex; gap: 8px;">
                  <router-link :to="`/users/${user.id}/edit`" class="btn btn-secondary btn-sm">✏️</router-link>
                  <button class="btn btn-danger btn-sm" @click="confirmDelete(user)">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="card">
      <div class="empty-state">
        <span class="icon">🛡️</span>
        <h3>No guild members yet</h3>
        <p>Start recruiting your first adventurer</p>
        <router-link to="/users/create" class="btn btn-primary">➕ Recruit Member</router-link>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-content" style="max-width: 480px;">
        <h3>Dismiss Member</h3>

        <!-- Error: user is an approver -->
        <div v-if="deleteError" style="margin-bottom: 20px;">
          <div style="background: rgba(192,57,43,0.1); border: 1px solid rgba(192,57,43,0.2); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <p style="color: #c0392b; font-weight: 700; margin-bottom: 8px;">⚠️ Cannot Dismiss</p>
            <p style="color: #8b7355; font-size: 13px; margin-bottom: 12px;">
              <strong style="color: #e8d5b7;">{{ userToDelete?.name }} {{ userToDelete?.surname }}</strong>
              {{ deleteAffectedUsers.length > 0 ? 'is an approver in the following flows. Remove them first:' : 'is used in the following patterns. Remove them first:' }}
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
              <span v-for="u in deleteAffectedUsers" :key="u.user_id"
                style="background: rgba(212,164,76,0.1); border: 1px solid rgba(212,164,76,0.2); padding: 4px 12px; border-radius: 6px; font-size: 12px; color: #d4a44c; font-weight: 600;">
                {{ u.user_name }}
              </span>
              <span v-for="p in deleteAffectedPatterns" :key="p.pattern_id"
                style="background: rgba(41,128,185,0.1); border: 1px solid rgba(41,128,185,0.2); padding: 4px 12px; border-radius: 6px; font-size: 12px; color: #2980b9; font-weight: 600;">
                📋 {{ p.pattern_name }}
              </span>
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showDeleteModal = false; deleteError = false">Close</button>
          </div>
        </div>

        <!-- Normal confirmation -->
        <template v-else>
          <p style="color: #8b7355; margin-bottom: 24px;">
            Are you sure you want to dismiss <strong style="color: #e8d5b7;">{{ userToDelete?.name }} {{ userToDelete?.surname }}</strong> from the guild? This action cannot be undone.
          </p>
          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showDeleteModal = false">Cancel</button>
            <button class="btn btn-danger" @click="handleDelete">Dismiss</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { getUsers, deleteUser, getDepartments } from '../services/api'

export default {
  inject: ['showToast'],
  data() {
    return {
      users: [],
      departments: [],
      search: '',
      filterDepartment: '',
      showDeleteModal: false,
      userToDelete: null,
      deleteError: false,
      deleteAffectedUsers: [],
      deleteAffectedPatterns: [],
      searchTimer: null,
    }
  },
  async mounted() {
    await Promise.all([this.loadUsers(), this.loadDepartments()])
  },
  methods: {
    async loadUsers() {
      try {
        const params = {}
        if (this.search) params.search = this.search
        if (this.filterDepartment) params.department = this.filterDepartment
        const { data } = await getUsers(params)
        this.users = data
      } catch (e) {
        console.error('Failed to load users', e)
      }
    },
    async loadDepartments() {
      try {
        const { data } = await getDepartments()
        this.departments = data
      } catch (e) {
        console.error(e)
      }
    },
    debouncedSearch() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => this.loadUsers(), 300)
    },
    confirmDelete(user) {
      this.userToDelete = user
      this.deleteError = false
      this.deleteAffectedUsers = []
      this.deleteAffectedPatterns = []
      this.showDeleteModal = true
    },
    async handleDelete() {
      try {
        await deleteUser(this.userToDelete.id)
        this.showToast('Member dismissed from guild')
        this.showDeleteModal = false
        await this.loadUsers()
      } catch (e) {
        if (e.response?.status === 409 && e.response?.data?.detail) {
          this.deleteError = true
          this.deleteAffectedUsers = e.response.data.detail.affected_users || []
          this.deleteAffectedPatterns = e.response.data.detail.affected_patterns || []
        } else {
          this.showToast('Failed to dismiss member', 'error')
        }
      }
    },
  },
}
</script>
