<template>
  <div class="staff-shell">
    <!-- Scrollable content area -->
    <div class="staff-scroll-area">
      <div class="staff-container">
        <router-view />
      </div>
    </div>
    
    <!-- Medieval Bottom Nav -->
    <div class="staff-bottom-nav">
      <router-link to="/staff/home" class="nav-tab" active-class="nav-tab--active">
        <span class="nav-icon-rpg">🏠</span>
        <span class="nav-label">Home</span>
      </router-link>

      <router-link to="/staff/check-in" class="nav-tab nav-tab--center" active-class="nav-tab--active">
        <div class="checkin-fab">
          <span style="font-size: 24px;">🗡️</span>
        </div>
        <span class="nav-label" style="margin-top: 28px; color: #d4a44c;">Daily Quest</span>
      </router-link>

      <router-link to="/staff/services" class="nav-tab" active-class="nav-tab--active">
        <span class="nav-icon-rpg">📜</span>
        <span class="nav-label">Services</span>
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.staff-shell {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  font-family: 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #e8d5b7;
  background: linear-gradient(160deg, #1a1a2e 0%, #16213e 40%, #1a1a2e 100%);
}

.staff-scroll-area {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 88px;
}

.staff-container {
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
  box-sizing: border-box;
}

/* Medieval Bottom Nav */
.staff-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: linear-gradient(180deg, rgba(44, 24, 16, 0.97), rgba(28, 18, 8, 0.98));
  border-top: 2px solid rgba(212, 164, 76, 0.3);
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.4);
  z-index: 50;
  padding-bottom: env(safe-area-inset-bottom);
}

.nav-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  color: #8b7355;
  text-decoration: none;
  transition: color 0.2s;
  position: relative;
}
.nav-tab:hover {
  color: #d4a44c;
}
.nav-tab--active {
  color: #d4a44c;
}

.nav-icon-rpg {
  font-size: 22px;
  margin-bottom: 4px;
}

.nav-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

/* Center Quest FAB */
.checkin-fab {
  position: absolute;
  top: -22px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  box-shadow: 0 4px 20px rgba(212, 164, 76, 0.4), 0 0 30px rgba(212, 164, 76, 0.15);
  border: 3px solid rgba(28, 18, 8, 0.95);
  transition: transform 0.2s;
}
.checkin-fab:hover {
  transform: scale(1.08);
}

@media (min-width: 640px) {
  .staff-container {
    max-width: 480px;
    padding: 0 28px;
  }
}
@media (min-width: 1024px) {
  .staff-container {
    max-width: 520px;
  }
  .staff-bottom-nav {
    max-width: 520px;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 12px 12px 0 0;
    border-left: 2px solid rgba(212, 164, 76, 0.3);
    border-right: 2px solid rgba(212, 164, 76, 0.3);
  }
}
</style>
