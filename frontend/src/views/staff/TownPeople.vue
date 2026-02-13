<template>
  <div class="staff-page">
    <div class="tp-header">
      <router-link to="/staff/services" class="tp-back">← Back</router-link>
      <h1 class="page-title">🏘️ Town People</h1>
      <p class="page-sub">Fellow adventurers of the realm</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Gathering townsfolk...</p>
    </div>

    <div v-else class="people-grid">
      <div v-for="p in people" :key="p.id" class="person-card" @click="selectedPerson = p">
        <!-- Portrait -->
        <div class="person-portrait">
          <img v-if="p.image" :src="p.image" class="person-img" />
          <div v-else class="person-placeholder">{{ (p.name || '?').charAt(0) }}</div>
          <span class="person-role-tag" :class="p.role">{{ p.role }}</span>
        </div>

        <!-- Info -->
        <div class="person-name">{{ p.name }}</div>
        <div class="person-surname">{{ p.surname }}</div>
        <div class="person-position">{{ p.position }}</div>

        <!-- Stats Row -->
        <div class="person-stats">
          <span class="ps str">⚔️ {{ p.stats.total_str }}</span>
          <span class="ps def">🛡️ {{ p.stats.total_def }}</span>
          <span class="ps luk">🍀 {{ p.stats.total_luk }}</span>
        </div>

        <!-- Badges -->
        <div class="person-badges" v-if="p.badges.length">
          <div v-for="b in p.badges.slice(0, 5)" :key="b.id" class="pb-circle" :title="b.name">
            <img v-if="b.image" :src="b.image" class="pb-img" />
            <span v-else>🏅</span>
          </div>
          <span v-if="p.badges.length > 5" class="pb-more">+{{ p.badges.length - 5 }}</span>
        </div>
        <div v-else class="person-no-badges">No badges yet</div>

        <!-- Currency -->
        <div class="person-currency">
          <span class="cur gold">💰 {{ p.coins }}</span>
          <span class="cur mana">✨ {{ p.angel_coins }}</span>
        </div>
      </div>
    </div>

    <!-- Staff Detail Modal -->
    <div v-if="selectedPerson" class="modal-overlay" @click.self="selectedPerson = null">
      <div class="modal-content">
        <button class="modal-close" @click="selectedPerson = null">✕</button>

        <!-- Portrait -->
        <div class="modal-portrait">
          <img v-if="selectedPerson.image" :src="selectedPerson.image" class="modal-avatar" />
          <div v-else class="modal-avatar-ph">{{ (selectedPerson.name || '?').charAt(0) }}</div>
          <span class="modal-role" :class="selectedPerson.role">{{ selectedPerson.role }}</span>
        </div>

        <div class="modal-name">{{ selectedPerson.name }}</div>
        <div class="modal-surname">{{ selectedPerson.surname }}</div>
        <div class="modal-position">{{ selectedPerson.position }}</div>

        <!-- Stats -->
        <div class="modal-section-title">⚔️ Stats</div>
        <div class="modal-stats">
          <div class="ms-item str"><span class="ms-label">STR</span><span class="ms-val">{{ selectedPerson.stats.total_str }}</span></div>
          <div class="ms-item def"><span class="ms-label">DEF</span><span class="ms-val">{{ selectedPerson.stats.total_def }}</span></div>
          <div class="ms-item luk"><span class="ms-label">LUK</span><span class="ms-val">{{ selectedPerson.stats.total_luk }}</span></div>
        </div>

        <!-- Currency -->
        <div class="modal-section-title">💰 Currency</div>
        <div class="modal-currency">
          <span class="mc gold">💰 {{ selectedPerson.coins }} Gold</span>
          <span class="mc mana">✨ {{ selectedPerson.angel_coins }} Mana</span>
        </div>

        <!-- Badges -->
        <div class="modal-section-title">🏅 Badges ({{ selectedPerson.badges.length }})</div>
        <div v-if="selectedPerson.badges.length" class="modal-badges">
          <div v-for="b in selectedPerson.badges" :key="b.id" class="mb-item">
            <div class="mb-icon">
              <img v-if="b.image" :src="b.image" class="mb-img" />
              <span v-else>🏅</span>
            </div>
            <div class="mb-info">
              <div class="mb-name">{{ b.name }}</div>
              <div v-if="b.bonus_str || b.bonus_def || b.bonus_luk" class="mb-bonus">
                <span v-if="b.bonus_str" class="bonus str">STR +{{ b.bonus_str }}</span>
                <span v-if="b.bonus_def" class="bonus def">DEF +{{ b.bonus_def }}</span>
                <span v-if="b.bonus_luk" class="bonus luk">LUK +{{ b.bonus_luk }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="modal-no-badges">No badges earned yet</div>
      </div>
    </div>
  </div>
</template>

<script>
import { getTownPeople } from '../../services/api'

export default {
  name: 'TownPeople',
  data() {
    return {
      people: [],
      loading: true,
      selectedPerson: null,
    }
  },
  async mounted() {
    try {
      const { data } = await getTownPeople()
      this.people = data
    } catch (e) {
      console.error('Failed to load town people', e)
    } finally {
      this.loading = false
    }
  },
}
</script>

<style scoped>
.staff-page { padding: 16px 0; }

.tp-header { margin-bottom: 20px; }
.tp-back {
  display: inline-block; margin-bottom: 8px;
  color: #b8860b; font-weight: 700; font-size: 13px;
  text-decoration: none; opacity: 0.8;
}
.tp-back:hover { opacity: 1; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 24px; font-weight: 800; color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub {
  color: #8b7355; font-size: 13px; font-weight: 600;
  font-style: italic;
}

.loading-state {
  text-align: center; padding: 60px 0; color: #8b7355;
}
.loading-spinner {
  width: 32px; height: 32px; border: 3px solid rgba(212,164,76,0.2);
  border-top-color: #d4a44c; border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Grid */
.people-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* Card */
.person-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 18px 14px 14px;
  display: flex; flex-direction: column; align-items: center;
  transition: all 0.2s;
  cursor: pointer;
}
.person-card:hover {
  border-color: rgba(212,164,76,0.4);
  box-shadow: 0 6px 24px rgba(212,164,76,0.1);
  transform: translateY(-2px);
}

/* Portrait */
.person-portrait {
  position: relative; margin-bottom: 10px;
}
.person-img {
  width: 56px; height: 56px; border-radius: 50%;
  object-fit: cover; border: 2px solid rgba(212,164,76,0.3);
}
.person-placeholder {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 800; color: #1c1208;
}
.person-role-tag {
  position: absolute; bottom: -4px; left: 50%; transform: translateX(-50%);
  font-size: 9px; font-weight: 800; padding: 1px 6px;
  border-radius: 6px; text-transform: uppercase;
  white-space: nowrap;
}
.person-role-tag.admin {
  background: linear-gradient(135deg, #c0392b, #e74c3c); color: #fff;
}
.person-role-tag.staff {
  background: linear-gradient(135deg, #27ae60, #2ecc71); color: #fff;
}
.person-role-tag.manager {
  background: linear-gradient(135deg, #2980b9, #3498db); color: #fff;
}

/* Name & Position */
.person-name {
  font-family: 'Cinzel', serif;
  font-size: 13px; font-weight: 700; color: #e8d5b7;
  text-align: center; margin-bottom: 0;
  line-height: 1.3;
}
.person-surname {
  font-family: 'Cinzel', serif;
  font-size: 12px; font-weight: 600; color: #c4b08a;
  text-align: center; margin-bottom: 2px;
  line-height: 1.3;
}
.person-position {
  font-size: 11px; color: #8b7355; font-weight: 600;
  margin-bottom: 8px; text-align: center;
}

/* Stats */
.person-stats {
  display: flex; gap: 6px; margin-bottom: 8px;
}
.ps {
  font-size: 10px; font-weight: 700; padding: 2px 6px;
  border-radius: 6px; display: flex; align-items: center; gap: 2px;
}
.ps.str { background: rgba(231,76,60,0.1); color: #e74c3c; }
.ps.def { background: rgba(52,152,219,0.1); color: #3498db; }
.ps.luk { background: rgba(46,204,113,0.1); color: #2ecc71; }

/* Badges */
.person-badges {
  display: flex; gap: 4px; align-items: center;
  margin-bottom: 8px; flex-wrap: wrap; justify-content: center;
}
.pb-circle {
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(212,164,76,0.1); border: 1px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; font-size: 12px;
}
.pb-img { width: 100%; height: 100%; object-fit: cover; }
.pb-more { font-size: 10px; color: #b8860b; font-weight: 700; }
.person-no-badges {
  font-size: 10px; color: #6b5a3e; font-style: italic;
  margin-bottom: 8px;
}

/* Currency */
.person-currency {
  display: flex; gap: 10px;
}
.cur {
  font-size: 11px; font-weight: 700;
}
.cur.gold { color: #d4a44c; }
.cur.mana { color: #9b59b6; }

@media (min-width: 540px) {
  .people-grid { grid-template-columns: repeat(3, 1fr); }
}

/* ── Staff Detail Modal ───────────────────────── */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 16px;
  animation: fadeIn 0.2s ease;
}
.modal-content {
  background: linear-gradient(145deg, #1a0a2e, #2c1810);
  border: 2px solid rgba(212,164,76,0.3);
  border-radius: 18px;
  padding: 28px 22px;
  max-width: 360px; width: 100%;
  max-height: 80vh; overflow-y: auto;
  position: relative;
  box-shadow: 0 0 40px rgba(212,164,76,0.15);
}
.modal-close {
  position: absolute; top: 12px; right: 14px;
  background: none; border: none; color: #8b7355;
  font-size: 18px; cursor: pointer; padding: 4px;
}
.modal-close:hover { color: #e8d5b7; }

.modal-portrait {
  display: flex; flex-direction: column; align-items: center;
  margin-bottom: 12px;
}
.modal-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  object-fit: cover; border: 3px solid rgba(212,164,76,0.4);
}
.modal-avatar-ph {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; font-weight: 800; color: #1c1208;
}
.modal-role {
  margin-top: 6px; font-size: 10px; font-weight: 800;
  padding: 2px 10px; border-radius: 8px; text-transform: uppercase;
}
.modal-role.admin { background: linear-gradient(135deg, #c0392b, #e74c3c); color: #fff; }
.modal-role.staff { background: linear-gradient(135deg, #27ae60, #2ecc71); color: #fff; }
.modal-role.manager { background: linear-gradient(135deg, #2980b9, #3498db); color: #fff; }

.modal-name {
  font-family: 'Cinzel', serif;
  font-size: 18px; font-weight: 800; color: #e8d5b7;
  text-align: center; line-height: 1.3;
}
.modal-surname {
  font-family: 'Cinzel', serif;
  font-size: 14px; font-weight: 600; color: #c4b08a;
  text-align: center; margin-bottom: 2px;
}
.modal-position {
  font-size: 12px; color: #8b7355; font-weight: 600;
  text-align: center; margin-bottom: 14px;
}

.modal-section-title {
  font-family: 'Cinzel', serif;
  font-size: 12px; font-weight: 700; color: #d4a44c;
  margin-bottom: 8px; padding-bottom: 4px;
  border-bottom: 1px solid rgba(212,164,76,0.15);
}

/* Stats */
.modal-stats {
  display: flex; gap: 8px; margin-bottom: 14px; justify-content: center;
}
.ms-item {
  flex: 1; padding: 8px 0; border-radius: 10px;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.ms-item.str { background: rgba(231,76,60,0.1); }
.ms-item.def { background: rgba(52,152,219,0.1); }
.ms-item.luk { background: rgba(46,204,113,0.1); }
.ms-label { font-size: 10px; font-weight: 700; color: #8b7355; }
.ms-item.str .ms-val { color: #e74c3c; }
.ms-item.def .ms-val { color: #3498db; }
.ms-item.luk .ms-val { color: #2ecc71; }
.ms-val { font-size: 20px; font-weight: 800; }

/* Currency */
.modal-currency {
  display: flex; gap: 16px; margin-bottom: 14px; justify-content: center;
}
.mc { font-size: 13px; font-weight: 700; }
.mc.gold { color: #d4a44c; }
.mc.mana { color: #9b59b6; }

/* Badges */
.modal-badges {
  display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px;
}
.mb-item {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 10px; border-radius: 10px;
  background: rgba(212,164,76,0.05);
  border: 1px solid rgba(212,164,76,0.1);
}
.mb-icon {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: rgba(212,164,76,0.1); border: 1px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; font-size: 16px;
}
.mb-img { width: 100%; height: 100%; object-fit: cover; }
.mb-name {
  font-size: 12px; font-weight: 700; color: #e8d5b7;
}
.mb-bonus {
  display: flex; gap: 6px; margin-top: 2px;
}
.bonus {
  font-size: 9px; font-weight: 700; padding: 1px 5px;
  border-radius: 4px;
}
.bonus.str { background: rgba(231,76,60,0.15); color: #e74c3c; }
.bonus.def { background: rgba(52,152,219,0.15); color: #3498db; }
.bonus.luk { background: rgba(46,204,113,0.15); color: #2ecc71; }
.modal-no-badges {
  font-size: 12px; color: #6b5a3e; font-style: italic;
  text-align: center; padding: 8px 0;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
