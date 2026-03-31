<template>
  <div class="page-center">
    <section class="card auth-card">
      <h1>Inscription</h1>

      <form class="form-stack" @submit.prevent="handleSubmit">
        <input
          v-model="firstName"
          type="text"
          placeholder="Prénom"
          required
        />

        <input
          v-model="lastName"
          type="text"
          placeholder="Nom"
          required
        />

        <input
          v-model="username"
          type="text"
          placeholder="Username"
          required
        />

        <input
          v-model="password"
          type="password"
          placeholder="Mot de passe"
          required
        />

        <button class="primary-btn" type="submit" :disabled="loading">
          {{ loading ? "Création..." : "Créer le compte" }}
        </button>

        <p v-if="error" class="text-danger">{{ error }}</p>
        <p v-if="success" class="text-success">{{ success }}</p>

        <p>
          Déjà inscrit ?
          <RouterLink to="/login">Se connecter</RouterLink>
        </p>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { registerUser } from "../services/api";

const router = useRouter();

const firstName = ref("");
const lastName = ref("");
const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");
const success = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";
  success.value = "";

  try {
    await registerUser({
      first_name: firstName.value,
      last_name: lastName.value,
      username: username.value,
      password: password.value
    });

    success.value = "Compte créé. Redirection vers la connexion...";

    setTimeout(() => {
      router.push("/login");
    }, 800);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}
</script>