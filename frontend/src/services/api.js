import { clearSession, getToken } from "./auth";
import * as mockBackend from "./mockBackend";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  const contentType = response.headers.get("content-type") || "";
  let data = null;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text ? { message: text } : {};
  }

  if (response.status === 401) {
    clearSession();
  }

  if (!response.ok) {
    throw new Error(data.detail || data.message || "Erreur API");
  }

  return data;
}

async function withMock(callable) {
  try {
    return await callable();
  } catch (error) {
    if (error.status === 401) {
      clearSession();
    }
    throw error;
  }
}

export function loginUser(payload) {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.loginUser(payload));
  }

  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function registerUser(payload) {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.registerUser(payload));
  }

  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMe() {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.getMe(getToken()));
  }

  return request("/auth/me");
}

export function getTrainings() {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.getTrainings(getToken()));
  }

  return request("/trainings");
}

export function getTrainingMetrics(trainingId) {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.getTrainingMetrics(getToken(), trainingId));
  }

  return request(`/trainings/${trainingId}/metrics`);
}

export function getTrainingDetails(trainingId) {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.getTrainingDetails(getToken(), trainingId));
  }

  return request(`/trainings/${trainingId}`);
}

export function createTraining(payload) {
  if (USE_MOCKS) {
    return withMock(() => mockBackend.createTraining(getToken(), payload));
  }

  return request("/trainings", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}