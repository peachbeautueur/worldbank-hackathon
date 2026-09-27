<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios'
import {
  LayerDirective,
  LayersDirective,
  MapsComponent,
  MapsTooltip,
  Selection,
  Zoom,
} from '@syncfusion/ej2-vue-maps'
import { world_map } from './world-map.js'

type MetricKey = 'unbanked_rate' | 'gender_account_gap' | 'income_account_gap'
type ProfileMetricKey =
  | 'z_internet_users'
  | 'z_mobile_subscriptions'
  | 'z_log_gdp_per_capita'
  | 'z_unemployment'
  | 'z_labor_force_participation'
  | 'z_urban_population'
  | 'z_log_atm_density'
  | 'z_log_bank_branch_density'

interface CountryRecord {
  country: string
  iso3: string
  year: number
  region: string | null
  current_income_group: string | null
  cluster_status: string
  cluster_id: number | null
  cluster_label: string | null
  pca_x: number | null
  pca_y: number | null
  observed_feature_count: number
  imputed_feature_count: number
  account_ownership: number | null
  unbanked_rate: number | null
  gender_account_gap: number | null
  income_account_gap: number | null
  internet_users: number | null
  mobile_subscriptions: number | null
  gdp_per_capita: number | null
  atm_density: number | null
  bank_branch_density: number | null
}

interface ClusterProfile {
  cluster_id: number
  country_count: number
  access_profile_score: number
  z_internet_users: number
  z_mobile_subscriptions: number
  z_log_gdp_per_capita: number
  z_unemployment: number
  z_labor_force_participation: number
  z_urban_population: number
  z_log_atm_density: number
  z_log_bank_branch_density: number
}

interface ProfileMetric {
  key: ProfileMetricKey
  label: string
}

interface ScatterCountry extends CountryRecord {
  plotX: number
  plotY: number
}

interface DashboardPayload {
  metadata: {
    year: number
    eligibility: {
      eligible_countries: number
      total_country_rows: number
    }
  }
  profiles: ClusterProfile[]
  countries: CountryRecord[]
}

interface MetricDefinition {
  key: MetricKey
  label: string
  shortLabel: string
  explanation: string
  colors: string[]
}

interface MapCountryRecord extends CountryRecord {
  Country: string
  colorValue: number
  metricLabel: string
  displayValue: string
}

