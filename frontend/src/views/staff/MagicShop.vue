<template>
  <div class="staff-page">
    <div class="ms-header">
      <router-link to="/staff/services" class="ms-back">← Back</router-link>
      <h1 class="page-title">🔮 Magic Shop</h1>
      <p class="page-sub">Spend your Gold on mystic arts</p>
      <div class="ms-gold">💰 {{ myCoins }} Gold</div>
    </div>

    <div class="magic-grid">
      <!-- Magic Lottery -->
      <div class="magic-card lottery-card">
        <div class="magic-icon">🎲</div>
        <div class="magic-name">Magic Lottery</div>
        <div class="magic-desc">Roll the dice! Pay 3 Gold, result: -6 to +8 Gold</div>
        <div class="magic-cost">Cost: 💰 3</div>
        <button class="magic-buy lottery-btn" :disabled="buying || myCoins < 3" @click="buyLottery">
          {{ buying === 'magic_lottery' ? '🎲 Rolling...' : '🎲 Try Luck!' }}
        </button>
      </div>

      <!-- Scroll of Luck -->
      <div class="magic-card scroll-card luk">
        <div class="magic-icon">🍀</div>
        <div class="magic-name">Scroll of Luck</div>
        <div class="magic-desc">Permanently gain +1 LUK</div>
        <div class="magic-cost">Cost: 💰 1</div>
        <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_luck')">
          {{ buying === 'scroll_of_luck' ? 'Learning...' : 'Buy Scroll' }}
        </button>
        <div v-if="lastResult && lastResult.item === 'Scroll of Luck'" class="magic-result win">
          🍀 LUK is now {{ lastResult.new_value }}!
        </div>
      </div>

      <!-- Scroll of Strength -->
      <div class="magic-card scroll-card str">
        <div class="magic-icon">⚔️</div>
        <div class="magic-name">Scroll of Strength</div>
        <div class="magic-desc">Permanently gain +1 STR</div>
        <div class="magic-cost">Cost: 💰 1</div>
        <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_strength')">
          {{ buying === 'scroll_of_strength' ? 'Learning...' : 'Buy Scroll' }}
        </button>
        <div v-if="lastResult && lastResult.item === 'Scroll of Strength'" class="magic-result win">
          ⚔️ STR is now {{ lastResult.new_value }}!
        </div>
      </div>

      <!-- Scroll of Defense -->
      <div class="magic-card scroll-card def">
        <div class="magic-icon">🛡️</div>
        <div class="magic-name">Scroll of Defense</div>
        <div class="magic-desc">Permanently gain +1 DEF</div>
        <div class="magic-cost">Cost: 💰 1</div>
        <button class="magic-buy" :disabled="buying || myCoins < 1" @click="buy('scroll_of_defense')">
          {{ buying === 'scroll_of_defense' ? 'Learning...' : 'Buy Scroll' }}
        </button>
        <div v-if="lastResult && lastResult.item === 'Scroll of Defense'" class="magic-result win">
          🛡️ DEF is now {{ lastResult.new_value }}!
        </div>
      </div>

      <!-- Title Scroll -->
      <div class="magic-card scroll-card title">
        <div class="magic-icon">📜</div>
        <div class="magic-name">Title Scroll</div>
        <div class="magic-desc">Write your own status (70 chars)</div>
        <div class="magic-cost">Cost: 💰 1</div>
        <div class="title-input-wrap">
          <input
            v-model="titleText"
            type="text"
            maxlength="70"
            placeholder="Enter your status..."
            class="title-input"
            :disabled="buying"
          />
          <span class="title-counter">{{ titleText.length }}/70</span>
        </div>
        <button class="magic-buy title-btn" :disabled="buying || myCoins < 1 || !titleText.trim()" @click="buyTitle">
          {{ buying === 'title_scroll' ? 'Writing...' : '📜 Set Status' }}
        </button>
        <div v-if="currentStatus" class="title-current">💬 {{ currentStatus }}</div>
        <div v-if="lastResult && lastResult.item === 'Title Scroll'" class="magic-result win">
          ✨ Status updated!
        </div>
      </div>
    </div>

    <!-- Lottery Spin Popup Overlay -->
    <div v-if="showLotteryPopup" class="lottery-overlay">
      <div class="lottery-popup">
        <div class="lottery-title">🎲 Magic Lottery 🎲</div>
        <div class="lottery-subtitle">Spending 3 Gold...</div>

        <div class="lottery-wheel-wrap">
          <div class="lottery-number" :class="{ spinning: isSpinning, reveal: isRevealed, 'is-win': isRevealed && lotteryWon > 3, 'is-lose': isRevealed && lotteryWon < 3 }">
            {{ displayNumber }}
          </div>
        </div>

        <div v-if="isRevealed" class="lottery-result-text" :class="lotteryWon >= 3 ? 'win-text' : 'lose-text'">
          <template v-if="lotteryWon > 0">🎉 You got {{ lotteryWon }} Gold! ({{ lotteryWon - 3 >= 0 ? '+' : '' }}{{ lotteryWon - 3 }} net)</template>
          <template v-else-if="lotteryWon === 0">😐 Zero! You lost 3 Gold</template>
          <template v-else>💀 Cursed! {{ lotteryWon }} Gold ({{ lotteryWon - 3 }} net)</template>
        </div>

        <button v-if="isRevealed" class="lottery-close-btn" @click="closeLotteryPopup">
          {{ lotteryWon >= 3 ? '🎉 Nice!' : '😤 Try Again' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { buyMagicItem } from '../../services/api'

export default {
  name: 'MagicShop',
  data() {
    return {
      myCoins: 0,
      buying: null,
      lastResult: null,
      // Lottery popup
      showLotteryPopup: false,
      isSpinning: false,
      isRevealed: false,
      displayNumber: 0,
      lotteryWon: 0,
      spinInterval: null,
      // Title Scroll
      titleText: '',
      currentStatus: '',
    }
  },
  mounted() {
    this.refreshCoins()
  },
  beforeUnmount() {
    if (this.spinInterval) clearInterval(this.spinInterval)
  },
  methods: {
    async refreshCoins() {
      try {
        const { data } = await import('../../services/api').then(m => m.default.get('/api/users/me'))
        this.myCoins = data.coins || 0
        this.currentStatus = data.status_text || ''
      } catch (e) { /* ignore */ }
    },

    async buyLottery() {
      if (this.myCoins < 3 || this.buying) return
      this.buying = 'magic_lottery'
      this.lastResult = null

      try {
        // Call API first to get the result
        const { data } = await buyMagicItem('magic_lottery')
        this.lotteryWon = data.won
        this.myCoins = data.coins

        // Update local storage
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        localStorage.setItem('user', JSON.stringify(user))

        // Start the animation
        this.showLotteryPopup = true
        this.isSpinning = true
        this.isRevealed = false
        this.displayNumber = 0

        // Spin through random numbers rapidly
        let spinCount = 0
        const totalSpins = 20
        const startSpeed = 60
        const endSpeed = 250

        const doSpin = () => {
          spinCount++
          this.displayNumber = Math.floor(Math.random() * 15) - 6 // -6 to 8

          if (spinCount >= totalSpins) {
            // Reveal the actual result
            this.displayNumber = this.lotteryWon
            this.isSpinning = false
            this.isRevealed = true
            return
          }

          // Gradually slow down
          const progress = spinCount / totalSpins
          const delay = startSpeed + (endSpeed - startSpeed) * Math.pow(progress, 2)
          this.spinInterval = setTimeout(doSpin, delay)
        }

        setTimeout(doSpin, 400) // Small delay before spinning starts
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        alert(msg)
        this.showLotteryPopup = false
      } finally {
        this.buying = null
      }
    },

    closeLotteryPopup() {
      this.showLotteryPopup = false
      this.isSpinning = false
      this.isRevealed = false
      if (this.spinInterval) clearTimeout(this.spinInterval)
    },

    async buy(itemType) {
      if (this.myCoins < 1) return
      this.buying = itemType
      this.lastResult = null
      try {
        const { data } = await buyMagicItem(itemType)
        this.lastResult = data
        this.myCoins = data.coins
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        alert(msg)
      } finally {
        this.buying = null
      }
    },

    async buyTitle() {
      if (!this.titleText.trim() || this.myCoins < 1 || this.buying) return
      this.buying = 'title_scroll'
      this.lastResult = null
      try {
        const { data } = await buyMagicItem('title_scroll', { status_text: this.titleText.trim() })
        this.lastResult = data
        this.myCoins = data.coins
        this.currentStatus = data.status_text
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        user.coins = data.coins
        user.status_text = data.status_text
        localStorage.setItem('user', JSON.stringify(user))
      } catch (e) {
        const msg = e.response?.data?.detail || 'Purchase failed'
        alert(msg)
      } finally {
        this.buying = null
      }
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 16px 0; }

.ms-header { margin-bottom: 20px; }
.ms-back {
  display: inline-block; margin-bottom: 8px;
  color: #b8860b; font-weight: 700; font-size: 13px;
  text-decoration: none; opacity: 0.8;
}
.ms-back:hover { opacity: 1; }
.page-title {
  font-family: 'Cinzel', serif;
  font-size: 24px; font-weight: 800; color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub {
  color: #8b7355; font-size: 13px; font-weight: 600;
  font-style: italic; margin-bottom: 8px;
}
.ms-gold {
  display: inline-block;
  background: linear-gradient(135deg, rgba(212,164,76,0.15), rgba(184,134,11,0.1));
  border: 1px solid rgba(212,164,76,0.3);
  border-radius: 8px; padding: 6px 14px;
  font-size: 16px; font-weight: 800; color: #d4a44c;
}

/* Grid */
.magic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

/* Card */
.magic-card {
  background: linear-gradient(145deg, rgba(44,24,16,0.85), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.15);
  border-radius: 14px;
  padding: 20px 14px 16px;
  display: flex; flex-direction: column; align-items: center;
  text-align: center;
  transition: all 0.2s;
}
.magic-card:hover {
  border-color: rgba(212,164,76,0.35);
  box-shadow: 0 6px 24px rgba(212,164,76,0.08);
}

.lottery-card { border-color: rgba(155,89,182,0.3); }
.lottery-card:hover { border-color: rgba(155,89,182,0.5); }
.scroll-card.luk { border-color: rgba(46,204,113,0.25); }
.scroll-card.str { border-color: rgba(231,76,60,0.25); }
.scroll-card.def { border-color: rgba(52,152,219,0.25); }
.scroll-card.title { border-color: rgba(241,196,15,0.3); grid-column: 1 / -1; }

.magic-icon {
  font-size: 36px; margin-bottom: 8px;
  filter: drop-shadow(0 2px 6px rgba(212,164,76,0.3));
}
.magic-name {
  font-family: 'Cinzel', serif;
  font-size: 14px; font-weight: 700; color: #e8d5b7;
  margin-bottom: 6px;
}
.magic-desc {
  font-size: 11px; color: #8b7355; font-weight: 600;
  margin-bottom: 10px; line-height: 1.4;
}
.magic-cost {
  font-size: 12px; font-weight: 700; color: #d4a44c;
  margin-bottom: 10px;
}

.magic-buy {
  width: 100%; padding: 8px 0;
  border: none; border-radius: 8px;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208; font-weight: 800; font-size: 13px;
  cursor: pointer; transition: all 0.2s;
}
.lottery-btn {
  background: linear-gradient(135deg, #8e44ad, #9b59b6) !important;
  color: #fff !important;
}
.magic-buy:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(212,164,76,0.3);
}
.magic-buy:disabled {
  opacity: 0.4; cursor: not-allowed;
}

.magic-result {
  margin-top: 10px; padding: 6px 10px;
  border-radius: 8px; font-size: 12px; font-weight: 700;
  animation: fadeIn 0.3s ease;
}
.magic-result.win {
  background: rgba(46,204,113,0.1); color: #2ecc71;
  border: 1px solid rgba(46,204,113,0.2);
}

/* Title Scroll Input */
.title-input-wrap {
  width: 100%; position: relative; margin-bottom: 8px;
}
.title-input {
  width: 100%; padding: 8px 10px; border-radius: 8px;
  border: 1px solid rgba(241,196,15,0.3);
  background: rgba(0,0,0,0.3); color: #e8d5b7;
  font-size: 13px; font-weight: 600;
  outline: none; box-sizing: border-box;
}
.title-input:focus {
  border-color: rgba(241,196,15,0.6);
  box-shadow: 0 0 10px rgba(241,196,15,0.1);
}
.title-input::placeholder { color: #6b5a3e; }
.title-counter {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  font-size: 10px; color: #6b5a3e; font-weight: 700;
}
.title-btn {
  background: linear-gradient(135deg, #d4a017, #f1c40f) !important;
  color: #1c1208 !important;
}
.title-current {
  margin-top: 8px; font-size: 11px; color: #f1c40f;
  font-style: italic; font-weight: 600;
  word-break: break-word;
}

/* ── Lottery Spin Popup ───────────────────────────── */
.lottery-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}
.lottery-popup {
  background: linear-gradient(145deg, #1a0a2e, #2c1810, #1a0a2e);
  border: 3px solid rgba(155,89,182,0.5);
  border-radius: 24px;
  padding: 32px 28px;
  text-align: center;
  max-width: 340px; width: 90%;
  box-shadow:
    0 0 40px rgba(155,89,182,0.3),
    0 0 80px rgba(155,89,182,0.1),
    inset 0 0 40px rgba(155,89,182,0.05);
}
.lottery-title {
  font-family: 'Cinzel', serif;
  font-size: 22px; font-weight: 800;
  color: #c39bd3;
  text-shadow: 0 0 20px rgba(155,89,182,0.5);
  margin-bottom: 4px;
}
.lottery-subtitle {
  font-size: 13px; color: #8b7355;
  margin-bottom: 24px; font-weight: 600;
}

.lottery-wheel-wrap {
  display: flex; align-items: center; justify-content: center;
  margin: 20px 0 24px;
}
.lottery-number {
  width: 120px; height: 120px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Cinzel', serif;
  font-size: 64px; font-weight: 900;
  color: #e8d5b7;
  background: radial-gradient(circle, rgba(44,24,16,0.9), rgba(26,26,46,0.95));
  border: 4px solid rgba(155,89,182,0.4);
  border-radius: 20px;
  text-shadow: 0 0 20px rgba(212,164,76,0.4);
  transition: all 0.15s;
}
.lottery-number.spinning {
  animation: numberSpin 0.1s infinite;
  border-color: rgba(155,89,182,0.7);
  box-shadow:
    0 0 30px rgba(155,89,182,0.4),
    0 0 60px rgba(155,89,182,0.15);
}
.lottery-number.reveal {
  animation: revealBounce 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  border-color: rgba(212,164,76,0.7);
  font-size: 72px;
  box-shadow: 0 0 40px rgba(212,164,76,0.4);
}
.lottery-number.reveal.is-win {
  border-color: rgba(46,204,113,0.8);
  color: #2ecc71;
  text-shadow: 0 0 30px rgba(46,204,113,0.5);
  box-shadow: 0 0 50px rgba(46,204,113,0.3);
}
.lottery-number.reveal.is-lose {
  border-color: rgba(231,76,60,0.6);
  color: #e74c3c;
  text-shadow: 0 0 30px rgba(231,76,60,0.4);
  box-shadow: 0 0 50px rgba(231,76,60,0.2);
}

.lottery-result-text {
  font-family: 'Cinzel', serif;
  font-size: 16px; font-weight: 700;
  margin: 16px 0 20px;
  animation: fadeIn 0.4s ease 0.2s both;
}
.win-text { color: #2ecc71; }
.lose-text { color: #e74c3c; }

.lottery-close-btn {
  padding: 10px 28px;
  border: none; border-radius: 10px;
  font-weight: 800; font-size: 14px;
  cursor: pointer; transition: all 0.2s;
  background: linear-gradient(135deg, #8e44ad, #9b59b6);
  color: #fff;
  animation: fadeIn 0.3s ease 0.4s both;
}
.lottery-close-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(155,89,182,0.4);
}

@keyframes numberSpin {
  0% { transform: scale(1) rotateX(0deg); }
  25% { transform: scale(1.05) rotateX(5deg); }
  50% { transform: scale(0.95) rotateX(-5deg); }
  75% { transform: scale(1.05) rotateX(3deg); }
  100% { transform: scale(1) rotateX(0deg); }
}

@keyframes revealBounce {
  0% { transform: scale(0.5); opacity: 0; }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
