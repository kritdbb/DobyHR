<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="castle-icon">🏰</div>
        <h1 class="login-title">Doby Kingdom</h1>
        <p class="login-sub">Enter the realm, brave adventurer ⚔️</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label>📧 Email</label>
          <input v-model="email" type="email" required class="form-input" placeholder="adventurer@kingdom.com">
        </div>
        
        <div class="form-group">
          <label>🔑 Password</label>
          <input v-model="password" type="password" required class="form-input" placeholder="••••••••">
        </div>
        
        <button type="submit" class="enter-btn" :disabled="loading">
          {{ loading ? '⏳ Opening gates...' : '⚔️ Enter the Kingdom' }}
        </button>
      </form>

      <div class="sso-divider">
        <span>or</span>
      </div>

      <div class="google-sso-wrap">
        <div id="google-signin-btn"></div>
        <p v-if="ssoError" class="sso-error">{{ ssoError }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { login, ssoLogin, getGoogleClientId } from '../services/api'

export default {
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      ssoError: '',
    }
  },
  inject: ['showToast'],
  methods: {
    _handleLoginResponse(data) {
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data))

      if (this.$router.currentRoute.value.query.redirect) {
        this.$router.push(this.$router.currentRoute.value.query.redirect)
      } else {
        this.$router.push('/staff/home')
      }
    },
    async handleLogin() {
      this.loading = true
      try {
        const { data } = await login(this.email, this.password)
        this._handleLoginResponse(data)
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'Login failed', 'error')
      } finally {
        this.loading = false
      }
    },
    async handleGoogleCallback(response) {
      this.ssoError = ''
      this.loading = true
      try {
        const { data } = await ssoLogin(response.credential)
        this._handleLoginResponse(data)
      } catch (e) {
        this.ssoError = e.response?.data?.detail || 'Google SSO login failed'
        this.showToast(this.ssoError, 'error')
      } finally {
        this.loading = false
      }
    },
    async initGoogleSSO() {
      try {
        const { data } = await getGoogleClientId()
        if (!data.client_id) return

        // Wait for GSI script to load
        const waitForGoogle = () => {
          return new Promise((resolve) => {
            if (window.google?.accounts) return resolve()
            const interval = setInterval(() => {
              if (window.google?.accounts) {
                clearInterval(interval)
                resolve()
              }
            }, 100)
            // Timeout after 5s
            setTimeout(() => { clearInterval(interval); resolve() }, 5000)
          })
        }

        await waitForGoogle()
        if (!window.google?.accounts) return

        window.google.accounts.id.initialize({
          client_id: data.client_id,
          callback: this.handleGoogleCallback,
        })
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-btn'),
          {
            theme: 'filled_black',
            size: 'large',
            width: '100%',
            text: 'signin_with',
            shape: 'rectangular',
          }
        )
      } catch (e) {
        console.error('Failed to init Google SSO', e)
      }
    }
  },
  async mounted() {
    this.initGoogleSSO()
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(160deg, #0f0a1a 0%, #1a1a2e 30%, #16213e 60%, #0f3460 100%);
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at center, rgba(212,164,76,0.03) 0%, transparent 70%);
  animation: slowRotate 60s linear infinite;
  pointer-events: none;
}

@keyframes slowRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.login-card {
  max-width: 420px;
  width: 100%;
  background: linear-gradient(145deg, rgba(44, 24, 16, 0.95), rgba(26, 26, 46, 0.95));
  border: 2px solid rgba(212, 164, 76, 0.4);
  border-radius: 16px;
  padding: 48px 36px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 60px rgba(212,164,76,0.08);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.castle-icon {
  font-size: 56px;
  margin-bottom: 12px;
  filter: drop-shadow(0 4px 12px rgba(212,164,76,0.3));
}

.login-title {
  font-family: 'Cinzel', serif;
  font-size: 32px;
  font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 16px rgba(212,164,76,0.3);
  margin-bottom: 6px;
}

.login-sub {
  color: #b8860b;
  font-size: 14px;
  font-weight: 600;
  font-style: italic;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.enter-btn {
  width: 100%;
  padding: 14px 0;
  border-radius: 10px;
  font-family: 'Cinzel', serif;
  font-size: 16px;
  font-weight: 700;
  border: 2px solid #d4a44c;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  color: #1c1208;
  cursor: pointer;
  transition: all 0.25s;
  text-shadow: 0 1px 1px rgba(255,255,255,0.2);
  box-shadow: 0 4px 20px rgba(212,164,76,0.3);
}

.enter-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d4a44c, #ffd700);
  box-shadow: 0 8px 32px rgba(212,164,76,0.4);
  transform: translateY(-2px);
}

.enter-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sso-divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
  gap: 12px;
}
.sso-divider::before,
.sso-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(212,164,76,0.2);
}
.sso-divider span {
  color: #8b7355;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.google-sso-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.sso-error {
  color: #c0392b;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}
</style>