export default defineComponent({
  name: 'FinancialInclusionDashboard',
  components: {
    'ejs-maps': MapsComponent,
    'e-layers': LayersDirective,
    'e-layer': LayerDirective,
  },
  provide: {
    maps: [MapsTooltip, Selection, Zoom],
  },
  data() {
    return {
      dashboard: null as DashboardPayload | null,
      selectedCountry: null as CountryRecord | null,
      selectedNoDataCountry: '',
      activeMetric: 'unbanked_rate' as MetricKey,
      loading: true,
      errorMessage: '',
      shapeData: world_map,
      shapePropertyPath: 'admin',
      shapeDataPath: 'Country',
      metricDefinitions: [
        {
          key: 'unbanked_rate',
          label: 'Population without an account',
          shortLabel: 'Unbanked rate',
          explanation: 'Share of adults without an account at a financial institution or mobile-money provider.',
          colors: ['#fff3d6', '#f7b955', '#c94235'],
        },
        {
          key: 'gender_account_gap',
          label: 'Gender account gap',
          shortLabel: 'Gender gap',
          explanation: 'Percentage-point difference between men and women who own an account.',
          colors: ['#e4f2f3', '#64a9b4', '#154d63'],
        },
        {
          key: 'income_account_gap',
          label: 'Income account gap',
          shortLabel: 'Income gap',
          explanation: 'Percentage-point difference between the richest 60% and poorest 40% who own an account.',
          colors: ['#f1e8f5', '#a878b3', '#55305f'],
        },
      ] as MetricDefinition[],
      profileMetrics: [
        { key: 'z_internet_users', label: 'Internet' },
        { key: 'z_mobile_subscriptions', label: 'Mobile' },
        { key: 'z_log_gdp_per_capita', label: 'GDP / capita' },
        { key: 'z_unemployment', label: 'Unemployment' },
        { key: 'z_labor_force_participation', label: 'Labor force' },
        { key: 'z_urban_population', label: 'Urbanization' },
        { key: 'z_log_atm_density', label: 'ATM density' },
        { key: 'z_log_bank_branch_density', label: 'Bank branches' },
      ] as ProfileMetric[],
      zoomSettings: {
        enable: true,
        enablePanning: true,
        mouseWheelZoom: true,
        doubleClickZoom: true,
        pinchZooming: true,
        minZoom: 1,
        maxZoom: 8,
      },
      selectionSettings: {
        enable: true,
        enableMultiSelect: false,
        fill: '#102f3e',
        opacity: 0.82,
        border: { color: '#ffffff', width: 1.5 },
      },
    }
  },
  computed: {
    activeDefinition(): MetricDefinition {
      return this.metricDefinitions.find((metric) => metric.key === this.activeMetric)!
    },
    mapDataSource(): MapCountryRecord[] {
      if (!this.dashboard) return []

      return this.dashboard.countries.flatMap((country) => {
        const value = this.getMetricValue(country, this.activeMetric)
        if (value === null) return []

        return [{
          ...country,
          Country: country.country,
          colorValue: value,
          metricLabel: this.activeDefinition.shortLabel,
          displayValue: this.formatMetricValue(value, this.activeMetric),
        }]
      })
    },
    numericRange(): { min: number; max: number } {
      const values = this.mapDataSource.map((country) => country.colorValue)
      return {
        min: values.length ? Math.min(...values) : 0,
        max: values.length ? Math.max(...values) : 0,
      }
    },
    shapeSettings(): Record<string, unknown> {
      return {
        colorValuePath: 'colorValue',
        fill: '#dde5e8',
        border: { color: '#ffffff', width: 0.45 },
        colorMapping: [{
          from: this.numericRange.min,
          to: this.numericRange.max,
          color: this.activeDefinition.colors,
        }],
      }
    },
    tooltipSettings(): Record<string, unknown> {
      return {
        visible: true,
        format: '${Country}<br>${metricLabel}: ${displayValue}',
      }
    },
    mapRenderKey(): string {
      return `${this.activeMetric}-${this.mapDataSource.length}`
    },
    selectedMetricValue(): number | null {
      if (!this.selectedCountry) return null
      return this.getMetricValue(this.selectedCountry, this.activeMetric)
    },
    analysisYear(): number | null {
      return this.dashboard?.metadata.year ?? null
    },
    eligibleCountryCount(): number {
      return this.dashboard?.metadata.eligibility.eligible_countries ?? 0
    },
    assignedCountryCount(): number {
      return this.dashboard?.countries.filter((country) => country.cluster_id !== null).length ?? 0
    },
    scatterCountries(): ScatterCountry[] {
      if (!this.dashboard) return []

      const countries = this.dashboard.countries.filter(
        (country): country is CountryRecord & { pca_x: number; pca_y: number } =>
          country.cluster_id !== null &&
          typeof country.pca_x === 'number' &&
          typeof country.pca_y === 'number',
      )
      if (!countries.length) return []

      const xValues = countries.map((country) => country.pca_x)
      const yValues = countries.map((country) => country.pca_y)
      const minX = Math.min(...xValues)
      const maxX = Math.max(...xValues)
      const minY = Math.min(...yValues)
      const maxY = Math.max(...yValues)
      const xSpan = maxX - minX || 1
      const ySpan = maxY - minY || 1

      return countries.map((country) => ({
        ...country,
        plotX: 56 + ((country.pca_x - minX) / xSpan) * 668,
        plotY: 344 - ((country.pca_y - minY) / ySpan) * 298,
      }))
    },
    clusterProfiles(): ClusterProfile[] {
      return [...(this.dashboard?.profiles ?? [])].sort((a, b) => a.cluster_id - b.cluster_id)
    },
  },
  mounted() {
    this.loadDashboard()
  },
  methods: {
    async loadDashboard(): Promise<void> {
      this.loading = true
      this.errorMessage = ''
      try {
        const response = await axios.get<DashboardPayload>('/api/cluster-dashboard')
        this.dashboard = response.data
      } catch (error) {
        this.errorMessage = axios.isAxiosError(error)
          ? String(error.response?.data?.error ?? error.message)
          : 'Unable to load the dashboard data.'
      } finally {
        this.loading = false
      }
    },
    setMetric(metric: MetricKey): void {
      this.activeMetric = metric
    },
    getMetricValue(country: CountryRecord, metric: MetricKey): number | null {
      const value = country[metric]
      return typeof value === 'number' && Number.isFinite(value) ? value : null
    },
    onShapeSelected(args: {
      data?: MapCountryRecord
      shapeData?: { admin?: string; name?: string }
    }): void {
      if (args.data?.iso3) {
        this.selectedCountry = args.data
        this.selectedNoDataCountry = ''
        return
      }

      this.selectedCountry = null
      this.selectedNoDataCountry = args.shapeData?.admin ?? args.shapeData?.name ?? 'Selected area'
    },
    onTooltipRender(args: { data?: Partial<MapCountryRecord>; cancel: boolean }): void {
      const hasMetricData =
        typeof args.data?.colorValue === 'number' &&
        Number.isFinite(args.data.colorValue) &&
        Boolean(args.data.displayValue)

      if (!hasMetricData) args.cancel = true
    },
    formatMetricValue(value: number | null, metric: MetricKey): string {
      if (value === null) return 'No data'
      return `${value.toFixed(1)} pp`
    },
    selectScatterCountry(country: CountryRecord): void {
      this.selectedCountry = country
      this.selectedNoDataCountry = ''
    },
    clusterColor(clusterId: number | null): string {
      if (clusterId === 1) return '#176b87'
      if (clusterId === 2) return '#e58b3a'
      return '#aab6bb'
    },
    profileValue(profile: ClusterProfile, key: ProfileMetricKey): number {
      return profile[key]
    },
    profileCellStyle(value: number): Record<string, string> {
      const strength = Math.min(Math.abs(value) / 1.2, 1)
      const color = value >= 0 ? `rgba(23, 107, 135, ${0.14 + strength * 0.72})` : `rgba(229, 139, 58, ${0.14 + strength * 0.72})`
      return {
        backgroundColor: color,
        color: strength > 0.58 ? '#ffffff' : '#102f3e',
      }
    },
    formatPercent(value: number | null): string {
      return value === null ? '—' : `${value.toFixed(1)}%`
    },
    formatDecimal(value: number | null): string {
      return value === null ? '—' : value.toLocaleString(undefined, { maximumFractionDigits: 1 })
    },
    formatCurrency(value: number | null): string {
      return value === null
        ? '—'
        : value.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
    },
    clusterName(clusterId: number | null): string {
      if (clusterId === 1) return 'Cluster 1 · stronger access environment'
      if (clusterId === 2) return 'Cluster 2 · more constrained environment'
      return 'Not assigned'
    },
  },
})
</script>

