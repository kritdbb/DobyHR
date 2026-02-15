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
        <div v-if="p.status_text" class="person-status">"{{ p.status_text }}"</div>

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

    <!-- ═══════ RPG Character Sheet Modal ═══════ -->
    <div v-if="selectedPerson" class="modal-overlay" @click.self="selectedPerson = null">
      <div class="char-sheet">
        <button class="sheet-close" @click="selectedPerson = null">✕</button>

        <!-- Decorative corners -->
        <div class="corner tl"></div><div class="corner tr"></div>
        <div class="corner bl"></div><div class="corner br"></div>

        <!-- Portrait -->
        <div class="portrait-frame">
          <div class="portrait-glow"></div>
          <div class="portrait-ring">
            <img v-if="selectedPerson.image" :src="selectedPerson.image" class="portrait-img" />
            <div v-else class="portrait-ph">{{ (selectedPerson.name || '?').charAt(0) }}</div>
          </div>
          <div class="rank-plate" :class="selectedPerson.role">{{ selectedPerson.role }}</div>
        </div>

        <!-- Identity -->
        <div class="char-identity">
          <div class="char-name">{{ selectedPerson.name }} {{ selectedPerson.surname }}</div>
          <div class="char-title">〈 {{ selectedPerson.position }} 〉</div>
          <div v-if="selectedPerson.status_text" class="char-quote">「{{ selectedPerson.status_text }}」</div>
        </div>

        <div class="sheet-divider"></div>

        <!-- Stat Bars -->
        <div class="stat-panel">
          <div class="stat-row">
            <span class="stat-icon">⚔️</span>
            <span class="stat-label str">STR</span>
            <div class="stat-bar-track">
              <div class="stat-bar-fill str" :style="{ width: Math.min(selectedPerson.stats.total_str, 100) + '%' }"></div>
            </div>
            <span class="stat-num str">{{ selectedPerson.stats.total_str }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-icon">🛡️</span>
            <span class="stat-label def">DEF</span>
            <div class="stat-bar-track">
              <div class="stat-bar-fill def" :style="{ width: Math.min(selectedPerson.stats.total_def, 100) + '%' }"></div>
            </div>
            <span class="stat-num def">{{ selectedPerson.stats.total_def }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-icon">🍀</span>
            <span class="stat-label luk">LUK</span>
            <div class="stat-bar-track">
              <div class="stat-bar-fill luk" :style="{ width: Math.min(selectedPerson.stats.total_luk, 100) + '%' }"></div>
            </div>
            <span class="stat-num luk">{{ selectedPerson.stats.total_luk }}</span>
          </div>
        </div>

        <div class="sheet-divider"></div>

        <!-- Currency -->
        <div class="currency-row">
          <div class="cur-block gold">
            <span class="cur-val">{{ selectedPerson.coins.toLocaleString() }}</span>
            <span class="cur-lbl">💰 Gold</span>
          </div>
          <div class="cur-sep"></div>
          <div class="cur-block mana">
            <span class="cur-val">{{ selectedPerson.angel_coins.toLocaleString() }}</span>
            <span class="cur-lbl">✨ Mana</span>
          </div>
        </div>

        <div class="sheet-divider"></div>

        <!-- Equipment -->
        <div class="equip-header">
          <span>🏅 Equipment</span>
          <span class="equip-count">{{ selectedPerson.badges.length }}</span>
        </div>

        <div v-if="selectedPerson.badges.length" class="equip-list">
          <div v-for="b in selectedPerson.badges" :key="b.id" class="equip-card">
            <div class="eq-icon">
              <img v-if="b.image" :src="b.image" class="eq-icon-img" />
              <span v-else>🏅</span>
            </div>
            <div class="eq-body">
              <div class="eq-name">{{ b.name }}</div>
              <div v-if="b.description" class="eq-desc">{{ b.description }}</div>
            </div>
            <div v-if="b.bonus_str || b.bonus_def || b.bonus_luk" class="eq-bonuses">
              <span v-if="b.bonus_str" class="eqb str">⚔️+{{ b.bonus_str }}</span>
              <span v-if="b.bonus_def" class="eqb def">🛡️+{{ b.bonus_def }}</span>
              <span v-if="b.bonus_luk" class="eqb luk">🍀+{{ b.bonus_luk }}</span>
            </div>
          </div>
        </div>
        <div v-else class="equip-empty">— No equipment found —</div>
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
.person-role-tag.god {
  background: linear-gradient(135deg, #b8860b, #d4a44c); color: #1c1208;
}
.person-role-tag.gm {
  background: linear-gradient(135deg, #2980b9, #3498db); color: #fff;
}
.person-role-tag.player {
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
  margin-bottom: 4px; text-align: center;
}
.person-status {
  font-size: 10px; color: #e74c3c; font-style: italic;
  font-weight: 600; margin-bottom: 6px; text-align: center;
  word-break: break-word; line-height: 1.3;
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

/* ═══════════════════════════════════════════════════
   RPG CHARACTER SHEET MODAL
   ═══════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999; padding: 16px;
  animation: fadeIn 0.25s ease;
}

.char-sheet {
  position: relative;
  background:
    linear-gradient(170deg, #110a1e 0%, #1e0e0a 40%, #0f0f1e 100%);
  border: 2px solid #d4a44c;
  border-radius: 4px;
  padding: 32px 24px 24px;
  max-width: 380px; width: 100%;
  max-height: 85vh; overflow-y: auto;
  box-shadow:
    0 0 0 1px rgba(212,164,76,0.15),
    0 0 60px rgba(212,164,76,0.08),
    inset 0 0 80px rgba(0,0,0,0.3);
}

/* Corner ornaments */
.corner {
  position: absolute; width: 16px; height: 16px;
  border-color: #d4a44c; border-style: solid;
}
.corner.tl { top: -1px; left: -1px; border-width: 3px 0 0 3px; }
.corner.tr { top: -1px; right: -1px; border-width: 3px 3px 0 0; }
.corner.bl { bottom: -1px; left: -1px; border-width: 0 0 3px 3px; }
.corner.br { bottom: -1px; right: -1px; border-width: 0 3px 3px 0; }

.sheet-close {
  position: absolute; top: 8px; right: 12px;
  background: none; border: none; color: #6b5a3e;
  font-size: 20px; cursor: pointer; z-index: 2;
  transition: color 0.15s;
}
.sheet-close:hover { color: #e8d5b7; }

/* ── Portrait ── */
.portrait-frame {
  display: flex; flex-direction: column; align-items: center;
  margin-bottom: 14px; position: relative;
}
.portrait-glow {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -55%);
  width: 120px; height: 120px; border-radius: 50%;
  background: radial-gradient(circle, rgba(212,164,76,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.portrait-ring {
  width: 88px; height: 88px; border-radius: 50%;
  border: 3px solid #d4a44c;
  box-shadow: 0 0 20px rgba(212,164,76,0.25), inset 0 0 16px rgba(0,0,0,0.4);
  overflow: hidden; position: relative; z-index: 1;
}
.portrait-img {
  width: 100%; height: 100%; object-fit: cover;
}
.portrait-ph {
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; font-weight: 800; color: #1c1208;
}
.rank-plate {
  margin-top: 6px; font-size: 10px; font-weight: 800;
  padding: 3px 14px; border-radius: 3px;
  text-transform: uppercase; letter-spacing: 1.5px;
  border: 1px solid; position: relative; z-index: 1;
}
.rank-plate.god {
  background: linear-gradient(135deg, #8b6914, #d4a44c);
  border-color: #ffd700; color: #1c1208;
  box-shadow: 0 0 10px rgba(212,164,76,0.4);
}
.rank-plate.gm {
  background: linear-gradient(135deg, #1a3a5c, #2980b9);
  border-color: #3498db; color: #d5e8ff;
  box-shadow: 0 0 10px rgba(52,152,219,0.3);
}
.rank-plate.player {
  background: linear-gradient(135deg, #1a5c2e, #27ae60);
  border-color: #2ecc71; color: #d5ffe0;
  box-shadow: 0 0 10px rgba(46,204,113,0.3);
}

/* ── Identity ── */
.char-identity { text-align: center; margin-bottom: 4px; }
.char-name {
  font-family: 'Cinzel', serif;
  font-size: 20px; font-weight: 800; color: #e8d5b7;
  text-shadow: 0 2px 12px rgba(212,164,76,0.3);
  line-height: 1.3;
}
.char-title {
  font-size: 12px; color: #b8860b; font-weight: 600;
  letter-spacing: 0.5px; margin-top: 2px;
}
.char-quote {
  font-size: 11px; color: #e74c3c; font-style: italic;
  font-weight: 600; margin-top: 4px;
  word-break: break-word;
}

.sheet-divider {
  height: 1px; margin: 14px 0;
  background: linear-gradient(90deg, transparent 0%, rgba(212,164,76,0.3) 50%, transparent 100%);
}

/* ── Stat Bars ── */
.stat-panel { display: flex; flex-direction: column; gap: 8px; }
.stat-row {
  display: flex; align-items: center; gap: 8px;
}
.stat-icon { font-size: 14px; width: 18px; text-align: center; }
.stat-label {
  font-family: 'Cinzel', serif; font-size: 11px; font-weight: 800;
  width: 30px; letter-spacing: 1px;
}
.stat-label.str { color: #e74c3c; }
.stat-label.def { color: #3498db; }
.stat-label.luk { color: #2ecc71; }

.stat-bar-track {
  flex: 1; height: 10px; border-radius: 5px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
}
.stat-bar-fill {
  height: 100%; border-radius: 4px;
  transition: width 0.6s ease;
}
.stat-bar-fill.str {
  background: linear-gradient(90deg, #8b1a1a, #e74c3c);
  box-shadow: 0 0 6px rgba(231,76,60,0.4);
}
.stat-bar-fill.def {
  background: linear-gradient(90deg, #1a3a5c, #3498db);
  box-shadow: 0 0 6px rgba(52,152,219,0.4);
}
.stat-bar-fill.luk {
  background: linear-gradient(90deg, #1a5c2e, #2ecc71);
  box-shadow: 0 0 6px rgba(46,204,113,0.4);
}

.stat-num {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 800;
  width: 30px; text-align: right;
}
.stat-num.str { color: #e74c3c; }
.stat-num.def { color: #3498db; }
.stat-num.luk { color: #2ecc71; }

/* ── Currency ── */
.currency-row {
  display: flex; align-items: center; justify-content: center;
  gap: 0;
}
.cur-block {
  flex: 1; text-align: center;
}
.cur-val {
  display: block;
  font-family: 'Cinzel', serif; font-size: 26px; font-weight: 800;
  line-height: 1.2;
}
.cur-lbl {
  display: block; font-size: 11px; font-weight: 600; margin-top: 2px;
}
.cur-block.gold .cur-val { color: #d4a44c; }
.cur-block.gold .cur-lbl { color: #8b7355; }
.cur-block.mana .cur-val { color: #9b59b6; }
.cur-block.mana .cur-lbl { color: #7d5a8e; }
.cur-sep {
  width: 1px; height: 36px;
  background: linear-gradient(180deg, transparent, rgba(212,164,76,0.3), transparent);
}

/* ── Equipment ── */
.equip-header {
  font-family: 'Cinzel', serif;
  font-size: 13px; font-weight: 700; color: #d4a44c;
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
}
.equip-count {
  background: rgba(212,164,76,0.15); border: 1px solid rgba(212,164,76,0.25);
  color: #d4a44c; font-size: 10px; font-weight: 800;
  padding: 1px 7px; border-radius: 10px;
}

.equip-list { display: flex; flex-direction: column; gap: 6px; }

.equip-card {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 6px;
  background: linear-gradient(135deg, rgba(212,164,76,0.04), rgba(212,164,76,0.08));
  border: 1px solid rgba(212,164,76,0.12);
  position: relative;
  transition: border-color 0.2s;
}
.equip-card:hover {
  border-color: rgba(212,164,76,0.3);
}

.eq-icon {
  width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; font-size: 18px;
}
.eq-icon-img { width: 100%; height: 100%; object-fit: cover; }

.eq-body { flex: 1; min-width: 0; }
.eq-name {
  font-size: 12px; font-weight: 700; color: #e8d5b7;
}
.eq-desc {
  font-size: 10px; color: #8b7355; font-weight: 500;
  margin-top: 1px; line-height: 1.3;
  overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
}

.eq-bonuses {
  display: flex; flex-direction: column; gap: 2px;
  flex-shrink: 0;
}
.eqb {
  font-size: 9px; font-weight: 800; padding: 1px 5px;
  border-radius: 3px; text-align: center; white-space: nowrap;
}
.eqb.str { background: rgba(231,76,60,0.12); color: #e74c3c; }
.eqb.def { background: rgba(52,152,219,0.12); color: #3498db; }
.eqb.luk { background: rgba(46,204,113,0.12); color: #2ecc71; }

.equip-empty {
  font-size: 12px; color: #6b5a3e; font-style: italic;
  text-align: center; padding: 12px 0;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
