<template>
    <div class="dashboard">
        <div class="page-header">
            <h2>🏰 Guild Hall</h2>
            <p>Overview of kingdom activity</p>
        </div>

        <div class="stats-grid">
            <!-- Attendance Card -->
            <div class="stat-card attendance-card">
                <div class="stat-icon">⚔️</div>
                <div class="stat-content">
                    <h3>Today's Quests</h3>
                    <div class="stat-value">{{ todayAttendance }}</div>
                    <div class="stat-sub">Adventurers active today</div>
                </div>
            </div>

            <!-- Leaves Card -->
            <div class="stat-card leaves-card">
                <div class="stat-icon">🏨</div>
                <div class="stat-content">
                    <h3>Pending Rest</h3>
                    <div class="stat-value">{{ pendingLeaves }}</div>
                    <div class="stat-sub">Requests waiting</div>
                </div>
                <router-link to="/reports" class="stat-action">View →</router-link>
            </div>

            <!-- Redemptions Card -->
            <div class="stat-card redeem-card">
                <div class="stat-icon">🛒</div>
                <div class="stat-content">
                    <h3>Pending Trades</h3>
                    <div class="stat-value">{{ pendingRedemptions }}</div>
                    <div class="stat-sub">Items claimed</div>
                </div>
                <router-link to="/verify-redemption" class="stat-action">Verify →</router-link>
            </div>
            
             <!-- Users Card -->
            <div class="stat-card users-card">
                <div class="stat-icon">🛡️</div>
                <div class="stat-content">
                    <h3>Guild Members</h3>
                    <div class="stat-value">{{ totalUsers }}</div>
                    <div class="stat-sub">Active adventurers</div>
                </div>
                 <router-link to="/users" class="stat-action">Manage →</router-link>
            </div>
        </div>
    </div>
</template>

<script>
import { getAttendanceReport, getAllLeaves, getAllRedemptions, getUsers } from '../../services/api'

export default {
    data() {
        return {
            todayAttendance: 0,
            pendingLeaves: 0,
            pendingRedemptions: 0,
            totalUsers: 0
        }
    },
    async mounted() {
        this.loadStats()
    },
    methods: {
        async loadStats() {
            try {
                const today = new Date().toISOString().split('T')[0]
                const attRes = await getAttendanceReport({ start_date: today, end_date: today })
                this.todayAttendance = attRes.data.length

                const leaveRes = await getAllLeaves({ status: 'pending' })
                this.pendingLeaves = leaveRes.data.length

                const redeemRes = await getAllRedemptions({ status: 'pending' })
                this.pendingRedemptions = redeemRes.data.length

                const userRes = await getUsers()
                this.totalUsers = userRes.data.length
            } catch (e) {
                console.error("Failed to load dashboard stats", e)
            }
        }
    }
}
</script>

<style scoped>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 24px;
    margin-top: 20px;
}

.stat-card {
    background: linear-gradient(145deg, rgba(44,24,16,0.8), rgba(26,26,46,0.9));
    padding: 28px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 18px;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 2px solid rgba(212,164,76,0.15);
}

.stat-card:hover {
    transform: translateY(-4px);
    border-color: rgba(212,164,76,0.3);
    box-shadow: 0 8px 24px rgba(212,164,76,0.1);
}

.attendance-card { border-color: rgba(41,128,185,0.3); }
.leaves-card { border-color: rgba(212,164,76,0.3); }
.redeem-card { border-color: rgba(39,174,96,0.3); }
.users-card { border-color: rgba(155,89,182,0.3); }

.stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    background: rgba(212,164,76,0.08);
    border: 1px solid rgba(212,164,76,0.15);
}

.stat-content h3 {
    margin: 0;
    font-size: 14px;
    color: #8b7355;
    font-weight: 600;
}

.stat-value {
    font-size: 32px;
    font-weight: 800;
    color: #d4a44c;
    margin: 4px 0;
}

.stat-sub {
    font-size: 12px;
    color: #8b7355;
    font-weight: 600;
}

.stat-action {
    position: absolute;
    top: 20px;
    right: 24px;
    font-size: 12px;
    color: #d4a44c;
    text-decoration: none;
    font-weight: 700;
    transition: color 0.2s;
}
.stat-action:hover { color: #ffd700; }
</style>