<template>
  <section class="dashboard-shell" aria-labelledby="dashboard-title">
    <header class="dashboard-header">
      <div>
        <p class="eyebrow">Global Findex · {{ analysisYear ?? 'latest year' }}</p>
        <h1 id="dashboard-title">Where financial access breaks down</h1>
        <p class="lede">
          Explore the scale of account exclusion and the gender, income and infrastructure patterns behind it.
        </p>
      </div>
      <div class="summary-strip" aria-label="Analysis coverage">
        <div>
          <strong>{{ mapDataSource.length }}</strong>
          <span>countries shown</span>
        </div>
        <div>
          <strong>{{ assignedCountryCount }}</strong>
          <span>countries clustered</span>
        </div>
        <div>
          <strong>{{ eligibleCountryCount }}</strong>
          <span>eligible observations</span>
        </div>
      </div>
    </header>

    <div class="metric-tabs" role="group" aria-label="Map metric">
      <button
        v-for="metric in metricDefinitions"
        :key="metric.key"
        type="button"
        :class="['metric-tab', { active: activeMetric === metric.key }]"
        :aria-pressed="activeMetric === metric.key"
        @click="setMetric(metric.key)"
      >
        {{ metric.shortLabel }}
      </button>
    </div>

    <div v-if="loading" class="status-message" aria-live="polite">Loading country data…</div>
    <div v-else-if="errorMessage" class="status-message error" role="alert">
      {{ errorMessage }}
      <button type="button" @click="loadDashboard">Try again</button>
    </div>

    <template v-else>
      <div class="map-heading">
        <div>
          <h2>{{ activeDefinition.label }}</h2>
          <p>{{ activeDefinition.explanation }}</p>
        </div>
        <div class="legend continuous" aria-label="Map color scale">
          <span>{{ numericRange.min.toFixed(1) }} pp</span>
          <i :style="{ background: `linear-gradient(90deg, ${activeDefinition.colors.join(',')})` }"></i>
          <span>{{ numericRange.max.toFixed(1) }} pp</span>
        </div>
      </div>

      <div class="dashboard-grid">
        <div class="map-panel">
          <ejs-maps
            :key="mapRenderKey"
            :zoomSettings="zoomSettings"
            width="100%"
            height="620px"
            @shapeSelected="onShapeSelected"
            @tooltipRender="onTooltipRender"
          >
            <e-layers>
              <e-layer
                :shapeData="shapeData"
                :shapePropertyPath="shapePropertyPath"
                :shapeDataPath="shapeDataPath"
                :dataSource="mapDataSource"
                :shapeSettings="shapeSettings"
                :selectionSettings="selectionSettings"
                :tooltipSettings="tooltipSettings"
              />
            </e-layers>
          </ejs-maps>
          <p class="map-help">Select a country for details. Scroll or pinch to zoom; drag to pan.</p>
        </div>

        <aside class="country-panel" aria-live="polite">
          <template v-if="selectedCountry">
            <p class="eyebrow">{{ selectedCountry.iso3 }} · {{ selectedCountry.year }}</p>
            <h2>{{ selectedCountry.country }}</h2>
            <p class="country-context">
              {{ selectedCountry.current_income_group ?? 'Income group unavailable' }}<br />
              {{ selectedCountry.region ?? 'Region unavailable' }}
            </p>

            <div class="featured-metric">
              <span>{{ activeDefinition.shortLabel }}</span>
              <strong>{{ formatMetricValue(selectedMetricValue, activeMetric) }}</strong>
            </div>

            <dl class="detail-grid">
              <div><dt>Own an account</dt><dd>{{ formatPercent(selectedCountry.account_ownership) }}</dd></div>
              <div><dt>Without an account</dt><dd>{{ formatPercent(selectedCountry.unbanked_rate) }}</dd></div>
              <div><dt>Gender gap</dt><dd>{{ formatMetricValue(selectedCountry.gender_account_gap, 'gender_account_gap') }}</dd></div>
              <div><dt>Income gap</dt><dd>{{ formatMetricValue(selectedCountry.income_account_gap, 'income_account_gap') }}</dd></div>
              <div><dt>Internet users</dt><dd>{{ formatPercent(selectedCountry.internet_users) }}</dd></div>
              <div><dt>GDP per capita</dt><dd>{{ formatCurrency(selectedCountry.gdp_per_capita) }}</dd></div>
              <div><dt>ATMs per 100k adults</dt><dd>{{ formatDecimal(selectedCountry.atm_density) }}</dd></div>
              <div><dt>Bank branches per 100k</dt><dd>{{ formatDecimal(selectedCountry.bank_branch_density) }}</dd></div>
            </dl>

            <div class="cluster-callout">
              <span>Cluster assignment</span>
              <strong>{{ clusterName(selectedCountry.cluster_id) }}</strong>
              <small>
                Based on {{ selectedCountry.observed_feature_count }} observed features;
                {{ selectedCountry.imputed_feature_count }} imputed.
              </small>
            </div>
          </template>
          <template v-else-if="selectedNoDataCountry">
            <div class="empty-state no-data-state">
              <span aria-hidden="true">—</span>
              <p class="eyebrow">Selected country or area</p>
              <h2>{{ selectedNoDataCountry }}</h2>
              <p>
                There is not enough data for this country or area in the selected {{ activeDefinition.shortLabel.toLowerCase() }} view.
              </p>
            </div>
          </template>
          <template v-else>
            <div class="empty-state">
              <span aria-hidden="true">↖</span>
              <h2>Select a country</h2>
              <p>Click a colored country to compare account access, inequality gaps and financial infrastructure.</p>
            </div>
          </template>
        </aside>
      </div>

      <section class="typology-section" aria-labelledby="typology-title">
        <div class="typology-heading">
          <div>
            <p class="eyebrow">Country typologies</p>
            <h2 id="typology-title">Two environments, not two rankings</h2>
          </div>
          <p>
            The clusters group countries by economic conditions, access to digital services, and financial infrastructure.
            Position shows similarity; color shows the assigned cluster.
          </p>
        </div>

        <div class="typology-grid">
          <figure class="scatter-panel">
            <div class="panel-title-row">
              <div>
                <h3>Country similarity</h3>
                <p>PCA projection of the eight clustering features</p>
              </div>
              <div class="cluster-legend" aria-label="Cluster colors">
                <span><i class="cluster-one"></i>Cluster 1</span>
                <span><i class="cluster-two"></i>Cluster 2</span>
              </div>
            </div>

            <svg
              class="scatterplot"
              viewBox="0 0 780 390"
              role="img"
              aria-label="PCA scatter plot of countries grouped into two financial-access clusters"
            >
              <line class="axis-line" x1="56" y1="344" x2="724" y2="344" />
              <line class="axis-line" x1="56" y1="46" x2="56" y2="344" />
              <line class="reference-line" x1="390" y1="46" x2="390" y2="344" />
              <line class="reference-line" x1="56" y1="195" x2="724" y2="195" />
              <text class="axis-label" x="390" y="378" text-anchor="middle">Principal component 1</text>
              <text class="axis-label" x="18" y="195" text-anchor="middle" transform="rotate(-90 18 195)">Principal component 2</text>
              <g
                v-for="country in scatterCountries"
                :key="country.iso3"
                class="scatter-country"
                role="button"
                tabindex="0"
                :aria-label="`${country.country}, ${clusterName(country.cluster_id)}`"
                @click="selectScatterCountry(country)"
                @keydown.enter="selectScatterCountry(country)"
                @keydown.space.prevent="selectScatterCountry(country)"
              >
                <circle
                  :cx="country.plotX"
                  :cy="country.plotY"
                  :r="selectedCountry?.iso3 === country.iso3 ? 7 : 5"
                  :fill="clusterColor(country.cluster_id)"
                  :class="{ selected: selectedCountry?.iso3 === country.iso3 }"
                />
                <title>{{ country.country }} · {{ clusterName(country.cluster_id) }}</title>
              </g>
            </svg>
            <figcaption>Select a country point to update the detail panel above.</figcaption>
          </figure>

          <section class="profile-panel" aria-labelledby="profile-title">
            <div class="panel-title-row">
              <div>
                <h3 id="profile-title">What separates the clusters</h3>
                <p>Average standardized feature values (z-scores)</p>
              </div>
            </div>

            <div
              class="profile-grid"
              :style="{ gridTemplateColumns: `150px repeat(${profileMetrics.length}, minmax(72px, 1fr))` }"
            >
              <div class="profile-corner">Cluster</div>
              <div v-for="metric in profileMetrics" :key="metric.key" class="profile-header">
                {{ metric.label }}
              </div>

              <template v-for="profile in clusterProfiles" :key="profile.cluster_id">
                <div class="profile-row-label">
                  <i :style="{ background: clusterColor(profile.cluster_id) }"></i>
                  <span>
                    <strong>Cluster {{ profile.cluster_id }}</strong>
                    {{ profile.country_count }} countries
                  </span>
                </div>
                <div
                  v-for="metric in profileMetrics"
                  :key="`${profile.cluster_id}-${metric.key}`"
                  class="profile-cell"
                  :style="profileCellStyle(profileValue(profile, metric.key))"
                  :aria-label="`Cluster ${profile.cluster_id}, ${metric.label}: ${profileValue(profile, metric.key).toFixed(2)}`"
                >
                  {{ profileValue(profile, metric.key) >= 0 ? '+' : '' }}{{ profileValue(profile, metric.key).toFixed(2) }}
                </div>
              </template>
            </div>

            <div class="heat-legend">
              <span>Below average</span>
              <i></i>
              <span>Above average</span>
            </div>
          </section>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.dashboard-shell {
  --ink: #102f3e;
  --muted: #5e6f78;
  --paper: #f7f3ea;
  --surface: #ffffff;
  --line: #d8dfdf;
  --accent: #d96c3f;
  width: 100%;
  min-width: 0;
  overflow: hidden;
  color: var(--ink);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  align-items: flex-end;
  padding: 2.5rem 0 1.5rem;
}

