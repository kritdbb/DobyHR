<template>
  <div class="party-quest-admin">
    <h1>🤝 Party Quest Management</h1>

    <button class="btn-create" @click="showForm = true" v-if="!showForm">+ Create New Quest</button>

    <!-- Create / Edit Form -->
    <div v-if="showForm" class="quest-form card">
      <h2>{{ editId ? 'Edit Quest' : 'New Quest' }}</h2>

      <div class="form-row">
        <label>Title</label>
        <input v-model="form.title" placeholder="e.g. Sprint Challenge Week 5" />
      </div>

      <div class="form-row two-col">
        <div>
          <label>Start Date</label>
          <input type="date" v-model="form.start_date" />
        </div>
        <div>
          <label>End Date</label>
          <input type="date" v-model="form.end_date" />
        </div>
      </div>

      <div class="form-row two-col">
        <div>
          <label>Team A Name</label>
          <input v-model="form.team_a_name" placeholder="Team A" />
        </div>
        <div>
          <label>Team B Name</label>
          <input v-model="form.team_b_name" placeholder="Team B" />
        </div>
      </div>

      <!-- Goals -->
      <h3>🎯 Goals <span class="hint">(leave 0 to skip)</span></h3>
      <div class="goals-grid">
        <div class="goal-item">
          <label>🥾 Total Steps</label>
          <input type="number" v-model.number="form.steps_goal" min="0" />
        </div>
        <div class="goal-item">
          <label>🎁 Gifts from Others</label>
          <input type="number" v-model.number="form.gifts_goal" min="0" />
        </div>
        <div class="goal-item">
          <label>⚔️ PvP Wins</label>
          <input type="number" v-model.number="form.battles_goal" min="0" />
        </div>
        <div class="goal-item">
          <label>💌 Thank You Cards</label>
          <input type="number" v-model.number="form.thankyou_goal" min="0" />
        </div>
      </div>

      <!-- Rewards -->
      <h3>🏆 Rewards (per winning team member)</h3>
      <div class="goals-grid">
        <div class="goal-item">
          <label>💰 Gold</label>
          <input type="number" v-model.number="form.reward_gold" min="0" />
        </div>
        <div class="goal-item">
          <label>✨ Mana</label>
          <input type="number" v-model.number="form.reward_mana" min="0" />
        </div>
        <div class="goal-item">
          <label>⚔️ STR</label>
          <input type="number" v-model.number="form.reward_str" min="0" />
        </div>
        <div class="goal-item">
          <label>🛡️ DEF</label>
          <input type="number" v-model.number="form.reward_def" min="0" />
        </div>
        <div class="goal-item">
          <label>🍀 LUK</label>
          <input type="number" v-model.number="form.reward_luk" min="0" />
        </div>
      </div>

      <!-- Team Members -->
      <h3>👥 Team Members</h3>
      <div class="teams-container">
        <div class="team-column team-a">
          <h4>{{ form.team_a_name || 'Team A' }}</h4>
          <div class="member-chips">
            <div v-for="m in teamAMembers" :key="m.id" class="chip">
              <span>{{ m.name }}</span>
              <button @click="removeMember(m.id, 'A')">×</button>
            </div>
          </div>
          <select @change="addMember($event, 'A')" class="add-member-select">
            <option value="">+ Add member...</option>
            <option v-for="u in availableUsers" :key="u.id" :value="u.id">{{ u.name }} {{ u.surname || '' }}</option>
          </select>
        </div>
        <div class="vs-divider">VS</div>
        <div class="team-column team-b">
          <h4>{{ form.team_b_name || 'Team B' }}</h4>
          <div class="member-chips">
            <div v-for="m in teamBMembers" :key="m.id" class="chip">
              <span>{{ m.name }}</span>
              <button @click="removeMember(m.id, 'B')">×</button>
            </div>
          </div>
          <select @change="addMember($event, 'B')" class="add-member-select">
            <option value="">+ Add member...</option>
            <option v-for="u in availableUsers" :key="u.id" :value="u.id">{{ u.name }} {{ u.surname || '' }}</option>
          </select>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn-save" @click="saveQuest" :disabled="saving">{{ saving ? 'Saving...' : (editId ? 'Update' : 'Create') }}</button>
        <button class="btn-cancel" @click="cancelForm">Cancel</button>
      </div>
    </div>

    <!-- Quest List -->
    <div class="quest-list">
      <div v-for="q in quests" :key="q.id" class="quest-card card" :class="{ completed: q.status !== 'active' }">
        <div class="quest-header">
          <h3>{{ q.title }}</h3>
          <span class="quest-status" :class="q.status">{{ q.status }}</span>
        </div>
        <div class="quest-dates">📅 {{ q.start_date }} → {{ q.end_date }}</div>
        <div class="quest-teams">
          <span class="team-label team-a-label">{{ q.team_a_name }} ({{ q.members.filter(m => m.team === 'A').length }})</span>
          <span class="vs">VS</span>
          <span class="team-label team-b-label">{{ q.team_b_name }} ({{ q.members.filter(m => m.team === 'B').length }})</span>
        </div>
        <div v-if="q.winner_team" class="winner-badge">
          🏆 {{ q.winner_team === 'A' ? q.team_a_name : q.team_b_name }} Wins!
        </div>
        <div class="quest-actions">
          <button @click="editQuest(q)" v-if="q.status === 'active'">✏️ Edit</button>
          <button @click="deleteQuest(q.id)" class="btn-danger">🗑️ Delete</button>
        </div>
      </div>
      <div v-if="quests.length === 0 && !showForm" class="empty">
        No party quests yet. Create one to get started! 🎉
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPartyQuests, createPartyQuest, updatePartyQuest, deletePartyQuest as apiDeleteQuest, getUsers } from '../../services/api'

