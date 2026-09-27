<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';
import { MapsComponent, MapsTooltip, LayerDirective, LayersDirective } from '@syncfusion/ej2-vue-maps';
import { world_map } from './world-map.js';
import { setCulture } from '@syncfusion/ej2-base';
setCulture('de');

interface GdpPerCapitaRecord {
  'country.value': string;
  value: number | null;
}

interface GdpPerCapitaGrowthTrendRecord {
  'country.value': string;
  growth_trend_percent_per_year: number | null;
}

interface MapCountryRecord {
  Country: string;
  population: number | null;
}

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
      format: 'n',
        startYear: 2016,
        endYear: 2016,
        countriesFromMapNoPrint: [] as string[],
        countriesInMap: [] as string[],
        useGroupingSeparator: true,
        shapeData: world_map,
        shapePropertyPath: 'admin',
        shapeDataPath: 'Country',
        dataSource: [
            { "Country": "China", population: 38332521 },
            { "Country": "France", population: 19651127 },
            { "Country": "Russia", population: 3090416 },
            { "Country": "Kazakhstan", population: 12325210 },
            { "Country": "Poland", population: 90332521 },
            { "Country": "Afghanistan", population: 383521 }
        ] as MapCountryRecord[],
        tooltipSettings: {
            visible: true,
            valuePath: 'population'
        },
    }
  },
  computed: {
    shapeSettings() {
      const populations = this.dataSource
        .map(country => country.population)
        .filter((population): population is number => population !== null);
      const minPopulation = populations.length ? Math.min(...populations) : 0;
      const maxPopulation = populations.length ? Math.max(...populations) : 0;
      const startColor = '#D84444';
      const endColor = '#316DB5';

      return {
        colorValuePath: 'population',
        colorMapping: [{
          from: minPopulation,
          to: maxPopulation,
          color: [0, 25, 50, 75, 100].map(percent =>
            this.interpolateColor(startColor, endColor, percent)
          ),
        }],
      }
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
    hexFromRGB(r: number, g: number, b: number): string {
      return "#" + [r, g, b].map((x: number) => {
        const hex = x.toString(16).padStart(2, '0');
        return hex;
      }).join('');
    },
    interpolateColor(color1: string, color2: string, percent: number): string {
      // Convert hex to RGB
      const r1 = parseInt(color1.slice(1, 3), 16);
      const g1 = parseInt(color1.slice(3, 5), 16);
      const b1 = parseInt(color1.slice(5, 7), 16);

      const r2 = parseInt(color2.slice(1, 3), 16);
      const g2 = parseInt(color2.slice(3, 5), 16);
      const b2 = parseInt(color2.slice(5, 7), 16);

      // Interpolate
      const r = Math.round(r1 + (r2 - r1) * (percent / 100));
      const g = Math.round(g1 + (g2 - g1) * (percent / 100));
      const b = Math.round(b1 + (b2 - b1) * (percent / 100));

      return this.hexFromRGB(r, g, b);
    },
    getAllCountriesFromMap(): string[] {
      this.countriesInMap = world_map.features.map(
        (feature: { properties: { admin: string } }) => feature.properties.admin
      );
      return this.countriesInMap
    },
    getAllCountriesFromMapNoPrint(): string[] {
      this.countriesFromMapNoPrint = world_map.features.map(
        (feature: { properties: { admin: string } }) => feature.properties.admin
      );
      return this.countriesFromMapNoPrint
    },
    getGdpPerCapita(startYear: number, endYear: number): void {
      axios
        .get<{ gdp_per_capita: GdpPerCapitaRecord[] }>(
          '/api/get_gdp_per_capita',
          { params: { startYear, endYear } },
        )
        .then(response => {
          const mapCountries = this.getAllCountriesFromMapNoPrint();
          const mapCountrySet = new Set(mapCountries);
          const records = response.data.gdp_per_capita;
          const countriesWithData = new Set(
            records
              .filter(
                (record): record is GdpPerCapitaRecord & { value: number } =>
                  record.value !== null && Number.isFinite(record.value),
              )
              .map(record => record['country.value'])
              .filter(country => mapCountrySet.has(country)),
          );
          const countriesMissingData = mapCountries.filter(
            country => !countriesWithData.has(country),
          );

          console.log(
            `Nations missing GDP-per-capita data for ${startYear}-${endYear}:`,
            countriesMissingData,
          );

          this.dataSource = records
            .filter(record => mapCountrySet.has(record['country.value']))
            .map(record => ({
              Country: record['country.value'],
              population: record.value,
            }));
        })
        .catch(error => {
          console.error('Failed to get GDP-per-capita data:', error);
        });
    },
    getGdpPerCapitaGrowthTrend(startYear: number, endYear: number): void {
      axios
        .get<{ gdp_per_capita_growth_trend: GdpPerCapitaGrowthTrendRecord[] }>(
          '/api/get_gdp_per_capita_growth_trend',
          { params: { startYear, endYear } },
        )
        .then(response => {
          const mapCountries = this.getAllCountriesFromMapNoPrint();
          const mapCountrySet = new Set(mapCountries);
          const records = response.data.gdp_per_capita_growth_trend;
          const countriesWithData = new Set(
            records
              .filter(
                (record): record is GdpPerCapitaGrowthTrendRecord & {
                  growth_trend_percent_per_year: number;
                } =>
                  record.growth_trend_percent_per_year !== null &&
                  Number.isFinite(record.growth_trend_percent_per_year),
              )
              .map(record => record['country.value'])
              .filter(country => mapCountrySet.has(country)),
          );
          const countriesMissingData = mapCountries.filter(
            country => !countriesWithData.has(country),
          );

          console.log(
            `Nations missing GDP-per-capita data for ${startYear}-${endYear}:`,
            countriesMissingData,
          );

          this.dataSource = records
            .filter(record => mapCountrySet.has(record['country.value']))
            .map(record => ({
              Country: record['country.value'],
              population: record.growth_trend_percent_per_year,
            }));
        })
        .catch(error => {
          console.error('Failed to get GDP-per-capita data:', error);
        });
    },
  },
})
</script>

<template>
  <div class="greetings">
    <button @click="getAllCountriesFromMap">Get all countries as text</button>
    <p>Countries in map: {{ countriesInMap }}</p>
    <button @click="getNonNullDataPercentage">Get Non-Null data percentage</button>
    <p>Non-Null-Data-Percentage: {{ non_null_data_percentage }}</p>
    <button @click="getGdpPerCapita(startYear, endYear)">Get Mean GDP-per-capita</button>
    <button @click="getGdpPerCapitaGrowthTrend(startYear, endYear)">Get Annualized GDP-per-capita growth</button>
    <input type="number" v-model.number="startYear" placeholder="Enter a start year" />
    <input type="number" v-model.number="endYear" placeholder="Enter an end year" />
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
