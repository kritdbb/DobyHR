<template>
  <div class="staff-page">
    <div class="tp-header">
      <router-link to="/staff/services" class="tp-back">← Back</router-link>
      <h1 class="page-title">🏘️ Town People</h1>
      <p class="page-sub">Fellow adventurers of the realm</p>
    </div>

    <!-- Matchmaking Card -->
    <div class="matchmake-card">
      <div class="matchmake-bg"></div>
      <div class="matchmake-overlay">
        <div class="matchmake-content">
          <div class="matchmake-title">⚔️ BATTLE ARENA</div>
          <div class="matchmake-rewards">
            <span class="reward-tag winner-tag">🏆 Winner +5 Gold</span>
            <span class="reward-tag loser-tag">💀 Loser -5 Gold</span>
          </div>
          <div class="matchmake-desc">สุ่มคู่ต่อสู้ วันละ 1 ครั้ง</div>
          <button class="btn-matchmake" :disabled="alreadyBattled || matchmaking" @click="startMatchmaking">
            {{ alreadyBattled ? '⚔️ ต่อสู้แล้ววันนี้' : (matchmaking ? '⏳ กำลังหาคู่ต่อสู้...' : '⚔️ Match Making') }}
          </button>
          <div v-if="alreadyBattled && lastBattleId" class="rematch-link">
            <router-link :to="'/staff/arena/' + lastBattleId" class="view-last-battle">📺 ดู replay ล่าสุด</router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Spin Wheel Modal -->
    <div v-if="showWheel" class="wheel-overlay" @click.self="cancelWheel">
      <div class="wheel-container">
        <div class="wheel-title">⚔️ สุ่มคู่ต่อสู้...</div>
        <div class="wheel-stage">
          <div class="wheel-pointer">▼</div>
          <div class="wheel-ring" :style="{ transform: 'rotate(' + wheelAngle + 'deg)', transition: wheelTransition }">
            <div v-for="(p, i) in wheelPlayers" :key="p.id" class="wheel-slot"
              :style="slotStyle(i)" :class="{ selected: wheelDone && wheelSelectedIdx === i }">
              <img v-if="p.image" :src="p.image" class="wheel-avatar" />
              <div v-else class="wheel-avatar-ph">{{ (p.name || '?').charAt(0) }}</div>
              <div class="wheel-name">{{ p.name }}</div>
            </div>
          </div>
        </div>
        <div v-if="wheelDone" class="wheel-result">
          <div class="vs-flash">⚔️ VS {{ wheelPlayers[wheelSelectedIdx]?.name }}!</div>
          <button class="btn-fight-now" @click="executeMatchmake">⚔️ FIGHT!</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Gathering townsfolk...</p>
    </div>

    <div v-else class="people-grid">
      <div v-for="p in people" :key="p.id" class="person-card" @click="selectedPerson = p"
        :style="p.magic_background ? { backgroundImage: 'linear-gradient(rgba(17,10,30,0.65), rgba(17,10,30,0.8)), url(' + apiBase + p.magic_background + ')', backgroundSize: 'cover', backgroundPosition: 'center' } : {}">
        <!-- Portrait -->
        <div class="person-portrait">
          <img v-if="p.circle_artifact && getArtifactImage(p.circle_artifact)" :src="getArtifactImage(p.circle_artifact)" class="person-artifact-ring-img" :class="'effect-' + getArtifactEffect(p)" />
          <div v-else-if="p.circle_artifact" class="person-artifact-ring" :class="'effect-' + getArtifactEffect(p)" :style="{ borderColor: getArtifactColor(p.circle_artifact), boxShadow: '0 0 14px ' + getArtifactColor(p.circle_artifact) + '66' }"></div>
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
      <div class="char-sheet" :style="selectedPerson.magic_background ? { backgroundImage: 'linear-gradient(rgba(17,10,30,0.55), rgba(17,10,30,0.75)), url(' + apiBase + selectedPerson.magic_background + ')', backgroundSize: 'cover', backgroundPosition: 'center' } : {}">
        <button class="sheet-close" @click="selectedPerson = null">✕</button>

        <!-- Decorative corners -->
        <div class="corner tl"></div><div class="corner tr"></div>
        <div class="corner bl"></div><div class="corner br"></div>

        <!-- Portrait -->
        <div class="portrait-frame">
          <div class="portrait-glow"></div>
          <img v-if="selectedPerson.circle_artifact && getArtifactImage(selectedPerson.circle_artifact)" :src="getArtifactImage(selectedPerson.circle_artifact)" class="portrait-artifact-ring-img" :class="'effect-' + getArtifactEffect(selectedPerson)" />
          <div v-else-if="selectedPerson.circle_artifact" class="portrait-artifact-ring" :class="'effect-' + getArtifactEffect(selectedPerson)"
            :style="{ borderColor: getArtifactColor(selectedPerson.circle_artifact), boxShadow: '0 0 24px ' + getArtifactColor(selectedPerson.circle_artifact) + '55' }"></div>
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

        <!-- Gift Mana Button (hide for self) -->
        <button v-if="selectedPerson.id !== currentUserId && !showGiftForm" class="gift-mana-btn" @click="openGiftForm()">
          ✨ Gift Mana
        </button>

        <!-- Gift Mana Form -->
        <div v-if="showGiftForm" class="gift-form">
          <div class="gift-form-title">✨ Gift Mana to {{ selectedPerson.name }}</div>
          <div class="gift-field">
            <label>Amount</label>
            <input v-model.number="giftAmount" type="number" min="1" class="gift-input" placeholder="0" />
            <div class="gift-balance">Your Mana: {{ myMana }}</div>
          </div>
          <div class="gift-field">
            <label>Comment</label>
            <input v-model="giftComment" type="text" class="gift-input" placeholder="Say something nice..." />
          </div>
          <div class="gift-field">
            <label>Deliver as</label>
            <div class="delivery-toggle">
              <button :class="['dt-btn', giftDeliveryType === 'gold' ? 'active gold' : '']" @click="giftDeliveryType = 'gold'">💰 Gold</button>
              <button :class="['dt-btn', giftDeliveryType === 'mana' ? 'active mana' : '']" @click="giftDeliveryType = 'mana'">✨ Mana</button>
            </div>
          </div>
          <div class="gift-actions">
            <button class="gift-cancel" @click="resetGift()">Cancel</button>
            <button class="gift-confirm" :disabled="!giftAmount || giftAmount <= 0 || giftAmount > myMana || giftSending" @click="confirmGift()">
              {{ giftSending ? 'Sending...' : '✨ Confirm' }}
            </button>
          </div>
        </div>

        <!-- Social Buttons (hide for self) -->
        <div v-if="selectedPerson.id !== currentUserId" class="social-buttons">
          <button class="social-btn thank-you" :disabled="thankYouSent || thankYouSending" @click="handleThankYou()">
            {{ thankYouSending ? '送出中...' : (thankYouSent ? '✅ ส่งแล้วสัปดาห์นี้' : '💌 Thank You Card') }}
          </button>
          <button class="social-btn anon-praise" :disabled="praiseSentToday || praiseSending" @click="showPraiseModal = true">
            {{ praiseSentToday ? '✅ ส่งแล้ววันนี้' : '💬 Anonymous Praise' }}
          </button>
        </div>

        <!-- Anonymous Praise Modal -->
        <div v-if="showPraiseModal" class="praise-popup">
          <div class="praise-title">💬 Anonymous Praise</div>
          <div class="praise-hint">ประกาศถึง <strong>{{ selectedPerson.name }}</strong> ใน Town Crier โดยไม่เปิดเผยว่าใครเป็นคนประกาศ!</div>
          <textarea v-model="praiseMessage" class="praise-input" placeholder="พิมพ์ข้อความชื่นชม..." maxlength="200" rows="3"></textarea>
          <div class="praise-actions">
            <button class="gift-cancel" @click="showPraiseModal = false; praiseMessage = ''">Cancel</button>
            <button class="gift-confirm" :disabled="!praiseMessage.trim() || praiseSending" @click="handleAnonymousPraise()">{{ praiseSending ? 'Sending...' : '✉️ ส่ง' }}</button>
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
import api, { getTownPeople, sendAngelCoins, getUser, sendThankYouCard, getThankYouStatus, sendAnonymousPraise, getAnonymousPraiseStatus, getArtifactCatalog } from '../../services/api'