const quests = ref([])
const allUsers = ref([])
const showForm = ref(false)
const editId = ref(null)
const saving = ref(false)
const members = ref([])  // { id, user_id, team, name }

const emptyForm = () => ({
  title: '', start_date: '', end_date: '',
  team_a_name: 'Team A', team_b_name: 'Team B',
  steps_goal: 0, gifts_goal: 0, battles_goal: 0, thankyou_goal: 0,
  reward_gold: 0, reward_mana: 0, reward_str: 0, reward_def: 0, reward_luk: 0,
  reward_badge_id: null,
})
const form = ref(emptyForm())

const teamAMembers = computed(() => members.value.filter(m => m.team === 'A'))
const teamBMembers = computed(() => members.value.filter(m => m.team === 'B'))
const usedIds = computed(() => new Set(members.value.map(m => m.user_id)))
const availableUsers = computed(() => allUsers.value.filter(u => !usedIds.value.has(u.id) && u.role !== 'god'))

async function loadData() {
  try {
    const [qRes, uRes] = await Promise.all([getPartyQuests(), getUsers()])
    quests.value = qRes.data
    allUsers.value = uRes.data
  } catch (e) {
    console.error('Load error', e)
  }
}

function addMember(event, team) {
  const userId = parseInt(event.target.value)
  if (!userId) return
  const user = allUsers.value.find(u => u.id === userId)
  if (user) {
    members.value.push({ id: Date.now(), user_id: userId, team, name: `${user.name} ${user.surname || ''}`.trim() })
  }
  event.target.value = ''
}

function removeMember(tmpId, team) {
  members.value = members.value.filter(m => !(m.id === tmpId && m.team === team))
}

async function saveQuest() {
  if (!form.value.title || !form.value.start_date || !form.value.end_date) {
    alert('Please fill in title and dates')
    return
  }
  if (members.value.length < 2) {
    alert('Please add at least 1 member per team')
    return
  }
  saving.value = true
  const data = {
    ...form.value,
    members: members.value.map(m => ({ user_id: m.user_id, team: m.team })),
  }
  try {
    if (editId.value) {
      await updatePartyQuest(editId.value, data)
    } else {
      await createPartyQuest(data)
    }
    cancelForm()
    await loadData()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error saving quest')
  }
  saving.value = false
}

function editQuest(q) {
  editId.value = q.id
  form.value = {
    title: q.title, start_date: q.start_date, end_date: q.end_date,
    team_a_name: q.team_a_name, team_b_name: q.team_b_name,
    steps_goal: q.steps_goal || 0, gifts_goal: q.gifts_goal || 0,
    battles_goal: q.battles_goal || 0, thankyou_goal: q.thankyou_goal || 0,
    reward_gold: q.reward_gold, reward_mana: q.reward_mana,
    reward_str: q.reward_str, reward_def: q.reward_def, reward_luk: q.reward_luk,
    reward_badge_id: q.reward_badge_id,
  }
  members.value = q.members.map(m => ({ id: m.id, user_id: m.user_id, team: m.team, name: m.name }))
  showForm.value = true
}

