<template>
  <header class="header card">
    <div>
      <h1>AI Benchmark</h1>
      <p class="subtitle">
        Connecté en tant que {{ userLabel }}
      </p>
    </div>

    <div class="actions">
      <span class="role-badge" :class="{ admin: user?.is_admin }">
        {{ user?.is_admin ? "Admin" : "User" }}
      </span>
      <button class="secondary-btn" @click="$emit('logout')">Logout</button>
    </div>
  </header>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  user: {
    type: Object,
    default: null
  }
});

defineEmits(["logout"]);

const userLabel = computed(() => {
  if (!props.user) return "inconnu";

  return (
    props.user.username ||
    [props.user.first_name, props.user.last_name].filter(Boolean).join(" ") ||
    "utilisateur"
  );
});
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0 0 4px 0;
}

.subtitle {
  margin: 0;
  color: #6b7280;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: #e5e7eb;
  font-size: 13px;
}

.role-badge.admin {
  background: #dbeafe;
  color: #1d4ed8;
}
</style>