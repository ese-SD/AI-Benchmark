<template>
  <section class="card">
    <h2 class="section-title">Trainings</h2>

    <p v-if="!trainings.length" class="empty-text">
      Aucun run disponible.
    </p>

    <div v-else class="training-list">
      <button
        v-for="training in trainings"
        :key="training.id"
        class="training-item"
        :class="{ active: String(modelValue) === String(training.id) }"
        @click="$emit('update:modelValue', training.id)"
      >
        <div class="training-top">
          <span class="training-name">
            {{ training.framework || training.model_name || "run" }}
          </span>
          <span class="status" :class="statusClass(training.status)">
            {{ training.status || "unknown" }}
          </span>
        </div>

        <div class="training-meta">
          <span>{{ training.dataset_name || training.dataset || "dataset" }}</span>
          <span>#{{ training.id }}</span>
        </div>
      </button>
    </div>
  </section>
</template>

<script setup>
defineProps({
  trainings: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: [String, Number, null],
    default: null
  }
});

defineEmits(["update:modelValue"]);

function statusClass(status) {
  if (!status) return "pending";

  const normalized = status.toLowerCase();

  if (normalized.includes("finish") || normalized.includes("done") || normalized.includes("success")) {
    return "finished";
  }

  if (normalized.includes("run") || normalized.includes("progress")) {
    return "running";
  }

  if (normalized.includes("fail") || normalized.includes("error")) {
    return "failed";
  }

  return "pending";
}
</script>

<style scoped>
.empty-text {
  color: #6b7280;
  margin: 0;
}

.training-list {
  display: grid;
  gap: 12px;
}

.training-item {
  width: 100%;
  text-align: left;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 14px;
  border-radius: 12px;
}

.training-item.active {
  border-color: #2563eb;
  background: #eff6ff;
}

.training-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.training-name {
  font-weight: 700;
  text-transform: capitalize;
}

.training-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6b7280;
}

.status {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.status.pending {
  background: #f3f4f6;
  color: #374151;
}

.status.running {
  background: #fef3c7;
  color: #92400e;
}

.status.finished {
  background: #dcfce7;
  color: #166534;
}

.status.failed {
  background: #fee2e2;
  color: #991b1b;
}
</style>