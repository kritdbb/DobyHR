<template>
  <transition name="gift-fade">
    <div v-if="visible" class="gift-overlay" @click="dismiss">
      <!-- Particles -->
      <div class="gift-particles">
        <div v-for="i in 40" :key="'p'+i"
          class="gift-particle"
          :class="theme"
          :style="particleStyle(i)">
        </div>
      </div>

      <!-- Sparkle ring -->
      <div class="gift-ring" :class="theme"></div>

      <!-- Central burst -->
      <div class="gift-center">
        <div class="gift-icon-burst" :class="theme">
          {{ theme === 'gold' ? '💰' : theme === 'buff' ? '⚡' : '✨' }}
        </div>
        <div class="gift-amount" :class="theme">{{ theme === 'gold' ? '💰' : theme === 'buff' ? '⚡' : '✨' }} {{ amount }}</div>
        <div class="gift-label" :class="theme">{{ theme === 'buff' ? 'Buff Sent!' : 'Gift Sent!' }}</div>
        <div class="gift-recipient">→ {{ recipientName }}</div>
      </div>

      <!-- Floating coins / stars -->
      <div v-for="i in 12" :key="'c'+i"
        class="gift-floater"
        :class="theme"
        :style="floaterStyle(i)">
        {{ theme === 'gold' ? '🪙' : theme === 'buff' ? '⚡' : '⭐' }}
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'GiftCelebration',
  props: {
    visible: { type: Boolean, default: false },
    theme: { type: String, default: 'gold' }, // 'gold', 'mana', or 'buff'
    amount: { type: [Number, String], default: 0 },
    recipientName: { type: String, default: '' },
  },
  emits: ['done'],
  watch: {
    visible(val) {
      if (val) {
        this.playSound()
        setTimeout(() => this.$emit('done'), 3000)
      }
    },
  },
  methods: {
    dismiss() {
      this.$emit('done')
    },
    playSound() {
      try {
        const src = this.theme === 'buff' ? '/sounds/addbuff.mp3' : '/sounds/coin.mp3'
        const audio = new Audio(src)
        audio.volume = 0.5
        audio.play().catch(() => {})
      } catch { /* ignore */ }
    },
    particleStyle(i) {
      const angle = (i / 40) * 360 + (Math.random() * 20 - 10)
      const dist = 120 + Math.random() * 180
      const size = 4 + Math.random() * 6
      const delay = Math.random() * 0.4
      const duration = 0.8 + Math.random() * 0.6
      return {
        '--angle': angle + 'deg',
        '--dist': dist + 'px',
        '--size': size + 'px',
        '--delay': delay + 's',
        '--duration': duration + 's',
      }
    },
    floaterStyle(i) {
      const angle = (i / 12) * 360
      const dist = 80 + Math.random() * 120
      const delay = 0.1 + Math.random() * 0.5
      const duration = 1.5 + Math.random() * 1
      return {
        '--f-angle': angle + 'deg',
        '--f-dist': dist + 'px',
        '--f-delay': delay + 's',
        '--f-duration': duration + 's',
        '--f-size': (18 + Math.random() * 14) + 'px',
      }
    },
  },
}
</script>

<style scoped>
.gift-overlay {
  position: fixed; inset: 0; z-index: 99999;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.75);
  backdrop-filter: blur(4px);
  animation: giftOverlayIn 0.3s ease-out;
}

/* ── Center content ── */
.gift-center {
  text-align: center; z-index: 3;
  animation: giftCenterPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both;
}

.gift-icon-burst {
  font-size: 64px;
  filter: drop-shadow(0 0 20px rgba(212,164,76,0.6));
  animation: giftIconPulse 1s ease-in-out infinite;
}
.gift-icon-burst.mana {
  filter: drop-shadow(0 0 20px rgba(155,89,182,0.6));
}
.gift-icon-burst.buff {
  filter: drop-shadow(0 0 20px rgba(34,197,94,0.6));
}

