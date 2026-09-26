<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';
import { MapsComponent, MapsTooltip, LayerDirective, LayersDirective } from '@syncfusion/ej2-vue-maps';
import { world_map } from './world-map.js';
import { setCulture } from '@syncfusion/ej2-base';
setCulture('de');

export default defineComponent({
  components: {
    'ejs-maps': MapsComponent,
    'e-layers': LayersDirective,
    'e-layer': LayerDirective,
  },
  provide: {
    maps: [MapsTooltip],
  },
  data() {
    return { non_null_data_percentage: 100,
      format: 'c',
        useGroupingSeparator: true,
        shapeData: world_map,
        shapePropertyPath: 'name',
        shapeDataPath: 'Country',
        dataSource: [
            { "Country": "China", "Membership": "Permanent", population: '38332521' },
            { "Country": "France", "Membership": "Permanent", population: '19651127' },
            { "Country": "Russia", "Membership": "Permanent", population: '3090416' },
            { "Country": "Kazakhstan", "Membership": "Non-Permanent", population: '12325210' },
            { "Country": "Poland", "Membership": "Non-Permanent", population: '90332521' },
            { "Country": "Sweden", "Membership": "Non-Permanent", population: '383521' }
        ],
        shapeSettings: {
            colorValuePath: 'Membership',
            colorMapping: [
                {
                    value: 'Permanent', color: '#D84444'
                },
                {
                    value: 'Non-Permanent', color: '#316DB5'
                }
            ]
        },
        tooltipSettings: {
            visible: true,
            valuePath: 'population'
        },
    }
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
    <div class='wrapper'>
      <ejs-maps
        :format="format"
        :useGroupingSeparator="useGroupingSeparator"
        width="100%"
        height="750px"
      >
          <e-layers>
              <e-layer :shapeData='shapeData' :shapePropertyPath='shapePropertyPath' :shapeDataPath='shapeDataPath' :dataSource='dataSource' :shapeSettings='shapeSettings' :tooltipSettings='tooltipSettings'></e-layer>
          </e-layers>
      </ejs-maps>
    </div>
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

.wrapper {
  width: 100%;
  max-width: none;
}

:deep(.e-map) {
  display: block;
  width: 100%;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: left;
  }
}
</style>
