<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const router = useRouter()
</script>

<template>
  <AppLayout>
    <RouterView v-slot="{ Component, route }">
      <keep-alive v-if="route.meta.keepAlive">
        <component :is="Component" />
      </keep-alive>
      <component :is="Component" v-else />
    </RouterView>
  </AppLayout>
</template>

<style scoped>
</style>