.gift-amount {
  font-family: 'Cinzel', serif;
  font-size: 32px; font-weight: 800;
  margin-top: 8px;
  text-shadow: 0 2px 12px rgba(0,0,0,0.5);
}
.gift-amount.gold { color: #ffd700; }
.gift-amount.mana { color: #c39bd3; }
.gift-amount.buff { color: #4ade80; }

.gift-label {
  font-family: 'Cinzel', serif;
  font-size: 22px; font-weight: 800;
  margin-top: 4px; letter-spacing: 0.05em;
  text-shadow: 0 2px 12px rgba(0,0,0,0.5);
}
.gift-label.gold { color: #d4a44c; }
.gift-label.mana { color: #9b59b6; }
.gift-label.buff { color: #22c55e; }

.gift-recipient {
  font-size: 14px; font-weight: 700;
  color: #e8d5b7; margin-top: 8px;
  opacity: 0.8;
}

/* ── Particles ── */
.gift-particles {
  position: absolute; top: 50%; left: 50%;
  width: 0; height: 0; z-index: 2;
}

.gift-particle {
  position: absolute;
  width: var(--size); height: var(--size);
  border-radius: 50%;
  animation: giftParticleFly var(--duration) ease-out var(--delay) both;
}
.gift-particle.gold {
  background: radial-gradient(circle, #ffd700, #b8860b);
  box-shadow: 0 0 6px rgba(255,215,0,0.6);
}
.gift-particle.mana {
  background: radial-gradient(circle, #c39bd3, #7d3c98);
  box-shadow: 0 0 6px rgba(155,89,182,0.6);
}
.gift-particle.buff {
  background: radial-gradient(circle, #4ade80, #16a34a);
  box-shadow: 0 0 6px rgba(34,197,94,0.6);
}

/* ── Ring burst ── */
.gift-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 0; height: 0; border-radius: 50%;
  border: 3px solid;
  animation: giftRingExpand 0.8s ease-out 0.1s both;
  z-index: 1; opacity: 0;
}
.gift-ring.gold { border-color: rgba(255,215,0,0.5); }
.gift-ring.mana { border-color: rgba(155,89,182,0.5); }
.gift-ring.buff { border-color: rgba(34,197,94,0.5); }

/* ── Floating coins/stars ── */
.gift-floater {
  position: absolute; top: 50%; left: 50%;
  font-size: var(--f-size);
  animation: giftFloaterFly var(--f-duration) ease-out var(--f-delay) both;
  z-index: 2;
  filter: drop-shadow(0 0 4px rgba(255,215,0,0.4));
}
.gift-floater.mana {
  filter: drop-shadow(0 0 4px rgba(155,89,182,0.4));
}
.gift-floater.buff {
  filter: drop-shadow(0 0 4px rgba(34,197,94,0.4));
}

/* ── Keyframes ── */
@keyframes giftOverlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes giftCenterPop {
  from { opacity: 0; transform: scale(0.3); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes giftIconPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

@keyframes giftParticleFly {
  0% {
    transform: translate(0, 0) scale(1);
    opacity: 1;
  }
  100% {
    transform:
      rotate(var(--angle))
      translateY(calc(-1 * var(--dist)))
      scale(0);
    opacity: 0;
  }
}

@keyframes giftRingExpand {
  0% {
    width: 0; height: 0; opacity: 0.8;
    border-width: 4px;
  }
  100% {
    width: 300px; height: 300px; opacity: 0;
    border-width: 1px;
    transform: translate(-50%, -50%);
  }
}

@keyframes giftFloaterFly {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
  }
  20% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  100% {
    transform:
      translate(-50%, -50%)
      rotate(var(--f-angle))
      translateY(calc(-1 * var(--f-dist)))
      scale(0.3);
    opacity: 0;
  }
}

/* Transition */
.gift-fade-leave-active {
  transition: opacity 0.4s ease;
}
.gift-fade-leave-to {
  opacity: 0;
}
</style>
