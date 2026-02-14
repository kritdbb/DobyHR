<template>
  <div class="staff-page">
    <!-- ═══════ RPG Character Sheet ═══════ -->
    <div class="char-sheet">
      <!-- Decorative corners -->
      <div class="corner tl"></div><div class="corner tr"></div>
      <div class="corner bl"></div><div class="corner br"></div>

      <!-- Profile Row: Portrait left, Info right -->
      <div class="cs-profile-row">
        <div class="cs-portrait">
          <div class="cs-portrait-glow"></div>
          <div class="cs-portrait-ring">
            <img v-if="userImage" :src="userImage" class="cs-portrait-img" />
            <div v-else class="cs-portrait-ph">{{ userName.charAt(0) || '?' }}</div>
          </div>
        </div>
        <div class="cs-identity">
          <div class="cs-name">{{ userName }}</div>
          <div class="cs-title">〈 {{ userPosition || 'Adventurer' }} 〉</div>
          <div v-if="userStatus" class="cs-quote">「{{ userStatus }}」</div>
        </div>
      </div>

      <!-- Badges Row -->
      <div class="cs-badges" @click="showBadgeModal = true" v-if="myBadges.length > 0">
        <div v-for="badge in myBadges.slice(0, 8)" :key="badge.id" class="cs-badge-circle" :title="badge.badge_name">
          <img v-if="badge.badge_image" :src="badge.badge_image" class="cs-badge-img" />
          <span v-else class="cs-badge-fb">🏅</span>
        </div>
        <div v-if="myBadges.length > 8" class="cs-badge-more">+{{ myBadges.length - 8 }}</div>
      </div>

      <div class="cs-divider"></div>

      <!-- Stat Bars -->
      <div class="cs-stats">
        <div class="cs-stat-row">
          <span class="cs-stat-icon">⚔️</span>
          <span class="cs-stat-label str">STR</span>
          <div class="cs-stat-track"><div class="cs-stat-fill str" :style="{ width: Math.min(myStats.total_str, 100) + '%' }"></div></div>
          <span class="cs-stat-num str">{{ myStats.total_str }}</span>
        </div>
        <div class="cs-stat-row">
          <span class="cs-stat-icon">🛡️</span>
          <span class="cs-stat-label def">DEF</span>
          <div class="cs-stat-track"><div class="cs-stat-fill def" :style="{ width: Math.min(myStats.total_def, 100) + '%' }"></div></div>
          <span class="cs-stat-num def">{{ myStats.total_def }}</span>
        </div>
        <div class="cs-stat-row">
          <span class="cs-stat-icon">🍀</span>
          <span class="cs-stat-label luk">LUK</span>
          <div class="cs-stat-track"><div class="cs-stat-fill luk" :style="{ width: Math.min(myStats.total_luk, 100) + '%' }"></div></div>
          <span class="cs-stat-num luk">{{ myStats.total_luk }}</span>
        </div>
      </div>

      <div class="cs-divider"></div>

      <!-- Currency -->
      <div class="cs-currency">
        <div class="cs-cur-block gold">
          <span class="cs-cur-val">{{ myCoins.toLocaleString() }}</span>
          <span class="cs-cur-lbl">💰 Gold</span>
        </div>
        <div class="cs-cur-sep"></div>
        <div class="cs-cur-block mana">
          <span class="cs-cur-val">{{ myAngelCoins.toLocaleString() }}</span>
          <span class="cs-cur-lbl">✨ Mana</span>
        </div>
      </div>
    </div>

    <!-- ═══════ Step Quests ═══════ -->
    <div v-if="fitbitConnected" class="section steps-section">
      <div class="steps-header">
        <h2 class="section-title">🥾 Step Quests</h2>
        <button @click="syncSteps" class="steps-sync-btn" :disabled="stepsSyncing">
          {{ stepsSyncing ? '⏳' : '🔄' }}
        </button>
      </div>

      <!-- Daily Quest Bar (unified multi-tier) -->
      <router-link to="/staff/fitbit" class="quest-bar-link">
        <div class="quest-bar quest-bar--multitier" :class="{ 'quest-bar--done': dailyAllClaimed, 'quest-bar--ready': dailyAnyReady }">
          <div class="quest-bar-icon">
            <span v-if="dailyAllClaimed">✅</span>
            <span v-else-if="dailyAnyReady">⭐</span>
            <span v-else>⚔️</span>
          </div>
          <div class="quest-bar-main">
            <div class="quest-bar-label">
              <span class="quest-bar-name">Daily Quest</span>
              <span class="quest-bar-pct">{{ dailyOverallPct }}%</span>
            </div>
            <!-- Bar + milestones wrapper -->
            <div class="multitier-wrap">
              <div class="quest-bar-track" style="position: relative;">
                <div class="quest-bar-fill" :style="{ width: dailyOverallPct + '%' }"
                     :class="{ 'quest-bar-fill--done': dailyAllClaimed }"></div>
                <!-- Tier 1 marker line -->
                <template v-if="hasTier2">
                  <div class="tier-marker" :style="{ left: tier1Pct + '%' }">
                    <div class="tier-marker-line"></div>
                  </div>
                </template>
              </div>
              <!-- Reward anchors below the bar -->
              <div class="tier-anchors">
                <!-- Tier 1 reward (positioned at tier1 %) -->
                <div class="tier-anchor" :style="{ left: hasTier2 ? tier1Pct + '%' : '50%' }">
                  <div class="tier-anchor-tags">
                    <span v-if="stepGoals.daily_goal.claimed" class="tier-check">✅</span>
                    <span v-else-if="stepGoals.daily_goal.reached" class="tier-check">⭐</span>
                    <span v-if="stepGoals.daily_goal.str > 0" class="qr-tag qr-str">STR+{{ stepGoals.daily_goal.str }}</span>
                    <span v-if="stepGoals.daily_goal.def > 0" class="qr-tag qr-def">DEF+{{ stepGoals.daily_goal.def }}</span>
                    <span v-if="stepGoals.daily_goal.luk > 0" class="qr-tag qr-luk">LUK+{{ stepGoals.daily_goal.luk }}</span>
                    <span v-if="stepGoals.daily_goal.gold > 0" class="qr-tag qr-gold">💰+{{ stepGoals.daily_goal.gold }}</span>
                    <span v-if="stepGoals.daily_goal.mana > 0" class="qr-tag qr-mana">✨+{{ stepGoals.daily_goal.mana }}</span>
                  </div>
                  <div class="tier-anchor-label">{{ (stepGoals.daily_goal.target || 0).toLocaleString() }}</div>
                </div>
                <!-- Tier 2 reward (positioned at right end) -->
                <div v-if="hasTier2" class="tier-anchor" style="left: 100%;">
                  <div class="tier-anchor-tags">
                    <span v-if="stepGoals.daily2_goal.claimed" class="tier-check">✅</span>
                    <span v-else-if="stepGoals.daily2_goal.reached" class="tier-check">⭐</span>
                    <span v-if="stepGoals.daily2_goal.str > 0" class="qr-tag qr-str">STR+{{ stepGoals.daily2_goal.str }}</span>
                    <span v-if="stepGoals.daily2_goal.def > 0" class="qr-tag qr-def">DEF+{{ stepGoals.daily2_goal.def }}</span>
                    <span v-if="stepGoals.daily2_goal.luk > 0" class="qr-tag qr-luk">LUK+{{ stepGoals.daily2_goal.luk }}</span>
                    <span v-if="stepGoals.daily2_goal.gold > 0" class="qr-tag qr-gold">💰+{{ stepGoals.daily2_goal.gold }}</span>
                    <span v-if="stepGoals.daily2_goal.mana > 0" class="qr-tag qr-mana">✨+{{ stepGoals.daily2_goal.mana }}</span>
                  </div>
                  <div class="tier-anchor-label">{{ (stepGoals.daily2_goal.target || 0).toLocaleString() }}</div>
                </div>
              </div>
            </div>
            <div class="quest-bar-sub">
              {{ (stepGoals.today_steps || 0).toLocaleString() }} steps today
            </div>
          </div>
        </div>
      </router-link>

      <!-- Monthly Quest Bar -->
      <router-link v-if="stepGoals.monthly_goal && stepGoals.monthly_goal.enabled" to="/staff/fitbit" class="quest-bar-link">
        <div class="quest-bar quest-bar--monthly" :class="{ 'quest-bar--done': stepGoals.monthly_goal.claimed, 'quest-bar--ready': stepGoals.monthly_goal.reached && !stepGoals.monthly_goal.claimed }">
          <div class="quest-bar-icon">
            <span v-if="stepGoals.monthly_goal.claimed">✅</span>
            <span v-else-if="stepGoals.monthly_goal.reached">⭐</span>
            <span v-else>🗓️</span>
          </div>
          <div class="quest-bar-main">
            <div class="quest-bar-label">
              <span class="quest-bar-name">Monthly Quest</span>
              <span class="quest-bar-pct">{{ monthlyPct }}%</span>
            </div>
            <div class="quest-bar-track quest-bar-track--monthly">
              <div class="quest-bar-fill quest-bar-fill--monthly" :style="{ width: monthlyPct + '%' }"
                   :class="{ 'quest-bar-fill--done': stepGoals.monthly_goal.claimed }"></div>
            </div>
            <div class="quest-bar-sub">
              {{ (stepGoals.monthly_steps || 0).toLocaleString() }} / {{ (stepGoals.monthly_goal.target || 0).toLocaleString() }} steps
            </div>
          </div>
          <div class="quest-bar-rewards">
            <span v-if="stepGoals.monthly_goal.str > 0" class="qr-tag qr-str">STR+{{ stepGoals.monthly_goal.str }}</span>
            <span v-if="stepGoals.monthly_goal.def > 0" class="qr-tag qr-def">DEF+{{ stepGoals.monthly_goal.def }}</span>
            <span v-if="stepGoals.monthly_goal.luk > 0" class="qr-tag qr-luk">LUK+{{ stepGoals.monthly_goal.luk }}</span>
            <span v-if="stepGoals.monthly_goal.gold > 0" class="qr-tag qr-gold">💰+{{ stepGoals.monthly_goal.gold }}</span>
            <span v-if="stepGoals.monthly_goal.mana > 0" class="qr-tag qr-mana">✨+{{ stepGoals.monthly_goal.mana }}</span>
          </div>
        </div>
      </router-link>
    </div>
    <div v-else-if="fitbitChecked" class="section steps-section steps-connect-mini">
      <router-link to="/staff/fitbit" class="steps-connect-link">
        <span class="steps-connect-icon">⌚</span>
        <div>
          <div class="steps-connect-title">Connect Fitbit</div>
          <div class="steps-connect-sub">Track your daily steps & earn rewards</div>
        </div>
        <span class="steps-connect-arrow">→</span>
      </router-link>
    </div>

    <!-- 💖 ชุบทีคับ: Mana Rescue -->
    <div v-if="negativeUsers.length > 0" class="section rescue-section">
      <h2 class="section-title">🆘 Rescue - ชุบชีวิตเพื่อน</h2>
      <div v-for="u in negativeUsers" :key="'rescue-'+u.id" class="rescue-card">
        <div class="rescue-portrait">
          <img v-if="u.image" :src="u.image" class="rescue-img" />
          <span v-else class="rescue-fb">{{ u.name.charAt(0) }}</span>
        </div>
        <div class="rescue-body">
          <div class="rescue-text">⚠️ <strong>{{ u.name }}</strong> กำลังติดลบ <span class="rescue-debt">{{ u.coins }} Gold</span>!</div>
          <div class="rescue-sub">ช่วยส่ง Mana ให้หน่อย! ทุก Mana ที่ส่งไป จะช่วย +5 Gold</div>
        </div>
        <button class="rescue-btn" @click="openRescueConfirm(u)" :disabled="myAngelCoins < 1">
          💖 ชุบชีวิต
        </button>
      </div>
    </div>

    <!-- Rescue Confirmation Modal -->
    <div v-if="showRescueModal" class="badge-modal-overlay" @click.self="showRescueModal = false">
      <div class="badge-modal rescue-modal">
        <div class="rescue-modal-icon">💖</div>
        <h3 class="badge-modal-title">ชุบชีวิตเพื่อน</h3>
        <p class="rescue-modal-text">
          คุณต้องการใช้ <strong>1 Mana</strong> ช่วยชุบชีวิต <strong>{{ rescueTarget?.name }}</strong> ไหม?<br>
          Mana จะมีผล <strong class="rescue-gold">+5 Gold</strong> ให้กับเพื่อนที่ติดลบ
        </p>
        <div class="rescue-modal-balance">✨ Mana ของคุณ: {{ myAngelCoins }}</div>
        <div class="rescue-modal-actions">
          <button class="btn-cancel" @click="showRescueModal = false">ยกเลิก</button>
          <button class="rescue-confirm-btn" @click="performRescue" :disabled="rescuing">
            {{ rescuing ? 'กำลังชุบชีวิต...' : '💖 ยืนยัน ชุบชีวิต' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Approval Board: Pending Approvals -->
    <div v-if="pendingLeaves.length > 0 || pendingRedemptions.length > 0 || pendingWorkRequests.length > 0" class="section">
      <h2 class="section-title">📜 Approval Board</h2>

      <!-- Pending Leaves -->
      <div v-for="item in pendingLeaves" :key="'leave-'+item.id" class="quest-card quest-card--leave">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">🏖️</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">{{ item.leave_type }} leave</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-detail">📅 {{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
        <div class="quest-detail" v-if="item.reason">💬 {{ item.reason }}</div>
        <div class="quest-actions">
          <button @click="handleApproveLeave(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectLeave(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>

      <!-- Pending Redemptions -->
      <div v-for="item in pendingRedemptions" :key="'redeem-'+item.id" class="quest-card quest-card--redeem">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">🛒</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">Trade: {{ item.reward_name }} ({{ item.point_cost }} 💰)</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-actions">
          <button @click="handleApproveRedeem(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectRedeem(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>

      <!-- Pending Work Requests -->
      <div v-for="item in pendingWorkRequests" :key="'wr-'+item.id" class="quest-card quest-card--work">
        <div class="quest-header">
          <div class="quest-info">
            <span class="quest-emoji">📋</span>
            <div>
              <div class="quest-name">{{ item.user_name }}</div>
              <div class="quest-type">Special Mission (non-working day)</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-detail" v-if="item.check_in_time">🕐 Quest started: {{ item.check_in_time }}</div>
        <div class="quest-actions">
          <button @click="handleApproveWorkRequest(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="handleRejectWorkRequest(item.id)" class="btn-reject">❌ Deny</button>
        </div>
      </div>
    </div>

    <!-- Gold Ledger -->
    <div class="section">
      <h2 class="section-title">💰 Gold Ledger</h2>
      <div v-if="coinLogs.length === 0" class="empty-state">
        <div class="empty-icon">💰</div>
        <p class="empty-text">No gold transactions yet</p>
      </div>
      <div v-else class="coin-list">
        <div v-for="log in coinLogs.slice(0, 5)" :key="log.id" class="coin-item">
          <span class="coin-dot">{{ log.amount >= 0 ? '🟢' : '🔴' }}</span>
          <div class="coin-info">
            <div class="coin-reason">{{ log.reason }}</div>
            <div class="coin-date">{{ formatDateTime(log.created_at) }}</div>
          </div>
          <span :class="['coin-amount', log.amount >= 0 ? 'coin-amount--plus' : 'coin-amount--minus']">
            {{ log.amount >= 0 ? '+' : '' }}{{ log.amount }}
          </span>
        </div>
        <button v-if="coinLogs.length > 5" class="btn-see-more" @click="showGoldModal = true">
          📜 See More ({{ coinLogs.length }} total)
        </button>
      </div>
    </div>

    <!-- Mana Received -->
    <div v-if="angelCoinReceipts.length > 0" class="section">
      <h2 class="section-title">✨ Mana Received</h2>
      <div class="mana-receipts">
        <div v-for="receipt in angelCoinReceipts" :key="receipt.id" class="mana-receipt-card">
          <div class="mana-receipt-icon">✨</div>
          <div class="mana-receipt-body">
            <div class="mana-receipt-text">{{ receipt.reason }}</div>
            <div class="mana-receipt-amount">+{{ receipt.amount }} 💰</div>
            <div class="mana-receipt-date">{{ formatDateTime(receipt.created_at) }}</div>
          </div>
        </div>
        <div class="balance-bar">
          <span>Your treasury</span>
          <span class="balance-value">💰 {{ myCoins }} Gold  &nbsp;|&nbsp; ✨ {{ myAngelCoins }} Mana</span>
        </div>
      </div>
    </div>

    <!-- Town Crier: Badge Awards -->
    <div class="section">
      <h2 class="section-title">📢 Town Crier</h2>
      <div v-if="recentAwards.length === 0" class="empty-state">
        <div class="empty-icon">📯</div>
        <p class="empty-text">No proclamations from the kingdom yet 🏰</p>
      </div>
      <div v-else class="award-announce-list">
        <div v-for="a in recentAwards.slice(0, 5)" :key="a.id" class="award-announce-card">
          <!-- Badge event -->
          <template v-if="a.type === 'badge'">
            <div class="award-announce-badge">
              <img v-if="a.badge_image" :src="a.badge_image" class="award-announce-img" />
              <span v-else class="award-announce-fb">🏅</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong>
                <template v-if="a.detail === 'Badge Quest'"> completed <strong class="quest-highlight">Quest</strong> and received Badge <strong>{{ a.badge_name }}</strong></template>
                <template v-else> received <strong>{{ a.badge_name }}</strong></template>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}{{ a.detail && a.detail !== 'Badge Quest' ? ` • by ${a.detail}` : '' }}
              </div>
            </div>
          </template>
          <!-- Mana event -->
          <template v-else-if="a.type === 'mana'">
            <div class="award-announce-badge mana-icon-circle">
              <span>✨</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} Mana</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Lucky Draw event -->
          <template v-else-if="a.type === 'lucky_draw'">
            <div class="award-announce-badge draw-icon-circle">
              <span>🎰</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> won <strong class="draw-highlight">{{ a.amount }} Gold</strong> from Lucky Draw!
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Magic Lottery event -->
          <template v-else-if="a.type === 'magic_lottery'">
            <div class="award-announce-badge lottery-icon-circle">
              <span>🎲</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> used <strong class="lottery-highlight">Magic Lottery</strong> — {{ a.reason }}
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Step Reward event -->
          <template v-else-if="a.type === 'step_reward'">
            <div class="award-announce-badge step-icon-circle">
              <span>🥾</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> completed <strong class="step-highlight">{{ a.goal_type }} Step Quest</strong> — {{ a.reward_label }}
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Mana Rescue event -->
          <template v-else-if="a.type === 'rescue'">
            <div class="award-announce-badge rescue-icon-circle">
              <span>🆘</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> ได้รับการชุบชีวิตแล้ว! <strong class="rescue-highlight">Gold +{{ a.amount }}</strong>
                <div class="rescue-by">โดย {{ a.rescuers }}</div>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
        </div>
        <button v-if="recentAwards.length > 5" class="btn-see-more" @click="showTownCrierModal = true">
          📯 See More ({{ recentAwards.length }} proclamations)
        </button>
      </div>
    </div>

    <!-- Gold Ledger Full Modal -->
    <div v-if="showGoldModal" class="badge-modal-overlay" @click.self="showGoldModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">💰 Gold Ledger ({{ coinLogs.length }})</h3>
        <div class="coin-list modal-coin-list">
          <div v-for="log in coinLogs.slice(0, 50)" :key="log.id" class="coin-item">
            <span class="coin-dot">{{ log.amount >= 0 ? '🟢' : '🔴' }}</span>
            <div class="coin-info">
              <div class="coin-reason">{{ log.reason }}</div>
              <div class="coin-date">{{ formatDateTime(log.created_at) }}</div>
            </div>
            <span :class="['coin-amount', log.amount >= 0 ? 'coin-amount--plus' : 'coin-amount--minus']">
              {{ log.amount >= 0 ? '+' : '' }}{{ log.amount }}
            </span>
          </div>
        </div>
        <button class="badge-modal-close" @click="showGoldModal = false">Close</button>
      </div>
    </div>

    <!-- Town Crier Full Modal -->
    <div v-if="showTownCrierModal" class="badge-modal-overlay" @click.self="showTownCrierModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">📢 Town Crier ({{ recentAwards.length }})</h3>
        <div class="award-announce-list modal-award-list">
          <div v-for="a in recentAwards.slice(0, 50)" :key="a.id" class="award-announce-card">
            <template v-if="a.type === 'badge'">
              <div class="award-announce-badge">
                <img v-if="a.badge_image" :src="a.badge_image" class="award-announce-img" />
                <span v-else class="award-announce-fb">🏅</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong>
                  <template v-if="a.detail === 'Badge Quest'"> completed <strong class="quest-highlight">Quest</strong> and received Badge <strong>{{ a.badge_name }}</strong></template>
                  <template v-else> received <strong>{{ a.badge_name }}</strong></template>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}{{ a.detail && a.detail !== 'Badge Quest' ? ` • by ${a.detail}` : '' }}
                </div>
              </div>
            </template>
            <template v-else-if="a.type === 'mana'">
              <div class="award-announce-badge mana-icon-circle">
                <span>✨</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} Mana</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Lucky Draw event -->
            <template v-else-if="a.type === 'lucky_draw'">
              <div class="award-announce-badge draw-icon-circle">
                <span>🎰</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> won <strong class="draw-highlight">{{ a.amount }} Gold</strong> from Lucky Draw!
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Magic Lottery event -->
            <template v-else-if="a.type === 'magic_lottery'">
              <div class="award-announce-badge lottery-icon-circle">
                <span>🎲</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> used <strong class="lottery-highlight">Magic Lottery</strong> — {{ a.reason }}
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Step Reward event (modal) -->
            <template v-else-if="a.type === 'step_reward'">
              <div class="award-announce-badge step-icon-circle">
                <span>🥾</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> completed <strong class="step-highlight">{{ a.goal_type }} Step Quest</strong> — {{ a.reward_label }}
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Mana Rescue event (modal) -->
            <template v-else-if="a.type === 'rescue'">
              <div class="award-announce-badge rescue-icon-circle">
                <span>🆘</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> ได้รับการชุบชีวิตแล้ว! <strong class="rescue-highlight">Gold +{{ a.amount }}</strong>
                  <div class="rescue-by">โดย {{ a.rescuers }}</div>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
          </div>
        </div>
        <button class="badge-modal-close" @click="showTownCrierModal = false">Close</button>
      </div>
    </div>
    <div v-if="showBadgeModal" class="badge-modal-overlay" @click.self="showBadgeModal = false">
      <div class="badge-modal">
        <h3 class="badge-modal-title">🏅 My Badges ({{ myBadges.length }})</h3>
        <div class="badge-list">
          <div v-for="b in myBadges" :key="b.id" class="badge-list-item">
            <div class="badge-list-icon">
              <img v-if="b.badge_image" :src="b.badge_image" class="badge-list-img" />
              <span v-else class="badge-list-fallback">🏅</span>
            </div>
            <div class="badge-list-info">
              <div class="badge-list-name">{{ b.badge_name }}</div>
              <div class="badge-list-desc">{{ b.badge_description || '' }}</div>
              <div class="badge-list-stats" v-if="b.stat_str || b.stat_def || b.stat_luk">
                <span v-if="b.stat_str" class="mini-stat str">⚔️+{{ b.stat_str }}</span>
                <span v-if="b.stat_def" class="mini-stat def">🛡️+{{ b.stat_def }}</span>
                <span v-if="b.stat_luk" class="mini-stat luk">🍀+{{ b.stat_luk }}</span>
              </div>
              <div class="badge-list-date">Awarded {{ formatBadgeDate(b.awarded_at) }}{{ b.awarded_by ? ` by ${b.awarded_by}` : '' }}</div>
            </div>
          </div>
        </div>
        <button class="badge-modal-close" @click="showBadgeModal = false">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import api, {
  getPendingLeaveApprovals, getPendingRedemptionApprovals,
  approveLeave, rejectLeave,
  approveRedemption, rejectRedemption,
  getPendingWorkRequests, approveWorkRequest, rejectWorkRequest,
  getMyBadges, getRecentBadgeAwards, getMyStats,
  getFitbitStatus, syncFitbitSteps, getStepGoals,
} from '../../services/api'

