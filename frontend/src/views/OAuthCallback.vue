<template>
  <div class="oauth-loading">
    <div class="spinner"></div>
    <p>Linking your Fitbit account...</p>
  </div>
</template>

<script>
export default {
  mounted() {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    if (code) {
      // Redirect to the Fitbit page within the staff layout, passing the code
      this.$router.replace({ path: '/staff/fitbit', query: { code } })
    } else {
      this.$router.replace('/staff/fitbit')
    }
  }
}
</script>

<style scoped>
.oauth-loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; color: #8b7355; font-size: 14px; font-weight: 600;
  background: linear-gradient(160deg, #1a1a2e 0%, #16213e 40%, #1a1a2e 100%);
}
.spinner {
  width: 40px; height: 40px; border-radius: 50%; margin-bottom: 16px;
  border: 4px solid rgba(212,164,76,0.2); border-top-color: #d4a44c;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
