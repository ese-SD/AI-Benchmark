<template>
  <div class="dashboard-page">
    <div class="dashboard-shell">
      <AppHeader :user="user" @logout="handleLogout" />

      <p v-if="error" class="text-danger global-message">{{ error }}</p>

      <div class="dashboard-grid">
        <aside class="left-column">
          <section v-if="isAdmin" class="card">
            <h2 class="section-title">Admin</h2>
            <p class="hint-text">
              Les benchmarks démarrent automatiquement au lancement des workers.
              Cette interface sert au monitoring en temps réel.
            </p>
          </section>

          <TrainingList
            v-model="selectedTrainingId"
            :trainings="trainings"
          />
        </aside>

        <section class="right-column">
          <section class="card">
            <h2 class="section-title">Run sélectionné</h2>

            <div v-if="selectedTraining" class="run-details">
              <div class="detail-item">
                <span class="detail-label">ID</span>
                <span>{{ selectedTraining.id }}</span>
              </div>

              <div class="detail-item">
                <span class="detail-label">Framework</span>
                <span>{{ selectedTraining.framework || "-" }}</span>
              </div>

              <div class="detail-item">
                <span class="detail-label">Dataset</span>
                <span>{{ selectedTraining.dataset_name || "-" }}</span>
              </div>

              <div class="detail-item">
                <span class="detail-label">Statut</span>
                <span>{{ selectedTraining.status || "-" }}</span>
              </div>

              <div class="detail-item">
                <span class="detail-label">Accuracy finale</span>
                <span>{{ selectedTraining.final_accuracy ?? "-" }}</span>
              </div>
            </div>

            <p v-else>Aucun run sélectionné.</p>
          </section>

          <div class="charts-grid">
            <LineChart
              title="Accuracy"
              value-label="Accuracy"
              :labels="chartLabels"
              :values="accuracyValues"
              color="#2563eb"
            />

            <LineChart
              title="Vitesse"
              value-label="Secondes"
              :labels="chartLabels"
              :values="speedValues"
              color="#059669"
            />

            <LineChart
              v-if="isAdmin"
              title="CPU"
              value-label="CPU %"
              :labels="chartLabels"
              :values="cpuValues"
              color="#ea580c"
            />

            <LineChart
              v-if="isAdmin"
              title="RAM"
              value-label="RAM %"
              :labels="chartLabels"
              :values="ramValues"
              color="#7c3aed"
            />
          </div>

          <div class="info-grid">
            <section class="card">
              <h2 class="section-title">Contacts</h2>
              <p>admin@ai-benchmark.local</p>
              <p>support@ai-benchmark.local</p>
            </section>

            <section class="card">
              <h2 class="section-title">CGU</h2>
              <p>
                Cette interface permet de suivre les benchmarks des modèles et
                de comparer leurs performances sur les datasets disponibles.
              </p>
            </section>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import AppHeader from "../components/AppHeader.vue";
import LineChart from "../components/LineChart.vue";
import TrainingList from "../components/TrainingList.vue";
import { getMe, getTrainingMetrics, getTrainings } from "../services/api";
import { clearSession, getStoredUser, setStoredUser } from "../services/auth";

const router = useRouter();

const user = ref(getStoredUser());
const trainings = ref([]);
const selectedTrainingId = ref(null);
const metrics = ref([]);
const error = ref("");

let poller = null;

const isAdmin = computed(() => !!user.value?.is_admin);

const selectedTraining = computed(() => {
  return trainings.value.find(
    (training) => String(training.id) === String(selectedTrainingId.value)
  ) || null;
});

const chartLabels = computed(() => {
  return metrics.value.map((metric, index) => {
    return metric.epoch ?? index + 1;
  });
});

const accuracyValues = computed(() => {
  return metrics.value.map((metric) => metric.accuracy ?? 0);
});

const speedValues = computed(() => {
  return metrics.value.map((metric) => metric.execution_speed_seconds ?? 0);
});

const cpuValues = computed(() => {
  return metrics.value.map((metric) => metric.cpu_usage_percent ?? 0);
});

const ramValues = computed(() => {
  return metrics.value.map((metric) => metric.ram_usage_percent ?? 0);
});

function normalizeTrainings(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.trainings)) return payload.trainings;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

function normalizeMetrics(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.metrics)) return payload.metrics;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

async function refreshUser() {
  const me = await getMe();
  user.value = me;
  setStoredUser(me);
}

async function refreshTrainings() {
  const data = await getTrainings();
  const list = normalizeTrainings(data);

  trainings.value = list;

  if (!list.length) {
    selectedTrainingId.value = null;
    metrics.value = [];
    stopPolling();
    return;
  }

  const stillExists = list.some(
    (training) => String(training.id) === String(selectedTrainingId.value)
  );

  if (!selectedTrainingId.value || !stillExists) {
    selectedTrainingId.value = list[0].id;
  }
}

async function loadMetrics() {
  if (!selectedTrainingId.value) {
    metrics.value = [];
    return;
  }

  const data = await getTrainingMetrics(selectedTrainingId.value);
  metrics.value = normalizeMetrics(data);
}

function stopPolling() {
  if (poller) {
    clearInterval(poller);
    poller = null;
  }
}

function startPolling() {
  stopPolling();

  if (!selectedTrainingId.value) return;

  poller = setInterval(async () => {
    try {
      await refreshTrainings();
      await loadMetrics();
    } catch (err) {
      error.value = err.message;
    }
  }, 5000);
}

function handleLogout() {
  clearSession();
  router.push("/login");
}

watch(selectedTrainingId, async (newValue) => {
  if (!newValue) {
    metrics.value = [];
    stopPolling();
    return;
  }

  try {
    await loadMetrics();
    startPolling();
  } catch (err) {
    error.value = err.message;
  }
});

onMounted(async () => {
  try {
    await refreshUser();
    await refreshTrainings();

    if (selectedTrainingId.value) {
      await loadMetrics();
      startPolling();
    }
  } catch {
    clearSession();
    router.push("/login");
  }
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
}

.dashboard-shell {
  max-width: 1400px;
  margin: 0 auto;
}

.global-message {
  margin: 0 0 16px 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
}

.left-column,
.right-column {
  display: grid;
  gap: 20px;
  align-content: start;
}

.hint-text {
  margin: 0;
  color: #4b5563;
}

.run-details {
  display: grid;
  grid-template-columns: repeat(2, minmax(180px, 1fr));
  gap: 12px;
}

.detail-item {
  background: #f9fafb;
  border-radius: 12px;
  padding: 14px;
  display: grid;
  gap: 4px;
}

.detail-label {
  color: #6b7280;
  font-size: 13px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 20px;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 800px) {
  .charts-grid,
  .info-grid,
  .run-details {
    grid-template-columns: 1fr;
  }
}
</style>