export default {
  name: 'TownPeople',
  inject: ['showToast'],
  data() {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return {
      people: [],
      loading: true,
      selectedPerson: null,
      currentUserId: user.user_id || user.id,
      myMana: 0,
      showGiftForm: false,
      giftAmount: null,
      giftComment: '',
      giftDeliveryType: 'gold',
      giftSending: false,
      apiBase: import.meta.env.VITE_API_URL || '',
      artifactCatalog: [],
      // Social features
      thankYouSent: false,
      thankYouSending: false,
      praiseSentToday: false,
      praiseSending: false,
      showPraiseModal: false,
      praiseMessage: '',
      // Matchmaking
      alreadyBattled: false,
      lastBattleId: null,
      matchmaking: false,
      showWheel: false,
      wheelPlayers: [],
      wheelAngle: 0,
      wheelTransition: 'none',
      wheelDone: false,
      wheelSelectedIdx: -1,
    }
  },
  async mounted() {
    try {
      const [peopleRes, catRes, statusRes] = await Promise.all([
        getTownPeople(),
        getArtifactCatalog(),
        api.get('/api/pvp/matchmake/status').catch(() => ({ data: {} })),
      ])
      this.people = peopleRes.data
      this.artifactCatalog = catRes.data
      if (statusRes.data) {
        this.alreadyBattled = statusRes.data.already_battled || false
        this.lastBattleId = statusRes.data.battle_id || null
      }
      await this.loadMyMana()
    } catch (e) {
      console.error('Failed to load town people', e)
    } finally {
      this.loading = false
    }
  },
  watch: {
    selectedPerson(val) {
      this.resetGift()
      this.showPraiseModal = false
      this.praiseMessage = ''
      if (val && val.id !== this.currentUserId) this.loadSocialStatus()
    },
  },
  methods: {
    resetGift() {
      this.showGiftForm = false
      this.giftAmount = null
      this.giftComment = ''
      this.giftDeliveryType = 'gold'
    },
    async loadMyMana() {
      try {
        if (!this.currentUserId) return
        const { data } = await getUser(this.currentUserId)
        this.myMana = data.angel_coins || 0
      } catch (e) {
        console.error('Failed to load mana', e)
      }
    },
    async openGiftForm() {
      await this.loadMyMana()
      this.showGiftForm = true
    },
    async confirmGift() {
      this.giftSending = true
      try {
        const res = await sendAngelCoins({
          recipient_id: this.selectedPerson.id,
          amount: this.giftAmount,
          comment: this.giftComment,
          delivery_type: this.giftDeliveryType,
        })
        this.myMana = res.data.sender_mana
        this.showToast(res.data.message, 'success')
        this.resetGift()
        // Refresh people list
        const { data } = await getTownPeople()
        this.people = data
        // Update selected person
        if (this.selectedPerson) {
          const updated = data.find(p => p.id === this.selectedPerson.id)
          if (updated) this.selectedPerson = updated
        }
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to send', 'error')
      } finally {
        this.giftSending = false
      }
    },
    getArtifactColor(artifactId) {
      const a = this.artifactCatalog.find(x => String(x.id) === String(artifactId))
      return a ? a.color : '#d4a44c'
    },
    getArtifactImage(artifactId) {
      const a = this.artifactCatalog.find(x => String(x.id) === String(artifactId))
      return a ? a.image : null
    },
    getArtifactEffect(person) {
      return person.artifact_effect || 'pulse'
    },
    async loadSocialStatus() {
      try {
        const [ty, ap] = await Promise.all([
          getThankYouStatus(),
          getAnonymousPraiseStatus(),
        ])
        this.thankYouSent = ty.data.sent_this_week
        this.praiseSentToday = ap.data.sent_today
      } catch (e) {
        console.error('Failed to load social status', e)
      }
    },
    async handleThankYou() {
      if (!confirm(`คุณแน่ใจว่าจะส่ง Thank You Card ให้ ${this.selectedPerson.name}? Thank You Card สามารถส่งได้แค่ 1 คนต่อสัปดาห์เท่านั้น!`)) return
      this.thankYouSending = true
      try {
        const { data } = await sendThankYouCard(this.selectedPerson.id)
        this.showToast(data.message, 'success')
        this.thankYouSent = true
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to send Thank You Card', 'error')
      } finally {
        this.thankYouSending = false
      }
    },
    async handleAnonymousPraise() {
      this.praiseSending = true
      try {
        const { data } = await sendAnonymousPraise({
          recipient_id: this.selectedPerson.id,
          message: this.praiseMessage,
        })
        this.showToast(data.message, 'success')
        this.praiseSentToday = true
        this.showPraiseModal = false
        this.praiseMessage = ''
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Failed to send praise', 'error')
      } finally {
        this.praiseSending = false
      }
    },
    // ─── Matchmaking ───────────────────────
    async startMatchmaking() {
      if (this.alreadyBattled || this.matchmaking) return
      this.matchmaking = true
      // Build wheel players: everyone except self
      this.wheelPlayers = this.people.filter(p => p.id !== this.currentUserId)
      if (this.wheelPlayers.length < 1) {
        this.showToast('ไม่มีคู่ต่อสู้', 'error')
        this.matchmaking = false
        return
      }
      // Pick random target (backend will pick its own, this is just visual)
      this.wheelSelectedIdx = Math.floor(Math.random() * this.wheelPlayers.length)
      this.wheelAngle = 0
      this.wheelTransition = 'none'
      this.wheelDone = false
      this.showWheel = true
      // Start spinning after a frame
      await this.$nextTick()
      requestAnimationFrame(() => {
        const count = this.wheelPlayers.length
        const slotAngle = 360 / count
        // Target angle: spin several full rotations + land on selected slot
        // Pointer is at top (0°), each slot i is at (i * slotAngle)°
        // We want the selected slot to be at the top → rotate by -(selectedIdx * slotAngle)
        const targetOffset = -(this.wheelSelectedIdx * slotAngle)
        const fullSpins = 360 * (5 + Math.floor(Math.random() * 3)) // 5-7 full spins
        this.wheelTransition = 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)'
        this.wheelAngle = fullSpins + targetOffset
      })
      // Wait for spin to finish
      setTimeout(() => {
        this.wheelDone = true
        this.matchmaking = false
      }, 4200)
    },
    cancelWheel() {
      if (!this.wheelDone) return // can't cancel during spin
      this.showWheel = false
      this.matchmaking = false
    },
    slotStyle(index) {
      const count = this.wheelPlayers.length
      const angle = (360 / count) * index
      const radius = Math.min(130, 100 + count * 2)
      return {
        transform: `rotate(${angle}deg) translateY(-${radius}px) rotate(-${angle}deg)`,
      }
    },
    async executeMatchmake() {
      try {
        const { data } = await api.post('/api/pvp/matchmake')
        this.showWheel = false
        this.alreadyBattled = true
        this.lastBattleId = data.battle_id
        this.$router.push(`/staff/arena/${data.battle_id}`)
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Matchmaking failed', 'error')
        this.showWheel = false
      }
    },
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
  width: 82px; height: 82px;
  display: flex; align-items: center; justify-content: center;
  overflow: visible;
}
.person-artifact-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 82px; height: 82px; border-radius: 50%;
  border: 3px solid; pointer-events: none; overflow: hidden;
  z-index: 0;
}
.person-artifact-ring-img {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 82px; height: 82px; border-radius: 50%;
  object-fit: cover; pointer-events: none; overflow: hidden;
  aspect-ratio: 1 / 1; z-index: 0;
}
.person-artifact-ring.effect-pulse,
.person-artifact-ring-img.effect-pulse {
  animation: artifactGlowPulse 3s ease-in-out infinite;
}
.person-artifact-ring.effect-spin,
.person-artifact-ring-img.effect-spin {
  animation: artifactGlowSpin 6s linear infinite;
}
.person-artifact-ring.effect-glow,
.person-artifact-ring-img.effect-glow {
  animation: artifactGlowGlow 2s ease-in-out infinite;
}
.person-artifact-ring.effect-bounce,
.person-artifact-ring-img.effect-bounce {
  animation: artifactGlowBounce 2s ease-in-out infinite;
}
.person-artifact-ring.effect-shake,
.person-artifact-ring-img.effect-shake {
  animation: artifactGlowShake 0.6s ease-in-out infinite;
}
.person-artifact-ring.effect-rainbow,
.person-artifact-ring-img.effect-rainbow {
  animation: artifactGlowRainbow 4s linear infinite;
}
@keyframes artifactGlowPulse {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.06); }
}
@keyframes artifactGlowSpin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}
@keyframes artifactGlowGlow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%); filter: brightness(1); }
  50% { opacity: 1; transform: translate(-50%, -50%); filter: brightness(1.4) drop-shadow(0 0 16px currentColor); }
}
@keyframes artifactGlowBounce {
  0%, 100% { transform: translate(-50%, -50%); }
  50% { transform: translate(-50%, calc(-50% - 6px)); }
}
@keyframes artifactGlowShake {
  0%, 100% { transform: translate(-50%, -50%); }
  25% { transform: translate(calc(-50% - 3px), -50%) rotate(-2deg); }
  75% { transform: translate(calc(-50% + 3px), -50%) rotate(2deg); }
}
@keyframes artifactGlowRainbow {
  from { transform: translate(-50%, -50%); filter: hue-rotate(0deg); }
  to { transform: translate(-50%, -50%); filter: hue-rotate(360deg); }
}
.person-img {
  width: 52px; height: 52px; border-radius: 50%;
  object-fit: cover; border: 2px solid rgba(212,164,76,0.3);
  position: relative; z-index: 1;
}
.person-placeholder {
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 1;
  font-size: 20px; font-weight: 800; color: #1c1208;
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
  transform: translate(-50%, -50%);
  width: 160px; height: 160px; border-radius: 50%;
  background: radial-gradient(circle, rgba(212,164,76,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.portrait-ring {
  width: 88px; height: 88px; border-radius: 50%;
  border: 3px solid #d4a44c;
  box-shadow: 0 0 20px rgba(212,164,76,0.25), inset 0 0 16px rgba(0,0,0,0.4);
  overflow: hidden; position: relative; z-index: 1;
}
.portrait-artifact-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, calc(-50% - 13px));
  width: 120px; height: 120px; border-radius: 50%;
  border: 4px solid; pointer-events: none; z-index: 0; overflow: hidden;
}
.portrait-artifact-ring-img {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, calc(-50% - 13px));
  width: 120px; height: 120px; border-radius: 50%;
  object-fit: cover; pointer-events: none; z-index: 0; overflow: hidden;
  aspect-ratio: 1 / 1;
}
.portrait-artifact-ring.effect-pulse,
.portrait-artifact-ring-img.effect-pulse {
  animation: portraitArtPulse 3s ease-in-out infinite;
}
.portrait-artifact-ring.effect-spin,
.portrait-artifact-ring-img.effect-spin {
  animation: portraitArtSpin 6s linear infinite;
}
.portrait-artifact-ring.effect-glow,
.portrait-artifact-ring-img.effect-glow {
  animation: portraitArtGlow 2s ease-in-out infinite;
}
.portrait-artifact-ring.effect-bounce,
.portrait-artifact-ring-img.effect-bounce {
  animation: portraitArtBounce 2s ease-in-out infinite;
}
.portrait-artifact-ring.effect-shake,
.portrait-artifact-ring-img.effect-shake {
  animation: portraitArtShake 0.6s ease-in-out infinite;
}
.portrait-artifact-ring.effect-rainbow,
.portrait-artifact-ring-img.effect-rainbow {
  animation: portraitArtRainbow 4s linear infinite;
}
@keyframes portraitArtPulse {
  0%, 100% { opacity: 0.7; transform: translate(-50%, calc(-50% - 13px)) scale(1); }
  50% { opacity: 1; transform: translate(-50%, calc(-50% - 13px)) scale(1.06); }
}
@keyframes portraitArtSpin {
  from { transform: translate(-50%, calc(-50% - 13px)) rotate(0deg); }
  to { transform: translate(-50%, calc(-50% - 13px)) rotate(360deg); }
}
@keyframes portraitArtGlow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, calc(-50% - 13px)); filter: brightness(1); }
  50% { opacity: 1; transform: translate(-50%, calc(-50% - 13px)); filter: brightness(1.4) drop-shadow(0 0 16px currentColor); }
}
@keyframes portraitArtBounce {
  0%, 100% { transform: translate(-50%, calc(-50% - 13px)); }
  50% { transform: translate(-50%, calc(-50% - 21px)); }
}
@keyframes portraitArtShake {
  0%, 100% { transform: translate(-50%, calc(-50% - 13px)); }
  25% { transform: translate(calc(-50% - 3px), calc(-50% - 13px)) rotate(-2deg); }
  75% { transform: translate(calc(-50% + 3px), calc(-50% - 13px)) rotate(2deg); }
}
@keyframes portraitArtRainbow {
  from { transform: translate(-50%, calc(-50% - 13px)); filter: hue-rotate(0deg); }
  to { transform: translate(-50%, calc(-50% - 13px)); filter: hue-rotate(360deg); }
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

/* ── Gift Mana ── */
.gift-mana-btn {
  display: block; width: 100%; margin-top: 12px;
  padding: 10px; border-radius: 8px; border: 2px solid rgba(155,89,182,0.4);
  background: linear-gradient(135deg, rgba(155,89,182,0.12), rgba(155,89,182,0.06));
  color: #c39bd3; font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.gift-mana-btn:hover {
  border-color: rgba(155,89,182,0.7);
  background: linear-gradient(135deg, rgba(155,89,182,0.2), rgba(155,89,182,0.1));
  box-shadow: 0 0 16px rgba(155,89,182,0.15);
}

.gift-form {
  margin-top: 12px; padding: 14px;
  border-radius: 10px; border: 1px solid rgba(155,89,182,0.25);
  background: linear-gradient(145deg, rgba(155,89,182,0.06), rgba(0,0,0,0.2));
}
.gift-form-title {
  font-family: 'Cinzel', serif; font-size: 13px; font-weight: 700;
  color: #c39bd3; margin-bottom: 12px; text-align: center;
}
.gift-field { margin-bottom: 10px; }
.gift-field label {
  display: block; font-size: 11px; font-weight: 700;
  color: #8b7355; margin-bottom: 4px; text-transform: uppercase;
  letter-spacing: 0.5px;
}
.gift-input {
  width: 100%; padding: 8px 10px; border-radius: 6px;
  border: 1px solid rgba(212,164,76,0.2);
  background: rgba(0,0,0,0.3); color: #e8d5b7;
  font-size: 14px; font-weight: 600; outline: none;
  box-sizing: border-box;
}
.gift-input:focus { border-color: rgba(155,89,182,0.5); }
.gift-input::placeholder { color: #6b5a3e; }
.gift-balance {
  font-size: 10px; color: #9b59b6; font-weight: 600; margin-top: 3px;
}

.delivery-toggle { display: flex; gap: 8px; }
.dt-btn {
  flex: 1; padding: 8px;
  border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(0,0,0,0.2); color: #8b7355;
  font-size: 13px; font-weight: 700; cursor: pointer;
  transition: all 0.15s;
}
.dt-btn.active.gold {
  border-color: rgba(212,164,76,0.5);
  background: rgba(212,164,76,0.12);
  color: #d4a44c;
  box-shadow: 0 0 8px rgba(212,164,76,0.15);
}
.dt-btn.active.mana {
  border-color: rgba(155,89,182,0.5);
  background: rgba(155,89,182,0.12);
  color: #c39bd3;
  box-shadow: 0 0 8px rgba(155,89,182,0.15);
}

.gift-actions { display: flex; gap: 8px; margin-top: 14px; }
.gift-cancel {
  flex: 1; padding: 8px; border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(0,0,0,0.2); color: #8b7355;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.gift-confirm {
  flex: 2; padding: 8px; border-radius: 6px;
  border: 1px solid rgba(155,89,182,0.4);
  background: linear-gradient(135deg, #7b2d8e, #9b59b6);
  color: #fff; font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.15s;
}
.gift-confirm:disabled {
  opacity: 0.4; cursor: not-allowed;
}
.gift-confirm:hover:not(:disabled) {
  box-shadow: 0 0 16px rgba(155,89,182,0.3);
}

/* ── Social Buttons ─────────────────── */
.social-buttons {
  display: flex; gap: 8px; margin-top: 12px;
}
.social-btn {
  flex: 1; padding: 10px 6px; border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all 0.2s;
}
.social-btn:disabled {
  opacity: 0.4; cursor: not-allowed;
}
.social-btn.thank-you {
  background: linear-gradient(135deg, #d4a44c33, #b8860b33);
  border-color: rgba(212,164,76,0.3);
  color: #d4a44c;
}
.social-btn.thank-you:hover:not(:disabled) {
  background: linear-gradient(135deg, #d4a44c55, #b8860b55);
  box-shadow: 0 0 14px rgba(212,164,76,0.2);
}
.social-btn.anon-praise {
  background: linear-gradient(135deg, #3498db33, #2980b933);
  border-color: rgba(52,152,219,0.3);
  color: #85c1e9;
}
.social-btn.anon-praise:hover:not(:disabled) {
  background: linear-gradient(135deg, #3498db55, #2980b955);
  box-shadow: 0 0 14px rgba(52,152,219,0.2);
}

.praise-popup {
  margin-top: 12px; padding: 14px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(52,152,219,0.2);
  border-radius: 10px;
}
.praise-title {
  font-size: 14px; font-weight: 700; color: #85c1e9;
  margin-bottom: 6px;
}
.praise-hint {
  font-size: 11px; color: #8b7355; margin-bottom: 10px; line-height: 1.4;
}
.praise-input {
  width: 100%; box-sizing: border-box;
  padding: 8px 10px; border-radius: 6px;
  border: 1px solid rgba(52,152,219,0.2);
  background: rgba(0,0,0,0.25); color: #e8d5b7;
  font-size: 13px; resize: none; font-family: inherit;
}
.praise-input:focus {
  outline: none; border-color: rgba(52,152,219,0.5);
}
.praise-actions {
  display: flex; gap: 8px; margin-top: 10px;
}

/* ═══════════════════════════════════════════════════
   MATCHMAKING CARD
   ═══════════════════════════════════════════════════ */
.matchmake-card {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 20px;
  border: 2px solid rgba(212,164,76,0.3);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 20px rgba(212,164,76,0.08);
}
.matchmake-bg {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: url('/images/battle_arena_bg.png') center/cover no-repeat;
  filter: brightness(0.6);
}
.matchmake-overlay {
  position: relative; z-index: 1;
  background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(17,10,30,0.85) 100%);
  padding: 24px 20px;
}
.matchmake-content {
  display: flex; flex-direction: column; align-items: center;
  gap: 10px;
}
.matchmake-title {
  font-family: 'Cinzel', serif; font-size: 22px; font-weight: 900;
  background: linear-gradient(135deg, #d4a44c, #ffd700, #d4a44c);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: 3px;
  filter: drop-shadow(0 2px 8px rgba(212,164,76,0.4));
}
.matchmake-rewards {
  display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;
}
.reward-tag {
  padding: 5px 14px; border-radius: 8px;
  font-size: 13px; font-weight: 700;
}
.winner-tag {
  background: rgba(46,204,113,0.15); border: 1px solid rgba(46,204,113,0.3);
  color: #2ecc71;
}
.loser-tag {
  background: rgba(231,76,60,0.15); border: 1px solid rgba(231,76,60,0.3);
  color: #e74c3c;
}
.matchmake-desc {
  font-size: 12px; color: #b8a080; font-weight: 600;
  font-style: italic;
}
.btn-matchmake {
  padding: 14px 40px; border-radius: 12px;
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 800;
  border: 2px solid #d4a44c;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; cursor: pointer;
  text-shadow: 0 1px 1px rgba(255,255,255,0.2);
  box-shadow: 0 4px 20px rgba(212,164,76,0.3);
  transition: all 0.25s; letter-spacing: 1px;
}
.btn-matchmake:hover:not(:disabled) {
  background: linear-gradient(135deg, #d4a44c, #ffd700);
  box-shadow: 0 8px 32px rgba(212,164,76,0.4);
  transform: translateY(-2px);
}
.btn-matchmake:disabled {
  opacity: 0.5; cursor: not-allowed; transform: none;
}
.rematch-link { margin-top: 4px; }
.view-last-battle {
  color: #d4a44c; font-size: 13px; font-weight: 600;
  text-decoration: none; opacity: 0.8;
}
.view-last-battle:hover { opacity: 1; text-decoration: underline; }

/* ═══ Spin Wheel Modal ═══ */
.wheel-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.9);
  display: flex; align-items: center; justify-content: center;
  z-index: 10000; padding: 16px;
  animation: fadeIn 0.3s ease;
}
.wheel-container {
  display: flex; flex-direction: column; align-items: center;
  gap: 16px;
}
.wheel-title {
  font-family: 'Cinzel', serif; font-size: 22px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 12px rgba(212,164,76,0.4);
  letter-spacing: 2px;
}
.wheel-stage {
  position: relative;
  width: 320px; height: 320px;
  display: flex; align-items: center; justify-content: center;
}
.wheel-pointer {
  position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
  font-size: 28px; color: #ffd700; z-index: 10;
  filter: drop-shadow(0 0 8px rgba(255,215,0,0.6));
  animation: pointerBounce 0.6s ease-in-out infinite;
}
@keyframes pointerBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(4px); }
}
.wheel-ring {
  position: absolute;
  width: 100%; height: 100%;
  transform-origin: center center;
}
.wheel-slot {
  position: absolute;
  top: 50%; left: 50%;
  margin-left: -24px; margin-top: -24px;
  display: flex; flex-direction: column; align-items: center;
  transition: transform 0.3s;
  transform-origin: center center;
}
.wheel-slot.selected .wheel-avatar,
.wheel-slot.selected .wheel-avatar-ph {
  border-color: #ffd700 !important;
  box-shadow: 0 0 20px rgba(255,215,0,0.6), 0 0 40px rgba(255,215,0,0.3);
  transform: scale(1.3);
}
.wheel-slot.selected .wheel-name {
  color: #ffd700; font-weight: 800;
  text-shadow: 0 0 8px rgba(255,215,0,0.5);
}
.wheel-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(212,164,76,0.4);
  transition: all 0.4s;
}
.wheel-avatar-ph {
  width: 48px; height: 48px; border-radius: 50%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800; color: #1c1208;
  border: 2px solid rgba(212,164,76,0.4);
  transition: all 0.4s;
}
.wheel-name {
  font-size: 10px; color: #e8d5b7; font-weight: 600;
  margin-top: 4px; white-space: nowrap;
  text-align: center; max-width: 60px;
  overflow: hidden; text-overflow: ellipsis;
  transition: all 0.3s;
}

/* ═══ Wheel Result ═══ */
.wheel-result {
  display: flex; flex-direction: column; align-items: center;
  gap: 12px;
  animation: fadeIn 0.5s ease;
}
.vs-flash {
  font-family: 'Cinzel', serif; font-size: 20px; font-weight: 900;
  color: #ff4a6a;
  text-shadow: 0 0 20px rgba(255,74,106,0.5);
  letter-spacing: 2px;
  animation: vsPulse 1s ease-in-out infinite;
}
@keyframes vsPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}
.btn-fight-now {
  padding: 14px 40px; border-radius: 12px;
  font-family: 'Cinzel', serif; font-size: 18px; font-weight: 900;
  border: 2px solid #e74c3c;
  background: linear-gradient(135deg, #c0392b, #e74c3c);
  color: #fff; cursor: pointer;
  box-shadow: 0 4px 20px rgba(231,76,60,0.4);
  transition: all 0.25s; letter-spacing: 2px;
}
.btn-fight-now:hover {
  background: linear-gradient(135deg, #e74c3c, #ff6b6b);
  box-shadow: 0 8px 32px rgba(231,76,60,0.5);
  transform: translateY(-2px);
}

@keyframes fadeIn {
  from { opacity: 0; } to { opacity: 1; }
}
</style>
