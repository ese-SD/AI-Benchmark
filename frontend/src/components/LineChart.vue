<template>
  <section class="card chart-card">
    <h2 class="section-title">{{ title }}</h2>
    <div class="chart-wrapper">
      <canvas ref="canvasRef"></canvas>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import Chart from "chart.js/auto";

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  labels: {
    type: Array,
    default: () => []
  },
  values: {
    type: Array,
    default: () => []
  },
  valueLabel: {
    type: String,
    default: "Valeur"
  },
  color: {
    type: String,
    default: "#2563eb"
  }
});

const canvasRef = ref(null);
let chart = null;

function createChart() {
  if (!canvasRef.value) return;

  chart = new Chart(canvasRef.value, {
    type: "line",
    data: {
      labels: [...props.labels],
      datasets: [
        {
          label: props.valueLabel,
          data: [...props.values],
          borderColor: props.color,
          backgroundColor: `${props.color}33`,
          tension: 0.25,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          display: true
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

function updateChart() {
  if (!chart) return;

  chart.data.labels = [...props.labels];
  chart.data.datasets[0].data = [...props.values];
  chart.data.datasets[0].label = props.valueLabel;
  chart.data.datasets[0].borderColor = props.color;
  chart.data.datasets[0].backgroundColor = `${props.color}33`;
  chart.update();
}

onMounted(() => {
  createChart();
});

watch(
  () => [props.labels, props.values, props.valueLabel, props.color],
  () => {
    updateChart();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy();
  }
});
</script>

<style scoped>
.chart-card {
  min-height: 320px;
}

.chart-wrapper {
  position: relative;
  height: 240px;
}
</style>