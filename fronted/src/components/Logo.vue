<template>
  <!-- 标志：翻开的书（循证文献）+ 从书脊生出的草叶（中药） -->
  <svg :width="size" :height="size" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" class="logo-mark">
    <defs>
      <linearGradient :id="gid" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#2a6094" />
        <stop offset="1" stop-color="#16344f" />
      </linearGradient>
    </defs>
    <rect width="48" height="48" rx="12" :fill="`url(#${gid})`" />
    <path d="M9.5 18c4.6-1.7 9.2-1.5 13.5 1v17.5c-4.3-2.5-8.9-2.7-13.5-1V18Z" fill="#fff" fill-opacity=".94" />
    <path d="M38.5 18c-4.6-1.7-9.2-1.5-13.5 1v17.5c4.3-2.5 8.9-2.7 13.5-1V18Z" fill="#fff" fill-opacity=".7" />
    <path d="M24 20.4c-.2-5.6 3-9.6 9.4-10.2-.5 6.3-4 9.9-9.4 10.2Z" fill="#e0a83f" />
    <path d="M24 20.4c-.6-3.6-2.9-6.2-7-6.8.5 4.4 3 6.8 7 6.8Z" fill="#f0c86a" />
    <path d="M24 20.6v4.2" stroke="#f0c86a" stroke-width="1.8" stroke-linecap="round" />
  </svg>
</template>

<script setup>
defineProps({ size: { type: [Number, String], default: 36 } });
const gid = "ebtcm-g-" + Math.random().toString(36).slice(2, 7);
</script>
