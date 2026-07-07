<script setup lang="ts"></script>
<template>
  <nav class="bg-white border-b border-gray-100 px-6 py-4">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <RouterLink to="/">
        <div class="flex items-center gap-3">
          <img src="/logo.png" alt="Peanut Trail" class="h-10" />
          <span class="text-lg font-bold text-gray-900">Peanut Trail</span>
        </div></RouterLink
      >

      <div class="flex gap-6 text-sm font-medium text-gray-500">
        <RouterLink to="/" class="hover:text-gray-900 transition-colors">Dashboard</RouterLink>
        <RouterLink to="/transactions" class="hover:text-gray-900 transition-colors"
          >Transactions</RouterLink
        >
        <RouterLink to="/upload" class="hover:text-gray-900 transition-colors">Upload</RouterLink>
      </div>
    </div>
  </nav>
</template>
