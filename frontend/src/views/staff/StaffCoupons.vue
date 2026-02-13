<template>
  <div class="staff-page">
    <h1 class="page-title">🎒 Inventory</h1>
    <p class="page-sub">Your acquired items</p>

    <div class="coupon-list">
      <div v-for="item in myRedemptions" :key="item.id" class="coupon-card">
        <!-- Left Side (Ticket Stub) -->
        <div class="coupon-stub">
          <div class="stub-notch stub-notch--top"></div>
          <div class="stub-notch stub-notch--bottom"></div>
          <img v-if="item.reward?.image" :src="item.reward.image" class="stub-item-img" />
          <span v-else class="stub-emoji">🎟️</span>
        </div>

        <!-- Right Side -->
        <div class="coupon-body">
          <div>
            <h4 class="coupon-name">{{ item.reward?.name || 'Item' }}</h4>
            <p class="coupon-date">Acquired: {{ new Date(item.created_at).toLocaleDateString('en-GB') }}</p>
          </div>

          <div class="coupon-footer">
            <span :class="['status-pill', 'status-pill--' + item.status]">
              {{ item.status }}
            </span>

            <button v-if="['ready', 'approved', 'pending'].includes(item.status)"
              class="qr-btn" @click="showQrModal(item)">
              Show Seal
            </button>
          </div>
        </div>
      </div>

      <div v-if="myRedemptions.length === 0" class="empty-state">
        <span class="empty-icon">🎒</span>
        <p class="empty-text">Inventory empty. Visit the Item Shop!</p>
      </div>
    </div>

    <!-- QR Modal -->
    <div v-if="qrItem" class="modal-overlay" @click.self="qrItem = null">
      <div class="modal-card">
        <div class="modal-accent"></div>
        <h3 class="modal-title">Present Seal</h3>
        <p class="modal-sub">Show this seal to the guild master</p>

        <div class="qr-container">
          <div v-if="qrItem.qr_code" class="qr-code">{{ qrItem.qr_code }}</div>
        </div>

        <button class="modal-done-btn" @click="qrItem = null">Done</button>
      </div>
    </div>
  </div>
</template>

<script>
import { getMyRedemptions } from '../../services/api'

export default {
  name: 'StaffCoupons',
  data() {
    return { myRedemptions: [], qrItem: null }
  },
  async mounted() {
    try { const { data } = await getMyRedemptions(); this.myRedemptions = data }
    catch (e) { console.error(e) }
  },
  methods: {
    showQrModal(item) { this.qrItem = item },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

.page-title {
  font-family: 'Cinzel', serif;
  font-size: 26px; font-weight: 800;
  color: #d4a44c;
  text-shadow: 0 2px 8px rgba(212,164,76,0.2);
  margin-bottom: 4px;
}
.page-sub { color: #8b7355; font-size: 14px; font-weight: 600; margin-bottom: 24px; font-style: italic; }

/* Coupon List */
.coupon-list { display: flex; flex-direction: column; gap: 14px; }
.coupon-card {
  display: flex;
  border-radius: 10px;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(44,24,16,0.7), rgba(26,26,46,0.8));
  border: 2px solid rgba(212,164,76,0.15);
  transition: all 0.2s;
}
.coupon-card:hover { border-color: rgba(212,164,76,0.3); }

/* Ticket Stub */
.coupon-stub {
  width: 100px;
  flex-shrink: 0;
  background: rgba(26,26,46,0.5);
  border-right: 2px dashed rgba(212,164,76,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.stub-notch {
  width: 14px; height: 14px;
  background: linear-gradient(145deg, rgba(44,24,16,0.7), rgba(26,26,46,0.8));
  border-radius: 50%;
  position: absolute;
  right: -7px;
  border: 2px solid rgba(212,164,76,0.15);
}
.stub-notch--top { top: -7px; }
.stub-notch--bottom { bottom: -7px; }
.stub-emoji { font-size: 28px; filter: grayscale(0.3); transition: filter 0.3s; }
.coupon-card:hover .stub-emoji { filter: grayscale(0); }
.stub-item-img {
  width: 100%; height: 100%;
  object-fit: cover;
  position: absolute; top: 0; left: 0;
}
.coupon-card:hover .stub-item-img { opacity: 0.9; }

/* Body */
.coupon-body {
  flex: 1;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 88px;
}
.coupon-name { font-weight: 700; font-size: 16px; color: #e8d5b7; margin-bottom: 2px; }
.coupon-date { font-size: 12px; color: #8b7355; }
.coupon-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }

/* Status pills */
.status-pill {
  padding: 3px 12px; border-radius: 6px;
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em;
  border: 1px solid;
}
.status-pill--pending { background: rgba(212,164,76,0.1); color: #d4a44c; border-color: rgba(212,164,76,0.3); }
.status-pill--approved { background: rgba(41,128,185,0.1); color: #3498db; border-color: rgba(41,128,185,0.3); }
.status-pill--ready { background: rgba(41,128,185,0.2); color: #3498db; border-color: rgba(41,128,185,0.4); }
.status-pill--completed { background: rgba(39,174,96,0.1); color: #27ae60; border-color: rgba(39,174,96,0.3); }
.status-pill--rejected { background: rgba(192,57,43,0.1); color: #e74c3c; border-color: rgba(192,57,43,0.3); }

.qr-btn {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px; font-weight: 700;
  color: #1c1208;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  border: 2px solid #d4a44c;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(212,164,76,0.2);
  transition: all 0.15s;
}
.qr-btn:active { transform: scale(0.96); }

/* Empty */
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 16px;
  border-radius: 12px; border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; padding: 24px;
  animation: fadeIn 0.25s ease-out;
}
.modal-card {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 2px solid #d4a44c;
  padding: 36px 28px;
  border-radius: 16px;
  text-align: center;
  max-width: 340px; width: 100%;
  box-shadow: 0 24px 64px rgba(0,0,0,0.4);
  position: relative;
  overflow: hidden;
}
.modal-accent {
  position: absolute; top: 0; left: 0;
  width: 100%; height: 3px;
  background: linear-gradient(90deg, transparent, #d4a44c, transparent);
}
.modal-title { font-family: 'Cinzel', serif; font-size: 22px; font-weight: 800; color: #d4a44c; margin-bottom: 6px; }
.modal-sub { font-size: 14px; color: #8b7355; margin-bottom: 24px; }
.qr-container {
  background: rgba(26,26,46,0.5); padding: 24px;
  border-radius: 12px; margin-bottom: 24px;
  display: inline-block; border: 2px solid rgba(212,164,76,0.2);
}
.qr-code {
  width: 180px; height: 180px;
  background: rgba(44,24,16,0.5);
  border: 2px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-family: monospace;
  color: #e8d5b7; word-break: break-all; padding: 16px;
  border-radius: 8px;
}
.modal-done-btn {
  width: 100%; padding: 14px 0;
  border-radius: 10px; font-weight: 700; font-size: 15px;
  color: #1c1208; background: linear-gradient(135deg, #b8860b, #d4a44c);
  border: 2px solid #d4a44c;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(212,164,76,0.2);
  transition: all 0.15s;
}
.modal-done-btn:active { transform: scale(0.97); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
