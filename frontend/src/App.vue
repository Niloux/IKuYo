<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const router = useRouter()
</script>

<template>
  <AppLayout>
    <transition name="fade-page" mode="out-in">
      <RouterView v-slot="{ Component, route }">
        <keep-alive v-if="route.meta.keepAlive">
          <component :is="Component" :key="route.fullPath" />
        </keep-alive>
        <component :is="Component" v-else :key="route.fullPath" />
      </RouterView>
    </transition>
  </AppLayout>
</template>

<style scoped>
</style>