async function deleteQuest(id) {
  if (!confirm('Delete this quest?')) return
  try {
    await apiDeleteQuest(id)
    await loadData()
  } catch (e) {
    alert('Error deleting quest')
  }
}

function cancelForm() {
  showForm.value = false
  editId.value = null
  form.value = emptyForm()
  members.value = []
}

onMounted(loadData)
</script>

<style scoped>
.party-quest-admin {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}
h1 { font-size: 1.8rem; margin-bottom: 20px; }
.card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 16px;
}
.quest-form h2 { font-size: 1.3rem; margin-bottom: 16px; color: #60a5fa; }
.quest-form h3 { font-size: 1rem; margin: 16px 0 8px; color: #a78bfa; }
.hint { font-size: 0.8rem; color: #888; }

.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 0.85rem; color: #aaa; margin-bottom: 4px; }
.form-row input, .add-member-select {
  width: 100%; padding: 10px 12px; font-size: 0.95rem;
  background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15);
  border-radius: 8px; color: #fff; outline: none;
}
.form-row input:focus, .add-member-select:focus {
  border-color: #60a5fa;
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.goals-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.goal-item label { display: block; font-size: 0.8rem; color: #aaa; margin-bottom: 2px; }
.goal-item input {
  width: 100%; padding: 8px; font-size: 0.9rem;
  background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15);
  border-radius: 8px; color: #fff; text-align: center;
}

.teams-container { display: flex; gap: 12px; align-items: flex-start; margin-top: 8px; }
.team-column { flex: 1; background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px; min-height: 120px; }
.team-a { border-left: 3px solid #f59e0b; }
.team-b { border-left: 3px solid #3b82f6; }
.team-column h4 { font-size: 0.95rem; margin-bottom: 8px; }
.vs-divider {
  font-size: 1.5rem; font-weight: bold; color: #ef4444; padding-top: 40px;
  display: flex; align-items: center;
}
.member-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.chip {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  background: rgba(255,255,255,0.1); border-radius: 20px; font-size: 0.85rem;
}
.chip button { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 1rem; }
.add-member-select { font-size: 0.85rem; }
.add-member-select option { background: #1e1e2e; color: #fff; }

.form-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-create, .btn-save {
  padding: 10px 24px; font-size: 0.95rem; font-weight: 600;
  background: linear-gradient(135deg, #8b5cf6, #6366f1); color: #fff;
  border: none; border-radius: 10px; cursor: pointer;
  transition: transform 0.2s;
}
.btn-create:hover, .btn-save:hover { transform: translateY(-2px); }
.btn-cancel {
  padding: 10px 24px; font-size: 0.95rem; background: rgba(255,255,255,0.1);
  color: #fff; border: none; border-radius: 10px; cursor: pointer;
}
.btn-danger { color: #ef4444 !important; }

.quest-list { margin-top: 20px; }
.quest-card { transition: transform 0.2s; }
.quest-card:hover { transform: translateY(-2px); }
.quest-card.completed { opacity: 0.6; }
.quest-header { display: flex; justify-content: space-between; align-items: center; }
.quest-header h3 { font-size: 1.1rem; margin: 0; }
.quest-status {
  padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
}
.quest-status.active { background: #22c55e22; color: #22c55e; }
.quest-status.completed { background: #6b728022; color: #6b7280; }
.quest-status.cancelled { background: #ef444422; color: #ef4444; }
.quest-dates { font-size: 0.85rem; color: #888; margin: 6px 0; }
.quest-teams { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
.team-label { font-weight: 600; font-size: 0.9rem; }
.team-a-label { color: #f59e0b; }
.team-b-label { color: #3b82f6; }
.vs { color: #ef4444; font-weight: bold; }
.winner-badge {
  background: linear-gradient(135deg, #f59e0b22, #eab30822);
  color: #f59e0b; padding: 6px 14px; border-radius: 8px;
  font-weight: 600; font-size: 0.9rem; margin: 8px 0;
  display: inline-block;
}
.quest-actions { display: flex; gap: 8px; margin-top: 8px; }
.quest-actions button {
  padding: 6px 14px; font-size: 0.85rem; background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;
  color: #fff; cursor: pointer;
}
.empty { text-align: center; color: #888; padding: 40px; font-size: 1.1rem; }
</style>
