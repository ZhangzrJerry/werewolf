<template>
    <div class="learning-chain-page">
        <router-link to="/" class="back-link">← 返回首页</router-link>

        <div class="header">
            <div class="role-icon">{{ roleIcon }}</div>
            <h1>{{ roleName }}学习链</h1>
            <p>观察AI智能体的学习成长历程</p>
        </div>

        <LearningChainDetailView :selectedRole="role" />
    </div>
</template>

<script>
import LearningChainDetailView from '../components/LearningChainDetailView.vue'

const roleConfigs = {
    seer: { name: '预言家', icon: '🔮' },
    werewolf: { name: '狼人', icon: '🐺' },
    witch: { name: '女巫', icon: '🧙‍♀️' },
    villager: { name: '村民', icon: '👨‍🌾' },
    guardian: { name: '守卫', icon: '🛡️' },
    hunter: { name: '猎人', icon: '🏹' }
}

export default {
    name: 'LearningChainPage',
    components: { LearningChainDetailView },
    props: {
        role: {
            type: String,
            required: true
        }
    },
    computed: {
        roleName() {
            return roleConfigs[this.role]?.name || this.role
        },
        roleIcon() {
            return roleConfigs[this.role]?.icon || '❓'
        }
    }
}
</script>

<style scoped>
.learning-chain-page {
    padding: 20px;
}

.back-link {
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: 10px 20px;
    border-radius: 25px;
    text-decoration: none;
    margin-bottom: 20px;
    transition: background-color 0.3s ease;
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
    display: block;
    margin: 10px;
}
</style>
