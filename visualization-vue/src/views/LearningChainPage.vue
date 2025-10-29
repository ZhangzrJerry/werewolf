<template>
    <div class="learning-chain-page">
        <router-link to="/" class="back-link">← 返回游戏回放</router-link>
        <LearningChainDetailView :selectedRole="role" />
    </div>
</template>

<script>
import LearningChainDetailView from '../components/LearningChainDetailView.vue'

export default {
    name: 'LearningChainPage',
    components: { LearningChainDetailView },
    props: {
        role: {
            type: String,
            required: true
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
    margin-bottom: 20px;
    color: white;
    text-decoration: none;
    padding: 8px 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    transition: all 0.3s;
}

.back-link:hover {
    background-color: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.4);
}
</style>
