<template>
    <div class="learning-chain-detail">
        <div class="stats" v-if="!loading && sessions.length > 0">
            <div class="stat-item">
                <span class="stat-number">{{ totalSessions }}</span>
                <span class="stat-label">学习会话</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{{ totalReviews }}</span>
                <span class="stat-label">复盘记录</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{{ totalStrategies }}</span>
                <span class="stat-label">策略更新</span>
            </div>
        </div>

        <div class="learning-chain">
            <div v-if="loading" class="empty-state">加载中...</div>
            <div v-else-if="sessions.length === 0" class="empty-state">
                暂无学习数据，请先运行游戏产生学习记录
            </div>
            <div v-else>
                <div v-for="session in sessions" :key="session.timestamp" class="chain-item">
                    <div class="timestamp">
                        <div class="date">{{ session.date }}</div>
                        <div class="time">{{ session.time }}</div>
                    </div>
                    <div class="content-area">
                        <div class="reviews-section">
                            <div class="section-title">📝 复盘记录</div>
                            <div v-if="session.reviews && session.reviews.length > 0">
                                <div v-for="(review, idx) in session.reviews" :key="idx" class="review-item">
                                    <div class="player-name">{{ review.player }}</div>
                                    <div class="review-text">{{ review.content }}</div>
                                </div>
                            </div>
                            <div v-else class="empty-state">本轮无相关复盘记录</div>
                        </div>
                        <div class="strategies-section">
                            <div class="section-title">🎯 策略更新</div>
                            <div v-if="session.strategies && session.strategies.length > 0">
                                <div v-for="(strategy, idx) in session.strategies" :key="idx" class="strategy-item">
                                    <div class="strategy-text">{{ strategy }}</div>
                                </div>
                            </div>
                            <div v-else class="empty-state">本轮无策略更新</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue'
import { getLearningChainData } from '../services/learningChainService'

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
        const totalReviews = ref(0)
        const totalStrategies = ref(0)

        const totalSessions = computed(() => sessions.value.length)

        const loadSessions = async () => {
            if (!props.selectedRole) return
            loading.value = true
            try {
                const data = await getLearningChainData(props.selectedRole)
                if (data && data.sessions) {
                    sessions.value = data.sessions
                    totalReviews.value = data.total_reviews || 0
                    totalStrategies.value = data.total_strategies || 0
                } else {
                    sessions.value = []
                    totalReviews.value = 0
                    totalStrategies.value = 0
                }
            } catch (error) {
                console.error('Failed to load learning chain:', error)
                sessions.value = []
                totalReviews.value = 0
                totalStrategies.value = 0
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
            totalSessions,
            totalReviews,
            totalStrategies
        }
    }
}
</script>

<style scoped>
.learning-chain-detail {
    color: white;
}

.stats {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    padding: 30px 20px;
    gap: 40px;
}

.stat-item {
    text-align: center;
    color: rgb(112, 107, 204);
    flex: 1;
}

.stat-number {
    font-size: 3.5em;
    font-weight: bold;
    display: block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 10px;
}

.stat-label {
    font-size: 1.1em;
    opacity: 0.95;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.learning-chain {
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    color: #333;
}

.chain-item {
    display: flex;
    border-bottom: 1px solid #eee;
    transition: background-color 0.3s ease;
}

.chain-item:hover {
    background-color: #f8f9fa;
}

.chain-item:last-child {
    border-bottom: none;
}

.timestamp {
    background: linear-gradient(45deg, #667eea, #764ba2);
    color: white;
    padding: 20px;
    width: 180px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-weight: bold;
    flex-shrink: 0;
}

.timestamp .date {
    font-size: 0.9em;
    margin-bottom: 5px;
}

.timestamp .time {
    font-size: 0.8em;
    opacity: 0.9;
}

.content-area {
    flex: 1;
    display: flex;
}

.reviews-section {
    flex: 1;
    padding: 20px;
    border-right: 1px solid #eee;
}

.strategies-section {
    flex: 1;
    padding: 20px;
    background-color: #f8f9fa;
}

.section-title {
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 15px;
    color: #2c3e50;
    display: flex;
    align-items: center;
}

.section-title::before {
    content: '';
    width: 4px;
    height: 20px;
    background: #3498db;
    margin-right: 10px;
    border-radius: 2px;
}

.strategies-section .section-title::before {
    background: #e74c3c;
}

.review-item {
    background: #f1f3f4;
    padding: 12px;
    margin-bottom: 10px;
    border-radius: 8px;
    border-left: 4px solid #3498db;
}

.player-name {
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 5px;
}

.review-text {
    color: #555;
    line-height: 1.4;
    font-size: 0.95em;
}

.strategy-item {
    background: white;
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
    border-left: 4px solid #e74c3c;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.strategy-text {
    color: #2c3e50;
    line-height: 1.4;
    font-size: 0.95em;
}

.empty-state {
    text-align: center;
    color: #999;
    padding: 40px;
    font-style: italic;
}

@media (max-width: 768px) {
    .chain-item {
        flex-direction: column;
    }

    .timestamp {
        width: 100%;
        padding: 15px;
    }

    .content-area {
        flex-direction: column;
    }

    .reviews-section,
    .strategies-section {
        border: none;
    }
}
</style>