export default {
  name: 'StaffHome',
  inject: ['showToast'],
  data() {
    return {
      userName: '',
      userImage: '',
      userPosition: '',
      userStatus: '',
      pendingLeaves: [],
      pendingRedemptions: [],
      pendingWorkRequests: [],
      coinLogs: [],
      angelCoinReceipts: [],
      myCoins: 0,
      myAngelCoins: 0,
      myBadges: [],
      showBadgeModal: false,
      myStats: { total_str: 1, total_def: 1, total_luk: 1, base_str: 1, base_def: 1, base_luk: 1, badge_str: 0, badge_def: 0, badge_luk: 0 },
      recentAwards: [],
      showGoldModal: false,
      showTownCrierModal: false,
      fitbitConnected: false,
      fitbitChecked: false,
      stepGoals: {
        today_steps: 0,
        daily_goal: { target: 5000, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false },
        daily2_goal: { target: 0, enabled: false, str: 0, def: 0, luk: 0, gold: 0, mana: 0, reached: false, claimed: false },
        monthly_steps: 0,
        monthly_goal: { target: 0, enabled: false, reached: false, claimed: false },
      },
      stepsSyncing: false,
      negativeUsers: [],
      showRescueModal: false,
      rescueTarget: null,
      rescuing: false,
    }
  },
  async mounted() {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const u = JSON.parse(userStr)
      this.userName = [u.name, u.surname].filter(Boolean).join(' ') || 'Adventurer'
      this.userImage = u.image || ''
      this.userPosition = u.position || ''
      this.userStatus = u.status_text || ''
    }
    await this.loadData()
    this.loadFitbit()  // fire-and-forget, won't block page
  },
  methods: {
    async loadData() {
      try {
        const userStr = localStorage.getItem('user')
        const u = userStr ? JSON.parse(userStr) : {}

        const [lRes, rRes, wRes] = await Promise.all([
          getPendingLeaveApprovals().catch(() => ({ data: [] })),
          getPendingRedemptionApprovals().catch(() => ({ data: [] })),
          getPendingWorkRequests().catch(() => ({ data: [] })),
        ])
        this.pendingLeaves = lRes.data
        this.pendingRedemptions = rRes.data
        this.pendingWorkRequests = wRes.data

        const userId = u.id || u.user_id
        if (userId) {
          try {
            const [coinRes, userRes] = await Promise.all([
              api.get(`/api/users/${userId}/coin-logs`),
              api.get(`/api/users/${userId}`).catch(() => null),
            ])
            const allLogs = coinRes.data || []
            this.coinLogs = allLogs.slice(0, 50)
            this.angelCoinReceipts = allLogs.filter(l => l.reason && l.reason.includes('Received Angel Coins')).slice(0, 5)
            if (userRes && userRes.data) {
              this.myCoins = userRes.data.coins || 0
              this.myAngelCoins = userRes.data.angel_coins || 0
              this.userImage = userRes.data.image || this.userImage
              this.userPosition = userRes.data.position || this.userPosition
              this.userName = [userRes.data.name, userRes.data.surname].filter(Boolean).join(' ') || this.userName
              this.userStatus = userRes.data.status_text || ''
              // Sync localStorage with latest data
              const stored = JSON.parse(localStorage.getItem('user') || '{}')
              stored.image = userRes.data.image
              stored.name = userRes.data.name
              stored.surname = userRes.data.surname
              stored.position = userRes.data.position
              localStorage.setItem('user', JSON.stringify(stored))
            }
          } catch (e) {
            this.coinLogs = []
          }
        }
      } catch (e) {
        console.error('Home load error:', e)
      }
      // Load badges and recent awards separately
      try {
        const [badgeRes, awardRes, statsRes] = await Promise.all([
          getMyBadges().catch(() => ({ data: [] })),
          getRecentBadgeAwards(50).catch(() => ({ data: [] })),
          getMyStats().catch(() => ({ data: this.myStats })),
        ])
        this.myBadges = badgeRes.data
        this.recentAwards = awardRes.data
        this.myStats = statsRes.data
        // Load negative-coin users for rescue
        try {
          const negRes = await api.get('/api/users/negative-coins')
          this.negativeUsers = negRes.data || []
        } catch (e2) { this.negativeUsers = [] }
      } catch (e) {
        this.myBadges = []
        this.recentAwards = []
      }
    },
    async loadFitbit() {
      try {
        const { data } = await getFitbitStatus()
        this.fitbitConnected = data.connected
        this.fitbitChecked = true
        if (this.fitbitConnected) {
          const goalsRes = await getStepGoals()
          this.stepGoals = goalsRes.data
        }
      } catch (e) { this.fitbitChecked = true }
    },
    async handleApproveLeave(id) {
      try { await approveLeave(id); this.showToast('Quest accepted! ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectLeave(id) {
      try { await rejectLeave(id); this.showToast('Quest denied'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleApproveRedeem(id) {
      try { await approveRedemption(id); this.showToast('Trade approved! 🛒'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectRedeem(id) {
      try { await rejectRedemption(id); this.showToast('Trade rejected'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleApproveWorkRequest(id) {
      try { await approveWorkRequest(id); this.showToast('Mission accepted! Gold granted. ⚔️'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    async handleRejectWorkRequest(id) {
      try { await rejectWorkRequest(id); this.showToast('Mission denied'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-GB') : '' },
    formatDateTime(d) {
      if (!d) return ''
      const dt = new Date(d)
      return dt.toLocaleDateString('en-GB') + ' ' + dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    },
    formatBadgeDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    },
    async syncSteps() {
      this.stepsSyncing = true
      try {
        await syncFitbitSteps()
        const goalsRes = await getStepGoals()
        this.stepGoals = goalsRes.data
      } catch (e) { console.error(e) }
      finally { this.stepsSyncing = false }
    },
    openRescueConfirm(user) {
      this.rescueTarget = user
      this.showRescueModal = true
    },
    async performRescue() {
      if (!this.rescueTarget) return
      this.rescuing = true
      try {
        const res = await api.post('/api/users/rescue', { recipient_id: this.rescueTarget.id })
        this.showToast(`💖 ชุบชีวิต ${res.data.recipient_name} สำเร็จ! Gold +5`)
        this.showRescueModal = false
        this.rescueTarget = null
        await this.loadData()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'ชุบชีวิตไม่สำเร็จ', 'error')
      } finally {
        this.rescuing = false
      }
    },
  },
  computed: {
    dailyMaxTarget() {
      const d2 = this.stepGoals.daily2_goal
      const maxTarget = (d2 && d2.enabled && d2.target > 0) ? Math.max(this.stepGoals.daily_goal?.target || 0, d2.target) : (this.stepGoals.daily_goal?.target || 1)
      return maxTarget || 1
    },
    dailyOverallPct() {
      return Math.min(100, Math.round(((this.stepGoals.today_steps || 0) / this.dailyMaxTarget) * 100))
    },
    tier1Pct() {
      const t1 = this.stepGoals.daily_goal?.target || 0
      return Math.round((t1 / this.dailyMaxTarget) * 100)
    },
    dailyAllClaimed() {
      const d1 = this.stepGoals.daily_goal?.claimed
      const d2 = this.stepGoals.daily2_goal
      return d2 && d2.enabled ? (d1 && d2.claimed) : d1
    },
    dailyAnyReady() {
      const d1 = this.stepGoals.daily_goal
      const d2 = this.stepGoals.daily2_goal
      const r1 = d1?.reached && !d1?.claimed
      const r2 = d2?.enabled && d2?.reached && !d2?.claimed
      return r1 || r2
    },
    hasTier2() {
      const d2 = this.stepGoals.daily2_goal
      return d2 && d2.enabled && d2.target > 0 && this.stepGoals.daily_goal.target < d2.target
    },
    monthlyPct() {
      const t = this.stepGoals.monthly_goal?.target || 1
      return Math.min(100, Math.round(((this.stepGoals.monthly_steps || 0) / t) * 100))
    },
  },
}
</script>

<style scoped>
.staff-page { padding: 28px 0 16px; }

/* ═══ Mana Rescue ═══ */
.rescue-section { }
.rescue-card {
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(135deg, rgba(231,76,60,0.08), rgba(192,57,43,0.04));
  border: 1px solid rgba(231,76,60,0.2);
  border-radius: 12px; padding: 14px 16px;
  margin-bottom: 10px;
}
.rescue-portrait { flex-shrink: 0; }
.rescue-img { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid rgba(231,76,60,0.3); }
.rescue-fb {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(135deg, #c0392b, #e74c3c);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800; color: #fff;
}
.rescue-body { flex: 1; min-width: 0; }
.rescue-text { font-size: 13px; color: #e8d5b7; line-height: 1.4; }
.rescue-debt { color: #e74c3c; font-weight: 700; }
.rescue-sub { font-size: 11px; color: #8b7355; margin-top: 2px; }
.rescue-btn {
  flex-shrink: 0; background: linear-gradient(135deg, #e74c3c, #c0392b);
  color: #fff; border: none; padding: 8px 16px; border-radius: 10px;
  font-weight: 700; font-size: 13px; cursor: pointer;
  box-shadow: 0 2px 8px rgba(231,76,60,0.3);
  transition: all 0.2s;
}
.rescue-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(231,76,60,0.4); }
.rescue-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* Rescue Modal */
.rescue-modal { text-align: center; max-width: 380px; }
.rescue-modal-icon { font-size: 48px; margin-bottom: 8px; }
.rescue-modal-text { font-size: 14px; color: #c4a97d; line-height: 1.6; margin-bottom: 12px; }
.rescue-gold { color: #f1c40f; }
.rescue-modal-balance { font-size: 12px; color: #8b7355; margin-bottom: 16px; padding: 6px 12px; background: rgba(212,164,76,0.08); border-radius: 8px; display: inline-block; }
.rescue-modal-actions { display: flex; gap: 10px; justify-content: center; }
.rescue-confirm-btn {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  color: #fff; border: none; padding: 10px 24px; border-radius: 10px;
  font-weight: 700; font-size: 14px; cursor: pointer;
  box-shadow: 0 2px 8px rgba(231,76,60,0.3);
}
.rescue-confirm-btn:hover { box-shadow: 0 4px 14px rgba(231,76,60,0.5); }
.rescue-confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-cancel {
  background: rgba(255,255,255,0.06); color: #8b7355;
  border: 1px solid rgba(255,255,255,0.1); padding: 10px 20px;
  border-radius: 10px; cursor: pointer; font-weight: 600;
}

/* Rescue event in Town Crier */
.rescue-icon-circle {
  background: linear-gradient(135deg, rgba(231,76,60,0.15), rgba(192,57,43,0.1));
  border: 1px solid rgba(231,76,60,0.25);
}
.rescue-highlight { color: #f1c40f; }
.rescue-by { font-size: 11px; color: #8b7355; margin-top: 2px; font-style: italic; }

/* ═══ RPG Character Sheet ═══ */
.char-sheet {
  position: relative;
  text-align: center;
  background: linear-gradient(170deg, #110a1e 0%, #1e0e0a 40%, #0f0f1e 100%);
  border: 2px solid #d4a44c;
  border-radius: 4px;
  padding: 28px 20px 20px;
  margin-bottom: 28px;
  box-shadow:
    0 0 0 1px rgba(212,164,76,0.15),
    0 0 40px rgba(212,164,76,0.06),
    inset 0 0 60px rgba(0,0,0,0.3);
}

/* Corner ornaments */
.corner {
  position: absolute; width: 14px; height: 14px;
  border-color: #d4a44c; border-style: solid;
}
.corner.tl { top: -1px; left: -1px; border-width: 3px 0 0 3px; }
.corner.tr { top: -1px; right: -1px; border-width: 3px 3px 0 0; }
.corner.bl { bottom: -1px; left: -1px; border-width: 0 0 3px 3px; }
.corner.br { bottom: -1px; right: -1px; border-width: 0 3px 3px 0; }

/* Profile Row */
.cs-profile-row {
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 12px;
}

/* Portrait */
.cs-portrait {
  position: relative; flex-shrink: 0;
}
.cs-portrait-glow {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 110px; height: 110px; border-radius: 50%;
  background: radial-gradient(circle, rgba(212,164,76,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.cs-portrait-ring {
  width: 80px; height: 80px; border-radius: 50%;
  border: 3px solid #d4a44c;
  box-shadow: 0 0 20px rgba(212,164,76,0.25), inset 0 0 16px rgba(0,0,0,0.4);
  overflow: hidden; position: relative; z-index: 1;
}
.cs-portrait-img { width: 100%; height: 100%; object-fit: cover; }
.cs-portrait-ph {
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #b8860b, #d4a44c);
  display: flex; align-items: center; justify-content: center;
  font-size: 30px; font-weight: 800; color: #1c1208;
}

/* Identity */
.cs-identity { text-align: left; flex: 1; min-width: 0; }
.cs-name {
  font-family: 'Cinzel', serif;
  font-size: 20px; font-weight: 800; color: #e8d5b7;
  text-shadow: 0 2px 12px rgba(212,164,76,0.3);
  line-height: 1.3;
}
.cs-title {
  font-size: 12px; color: #b8860b; font-weight: 600;
  letter-spacing: 0.5px; margin-top: 2px;
}
.cs-quote {
  font-size: 12px; color: #e74c3c; font-style: italic;
  font-weight: 600; margin-top: 4px;
  word-break: break-word;
}

/* Badges */
.cs-badges {
  display: flex; align-items: center; justify-content: center;
  gap: 6px; margin-bottom: 6px;
  cursor: pointer; padding: 6px 12px; border-radius: 10px;
  transition: background .2s;
}
.cs-badges:hover { background: rgba(212,164,76,0.08); }
.cs-badge-circle {
  width: 36px; height: 36px; border-radius: 50%;
  overflow: hidden; border: 2px solid rgba(212,164,76,0.3);
  transition: transform .2s;
}
.cs-badge-circle:hover { transform: scale(1.15); }
.cs-badge-img { width: 100%; height: 100%; object-fit: cover; }
.cs-badge-fb {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 16px;
}
.cs-badge-more {
  font-size: 11px; color: #b8860b; font-weight: 700;
  padding: 2px 8px; background: rgba(212,164,76,0.1); border-radius: 8px;
}

/* Divider */
.cs-divider {
  height: 1px; margin: 14px 0;
  background: linear-gradient(90deg, transparent 0%, rgba(212,164,76,0.3) 50%, transparent 100%);
}

/* Stat Bars */
.cs-stats { display: flex; flex-direction: column; gap: 8px; }
.cs-stat-row { display: flex; align-items: center; gap: 8px; }
.cs-stat-icon { font-size: 14px; width: 18px; text-align: center; }
.cs-stat-label {
  font-family: 'Cinzel', serif; font-size: 11px; font-weight: 800;
  width: 30px; letter-spacing: 1px;
}
.cs-stat-label.str { color: #e74c3c; }
.cs-stat-label.def { color: #3498db; }
.cs-stat-label.luk { color: #2ecc71; }
.cs-stat-track {
  flex: 1; height: 10px; border-radius: 5px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
}
.cs-stat-fill {
  height: 100%; border-radius: 4px;
  transition: width 0.6s ease;
}
.cs-stat-fill.str {
  background: linear-gradient(90deg, #8b1a1a, #e74c3c);
  box-shadow: 0 0 6px rgba(231,76,60,0.4);
}
.cs-stat-fill.def {
  background: linear-gradient(90deg, #1a3a5c, #3498db);
  box-shadow: 0 0 6px rgba(52,152,219,0.4);
}
.cs-stat-fill.luk {
  background: linear-gradient(90deg, #1a5c2e, #2ecc71);
  box-shadow: 0 0 6px rgba(46,204,113,0.4);
}
.cs-stat-num {
  font-family: 'Cinzel', serif; font-size: 16px; font-weight: 800;
  width: 30px; text-align: right;
}
.cs-stat-num.str { color: #e74c3c; }
.cs-stat-num.def { color: #3498db; }
.cs-stat-num.luk { color: #2ecc71; }

/* Currency */
.cs-currency {
  display: flex; align-items: center; justify-content: center;
}
.cs-cur-block { flex: 1; text-align: center; }
.cs-cur-val {
  display: block;
  font-family: 'Cinzel', serif; font-size: 28px; font-weight: 800;
  line-height: 1.2;
}
.cs-cur-lbl {
  display: block; font-size: 11px; font-weight: 600; margin-top: 2px;
}
.cs-cur-block.gold .cs-cur-val { color: #d4a44c; }
.cs-cur-block.gold .cs-cur-lbl { color: #8b7355; }
.cs-cur-block.mana .cs-cur-val { color: #9b59b6; }
.cs-cur-block.mana .cs-cur-lbl { color: #7d5a8e; }
.cs-cur-sep {
  width: 1px; height: 36px;
  background: linear-gradient(180deg, transparent, rgba(212,164,76,0.3), transparent);
}

/* Badge Modal */
.badge-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}
.badge-modal {
  background: linear-gradient(145deg, #2c1810, #1a1a2e);
  border: 1px solid rgba(212,164,76,0.3); border-radius: 16px;
  padding: 24px; width: 100%; max-width: 400px; max-height: 80vh; overflow-y: auto;
}
.badge-modal-title {
  font-family: 'Cinzel', serif; font-size: 18px; color: #d4a44c; margin: 0 0 16px;
}
.badge-list-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid rgba(212,164,76,0.1);
}
.badge-list-item:last-child { border-bottom: none; }
.badge-list-icon { width: 44px; height: 44px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); }
.badge-list-img { width: 100%; height: 100%; object-fit: cover; }
.badge-list-fallback { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 20px; }
.badge-list-info { flex: 1; }
.badge-list-name { font-family: 'Cinzel', serif; font-size: 14px; font-weight: 700; color: #d4a44c; }
.badge-list-desc { font-size: 12px; color: #8b7355; }
.badge-list-date { font-size: 11px; color: #6b5a3e; margin-top: 2px; }
.badge-modal-close {
  margin-top: 16px; width: 100%; padding: 10px;
  background: rgba(212,164,76,0.1); color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.2); border-radius: 10px;
  cursor: pointer; font-weight: 700; font-size: 14px;
}
.badge-modal-close:hover { background: rgba(212,164,76,0.2); }
.badge-list-stats { display: flex; gap: 4px; margin-top: 3px; }
.mini-stat { font-size: 10px; padding: 1px 5px; border-radius: 5px; font-weight: 700; }
.mini-stat.str { background: rgba(231,76,60,0.15); color: #e74c3c; }
.mini-stat.def { background: rgba(52,152,219,0.15); color: #3498db; }
.mini-stat.luk { background: rgba(46,204,113,0.15); color: #2ecc71; }

/* Award Announcements (Town Crier) */
.award-announce-list { display: flex; flex-direction: column; gap: 8px; }
.award-announce-card {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(44,24,16,0.5);
  border: 1px solid rgba(212,164,76,0.08);
}
.award-announce-badge { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); }
.award-announce-img { width: 100%; height: 100%; object-fit: cover; }
.award-announce-fb { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #b8860b, #d4a44c); font-size: 16px; }
.award-announce-body { flex: 1; }
.award-announce-text { font-size: 13px; color: #e8dcc8; }
.award-announce-text strong { color: #d4a44c; }
.award-announce-meta { font-size: 11px; color: #6b5a3e; margin-top: 2px; }
.mana-icon-circle {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.mana-highlight { color: #9b59b6; }
.draw-icon-circle {
  background: linear-gradient(135deg, #d4a44c, #b8860b);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.draw-highlight { color: #d4a44c; }
.lottery-icon-circle {
  background: linear-gradient(135deg, #9b59b6, #8e44ad);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.lottery-highlight { color: #9b59b6; }
.quest-highlight { color: #2ecc71; }

/* See More Button */
.btn-see-more {
  display: block; width: 100%; margin-top: 8px;
  padding: 8px; text-align: center;
  background: rgba(212,164,76,0.06);
  border: 1px dashed rgba(212,164,76,0.2);
  border-radius: 8px; color: #b8860b;
  font-size: 12px; font-weight: 700; cursor: pointer;
  transition: all .2s;
}
.btn-see-more:hover { background: rgba(212,164,76,0.12); border-color: rgba(212,164,76,0.4); }

/* Modal list variants */
.modal-coin-list { max-height: 60vh; overflow-y: auto; }
.modal-award-list { max-height: 60vh; overflow-y: auto; }


/* Sections */
.section { margin-bottom: 28px; }
.section-title {
  font-family: 'Cinzel', serif;
  font-size: 14px; font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #d4a44c;
  margin-bottom: 14px;
}

/* Quest Cards */
.quest-card {
  padding: 16px;
  border-radius: 12px;
  border-left: 4px solid;
  background: rgba(44,24,16,0.7);
  border-color: rgba(212,164,76,0.3);
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
  margin-bottom: 12px;
}
.quest-card--leave { border-color: #d4a44c; }
.quest-card--redeem { border-color: #9b59b6; }
.quest-card--work { border-color: #27ae60; }
.quest-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.quest-info { display: flex; align-items: center; gap: 10px; }
.quest-emoji { font-size: 24px; }
.quest-name { font-weight: 700; font-size: 14px; color: #e8d5b7; }
.quest-type { font-size: 11px; color: #8b7355; font-weight: 700; text-transform: uppercase; }
.quest-detail { font-size: 13px; color: #b8a080; margin-bottom: 4px; }
.quest-badge {
  padding: 2px 10px; border-radius: 6px;
  font-size: 10px; font-weight: 800; text-transform: uppercase;
  background: rgba(212,164,76,0.15); color: #d4a44c; border: 1px solid rgba(212,164,76,0.3);
}
.quest-actions { display: flex; gap: 10px; margin-top: 12px; }
.btn-approve {
  flex: 1; padding: 10px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700;
  color: #fff; background: linear-gradient(135deg, #1e8449, #27ae60);
  border: 1px solid #2ecc71; cursor: pointer; transition: all 0.15s;
}
.btn-approve:active { transform: scale(0.97); }
.btn-reject {
  flex: 1; padding: 10px 0; border-radius: 8px;
  font-size: 13px; font-weight: 700;
  color: #e74c3c; background: rgba(192,57,43,0.15);
  border: 1px solid rgba(192,57,43,0.3); cursor: pointer; transition: all 0.15s;
}
.btn-reject:active { transform: scale(0.97); }

/* Empty State */
.empty-state {
  padding: 32px 16px; text-align: center;
  border-radius: 12px;
  border: 2px dashed rgba(212,164,76,0.15);
  background: rgba(44,24,16,0.4);
}
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-text { color: #8b7355; font-size: 14px; font-weight: 600; }

/* Gold List */
.coin-list { display: flex; flex-direction: column; gap: 8px; }
.coin-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: 10px;
  background: rgba(44,24,16,0.6);
  border: 1px solid rgba(212,164,76,0.1);
}
.coin-dot { font-size: 18px; flex-shrink: 0; }
.coin-info { flex: 1; min-width: 0; }
.coin-reason { font-weight: 700; font-size: 14px; color: #e8d5b7; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.coin-date { font-size: 11px; color: #8b7355; }
.coin-amount { font-weight: 800; font-size: 14px; flex-shrink: 0; }
.coin-amount--plus { color: #27ae60; }
.coin-amount--minus { color: #e74c3c; }

/* Mana Receipts */
.mana-receipts { display: flex; flex-direction: column; gap: 10px; }
.mana-receipt-card {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 14px 16px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(155,89,182,0.15), rgba(142,68,173,0.1));
  border: 1px solid rgba(155,89,182,0.2);
}
.mana-receipt-icon { font-size: 28px; flex-shrink: 0; }
.mana-receipt-body { flex: 1; min-width: 0; }
.mana-receipt-text { font-weight: 700; font-size: 14px; color: #c39bd3; margin-bottom: 2px; }
.mana-receipt-amount { font-weight: 800; font-size: 15px; color: #27ae60; }
.mana-receipt-date { font-size: 11px; color: #9b59b6; margin-top: 2px; }
.balance-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 16px; border-radius: 8px;
  background: rgba(212,164,76,0.08);
  border: 1px solid rgba(212,164,76,0.15);
  font-size: 13px; font-weight: 700; color: #8b7355;
}
.balance-value { color: #d4a44c; }
/* ═══ Step Quests ═══ */
.steps-section {
  padding: 20px; border-radius: 14px;
  background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
  border: 2px solid rgba(212,164,76,0.25);
}
.steps-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.steps-sync-btn {
  width: 32px; height: 32px; border-radius: 8px; font-size: 14px;
  background: rgba(212,164,76,0.12); color: #d4a44c;
  border: 1px solid rgba(212,164,76,0.25); cursor: pointer; transition: all 0.2s;
}
.steps-sync-btn:hover:not(:disabled) { background: rgba(212,164,76,0.22); }
.steps-sync-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* Quest progress bars */
.quest-bar-link { text-decoration: none; color: inherit; display: block; margin-bottom: 10px; }
.quest-bar-link:last-child { margin-bottom: 0; }
.quest-bar {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 12px;
  background: rgba(26,26,46,0.5);
  border: 1px solid rgba(212,164,76,0.1);
  transition: all 0.25s;
}
.quest-bar:hover { background: rgba(212,164,76,0.06); border-color: rgba(212,164,76,0.2); }
.quest-bar--ready {
  border-color: rgba(212,164,76,0.4);
  background: rgba(212,164,76,0.08);
  animation: quest-glow 2s ease-in-out infinite;
}
.quest-bar--done { opacity: 0.6; }
@keyframes quest-glow {
  0%, 100% { box-shadow: 0 0 6px rgba(212,164,76,0.1); }
  50% { box-shadow: 0 0 16px rgba(212,164,76,0.25); }
}
.quest-bar-icon { font-size: 24px; flex-shrink: 0; }
.quest-bar-main { flex: 1; min-width: 0; }
.quest-bar-label { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.quest-bar-name { font-weight: 700; font-size: 13px; color: #d4a44c; }
.quest-bar-pct { font-size: 11px; font-weight: 700; color: #8b7355; }
.quest-bar-track {
  height: 10px; border-radius: 5px;
  background: rgba(26,26,46,0.8); overflow: hidden;
  border: 1px solid rgba(212,164,76,0.1);
}
.quest-bar-track--monthly { border-color: rgba(46,204,113,0.15); }
.quest-bar-fill {
  height: 100%; border-radius: 5px; transition: width 0.6s ease;
  background: linear-gradient(90deg, #b8860b, #d4a44c, #ffd700);
  box-shadow: 0 0 8px rgba(212,164,76,0.3);
}
.quest-bar-fill--monthly {
  background: linear-gradient(90deg, #27ae60, #2ecc71, #58d68d);
  box-shadow: 0 0 8px rgba(46,204,113,0.3);
}
.quest-bar-fill--done {
  background: linear-gradient(90deg, #555, #777) !important;
  box-shadow: none !important;
}
.quest-bar-sub { font-size: 11px; color: #8b7355; margin-top: 4px; font-weight: 600; }

/* Reward tags at the right end */
.quest-bar-rewards {
  display: flex; flex-direction: column; gap: 3px; flex-shrink: 0;
  align-items: flex-end;
}
.qr-tag {
  display: inline-block; padding: 2px 7px; border-radius: 5px;
  font-size: 10px; font-weight: 800; white-space: nowrap;
}
.qr-str { background: rgba(231,76,60,0.15); color: #e74c3c; }
.qr-def { background: rgba(52,152,219,0.15); color: #3498db; }
.qr-luk { background: rgba(155,89,182,0.15); color: #9b59b6; }
.qr-gold { background: rgba(212,164,76,0.15); color: #d4a44c; }
.qr-mana { background: rgba(46,204,113,0.15); color: #2ecc71; }

/* Tier milestone marker on progress bar */
.tier-marker {
  position: absolute; top: -2px; bottom: -2px; z-index: 2;
  transform: translateX(-50%);
}
.tier-marker-line {
  width: 3px; height: 100%; background: rgba(255,255,255,0.8);
  border-radius: 2px; box-shadow: 0 0 6px rgba(255,255,255,0.5);
}

/* Multi-tier bar layout */
.quest-bar--multitier .quest-bar-main { overflow: visible; }
.multitier-wrap { position: relative; }

/* Anchor rewards below the bar */
.tier-anchors {
  position: relative; height: 40px; margin-top: 4px;
}
.tier-anchor {
  position: absolute; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.tier-anchor-tags {
  display: flex; gap: 3px; flex-wrap: nowrap; white-space: nowrap;
}
.tier-anchor-label {
  font-size: 9px; font-weight: 700; color: #8b7355;
}
.tier-check { font-size: 11px; }

/* Town Crier step reward style */
.step-icon-circle {
  background: linear-gradient(135deg, rgba(184,134,11,0.2), rgba(212,164,76,0.3)) !important;
  border-color: rgba(212,164,76,0.3) !important;
}
.step-highlight { color: #d4a44c; }

/* Connect mini card */
.steps-connect-mini { padding: 0 !important; overflow: hidden; }
.steps-connect-link {
  display: flex; align-items: center; gap: 14px; padding: 18px 20px;
  text-decoration: none; color: inherit; transition: background 0.2s;
}
.steps-connect-link:hover { background: rgba(212,164,76,0.06); }
.steps-connect-icon { font-size: 32px; }
.steps-connect-title { font-weight: 700; font-size: 14px; color: #d4a44c; }
.steps-connect-sub { font-size: 12px; color: #8b7355; }
.steps-connect-arrow { font-size: 18px; color: #8b7355; margin-left: auto; }
</style>