.dashboard-header > div:first-child {
  min-width: 0;
}

.eyebrow {
  margin: 0 0 0.45rem;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  max-width: 760px;
  margin-bottom: 0.65rem;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(2.4rem, 5vw, 5.3rem);
  font-weight: 500;
  letter-spacing: -0.045em;
  line-height: 0.97;
  overflow-wrap: anywhere;
}

.lede {
  max-width: 720px;
  margin-bottom: 0;
  color: var(--muted);
  font-size: 1.05rem;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(90px, 1fr));
  min-width: 360px;
  border-block: 1px solid var(--line);
}

.summary-strip div {
  padding: 0.9rem;
}

.summary-strip div + div {
  border-left: 1px solid var(--line);
}

.summary-strip strong,
.summary-strip span {
  display: block;
}

.summary-strip strong {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.8rem;
}

.summary-strip span {
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.25;
}

.metric-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-bottom: 1.5rem;
  max-width: 100%;
}

.metric-tab,
.status-message button {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  padding: 0.65rem 1rem;
}

.metric-tab:hover,
.metric-tab:focus-visible {
  border-color: var(--ink);
}

.metric-tab.active {
  border-color: var(--ink);
  background: var(--ink);
  color: #fff;
}

.map-heading {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-end;
  padding: 1rem 0;
  border-top: 1px solid var(--line);
}

