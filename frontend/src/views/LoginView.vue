<template>
  <div class="page-center">
    <section class="card auth-card">
      <h1>Connexion</h1>

      <form class="form-stack" @submit.prevent="handleSubmit">
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
          {{ loading ? "Connexion..." : "Se connecter" }}
        </button>

        <p v-if="error" class="text-danger">{{ error }}</p>

        <p>
          Pas de compte ?
          <RouterLink to="/register">Créer un compte</RouterLink>
        </p>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { loginUser } from "../services/api";
import { setSession } from "../services/auth";

const router = useRouter();

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function handleSubmit() {
  loading.value = true;
  error.value = "";

  try {
    const data = await loginUser({
      username: username.value,
      password: password.value
    });

    setSession({
      accessToken: data.access_token || data.token,
      user: data.user
    });

    router.push("/dashboard");
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}
</script>