<template>
  <div id="app">
    <!-- Admin Layout (Guild Hall) -->
    <div v-if="layout === 'admin'" class="flex h-screen overflow-hidden">
        <aside class="sidebar w-64 flex flex-col justify-between shrink-0 transition-all duration-300">
            <div>
                <div class="p-6 border-b" style="border-color: rgba(212,164,76,0.3);">
                    <h1 style="font-family: 'Cinzel', serif; font-size: 20px; font-weight: 800; color: #d4a44c; text-shadow: 0 0 20px rgba(212,164,76,0.3);">⚔️ Doby Kingdom</h1>
                    <p style="font-size: 11px; color: #b8860b; font-weight: 600; font-style: italic; margin-top: 4px;">{{ userRole === 'god' ? "God's Throne Room 👑" : "Guild Master's Hall 🏰" }}</p>
                </div>
                <nav class="flex-1 p-4 space-y-2">
                    <router-link v-if="userRole === 'god'" to="/admin" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🏰</span>
                        <span class="font-semibold">Guild Hall</span>
                    </router-link>
                    <router-link v-if="userRole === 'god'" to="/company" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">⚙️</span>
                        <span class="font-semibold">Kingdom Settings</span>
                    </router-link>
                    <router-link to="/users" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">⚔️</span>
                        <span class="font-semibold">Adventurers</span>
                    </router-link>
                    <router-link to="/approval-patterns" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🛡️</span>
                        <span class="font-semibold">Approval Patterns</span>
                    </router-link>
                    <router-link to="/approval" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">📜</span>
                        <span class="font-semibold">Approval Lines</span>
                    </router-link>
                    <router-link to="/verify-redemption" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🔮</span>
                        <span class="font-semibold">Verify Trades</span>
                    </router-link>
                    <router-link to="/expense-management" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">💰</span>
                        <span class="font-semibold">Expense Requests</span>
                    </router-link>

                    <div class="nav-divider"></div>

                    <router-link v-if="userRole === 'god'" to="/rewards" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🛒</span>
                        <span class="font-semibold">Item Shop</span>
                    </router-link>
                    <router-link v-if="userRole === 'god'" to="/fortune-wheel" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🎡</span>
                        <span class="font-semibold">Fortune Wheel</span>
                    </router-link>

                    <div class="nav-divider"></div>

                    <router-link v-if="userRole === 'god'" to="/badges" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🏅</span>
                        <span class="font-semibold">Badge Forge</span>
                    </router-link>
                    <router-link v-if="userRole === 'god'" to="/badge-quests" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🎯</span>
                        <span class="font-semibold">Badge Quest</span>
                    </router-link>
                    <router-link v-if="userRole === 'god'" to="/badge-shop-admin" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">🏪</span>
                        <span class="font-semibold">Badge Shop</span>
                    </router-link>

                    <div class="nav-divider"></div>

                    <router-link to="/battle-arena" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">⚔️</span>
                        <span class="font-semibold">Battle Arena</span>
                    </router-link>

                    <router-link to="/artifact-shop" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">💎</span>
                        <span class="font-semibold">Artifact Shop</span>
                    </router-link>

                    <router-link to="/reports" class="nav-item flex items-center p-3 rounded-xl transition-all duration-200" active-class="active">
                        <span class="mr-3 text-lg">📊</span>
                        <span class="font-semibold">Chronicles</span>
                    </router-link>
                </nav>
            </div>
            
            <div class="p-4" style="border-top: 2px solid rgba(212,164,76,0.2); background: linear-gradient(135deg, rgba(44,24,16,0.6), rgba(26,26,46,0.4));">
                <router-link to="/staff/home" class="flex items-center w-full p-2.5 text-sm rounded-xl mb-2 transition-all font-bold" style="text-decoration: none; color: #d4a44c;" onmouseover="this.style.background='rgba(212,164,76,0.1)'" onmouseout="this.style.background='transparent'">
                    <span class="mr-2">🗡️</span> Enter the Kingdom
                </router-link>
                <button @click="logout" class="flex items-center w-full p-2.5 text-sm rounded-xl transition-all font-semibold" style="color: #c0392b;" onmouseover="this.style.background='rgba(192,57,43,0.1)'" onmouseout="this.style.background='transparent'">
                    <span class="mr-2">🚪</span> Leave Guild
                </button>
                <div class="mt-4 pt-2" style="border-top: 1px solid rgba(212,164,76,0.15);">
                    <p style="font-size: 10px; color: #b8860b; text-align: center; font-weight: 700; font-family: 'Cinzel', serif;">⚔️ Doby Kingdom v1.1</p>
                </div>
            </div>
        </aside>

        <main class="main-content flex-1 overflow-y-auto p-8">
             <router-view />
        </main>
    </div>

    <!-- Staff/Empty Layout -->
    <div v-else style="flex:1; background: linear-gradient(160deg, #1a1a2e 0%, #16213e 40%, #1a1a2e 100%);" class="h-screen w-full">
         <router-view />
    </div>

    <!-- Toast notifications (Scroll Banner) -->
    <transition name="bounce">
        <div v-if="toast.show" :class="['fixed top-4 right-4 px-6 py-3 rounded-lg shadow-xl z-50 font-bold text-white text-sm flex items-center gap-2', toast.type === 'success' ? 'toast-success' : 'toast-error']" style="animation: bounceIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);">
            <span>{{ toast.type === 'success' ? '⚔️' : '💀' }}</span>
            {{ toast.message }}
        </div>
    </transition>
  </div>
</template>

<script>
export default {
  data() {
    return {
      toast: { show: false, message: '', type: 'success' },
    }
  },
  computed: {
    userRole() {
      const userStr = localStorage.getItem('user')
      if (!userStr) return 'player'
      try { return JSON.parse(userStr).role || 'player' }
      catch { return 'player' }
    },
    layout() {
        if (this.$route.meta.layout === 'empty') return 'empty'
        if (this.$route.path.startsWith('/staff')) return 'staff'
        if (['god', 'gm'].includes(this.userRole)) return 'admin'
        return 'staff'
    }
  },
  methods: {
    showToast(message, type = 'success') {
      this.toast = { show: true, message, type }
      setTimeout(() => { this.toast.show = false }, 3000)
    },
    logout() {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        this.$router.push('/login')
    },
    goToStaff() {
        this.$router.push('/staff/dashboard')
    }
  },
  provide() {
    return {
      showToast: this.showToast,
    }
  },
}
</script>

<style>
.bounce-enter-active {
  animation: bounceIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.bounce-leave-active {
  animation: bounceIn 0.3s ease reverse;
}
.nav-divider {
  height: 1px;
  margin: 8px 12px;
  background: rgba(212,164,76,0.15);
}
</style>
