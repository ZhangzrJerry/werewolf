<template>
    <div class="learning-chain-container" :class="`role-${role}`">
        <div class="container">
            <el-button class="back-link" @click="$router.push('/')" :icon="ArrowLeft" type="default" size="large">
                返回首页
            </el-button>

            <div class="header">
                <div class="role-icon">{{ roleConfig.icon }}</div>
                <h1>{{ roleConfig.name }}学习链</h1>
                <p>观察AI智能体的学习成长历程</p>
            </div>

            <div class="stats">
                <div class="stat-item">
                    <span class="stat-number">{{ learningStats.total_sessions }}</span>
                    <span class="stat-label">学习会话</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{ learningStats.total_reviews }}</span>
                    <span class="stat-label">复盘记录</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{ learningStats.total_strategies }}</span>
                    <span class="stat-label">策略更新</span>
                </div>
            </div>

            <div v-loading="loading" class="learning-chain">
                <div v-if="error" class="error-message">
                    <el-alert :title="error" type="error" :closable="false" show-icon />
                </div>

                <div v-else-if="learningData.length === 0 && !loading" class="empty-state">
                    <el-empty description="暂无学习数据，请先运行游戏产生学习记录" />
                </div>

                <div v-else>
                    <div v-for="(session, index) in learningData" :key="index" class="chain-item">
                        <div class="timestamp">
                            <div class="date">{{ session.date }}</div>
                            <div class="time">{{ session.time }}</div>
                        </div>
                        <div class="content-area">
                            <div class="reviews-section">
                                <div class="section-title">📝 复盘记录</div>
                                <div v-if="session.reviews && session.reviews.length > 0">
                                    <div v-for="(review, reviewIndex) in session.reviews" :key="reviewIndex"
                                        class="review-item">
                                        <div class="player-name">{{ review.player }}</div>
                                        <div class="review-text">{{ review.content }}</div>
                                    </div>
                                </div>
                                <div v-else class="empty-state">本轮无相关复盘记录</div>
                            </div>
                            <div class="strategies-section">
                                <div class="section-title">🎯 策略更新</div>
                                <div v-if="session.strategies && session.strategies.length > 0">
                                    <div v-for="(strategy, strategyIndex) in session.strategies" :key="strategyIndex"
                                        class="strategy-item">
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
    </div>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import { useLearningStore } from '../stores/learning'

const route = useRoute()
const learningStore = useLearningStore()

const role = computed(() => route.params.role)
const { loading, error } = storeToRefs(learningStore)

// 角色配置
const roleConfigs = {
    'seer': { name: '预言家', icon: '🔮' },
    'werewolf': { name: '狼人', icon: '🐺' },
    'witch': { name: '女巫', icon: '🧙‍♀️' },
    'villager': { name: '村民', icon: '👨‍🌾' },
    'guardian': { name: '守卫', icon: '🛡️' },
    'hunter': { name: '猎人', icon: '🏹' }
}

const roleConfig = computed(() => {
    return roleConfigs[role.value] || { name: '未知角色', icon: '❓' }
})

// 学习数据和统计
const learningData = ref([])
const learningStats = ref({
    total_sessions: 0,
    total_reviews: 0,
    total_strategies: 0
})

// 组件挂载时获取学习数据
onMounted(async () => {
    await fetchLearningData()
})

// 监听路由变化
watch(() => route.params.role, async (newRole) => {
    if (newRole) {
        await fetchLearningData()
    }
})

async function fetchLearningData() {
    try {
        // 这里需要实现获取角色学习数据的逻辑
        // 由于原 Flask 代码中 get_role_learning_data 函数比较复杂
        // 我们可能需要创建一个专门的 API 端点来获取这些数据

        // 临时模拟数据结构
        const mockData = {
            sessions: [
                {
                    date: '2024-01-15',
                    time: '14:30:00',
                    reviews: [
                        {
                            player: 'Player1',
                            content: '在这局游戏中，我作为预言家发挥得不错，成功验出了狼人...'
                        }
                    ],
                    strategies: [
                        '优先验证发言可疑的玩家',
                        '注意保护自己的身份不被暴露'
                    ]
                }
            ],
            total_sessions: 1,
            total_reviews: 1,
            total_strategies: 2
        }

        learningData.value = mockData.sessions
        learningStats.value = {
            total_sessions: mockData.total_sessions,
            total_reviews: mockData.total_reviews,
            total_strategies: mockData.total_strategies
        }
    } catch (err) {
        console.error('获取学习数据失败:', err)
    }
}
</script>

<style scoped>
.learning-chain-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.back-link {
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: none;
}

.back-link:hover {
    background: rgba(255, 255, 255, 0.3);
}

.header {
    text-align: center;
    color: white;
    margin-bottom: 30px;
}

.header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.header p {
    font-size: 1.2em;
    opacity: 0.9;
}

.role-icon {
    font-size: 3em;
    margin: 10px;
}

.stats {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    padding: 15px;
}

.stat-item {
    text-align: center;
    color: white;
}

.stat-number {
    font-size: 2em;
    font-weight: bold;
    display: block;
}

.stat-label {
    font-size: 0.9em;
    opacity: 0.9;
}

.learning-chain {
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.error-message {
    padding: 20px;
}

.empty-state {
    text-align: center;
    color: #999;
    padding: 40px;
    font-style: italic;
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
    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
    color: white;
    padding: 20px;
    width: 180px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-weight: bold;
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

.review-item .player-name {
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 5px;
}

.review-item .review-text {
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

/* 角色特定的渐变背景 */
.role-seer {
    background: linear-gradient(135deg, #74b9ff, #0984e3);
}

.role-werewolf {
    background: linear-gradient(135deg, #fd79a8, #e84393);
}

.role-witch {
    background: linear-gradient(135deg, #a29bfe, #6c5ce7);
}

.role-villager {
    background: linear-gradient(135deg, #55a3ff, #2d3436);
}

.role-guardian {
    background: linear-gradient(135deg, #fdcb6e, #f39c12);
}

.role-hunter {
    background: linear-gradient(135deg, #fd79a8, #d63031);
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

    .stats {
        flex-direction: column;
        gap: 15px;
    }
}
</style>