.map-heading h2,
.country-panel h2 {
  margin-bottom: 0.25rem;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.7rem;
  font-weight: 500;
}

.map-heading p {
  max-width: 760px;
  margin-bottom: 0;
  color: var(--muted);
}

.legend {
  display: flex;
  align-items: center;
  color: var(--muted);
  font-size: 0.75rem;
  white-space: nowrap;
}

.legend.continuous i {
  width: 150px;
  height: 10px;
  margin: 0 0.55rem;
  border-radius: 999px;
}

.legend.categorical {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem 1rem;
}

.legend.categorical span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.legend.categorical i {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend .no-data {
  background: #dde5e8;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  overflow: hidden;
  border: 1px solid var(--line);
  background: var(--surface);
}

.map-panel {
  min-width: 0;
  padding: 0.5rem 0.75rem 0;
}

.map-help {
  margin: -0.3rem 0 0.75rem;
  color: var(--muted);
  font-size: 0.78rem;
}

.country-panel {
  min-height: 620px;
  padding: 1.5rem;
  border-left: 1px solid var(--line);
  background: var(--paper);
}

.country-context {
  margin-bottom: 1.4rem;
  color: var(--muted);
  font-size: 0.86rem;
}

.featured-metric {
  padding: 1rem 0;
  border-block: 1px solid rgba(16, 47, 62, 0.16);
}

.featured-metric span,
.featured-metric strong {
  display: block;
}

.featured-metric span,
.cluster-callout span {
  color: var(--muted);
  font-size: 0.74rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.featured-metric strong {
  margin-top: 0.2rem;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.9rem;
  font-weight: 500;
  line-height: 1.1;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  margin: 1rem 0;
}

.detail-grid div {
  padding: 0.65rem 0;
  border-bottom: 1px solid rgba(16, 47, 62, 0.12);
}

.detail-grid div:nth-child(even) {
  padding-left: 0.75rem;
  border-left: 1px solid rgba(16, 47, 62, 0.12);
}

.detail-grid dt {
  color: var(--muted);
  font-size: 0.7rem;
}

.detail-grid dd {
  margin: 0.1rem 0 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.cluster-callout {
  padding-top: 0.85rem;
}

.cluster-callout strong,
.cluster-callout small {
  display: block;
}

.cluster-callout strong {
  margin: 0.2rem 0;
  line-height: 1.3;
}

.cluster-callout small {
  color: var(--muted);
}

.empty-state {
  display: grid;
  min-height: 520px;
  place-content: center;
  text-align: center;
}

.empty-state > span {
  color: var(--accent);
  font-size: 3rem;
}

.empty-state p {
  color: var(--muted);
}

.status-message {
  padding: 4rem 1rem;
  border-block: 1px solid var(--line);
  text-align: center;
}

.status-message.error {
  color: #922f25;
}

.status-message button {
  margin-left: 0.75rem;
}

.typology-section {
  margin-top: 4.5rem;
  padding: 2.5rem 0 3rem;
  border-top: 1px solid var(--line);
}

.typology-heading {
  display: flex;
  justify-content: space-between;
  gap: 3rem;
  align-items: flex-end;
  margin-bottom: 1.5rem;
}

.typology-heading h2 {
  margin: 0;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 2.5rem;
  font-weight: 500;
  letter-spacing: -0.03em;
}

.typology-heading > p {
  max-width: 620px;
  margin-bottom: 0.25rem;
  color: var(--muted);
}

.typology-grid {
  display: grid;
  gap: 1.25rem;
}

.scatter-panel,
.profile-panel {
  margin: 0;
  padding: 1.25rem;
  border: 1px solid var(--line);
  background: var(--surface);
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.panel-title-row h3 {
  margin: 0;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.35rem;
  font-weight: 500;
}

.panel-title-row p,
.scatter-panel figcaption {
  margin: 0.2rem 0 0;
  color: var(--muted);
  font-size: 0.78rem;
}

.cluster-legend {
  display: flex;
  gap: 1rem;
  color: var(--muted);
  font-size: 0.76rem;
}

.cluster-legend span {
  display: inline-flex;
  gap: 0.35rem;
  align-items: center;
}

.cluster-legend i,
.profile-row-label i {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.cluster-one {
  background: #176b87;
}

.cluster-two {
  background: #e58b3a;
}

.scatterplot {
  display: block;
  width: 100%;
  max-height: 500px;
  background: #fbfcfc;
}

.axis-line {
  stroke: #70818a;
  stroke-width: 1;
}

.reference-line {
  stroke: #d8dfdf;
  stroke-width: 1;
  stroke-dasharray: 4 5;
}

.axis-label {
  fill: var(--muted);
  font-size: 12px;
}

.scatter-country {
  cursor: pointer;
  outline: none;
}

.scatter-country circle {
  stroke: #ffffff;
  stroke-width: 1.5;
  opacity: 0.82;
  transition: r 120ms ease, opacity 120ms ease, stroke-width 120ms ease;
}

.scatter-country:hover circle,
.scatter-country:focus circle,
.scatter-country circle.selected {
  stroke: #102f3e;
  stroke-width: 2.5;
  opacity: 1;
}

.profile-panel {
  overflow-x: auto;
}

.profile-grid {
  display: grid;
  min-width: 850px;
  gap: 3px;
}

.profile-corner,
.profile-header,
.profile-row-label,
.profile-cell {
  min-height: 56px;
  padding: 0.6rem;
}

.profile-corner,
.profile-header {
  display: flex;
  align-items: flex-end;
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 700;
}

.profile-row-label {
  display: flex;
  gap: 0.55rem;
  align-items: center;
  background: var(--paper);
}

.profile-row-label i {
  flex: 0 0 10px;
}

.profile-row-label strong,
.profile-row-label span {
  display: block;
}

.profile-row-label span {
  color: var(--muted);
  font-size: 0.7rem;
}

.profile-row-label strong {
  color: var(--ink);
  font-size: 0.83rem;
}

.profile-cell {
  display: grid;
  place-items: center;
  font-size: 0.82rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.heat-legend {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  align-items: center;
  margin-top: 0.75rem;
  color: var(--muted);
  font-size: 0.7rem;
}

.heat-legend i {
  width: 150px;
  height: 9px;
  border-radius: 999px;
  background: linear-gradient(90deg, #e58b3a, #f2eee7 50%, #176b87);
}

:deep(.e-map) {
  display: block;
  width: 100%;
}

@media (max-width: 980px) {
  .dashboard-header {
    display: block;
  }

  .summary-strip {
    min-width: 0;
    margin-top: 1.5rem;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .country-panel {
    min-height: 0;
    border-top: 1px solid var(--line);
    border-left: 0;
  }

  .empty-state {
    min-height: 180px;
  }
}

@media (max-width: 680px) {
  .dashboard-header {
    padding-top: 1.5rem;
  }

  .summary-strip {
    grid-template-columns: 1fr;
  }

  .summary-strip div + div {
    border-top: 1px solid var(--line);
    border-left: 0;
  }

  .map-heading {
    display: block;
  }

  .legend {
    justify-content: flex-start;
    margin-top: 0.8rem;
  }

  .legend.categorical {
    justify-content: flex-start;
  }
}
</style>
