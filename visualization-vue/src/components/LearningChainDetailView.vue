<template>
    <div class="learning-chain-detail">
        <h2 v-if="selectedRole" class="role-title">{{ getRoleLabel(selectedRole) }} 的学习链</h2>

        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="sessions.length === 0" class="no-data">暂无学习数据</div>
        <div v-else class="sessions-container">
            <div v-for="session in sessions" :key="session.timestamp" class="session-card">
                <div class="session-header">
                    <span class="timestamp">{{ formatTime(session.timestamp) }}</span>
                </div>

                <div v-if="session.reviews && session.reviews.length > 0" class="reviews-section">
                    <h4>📋 玩家评论</h4>
                    <div v-for="(review, idx) in session.reviews" :key="idx" class="review-item">
                        <strong>{{ review.player }}:</strong> {{ review.content }}
                    </div>
                </div>

                <div v-if="session.strategies && session.strategies.length > 0" class="strategies-section">
                    <h4>💡 学习策略</h4>
                    <div v-for="(strategy, idx) in session.strategies" :key="idx" class="strategy-item">
                        {{ strategy }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue'
import { getLearningChainData, getRoleConfig } from '../services/learningChainService'

export default {
    name: 'LearningChainDetailView',
    props: {
        selectedRole: {
            type: String,
            default: null
        }
    },
    setup(props) {
        const sessions = ref([])
        const loading = ref(false)

        const roleLabels = {
            seer: '🔮 预言家',
            werewolf: '🐺 狼人',
            witch: '🧙‍♀️ 女巫',
            villager: '👨‍🌾 村民',
            guardian: '🛡️ 守卫',
            hunter: '🏹 猎人'
        }

        const getRoleLabel = (role) => roleLabels[role] || role

        const formatTime = (timestamp) => {
            if (!timestamp) return '未知时间'
            const date = new Date(timestamp)
            return date.toLocaleString('zh-CN')
        }

        const loadSessions = async () => {
            if (!props.selectedRole) return
            loading.value = true
            try {
                const data = await getLearningChainData(props.selectedRole)
                if (data && data.sessions) {
                    sessions.value = data.sessions
                } else {
                    sessions.value = []
                }
            } catch (error) {
                console.error('Failed to load learning chain:', error)
                sessions.value = []
            } finally {
                loading.value = false
            }
        }

        onMounted(() => {
            loadSessions()
        })

        watch(() => props.selectedRole, () => {
            loadSessions()
        })

        return {
            sessions,
            loading,
            getRoleLabel,
            formatTime
        }
    }
}
</script>

<style scoped>
.learning-chain-detail {
    padding: 20px;
}

.role-title {
    color: white;
    font-size: 24px;
    margin-bottom: 20px;
    text-align: center;
}

.loading,
.no-data {
    color: white;
    text-align: center;
    padding: 40px;
    font-size: 16px;
}

.sessions-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.session-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 16px;
    color: white;
}

.session-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 12px;
    margin-bottom: 12px;
}

.timestamp {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
}

.reviews-section,
.strategies-section {
    margin-bottom: 16px;
}

.reviews-section:last-child,
.strategies-section:last-child {
    margin-bottom: 0;
}

.reviews-section h4,
.strategies-section h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
}

.review-item,
.strategy-item {
    padding: 8px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    border-left: 3px solid rgba(59, 130, 246, 0.5);
    padding-left: 12px;
    margin-bottom: 4px;
}

.strategy-item {
    border-left-color: rgba(239, 68, 68, 0.5);
}
</style>
