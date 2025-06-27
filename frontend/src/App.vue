<script setup lang="ts">
import { RouterView } from 'vue-router'
import { ref } from 'vue'
import AppLayout from './components/AppLayout.vue'

const cachedViews = ref(['HomeView', 'ResourceLibraryView'])
</script>

<template>
  <AppLayout>
    <RouterView v-slot="{ Component }">
      <keep-alive :include="cachedViews">
        <component :is="Component" />
      </keep-alive>
    </RouterView>
  </AppLayout>
</template>

<style scoped>
/* App.vue现在只需要简单的容器样式 */
</style>
