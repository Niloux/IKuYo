<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const router = useRouter()
</script>

<template>
  <AppLayout>
    <RouterView v-slot="{ Component, route }">
      <template v-if="route && Component">
        <keep-alive v-if="route.meta && route.meta.keepAlive">
          <transition name="fade-page" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </keep-alive>
        <transition v-else name="fade-page" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </transition>
      </template>
    </RouterView>
  </AppLayout>
</template>

<style scoped>
</style>
