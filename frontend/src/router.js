import { createRouter, createWebHistory } from "vue-router";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";
import DashboardView from "./views/DashboardView.vue";
import { getToken } from "./services/auth";

const routes = [
  {
    path: "/",
    redirect: "/login"
  },
  {
    path: "/login",
    component: LoginView,
    meta: { public: true }
  },
  {
    path: "/register",
    component: RegisterView,
    meta: { public: true }
  },
  {
    path: "/dashboard",
    component: DashboardView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  const token = getToken();

  if (to.meta.requiresAuth && !token) {
    return "/login";
  }

  if (to.meta.public && token) {
    return "/dashboard";
  }

  return true;
});

export default router;