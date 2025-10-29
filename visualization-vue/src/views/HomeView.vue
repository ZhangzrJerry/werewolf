<template>
    <div class="home-view">
        <div class="main-grid">
            <aside class="learning-column">
                <LearningChainViewer />
            </aside>
            <section class="replay-column">
                <GameViewer />
            </section>
        </div>
    </div>
</template>

<script>
import GameViewer from '../components/GameViewer.vue'
import LearningChainViewer from '../components/LearningChainViewer.vue'

export default {
    name: 'HomeView',
    components: { GameViewer, LearningChainViewer }
}
</script>

<style scoped>
.main-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0px;
}

.replay-column {
    min-height: 50vh;
}

.learning-column {
    min-height: 50vh;
}

/* Responsive: stack on small screens */
@media (max-width: 900px) {
    .main-grid {
        grid-template-columns: 1fr;
    }
}
</style>
