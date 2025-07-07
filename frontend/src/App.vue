<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const router = useRouter()
</script>

<template>
  <AppLayout>
  <RouterView v-slot="{ Component, route }">
    <transition name="fade-page" mode="out-in">
      <keep-alive v-if="route.meta.keepAlive">
        <component :is="Component" :key="route.fullPath" />
      </keep-alive>
      <component v-else :is="Component" :key="route.fullPath" />
    </transition>
  </RouterView>
</AppLayout>
</template>

<style scoped>
</style>
