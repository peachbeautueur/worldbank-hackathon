<script setup lang="ts">
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <main class="app-main">
    <nav class="technology-icons" aria-label="Technologies used">
      <a
        class="technology-icon"
        href="https://www.python.org/"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Python"
        title="Python"
      >
        <svg viewBox="0 0 100 100" role="img" aria-hidden="true">
          <path
            d="M49 8c-18 0-19 8-19 17v12h22v5H22c-10 0-17 8-17 20v10c0 12 8 18 18 18h10V76c0-11 7-18 18-18h20c9 0 14-6 14-15V25C85 13 75 8 62 8H49zm-9 11a4 4 0 1 1 0 8 4 4 0 0 1 0-8z"
            fill="#3776ab"
          />
          <path
            d="M51 92c18 0 19-8 19-17V63H48v-5h30c10 0 17-8 17-20V28c0-12-8-18-18-18H67v14c0 11-7 18-18 18H29c-9 0-14 6-14 15v18c0 12 10 17 23 17h13zm9-11a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"
            fill="#ffd343"
          />
        </svg>
      </a>
      <a
        class="technology-icon"
        href="https://flask.palletsprojects.com/"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Flask"
        title="Flask"
      >
        <svg viewBox="0 0 100 100" role="img" aria-hidden="true">
          <path
            d="M39 12h22v8l-4 5v17l22 34c5 8 0 16-10 16H31c-10 0-15-8-10-16l22-34V25l-4-5v-8zm6 37L27 76h46L55 49V23H45v26z"
            fill="#222"
          />
          <path d="M32 68h36l6 9H26l6-9z" fill="#555" />
        </svg>
      </a>
      <a
        class="technology-icon"
        href="https://vuejs.org/"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Vue.js"
        title="Vue.js"
      >
        <svg viewBox="0 0 100 100" role="img" aria-hidden="true">
          <path d="M8 20h22l20 32 20-32h22L50 88 8 20z" fill="#41b883" />
          <path d="M30 20h18l2 4 2-4h18L50 52 30 20z" fill="#35495e" />
        </svg>
      </a>
      <a
        class="technology-icon"
        href="https://www.syncfusion.com/"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Syncfusion"
        title="Syncfusion"
      >
        <svg viewBox="0 0 100 100" role="img" aria-hidden="true">
          <defs>
            <linearGradient id="syncfusion-gradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#68217a" />
              <stop offset="1" stop-color="#a333c8" />
            </linearGradient>
          </defs>
          <rect x="10" y="10" width="80" height="80" rx="20" fill="url(#syncfusion-gradient)" />
          <path
            d="M67 30H43c-8 0-13 5-13 12s5 12 13 14l14 3c8 2 13 7 13 14S64 86 55 86H31v-9h24c4 0 6-1 6-4s-2-5-6-6l-14-3c-13-3-20-11-20-22s9-21 22-21h24v9z"
            fill="#fff"
            transform="translate(3 -8) scale(.9)"
          />
        </svg>
      </a>
    </nav>
    <HelloWorld />
  </main>
</template>

<style scoped>
.app-main {
  position: relative;
  width: 100%;
}

.technology-icons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px;
}

.technology-icon {
  display: block;
  width: 100px;
  height: 100px;
  flex: 0 0 100px;
  border-radius: 12px;
  transition: background-color 150ms ease, transform 150ms ease;
}

.technology-icon:hover,
.technology-icon:focus-visible {
  background-color: #f1f5f9;
  transform: translateY(-2px);
}

.technology-icon svg {
  display: block;
  width: 100%;
  height: 100%;
  padding: 8px;
}

@media (max-width: 460px) {
  .technology-icons {
    gap: 2px;
    padding-inline: 4px;
  }

  .technology-icon {
    width: 25vw;
    height: 25vw;
    flex-basis: 25vw;
  }
}
</style>
