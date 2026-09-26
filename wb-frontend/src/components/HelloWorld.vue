<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';
export default defineComponent({
  data() {
    return { non_null_data_percentage: 100 };
  },
  methods: {
    getNonNullDataPercentage() {
      axios
        .get('/api/get_non_null_data_percentage')
        .then(response => {
          console.log("received response")
          this.non_null_data_percentage = response.data.non_null_data_percentage;
        })
        .catch(error => {
          console.error('Failed to get non-null data percentage:', error);
        });
    },
  },
})
</script>

<template>
  <div class="greetings">
    <button @click="getNonNullDataPercentage">Get Non-Null data percentage</button>
    <p>Non-Null-Data-Percentage: {{ non_null_data_percentage }}</p>
  </div>
</template>

<style scoped>
h1 {
  font-weight: 500;
  font-size: 2.6rem;
  position: relative;
  top: -10px;
}

h3 {
  font-size: 1.2rem;
}

.greetings h1,
.greetings h3 {
  text-align: center;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: left;
  }
}
</style>
