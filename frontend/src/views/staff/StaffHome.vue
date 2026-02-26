<template>
  <div class="staff-page">
    <!-- ═══════ RPG Character Sheet ═══════ -->
    <div class="char-sheet" :style="charSheetBgStyle">
      <!-- Decorative corners -->
      <div class="corner tl"></div><div class="corner tr"></div>
      <div class="corner bl"></div><div class="corner br"></div>

      <!-- Profile Row: Portrait left, Info right -->
      <div class="cs-profile-row">
        <div class="cs-portrait">
          <div class="cs-portrait-glow"></div>
          <img v-if="artifactImage" :src="artifactImage" class="cs-artifact-ring-img" />
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
          <span class="cs-stat-num str">{{ myStats.total_str - (myStats.buff_str || 0) }}<span v-if="myStats.buff_str" class="buff-plus">+{{ myStats.buff_str }}</span></span>
        </div>
        <div class="cs-stat-row">
          <span class="cs-stat-icon">🛡️</span>
          <span class="cs-stat-label def">DEF</span>
          <div class="cs-stat-track"><div class="cs-stat-fill def" :style="{ width: Math.min(myStats.total_def, 100) + '%' }"></div></div>
          <span class="cs-stat-num def">{{ myStats.total_def - (myStats.buff_def || 0) }}<span v-if="myStats.buff_def" class="buff-plus">+{{ myStats.buff_def }}</span></span>
        </div>
        <div class="cs-stat-row">
          <span class="cs-stat-icon">🍀</span>
          <span class="cs-stat-label luk">LUK</span>
          <div class="cs-stat-track"><div class="cs-stat-fill luk" :style="{ width: Math.min(myStats.total_luk, 100) + '%' }"></div></div>
          <span class="cs-stat-num luk">{{ myStats.total_luk - (myStats.buff_luk || 0) }}<span v-if="myStats.buff_luk" class="buff-plus">+{{ myStats.buff_luk }}</span></span>
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
                  <div class="tier-anchor-label">{{ (stepGoals.daily_goal.target || 0).toLocaleString() }}</div>
                  <div class="tier-anchor-tags">
                    <span v-if="stepGoals.daily_goal.claimed" class="tier-check">✅</span>
                    <span v-else-if="stepGoals.daily_goal.reached" class="tier-check">⭐</span>
                    <span v-if="stepGoals.daily_goal.str > 0" class="qr-tag qr-str">STR+{{ stepGoals.daily_goal.str }}</span>
                    <span v-if="stepGoals.daily_goal.def > 0" class="qr-tag qr-def">DEF+{{ stepGoals.daily_goal.def }}</span>
                    <span v-if="stepGoals.daily_goal.luk > 0" class="qr-tag qr-luk">LUK+{{ stepGoals.daily_goal.luk }}</span>
                    <span v-if="stepGoals.daily_goal.gold > 0" class="qr-tag qr-gold">💰+{{ stepGoals.daily_goal.gold }}</span>
                    <span v-if="stepGoals.daily_goal.mana > 0" class="qr-tag qr-mana">✨+{{ stepGoals.daily_goal.mana }}</span>
                  </div>
                </div>
                <!-- Tier 2 reward (positioned at right end) -->
                <div v-if="hasTier2" class="tier-anchor" style="left: 100%;">
                  <div class="tier-anchor-label">{{ (stepGoals.daily2_goal.target || 0).toLocaleString() }}</div>
                  <div class="tier-anchor-tags">
                    <span v-if="stepGoals.daily2_goal.claimed" class="tier-check">✅</span>
                    <span v-else-if="stepGoals.daily2_goal.reached" class="tier-check">⭐</span>
                    <span v-if="stepGoals.daily2_goal.str > 0" class="qr-tag qr-str">STR+{{ stepGoals.daily2_goal.str }}</span>
                    <span v-if="stepGoals.daily2_goal.def > 0" class="qr-tag qr-def">DEF+{{ stepGoals.daily2_goal.def }}</span>
                    <span v-if="stepGoals.daily2_goal.luk > 0" class="qr-tag qr-luk">LUK+{{ stepGoals.daily2_goal.luk }}</span>
                    <span v-if="stepGoals.daily2_goal.gold > 0" class="qr-tag qr-gold">💰+{{ stepGoals.daily2_goal.gold }}</span>
                    <span v-if="stepGoals.daily2_goal.mana > 0" class="qr-tag qr-mana">✨+{{ stepGoals.daily2_goal.mana }}</span>
                  </div>
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

    <!-- 🎡 Daily Lucky Wheel -->
    <div v-if="luckyWheel" class="section wheel-section">
      <h2 class="section-title">🎡 Daily Lucky Draw</h2>
      <div class="wheel-card" :class="{ 'wheel-card--rewarded': luckyWheel.status === 'rewarded' }" @click="openWheelModal">
        <div class="wheel-card-icon">🎰</div>
        <div class="wheel-card-body">
          <div class="wheel-card-title" v-if="luckyWheel.status === 'rewarded'">🏆 Today's Lucky Draw Result!</div>
          <div class="wheel-card-title" v-else>Today's Spin Wheel is ready!</div>
          <div class="wheel-card-sub" v-if="luckyWheel.status === 'rewarded'">Tap to see who won 🍀</div>
          <div class="wheel-card-sub" v-else>Tap to spin and reveal the winner 🌟</div>
        </div>
        <div class="wheel-card-arrow">→</div>
      </div>
    </div>

    <!-- ⚔️ TEAM CHALLENGE — Epic RPG Battle -->
    <div v-for="pq in partyQuests" :key="pq.id" class="section party-quest-section">
      <!-- Upcoming (preview card) -->
      <template v-if="pq.quest_state === 'upcoming'">
        <div class="pq-card pq-upcoming">
          <div class="pq-battle-bg">
            <div class="pq-particle" v-for="i in 20" :key="'pu'+i" :style="{ left: Math.random()*100+'%', animationDelay: Math.random()*3+'s', animationDuration: (2+Math.random()*2)+'s' }"></div>
          </div>
          <div class="pq-battle-title">⚔️ TEAM CHALLENGE</div>
          <div class="pq-quest-name">{{ pq.title }}</div>
          <div class="pq-upcoming-badge">⏳ เตรียมตัวให้พร้อม!</div>
          <div class="pq-arena">
            <div class="pq-team pq-team-a">
              <div class="pq-team-crest team-a-glow">🔥</div>
              <div class="pq-team-name">{{ pq.team_a_name }}</div>
              <div class="pq-members">
                <div v-for="m in pq.team_a" :key="m.user_id" class="pq-avatar pq-avatar-a" :title="m.name">
                  <img v-if="m.image" :src="m.image" />
                  <span v-else>{{ m.name[0] }}</span>
                </div>
              </div>
            </div>
            <div class="pq-vs-emblem">
              <div class="pq-vs-ring"></div>
              <div class="pq-vs-text">VS</div>
            </div>
            <div class="pq-team pq-team-b">
              <div class="pq-team-crest team-b-glow">❄️</div>
              <div class="pq-team-name">{{ pq.team_b_name }}</div>
              <div class="pq-members">
                <div v-for="m in pq.team_b" :key="m.user_id" class="pq-avatar pq-avatar-b" :title="m.name">
                  <img v-if="m.image" :src="m.image" />
                  <span v-else>{{ m.name[0] }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="pq-quest-info">
            <div v-for="g in pq.goals" :key="g.type" class="pq-quest-objective">
              🎯 {{ g.label }} — Target: {{ g.target.toLocaleString() }}
            </div>
          </div>
          <div class="pq-footer-epic">
            <span class="pq-date-epic">📅 {{ pq.start_date }} → {{ pq.end_date }}</span>
            <span class="pq-reward-epic">🏆 TEAM REWARD : {{ pq.rewards.join(' , ') }}</span>
          </div>
        </div>
      </template>
      <!-- Active -->
      <template v-else-if="pq.quest_state === 'active' && !pq.winner_team">
        <div class="pq-card pq-active">
          <div class="pq-battle-bg">
            <div class="pq-particle" v-for="i in 30" :key="'pa'+i" :style="{ left: Math.random()*100+'%', animationDelay: Math.random()*3+'s', animationDuration: (2+Math.random()*2)+'s' }"></div>
          </div>
          <div class="pq-battle-title">⚔️ BATTLE IN PROGRESS</div>
          <div class="pq-quest-name">{{ pq.title }}</div>
          <div class="pq-arena">
            <div class="pq-team pq-team-a">
              <div class="pq-team-crest team-a-glow">🔥</div>
              <div class="pq-team-name">{{ pq.team_a_name }}</div>
              <div class="pq-members">
                <div v-for="m in pq.team_a" :key="m.user_id" class="pq-avatar pq-avatar-a" :title="m.name">
                  <img v-if="m.image" :src="m.image" />
                  <span v-else>{{ m.name[0] }}</span>
                </div>
              </div>
            </div>
            <div class="pq-vs-emblem pq-vs-active">
              <div class="pq-vs-ring"></div>
              <div class="pq-vs-text">VS</div>
            </div>
            <div class="pq-team pq-team-b">
              <div class="pq-team-crest team-b-glow">❄️</div>
              <div class="pq-team-name">{{ pq.team_b_name }}</div>
              <div class="pq-members">
                <div v-for="m in pq.team_b" :key="m.user_id" class="pq-avatar pq-avatar-b" :title="m.name">
                  <img v-if="m.image" :src="m.image" />
                  <span v-else>{{ m.name[0] }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="pq-goals-battle">
            <div v-for="g in pq.goals" :key="g.type" class="pq-goal-battle">
              <div class="pq-goal-header">{{ g.label }} — Target: {{ g.target.toLocaleString() }}</div>
              <div class="pq-energy-bars">
                <div class="pq-energy-row">
                  <span class="pq-energy-name team-a-color">{{ pq.team_a_name }}</span>
                  <div class="pq-energy-track">
                    <div class="pq-energy-fill team-a-energy" :style="{ width: Math.min(100, g.a / g.target * 100) + '%' }">
                      <span class="pq-energy-glow"></span>
                    </div>
                  </div>
                  <span class="pq-energy-val team-a-color">{{ g.a.toLocaleString() }}</span>
                </div>
                <div class="pq-energy-row">
                  <span class="pq-energy-name team-b-color">{{ pq.team_b_name }}</span>
                  <div class="pq-energy-track">
                    <div class="pq-energy-fill team-b-energy" :style="{ width: Math.min(100, g.b / g.target * 100) + '%' }">
                      <span class="pq-energy-glow"></span>
                    </div>
                  </div>
                  <span class="pq-energy-val team-b-color">{{ g.b.toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="pq-footer-epic">
            <span class="pq-date-epic">📅 {{ pq.start_date }} → {{ pq.end_date }}</span>
            <span class="pq-reward-epic">🏆 TEAM REWARD : {{ pq.rewards.join(' , ') }}</span>
          </div>
        </div>
      </template>
      <!-- Completed (winner) -->
      <template v-else-if="pq.winner_team">
        <div class="pq-card pq-victory">
          <div class="pq-battle-bg pq-victory-bg">
            <div class="pq-particle pq-gold-particle" v-for="i in 30" :key="'pv'+i" :style="{ left: Math.random()*100+'%', animationDelay: Math.random()*3+'s', animationDuration: (2+Math.random()*2)+'s' }"></div>
          </div>
          <div class="pq-battle-title">⚔️ BATTLE COMPLETE</div>
          <div class="pq-quest-name">{{ pq.title }}</div>
          <div class="pq-victory-banner">
            <div class="pq-trophy">🏆</div>
            <div class="pq-winner-name">{{ pq.winner_team === 'A' ? pq.team_a_name : pq.team_b_name }}</div>
            <div class="pq-victory-text">VICTORY!</div>
          </div>
        </div>
      </template>
    </div>

    <!-- ⚔️ Friendly Arena -->
    <div v-if="arenaBattles.length > 0" class="section arena-section">
      <h2 class="section-title">⚔️ Friendly Arena</h2>
      <div class="arena-list">
        <router-link v-for="b in arenaBattles" :key="b.id" :to="'/staff/arena/' + b.id" class="arena-card" :class="{ 'arena-card--resolved': b.status === 'resolved' }">
          <div class="arena-card-fighters">
            <div class="arena-fighter arena-fighter-a">
              <div class="arena-avatar">
                <img v-if="b.player_a.image" :src="b.player_a.image" />
                <span v-else>{{ (b.player_a.name||'?').charAt(0) }}</span>
              </div>
              <span class="arena-fname">{{ b.player_a.name }}</span>
            </div>
            <div class="arena-vs">⚔️</div>
            <div class="arena-fighter arena-fighter-b">
              <div class="arena-avatar">
                <img v-if="b.player_b.image" :src="b.player_b.image" />
                <span v-else>{{ (b.player_b.name||'?').charAt(0) }}</span>
              </div>
              <span class="arena-fname">{{ b.player_b.name }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- 💖 ชุบทีคับ: Revival Pool -->
    <div v-if="negativeUsers.length > 0" class="section rescue-section">
      <h2 class="section-title">🆘 Revival Pool - รวมพลังชุบชีวิต</h2>
      <div v-for="u in negativeUsers" :key="'rescue-'+u.id" class="rescue-card">
        <div class="rescue-portrait">
          <img v-if="u.image" :src="u.image" class="rescue-img" />
          <span v-else class="rescue-fb">{{ u.name.charAt(0) }}</span>
        </div>
        <div class="rescue-body">
          <div class="rescue-text">💀 <strong>{{ u.name }}</strong> ถูกลงทัณฑ์ <span class="rescue-debt">{{ u.coins }} Gold</span></div>
          <div v-if="u.pool" class="rescue-pool-bar">
            <div class="rescue-pool-fill" :style="{width: Math.min(100, (u.pool.prayer_count / u.pool.required) * 100) + '%'}"></div>
            <span class="rescue-pool-label">🙏 {{ u.pool.prayer_count }}/{{ u.pool.required }} คน</span>
          </div>
          <div v-if="u.pool && u.pool.contributors.length" class="rescue-contributors">{{ u.pool.contributors.join(', ') }}</div>
          <div class="rescue-sub">ร่วมสวดภาวนาชุบชีวิต! ใช้ {{ u.pool?.cost || 1 }} Mana ต่อคน</div>
        </div>
        <button class="rescue-btn" @click="openRescueConfirm(u)" :disabled="myAngelCoins < (u.pool?.cost || 1) || u.pool?.already_contributed">
          {{ u.pool?.already_contributed ? '✅ สวดแล้ว' : '🙏 สวดภาวนา' }}
        </button>
      </div>
    </div>

    <!-- Rescue Confirmation Modal -->
    <div v-if="showRescueModal" class="badge-modal-overlay" @click.self="showRescueModal = false">
      <div class="badge-modal rescue-modal">
        <div class="rescue-modal-icon"><img src="/rescue-revive.png" class="rescue-revive-img" /></div>
        <h3 class="badge-modal-title">🙏 สวดภาวนาชุบชีวิต</h3>
        <p class="rescue-modal-text">
          คุณต้องการใช้ <strong>{{ rescueTarget?.pool?.cost || 1 }} Mana</strong> ร่วมชุบชีวิต <strong>{{ rescueTarget?.name }}</strong> ไหม?<br>
          ต้องการอีก <strong class="rescue-gold">{{ (rescueTarget?.pool?.required || 3) - (rescueTarget?.pool?.prayer_count || 0) }} คน</strong> ถึงจะชุบชีวิตสำเร็จ!
        </p>
        <div class="rescue-modal-balance">✨ Mana ของคุณ: {{ myAngelCoins }}</div>
        <div class="rescue-modal-actions">
          <button class="btn-cancel" @click="showRescueModal = false">ยกเลิก</button>
          <button class="rescue-confirm-btn" @click="performRescue" :disabled="rescuing">
            {{ rescuing ? 'กำลังสวดภาวนา...' : '🙏 ยืนยัน สวดภาวนา' }}
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
          <span class="quest-badge">{{ item.evidence_image ? 'รออนุมัติอีกครั้ง' : 'pending' }}</span>
        </div>
        <div class="quest-detail" v-if="item.start_time">
          📅 {{ formatDate(item.start_date) }} {{ item.start_time }}–{{ item.end_time }}
        </div>
        <div class="quest-detail" v-else>📅 {{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</div>
        <div class="quest-detail" v-if="item.reason">💬 {{ item.reason }}</div>
        <div v-if="item.evidence_image" class="quest-evidence">
          <img :src="apiBase + item.evidence_image" class="quest-evidence-img" @click="openEvidenceViewer(item.evidence_image)" />
          <span class="quest-evidence-label">📷 หลักฐานลาป่วย</span>
        </div>
        <div class="quest-actions">
          <button @click="handleApproveLeave(item.id)" class="btn-approve">✅ Accept</button>
          <button @click="confirmRejectLeave(item)" class="btn-reject">❌ Deny</button>
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
              <div class="quest-type">{{ workRequestLabel(item.request_type) }}</div>
            </div>
          </div>
          <span class="quest-badge">pending</span>
        </div>
        <div class="quest-detail" v-if="item.check_in_time">🕐 เวลา: {{ item.check_in_time }}</div>
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
          <div class="mana-receipt-icon">{{ receipt.reason && receipt.reason.includes('Received Gold') ? '💰' : '✨' }}</div>
          <div class="mana-receipt-body">
            <div class="mana-receipt-text">{{ receipt.reason }}</div>
            <div class="mana-receipt-amount">+{{ receipt.amount }} {{ receipt.reason && receipt.reason.includes('Received Gold') ? '💰' : '✨' }}</div>
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
              <span>{{ a.delivery_type === 'gold' ? '💰' : '✨' }}</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} {{ a.delivery_type === 'gold' ? 'Gold' : 'Mana' }}</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
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
                <strong>{{ a.user_name }}</strong> Reach <strong class="step-highlight">{{ a.goal_type }} Step Quest</strong> — {{ a.reward_label }}
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Mana Rescue event -->
          <template v-else-if="a.type === 'rescue'">
            <div class="award-announce-badge rescue-icon-circle">
              <img src="/rescue-revive.png" class="rescue-revive-announce-img" />
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
          <!-- Thank You Card event -->
          <template v-else-if="a.type === 'thank_you'">
            <div class="award-announce-badge thankyou-icon-circle">
              <span>💌</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.sender_name }}</strong> ส่ง Thank You Card ให้ <strong class="thankyou-highlight">{{ a.user_name }}</strong> 💛
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Anonymous Praise event -->
          <template v-else-if="a.type === 'anonymous_praise'">
            <div class="award-announce-badge praise-icon-circle">
              <span>💬</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.user_name }}</strong> ถูกพูดถึงโดยบุคคลนิรนามว่า <em class="praise-msg">"​{{ a.message }}​"</em>
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- PvP Battle event -->
          <template v-else-if="a.type === 'pvp'">
            <div class="award-announce-badge pvp-icon-circle">
              <span>⚔️</span>
            </div>
            <div class="award-announce-body">
              <div class="award-announce-text">
                <strong>{{ a.challenger_name || a.user_name }}</strong> ท้าต่อสู้กับ <strong>{{ a.opponent_name }}</strong> — <strong class="pvp-highlight">{{ a.winner_name || a.user_name }} Wins!</strong> Take {{ a.amount }} Gold 🏆
              </div>
              <div class="award-announce-meta">
                {{ formatBadgeDate(a.timestamp) }}
              </div>
            </div>
          </template>
          <!-- Reaction Bar -->
          <div class="reaction-bar">
            <button v-for="emoji in ['❤️', '👏', '🎉']" :key="emoji"
              class="reaction-btn" :class="{ reacted: reactions[a.id]?.[emoji]?.reacted }"
              @click="doReaction(a.id, emoji)">
              {{ emoji }} <span v-if="reactions[a.id]?.[emoji]?.count">{{ reactions[a.id][emoji].count }}</span>
            </button>
          </div>
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
                <span>{{ a.delivery_type === 'gold' ? '💰' : '✨' }}</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> received <strong class="mana-highlight">{{ a.amount }} {{ a.delivery_type === 'gold' ? 'Gold' : 'Mana' }}</strong> from {{ a.detail }}<span v-if="a.message"> — <em>"{{ a.message }}"</em></span>
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
                  <strong>{{ a.user_name }}</strong> Reach <strong class="step-highlight">{{ a.goal_type }} Step Quest</strong> — {{ a.reward_label }}
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Mana Rescue event (modal) -->
            <template v-else-if="a.type === 'rescue'">
              <div class="award-announce-badge rescue-icon-circle">
                <img src="/rescue-revive.png" class="rescue-revive-announce-img" />
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
            <!-- Thank You Card event (modal) -->
            <template v-else-if="a.type === 'thank_you'">
              <div class="award-announce-badge thankyou-icon-circle">
                <span>💌</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.sender_name }}</strong> ส่ง Thank You Card ให้ <strong class="thankyou-highlight">{{ a.user_name }}</strong> 💛
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- Anonymous Praise event (modal) -->
            <template v-else-if="a.type === 'anonymous_praise'">
              <div class="award-announce-badge praise-icon-circle">
                <span>💬</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.user_name }}</strong> ถูกพูดถึงโดยบุคคลนิรนามว่า <em class="praise-msg">"​{{ a.message }}​"</em>
                </div>
                <div class="award-announce-meta">
                  {{ formatBadgeDate(a.timestamp) }}
                </div>
              </div>
            </template>
            <!-- PvP Battle event (modal) -->
            <template v-else-if="a.type === 'pvp'">
              <div class="award-announce-badge pvp-icon-circle">
                <span>⚔️</span>
              </div>
              <div class="award-announce-body">
                <div class="award-announce-text">
                  <strong>{{ a.challenger_name || a.user_name }}</strong> ท้าต่อสู้กับ <strong>{{ a.opponent_name }}</strong> — <strong class="pvp-highlight">{{ a.winner_name || a.user_name }} Wins!</strong> Take {{ a.amount }} Gold 🏆
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
    <!-- Lucky Wheel Modal -->
    <div v-if="showWheelModal" class="badge-modal-overlay" @click.self="showWheelModal = false">
      <div class="badge-modal wheel-modal">
        <h3 class="badge-modal-title">🎡 Daily Lucky Draw</h3>
        <canvas ref="wheelCanvas" width="320" height="320"></canvas>
        <button v-if="!wheelDone" class="wheel-spin-btn" @click="spinWheel" :disabled="wheelSpinning">
          {{ wheelSpinning ? '🌀 Spinning...' : '🎰 Spin!' }}
        </button>
        <div v-if="wheelDone" class="wheel-result">
          <div class="wheel-result-winner">🏆 {{ luckyWheel.winner_name }}</div>
          <div class="wheel-result-reward" v-if="luckyWheel.status === 'rewarded'">
            Won <strong>{{ luckyWheel.reward_amount }} Gold 💰</strong>!
          </div>
          <div class="wheel-result-reward" v-else>
            Will receive <strong>{{ luckyWheel.reward_amount }} Gold 💰</strong> at 17:00 ⏰
          </div>
        </div>
        <button class="badge-modal-close" @click="showWheelModal = false" style="margin-top: 14px;">Close</button>
      </div>
    </div>

    <!-- Reject Sick Leave Confirmation Modal -->
    <div v-if="showRejectConfirm" class="badge-modal-overlay" @click.self="showRejectConfirm = false">
      <div class="badge-modal rescue-modal">
        <div class="rescue-modal-icon">⚠️</div>
        <h3 class="badge-modal-title">ยืนยันการ Reject</h3>
        <p class="rescue-modal-text">
          หาก <strong>Reject</strong> การลาป่วยของ <strong>{{ rejectTarget?.user_name }}</strong><br>
          จะถือว่าพนักงาน<strong style="color: #e74c3c;">ขาดงาน</strong>ในวันนั้นทันที<br>
          และจะถูก<strong style="color: #e74c3c;">หัก Gold ขาดงาน</strong>
        </p>
        <div class="rescue-modal-actions">
          <button class="btn-cancel" @click="showRejectConfirm = false">ยกเลิก</button>
          <button class="btn-reject" style="flex:1; padding:11px 0; border-radius:8px;" @click="doRejectLeave">❌ ยืนยัน Reject</button>
        </div>
      </div>
    </div>

    <!-- Evidence Viewer -->
    <div v-if="showEvidenceViewer" class="badge-modal-overlay" style="z-index:10001" @click="showEvidenceViewer = false">
      <img :src="apiBase + evidenceViewerSrc" style="max-width:90vw;max-height:90vh;border-radius:8px;" />
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
  getArtifactCatalog, getLuckyWheelToday,
  getActivePartyQuest, toggleReaction, getReactions,
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
      userArtifact: '',
      userBackground: '',
      artifactCatalog: [],
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
      reactions: {},
      partyQuests: [],
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
      arenaBattles: [],
      // Lucky Wheel
      luckyWheel: null,
      showWheelModal: false,
      wheelSpinning: false,
      wheelDone: false,
      // Reject confirmation
      showRejectConfirm: false,
      rejectTarget: null,
      // Evidence viewer
      showEvidenceViewer: false,
      evidenceViewerSrc: '',
      apiBase: import.meta.env.VITE_API_URL || '',
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
      this.userArtifact = u.circle_artifact || ''
      this.userBackground = u.magic_background || ''
    }
    await this.loadData()
    this.loadArtifactCatalog()  // fire-and-forget
    this.loadFitbit()  // fire-and-forget, won't block page
  },
  methods: {
    formatBattleTime(iso) {
      if (!iso) return 'Battle Time TBD'
      const d = new Date(iso)
      return d.toLocaleString('th-TH', { dateStyle: 'short', timeStyle: 'short' })
    },
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
            this.angelCoinReceipts = allLogs.filter(l => l.reason && (l.reason.includes('Received Angel Coins') || l.reason.includes('Received Gold from') || l.reason.includes('Received Mana from'))).slice(0, 5)
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
              stored.circle_artifact = userRes.data.circle_artifact || ''
              stored.magic_background = userRes.data.magic_background || ''
              localStorage.setItem('user', JSON.stringify(stored))
              this.userArtifact = userRes.data.circle_artifact || ''
              this.userBackground = userRes.data.magic_background || ''
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
        // Load reactions for town crier events
        if (this.recentAwards.length > 0) {
          try {
            const eventIds = this.recentAwards.map(a => a.id).join(',')
            const reactRes = await getReactions(eventIds)
            this.reactions = reactRes.data || {}
          } catch (er) { this.reactions = {} }
        }
        // Load active party quest
        try {
          const pqRes = await getActivePartyQuest()
          this.partyQuests = pqRes.data || []
        } catch (ep) { this.partyQuests = [] }
        // Load negative-coin users for rescue
        try {
          const negRes = await api.get('/api/users/negative-coins')
          const users = negRes.data || []
          // Fetch pool status for each dead user
          for (const u of users) {
            try {
              const poolRes = await api.get(`/api/users/rescue/pool/${u.id}`)
              u.pool = poolRes.data
            } catch (ep) { u.pool = null }
          }
          this.negativeUsers = users
        } catch (e2) { this.negativeUsers = [] }
        // Load PVP arena battles
        try {
          const pvpRes = await api.get('/api/pvp/today')
          this.arenaBattles = pvpRes.data || []
        } catch (ep) { this.arenaBattles = [] }
        // Load Lucky Wheel
        try {
          const wheelRes = await getLuckyWheelToday()
          this.luckyWheel = wheelRes.data || null
        } catch (ew) { this.luckyWheel = null }
      } catch (e) {
        this.myBadges = []
        this.recentAwards = []
      }
    },
    async loadArtifactCatalog() {
      try {
        const { data } = await getArtifactCatalog()
        this.artifactCatalog = data
      } catch (e) { /* silent */ }
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
    confirmRejectLeave(item) {
      if (item.leave_type === 'sick') {
        this.rejectTarget = item
        this.showRejectConfirm = true
      } else {
        this.handleRejectLeave(item.id)
      }
    },
    async doRejectLeave() {
      const id = this.rejectTarget?.id
      this.showRejectConfirm = false
      this.rejectTarget = null
      if (id) await this.handleRejectLeave(id)
    },
    async handleRejectLeave(id) {
      try { await rejectLeave(id); this.showToast('Leave denied ❌'); await this.loadData() }
      catch (e) { this.showToast(e.response?.data?.detail || 'Failed', 'error') }
    },
    openEvidenceViewer(src) {
      this.evidenceViewerSrc = src
      this.showEvidenceViewer = true
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
    workRequestLabel(type) {
      if (type === 'remote_request') return 'ขอเช็คอินนอกสถานที่'
      if (type === 'holiday_request') return 'ขอทำงานในวันหยุดราชการ'
      return 'ขอทำงานนอกวันงานปกติ'
    },
    formatBadgeDate(d) {
      if (!d) return ''
      return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    },
    async doReaction(eventId, emoji) {
      // Optimistic update
      if (!this.reactions[eventId]) this.reactions[eventId] = {}
      const cur = this.reactions[eventId][emoji]
      if (cur && cur.reacted) {
        cur.count = Math.max(0, (cur.count || 1) - 1)
        cur.reacted = false
      } else {
        if (!cur) this.reactions[eventId][emoji] = { count: 1, reacted: true }
        else { cur.count = (cur.count || 0) + 1; cur.reacted = true }
      }
      try {
        await toggleReaction({ event_id: eventId, emoji })
      } catch (e) {
        console.error('Reaction error', e)
      }
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
        if (res.data.revived) {
          this.showToast(`🎉 ${this.rescueTarget.name} ได้รับการชุบชีวิตแล้ว! รวมพลัง ${res.data.rescuers?.join(', ')}`)
        } else {
          this.showToast(`🙏 สวดภาวนาสำเร็จ! ${res.data.prayer_count}/${res.data.required} คน`)
        }
        this.showRescueModal = false
        this.rescueTarget = null
        await this.loadData()
      } catch (e) {
        this.showToast(e.response?.data?.detail || 'สวดภาวนาไม่สำเร็จ', 'error')
      } finally {
        this.rescuing = false
      }
    },
    openWheelModal() {
      this.showWheelModal = true
      this.wheelDone = false
      this.wheelSpinning = false
      this.$nextTick(() => this.drawWheel(0))
    },
    drawWheel(rotation) {
      const canvas = this.$refs.wheelCanvas
      if (!canvas || !this.luckyWheel) return
      const ctx = canvas.getContext('2d')
      const w = canvas.width, h = canvas.height
      const cx = w / 2, cy = h / 2, r = Math.min(cx, cy) - 10
      ctx.clearRect(0, 0, w, h)
      ctx.save()
      ctx.translate(cx, cy)
      ctx.rotate(rotation)

      const segments = this.luckyWheel.segments
      const totalLuk = segments.reduce((sum, s) => sum + s.luk, 0)

      // Palette
      const colors = [
        '#d4a44c', '#3a2a5e', '#5b3a8a', '#8b5e3c', '#2a6a4a',
        '#6a3a3a', '#3a5a8a', '#7a6a3a', '#4a3a6a', '#8a4a3a',
        '#2a5a5a', '#6a4a6a', '#5a6a3a', '#4a4a7a', '#7a3a5a',
        '#3a7a5a', '#6a6a2a', '#5a3a7a', '#4a6a5a', '#7a5a4a',
      ]

      let angle = 0
      for (let i = 0; i < segments.length; i++) {
        const seg = segments[i]
        const sliceAngle = (seg.luk / totalLuk) * Math.PI * 2
        // Draw segment
        ctx.beginPath()
        ctx.moveTo(0, 0)
        ctx.arc(0, 0, r, angle, angle + sliceAngle)
        ctx.closePath()
        ctx.fillStyle = colors[i % colors.length]
        ctx.fill()
        ctx.strokeStyle = 'rgba(0,0,0,0.3)'
        ctx.lineWidth = 1
        ctx.stroke()
        // Label
        ctx.save()
        ctx.rotate(angle + sliceAngle / 2)
        ctx.textAlign = 'right'
        ctx.fillStyle = '#fff'
        const fontSize = Math.max(8, Math.min(13, sliceAngle * r * 0.12))
        ctx.font = `bold ${fontSize}px 'Inter', sans-serif`
        const name = seg.name.length > 10 ? seg.name.slice(0, 10) + '…' : seg.name
        ctx.fillText(name, r - 12, 4)
        ctx.restore()
        angle += sliceAngle
      }
      ctx.restore()

      // Pointer triangle at top
      ctx.beginPath()
      ctx.moveTo(cx, 8)
      ctx.lineTo(cx - 14, 0)
      ctx.lineTo(cx + 14, 0)
      ctx.closePath()
      ctx.fillStyle = '#ff4a6a'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
    },
    spinWheel() {
      if (this.wheelSpinning || this.wheelDone || !this.luckyWheel) return
      this.wheelSpinning = true

      const segments = this.luckyWheel.segments
      const totalLuk = segments.reduce((sum, s) => sum + s.luk, 0)
      const winnerIndex = this.luckyWheel.winner_index

      // Calculate angle to land on winner segment center
      let winnerStartAngle = 0
      for (let i = 0; i < winnerIndex; i++) {
        winnerStartAngle += (segments[i].luk / totalLuk) * Math.PI * 2
      }
      const winnerSlice = (segments[winnerIndex].luk / totalLuk) * Math.PI * 2
      const winnerCenter = winnerStartAngle + winnerSlice / 2

      // Top pointer is at -π/2 (12 o'clock). We need to rotate so winnerCenter aligns there.
      // Final rotation = -winnerCenter - π/2 + fullSpins
      const fullSpins = 6 * Math.PI * 2 // 6 full rotations
      const targetAngle = fullSpins - winnerCenter - Math.PI / 2

      const duration = 5000
      const start = performance.now()

      const animate = (now) => {
        const elapsed = now - start
        const progress = Math.min(1, elapsed / duration)
        // Ease out cubic
        const ease = 1 - Math.pow(1 - progress, 3)
        const currentAngle = targetAngle * ease
        this.drawWheel(currentAngle)
        if (progress < 1) {
          requestAnimationFrame(animate)
        } else {
          this.wheelSpinning = false
          this.wheelDone = true
        }
      }
      requestAnimationFrame(animate)
    },
  },
  computed: {
    charSheetBgStyle() {
      if (!this.userBackground) return {}
      const apiBase = import.meta.env.VITE_API_URL || ''
      return {
        backgroundImage: `linear-gradient(rgba(17,10,30,0.65), rgba(17,10,30,0.8)), url(${apiBase + this.userBackground})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
      }
    },
    artifactImage() {
      if (!this.userArtifact || !this.artifactCatalog.length) return null
      const a = this.artifactCatalog.find(x => String(x.id) === String(this.userArtifact))
      return a ? a.image : null
    },
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

/* ═══ Friendly Arena ═══ */
.arena-section { }
.arena-list {
  display: flex; flex-direction: column; gap: 10px;
}
.arena-card {
  box-sizing: border-box;
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  background: linear-gradient(135deg, rgba(26,14,46,0.7), rgba(13,13,32,0.75)), url('/arena_bg.png') center/cover;
  border: 1px solid rgba(212,164,76,0.15);
  border-radius: 12px; padding: 10px 14px;
  text-decoration: none; color: inherit;
  transition: all 0.3s;
}
.arena-card:hover {
  border-color: rgba(212,164,76,0.35);
  box-shadow: 0 0 20px rgba(212,164,76,0.1);
  transform: translateY(-1px);
}
.arena-card--resolved {
  border-color: rgba(255,215,0,0.2);
  background: linear-gradient(135deg, rgba(40,20,10,0.7), rgba(20,10,5,0.75)), url('/arena_bg.png') center/cover;
}
.arena-card-fighters {
  display: flex; align-items: center; gap: 8px; flex: 1; justify-content: center;
}
.arena-fighter { display: flex; align-items: center; gap: 8px; }
.arena-avatar {
  width: 32px; height: 32px; border-radius: 50%; overflow: hidden;
  border: 1.5px solid rgba(212,164,76,0.2);
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #1a1a3e, #2a1a4a);
}
.arena-fighter-a .arena-avatar { border-color: rgba(74,158,255,0.4); }
.arena-fighter-b .arena-avatar { border-color: rgba(255,74,106,0.4); }
.arena-avatar img { width: 100%; height: 100%; object-fit: cover; }
.arena-avatar span { font-size: 14px; font-weight: 700; color: #8b7355; }
.arena-fname { font-size: 11px; font-weight: 600; color: #c8b89a; }
.arena-fighter-a .arena-fname { color: #7ec8ff; }
.arena-fighter-b .arena-fname { color: #ff8fa3; }
.arena-vs { font-size: 14px; opacity: 0.8; }
.arena-card-status { flex-shrink: 0; }
.arena-battle-time {
  font-size: 11px; color: #8b7355;
  padding: 3px 8px; border-radius: 6px;
  background: rgba(212,164,76,0.06);
  border: 1px solid rgba(212,164,76,0.1);
}
.arena-see-result {
  font-size: 11px; font-weight: 700; color: #ffd700;
  padding: 3px 10px; border-radius: 6px;
  background: rgba(255,215,0,0.1);
  border: 1px solid rgba(255,215,0,0.2);
  animation: result-pulse 2s infinite;
}
@keyframes result-pulse {
  0%,100% { opacity: 1; }
  50% { opacity: 0.7; }
}
.arena-card-rewards {
  display: flex; flex-direction: column; align-items: flex-end; gap: 1px;
  font-size: 10px; flex-shrink: 0; min-width: 80px;
}
.arena-reward-win { color: #ffd700; }
.arena-reward-lose { color: #ff6b6b; }
.arena-reward-sep { display: none; }

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
.rescue-pool-bar {
  position: relative; height: 18px; border-radius: 9px; margin-top: 6px;
  background: rgba(255,255,255,0.08); overflow: hidden;
}
.rescue-pool-fill {
  height: 100%; border-radius: 9px; transition: width 0.4s ease;
  background: linear-gradient(90deg, #e74c3c, #f39c12, #2ecc71);
}
.rescue-pool-label {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
.rescue-contributors {
  font-size: 10px; color: #d4a44c; margin-top: 3px; font-style: italic;
}
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
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.rescue-highlight { color: #f1c40f; }
.rescue-by { font-size: 11px; color: #8b7355; margin-top: 2px; font-style: italic; }
.rescue-revive-img { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; }
.rescue-revive-announce-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

/* Thank You Card event in Town Crier */
.thankyou-icon-circle {
  background: linear-gradient(135deg, rgba(212,164,76,0.15), rgba(184,134,11,0.1));
  border: 1px solid rgba(212,164,76,0.25);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.thankyou-highlight { color: #d4a44c; }

/* Anonymous Praise event in Town Crier */
.praise-icon-circle {
  background: linear-gradient(135deg, rgba(52,152,219,0.15), rgba(41,128,185,0.1));
  border: 1px solid rgba(52,152,219,0.25);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.praise-msg { color: #85c1e9; font-style: italic; }

/* PvP Battle event in Town Crier */
.pvp-icon-circle {
  background: linear-gradient(135deg, rgba(231,76,60,0.15), rgba(192,57,43,0.1));
  border: 1px solid rgba(231,76,60,0.25);
  display: flex; align-items: center; justify-content: center; font-size: 16px;
}
.pvp-highlight { color: #e74c3c; }

/* ═══ RPG Character Sheet ═══ */
.char-sheet {
  position: relative;
  text-align: center;
  background: linear-gradient(170deg, rgba(17,10,30,0.85) 0%, rgba(30,14,10,0.85) 40%, rgba(15,15,30,0.85) 100%),
    url('/icons/user_frame.png') center / cover no-repeat;
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
.cs-artifact-ring-img {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 100px; height: 100px; border-radius: 50%;
  object-fit: cover; pointer-events: none; overflow: hidden;
  aspect-ratio: 1 / 1; z-index: 0;
  animation: csArtifactGlow 3s ease-in-out infinite;
}
@keyframes csArtifactGlow {
  0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.06); }
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
.buff-plus { color: #22c55e; font-size: 13px; font-weight: 700; }

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
.award-announce-badge { width: 36px; height: 36px; flex-shrink: 0; border-radius: 50%; overflow: hidden; border: 2px solid rgba(212,164,76,0.3); display: flex; align-items: center; justify-content: center; }
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
.quest-evidence { margin: 8px 0; display: flex; align-items: center; gap: 8px; }
.quest-evidence-img { width: 64px; height: 64px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(212,164,76,0.2); cursor: pointer; }
.quest-evidence-label { font-size: 11px; color: #d4a44c; font-weight: 600; }
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
  background: linear-gradient(145deg, rgba(44,24,16,0.4), rgba(26,26,46,0.45)),
    url('/icons/step_quests.png') center / cover no-repeat;
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
  display: flex; align-items: center; justify-content: center; font-size: 16px;
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
/* ═══ Lucky Wheel Card ═══ */
.wheel-section { }
.wheel-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 20px; border-radius: 14px; cursor: pointer;
  background: linear-gradient(135deg, rgba(212,164,76,0.08), rgba(90,60,200,0.06));
  border: 1px solid rgba(212,164,76,0.15);
  transition: all 0.25s; position: relative; overflow: hidden;
}
.wheel-card::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle at 30% 50%, rgba(212,164,76,0.1), transparent 70%);
  pointer-events: none;
}
.wheel-card:hover { border-color: rgba(212,164,76,0.35); transform: translateY(-1px); }
.wheel-card-icon { font-size: 36px; flex-shrink: 0; animation: wheel-wobble 3s ease-in-out infinite; }
@keyframes wheel-wobble {
  0%,100% { transform: rotate(-8deg); }
  50% { transform: rotate(8deg); }
}
.wheel-card-body { flex: 1; min-width: 0; }
.wheel-card-title { font-weight: 700; font-size: 14px; color: #d4a44c; margin-bottom: 3px; }
.wheel-card-sub { font-size: 12px; color: #8b7355; line-height: 1.4; }
.wheel-card-arrow { font-size: 18px; color: #8b7355; flex-shrink: 0; }
.wheel-card--rewarded { border-color: rgba(255,215,0,0.25); }
.wheel-card--rewarded .wheel-card-title { color: #ffd700; }

/* ═══ Lucky Wheel Modal ═══ */
.wheel-modal {
  max-width: 380px; width: 94vw; padding: 24px 16px;
  text-align: center;
}
.wheel-modal canvas {
  display: block; margin: 0 auto 16px; border-radius: 50%;
  box-shadow: 0 0 30px rgba(212,164,76,0.2);
}
.wheel-spin-btn {
  padding: 12px 36px; border-radius: 10px; border: none; cursor: pointer;
  font-size: 16px; font-weight: 700; color: #1a0a2e;
  background: linear-gradient(135deg, #ffd700, #d4a44c);
  box-shadow: 0 4px 15px rgba(212,164,76,0.3);
  transition: all 0.2s;
}
.wheel-spin-btn:hover { transform: scale(1.05); }
.wheel-spin-btn:disabled { opacity: 0.5; cursor: default; transform: none; }
.wheel-result {
  margin-top: 16px; padding: 14px; border-radius: 12px;
  background: rgba(212,164,76,0.08); border: 1px solid rgba(212,164,76,0.15);
}
.wheel-result-winner {
  font-size: 18px; font-weight: 700; color: #ffd700; margin-bottom: 6px;
}
.wheel-result-reward {
  font-size: 13px; color: #8b7355;
}

/* ── Epic Team Challenge — RPG Battle Theme ── */
.party-quest-section { margin-bottom: 8px; }
.pq-card {
  position: relative; overflow: hidden;
  border-radius: 16px; padding: 24px 20px;
  border: 1px solid rgba(239,68,68,0.25);
  background:
    radial-gradient(ellipse at 20% 0%, rgba(239,68,68,0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 0%, rgba(59,130,246,0.12) 0%, transparent 50%),
    linear-gradient(180deg, rgba(15,10,25,0.95) 0%, rgba(10,5,20,0.98) 100%);
  box-shadow: 0 0 30px rgba(239,68,68,0.08), 0 0 30px rgba(59,130,246,0.08), inset 0 1px 0 rgba(255,255,255,0.05);
}
.pq-upcoming {
  border-color: rgba(245,158,11,0.3);
  background:
    radial-gradient(ellipse at 50% 0%, rgba(245,158,11,0.1) 0%, transparent 60%),
    linear-gradient(180deg, rgba(15,10,25,0.95) 0%, rgba(10,5,20,0.98) 100%);
  box-shadow: 0 0 30px rgba(245,158,11,0.08);
}
.pq-active {
  border-color: rgba(239,68,68,0.35);
  animation: pq-border-pulse 3s ease-in-out infinite;
}
@keyframes pq-border-pulse {
  0%, 100% { border-color: rgba(239,68,68,0.25); box-shadow: 0 0 20px rgba(239,68,68,0.05), 0 0 20px rgba(59,130,246,0.05); }
  50% { border-color: rgba(239,68,68,0.5); box-shadow: 0 0 40px rgba(239,68,68,0.12), 0 0 40px rgba(59,130,246,0.12); }
}

/* Battle BG Particles */
.pq-battle-bg {
  position: absolute; inset: 0; overflow: hidden; z-index: 0; pointer-events: none;
}
.pq-particle {
  position: absolute; bottom: -10px;
  width: 3px; height: 3px; border-radius: 50%;
  background: rgba(239,68,68,0.6);
  box-shadow: 0 0 6px rgba(239,68,68,0.4);
  animation: pq-particle-rise var(--duration, 3s) ease-out infinite;
  animation-delay: var(--delay, 0s);
}
.pq-particle:nth-child(even) {
  background: rgba(59,130,246,0.6);
  box-shadow: 0 0 6px rgba(59,130,246,0.4);
}
.pq-gold-particle {
  background: rgba(255,215,0,0.7) !important;
  box-shadow: 0 0 8px rgba(255,215,0,0.5) !important;
}
@keyframes pq-particle-rise {
  0% { transform: translateY(0) scale(1); opacity: 0.8; }
  100% { transform: translateY(-300px) scale(0); opacity: 0; }
}

/* Title & Quest Name */
.pq-battle-title {
  position: relative; z-index: 1;
  text-align: center; font-family: 'Cinzel', serif;
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.2em;
  color: #ef4444; text-shadow: 0 0 12px rgba(239,68,68,0.4);
  margin-bottom: 4px; text-transform: uppercase;
}
.pq-quest-name {
  position: relative; z-index: 1;
  text-align: center; font-family: 'Cinzel', serif;
  font-size: 1.2rem; font-weight: 800; color: #f5f5f5;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
  margin-bottom: 12px;
}
.pq-upcoming-badge {
  position: relative; z-index: 1;
  text-align: center; font-size: 0.9rem; font-weight: 700; color: #f59e0b;
  padding: 6px 16px; margin: 0 auto 16px;
  background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25);
  border-radius: 20px; width: fit-content;
  animation: pulse-upcoming 2s ease-in-out infinite;
}
@keyframes pulse-upcoming {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.02); }
}

/* Arena Layout */
.pq-arena {
  position: relative; z-index: 1;
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px; gap: 8px;
}
.pq-team { flex: 1; text-align: center; }
.pq-team-crest {
  font-size: 2rem; margin-bottom: 4px;
  filter: drop-shadow(0 0 8px rgba(255,255,255,0.2));
}
.team-a-glow { animation: pq-glow-fire 2s ease-in-out infinite; }
.team-b-glow { animation: pq-glow-ice 2s ease-in-out infinite; }
@keyframes pq-glow-fire {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(239,68,68,0.4)); }
  50% { filter: drop-shadow(0 0 16px rgba(239,68,68,0.8)); transform: scale(1.1); }
}
@keyframes pq-glow-ice {
  0%, 100% { filter: drop-shadow(0 0 8px rgba(59,130,246,0.4)); }
  50% { filter: drop-shadow(0 0 16px rgba(59,130,246,0.8)); transform: scale(1.1); }
}
.pq-team-name {
  font-family: 'Cinzel', serif;
  font-weight: 700; font-size: 0.95rem; margin-bottom: 6px;
  text-shadow: 0 2px 6px rgba(0,0,0,0.5);
}
.pq-team-a .pq-team-name { color: #fb923c; }
.pq-team-b .pq-team-name { color: #60a5fa; }
.pq-members { display: flex; justify-content: center; gap: 4px; flex-wrap: wrap; }
.pq-avatar {
  width: 36px; height: 36px; border-radius: 50%; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; color: #fff;
  transition: transform 0.2s;
}
.pq-avatar:hover { transform: scale(1.15); }
.pq-avatar img { width: 100%; height: 100%; object-fit: cover; }
.pq-avatar-a {
  border: 2px solid rgba(239,68,68,0.5);
  background: rgba(239,68,68,0.15);
  box-shadow: 0 0 8px rgba(239,68,68,0.2);
}
.pq-avatar-b {
  border: 2px solid rgba(59,130,246,0.5);
  background: rgba(59,130,246,0.15);
  box-shadow: 0 0 8px rgba(59,130,246,0.2);
}

/* VS Emblem */
.pq-vs-emblem {
  position: relative; width: 56px; height: 56px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.pq-vs-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 2px solid rgba(239,68,68,0.4);
  box-shadow: 0 0 12px rgba(239,68,68,0.2), inset 0 0 12px rgba(59,130,246,0.2);
}
.pq-vs-active .pq-vs-ring {
  animation: pq-vs-spin 4s linear infinite;
  border: 2px solid transparent;
  border-top-color: #ef4444; border-bottom-color: #3b82f6;
}
@keyframes pq-vs-spin { to { transform: rotate(360deg); } }
.pq-vs-text {
  font-family: 'Cinzel', serif; font-size: 1.1rem; font-weight: 900;
  color: #fff; text-shadow: 0 0 12px rgba(239,68,68,0.5), 0 0 24px rgba(59,130,246,0.3);
  z-index: 1;
}

/* Quest Info (Upcoming) */
.pq-quest-info {
  position: relative; z-index: 1;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 12px;
}
.pq-quest-objective {
  font-size: 0.82rem; color: #ccc; padding: 3px 0;
  letter-spacing: 0.02em;
}

/* Goals (Active) */
.pq-goals-battle { position: relative; z-index: 1; margin-bottom: 12px; }
.pq-goal-battle {
  padding: 10px 14px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 8px;
}
.pq-goal-header {
  font-size: 0.82rem; font-weight: 600; color: #ccc;
  margin-bottom: 8px; letter-spacing: 0.02em;
}
.pq-energy-bars { }
.pq-energy-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.pq-energy-name { font-size: 0.72rem; font-weight: 700; width: 55px; text-align: right; }
.team-a-color { color: #fb923c; }
.team-b-color { color: #60a5fa; }
.pq-energy-track {
  flex: 1; height: 16px; border-radius: 8px;
  background: rgba(255,255,255,0.06); overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
}
.pq-energy-fill {
  height: 100%; border-radius: 8px; position: relative;
  transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}
.team-a-energy {
  background: linear-gradient(90deg, #dc2626, #f97316, #fbbf24);
  box-shadow: 0 0 10px rgba(239,68,68,0.4);
}
.team-b-energy {
  background: linear-gradient(90deg, #2563eb, #3b82f6, #60a5fa);
  box-shadow: 0 0 10px rgba(59,130,246,0.4);
}
.pq-energy-glow {
  position: absolute; right: 0; top: 0; bottom: 0; width: 20px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
  border-radius: 0 8px 8px 0;
  animation: pq-glow-throb 1.5s ease-in-out infinite;
}
@keyframes pq-glow-throb {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
.pq-energy-val { font-size: 0.78rem; font-weight: 700; width: 55px; }

/* Footer */
.pq-footer-epic {
  position: relative; z-index: 1;
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06);
  font-size: 0.78rem;
}
.pq-date-epic { color: #888; }
.pq-reward-epic {
  font-weight: 700; color: #ffd700;
  text-shadow: 0 0 8px rgba(255,215,0,0.3);
  letter-spacing: 0.03em;
}

/* Victory */
.pq-victory {
  border-color: rgba(255,215,0,0.4);
  background:
    radial-gradient(ellipse at 50% 30%, rgba(255,215,0,0.12) 0%, transparent 60%),
    linear-gradient(180deg, rgba(15,10,25,0.95) 0%, rgba(10,5,20,0.98) 100%);
  box-shadow: 0 0 40px rgba(255,215,0,0.1);
}
.pq-victory-banner {
  position: relative; z-index: 1;
  text-align: center; padding: 20px 0;
}
.pq-trophy {
  font-size: 3rem;
  animation: pq-trophy-bounce 2s ease-in-out infinite;
  filter: drop-shadow(0 0 20px rgba(255,215,0,0.5));
}
@keyframes pq-trophy-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15) rotate(-5deg); }
}
.pq-winner-name {
  font-family: 'Cinzel', serif; font-size: 1.6rem; font-weight: 900;
  background: linear-gradient(135deg, #ffd700, #f59e0b, #ffd700);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: none; margin: 8px 0 4px;
  animation: pq-shimmer 3s ease-in-out infinite;
}
@keyframes pq-shimmer {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.3); }
}
.pq-victory-text {
  font-family: 'Cinzel', serif; font-size: 1.1rem; font-weight: 700;
  color: #f59e0b; letter-spacing: 0.3em;
  text-shadow: 0 0 12px rgba(245,158,11,0.4);
}

/* ── Reaction Bar ── */
.reaction-bar {
  display: flex; gap: 6px; margin-top: 6px; padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.reaction-btn {
  display: flex; align-items: center; gap: 3px;
  padding: 2px 8px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.03); cursor: pointer; font-size: 0.8rem;
  color: #888; transition: all 0.15s;
}
.reaction-btn:hover { background: rgba(255,255,255,0.08); }
.reaction-btn.reacted {
  background: rgba(139,92,246,0.15); border-color: rgba(139,92,246,0.3);
  color: #c4b5fd;
}
.reaction-btn span { font-size: 0.75rem; }
</style>
