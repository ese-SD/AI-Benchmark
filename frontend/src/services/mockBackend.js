const STATE_KEY = "ai_benchmark_mock_state_v1";

function delay(ms = 250) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function makeError(message, status = 400) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function createToken(userId) {
  return `mock-token-${userId}`;
}

function parseToken(token) {
  if (!token || !token.startsWith("mock-token-")) {
    throw makeError("Non authentifié", 401);
  }

  const rawId = token.replace("mock-token-", "");
  const userId = Number(rawId);

  if (!Number.isInteger(userId)) {
    throw makeError("Token invalide", 401);
  }

  return userId;
}

function publicUser(user) {
  return {
    id: user.id,
    first_name: user.first_name,
    last_name: user.last_name,
    username: user.username,
    is_admin: user.is_admin
  };
}

function buildMetricScript(framework, datasetName) {
  const isTorch = framework === "pytorch";

  if (datasetName === "cifar100") {
    return [
      {
        epoch: 1,
        accuracy: isTorch ? 18 : 15,
        execution_speed_seconds: isTorch ? 1.9 : 2.1,
        cpu_usage_percent: 28,
        ram_usage_percent: 34
      },
      {
        epoch: 2,
        accuracy: isTorch ? 27 : 23,
        execution_speed_seconds: isTorch ? 1.8 : 2.0,
        cpu_usage_percent: 31,
        ram_usage_percent: 36
      },
      {
        epoch: 3,
        accuracy: isTorch ? 35 : 31,
        execution_speed_seconds: isTorch ? 1.8 : 1.9,
        cpu_usage_percent: 35,
        ram_usage_percent: 39
      },
      {
        epoch: 4,
        accuracy: isTorch ? 42 : 38,
        execution_speed_seconds: isTorch ? 1.7 : 1.9,
        cpu_usage_percent: 39,
        ram_usage_percent: 42
      },
      {
        epoch: 5,
        accuracy: isTorch ? 48 : 44,
        execution_speed_seconds: isTorch ? 1.7 : 1.8,
        cpu_usage_percent: 43,
        ram_usage_percent: 45
      }
    ];
  }

  return [
    {
      epoch: 1,
      accuracy: isTorch ? 62 : 58,
      execution_speed_seconds: isTorch ? 1.2 : 1.4,
      cpu_usage_percent: 22,
      ram_usage_percent: 26
    },
    {
      epoch: 2,
      accuracy: isTorch ? 71 : 67,
      execution_speed_seconds: isTorch ? 1.1 : 1.3,
      cpu_usage_percent: 26,
      ram_usage_percent: 29
    },
    {
      epoch: 3,
      accuracy: isTorch ? 79 : 75,
      execution_speed_seconds: isTorch ? 1.1 : 1.2,
      cpu_usage_percent: 29,
      ram_usage_percent: 32
    },
    {
      epoch: 4,
      accuracy: isTorch ? 84 : 81,
      execution_speed_seconds: isTorch ? 1.0 : 1.2,
      cpu_usage_percent: 33,
      ram_usage_percent: 35
    },
    {
      epoch: 5,
      accuracy: isTorch ? 88 : 86,
      execution_speed_seconds: isTorch ? 1.0 : 1.1,
      cpu_usage_percent: 36,
      ram_usage_percent: 37
    }
  ];
}

function createSeedRuns() {
  const finishedScript = buildMetricScript("pytorch", "fashion_mnist");
  const runningScript = buildMetricScript("tensorflow", "cifar100");

  return [
    {
      id: 1,
      framework: "pytorch",
      dataset_name: "fashion_mnist",
      status: "finished",
      final_accuracy: finishedScript[finishedScript.length - 1].accuracy,
      created_by: 1,
      created_at: Date.now() - 600000,
      metrics: clone(finishedScript),
      metrics_script: clone(finishedScript)
    },
    {
      id: 2,
      framework: "tensorflow",
      dataset_name: "cifar100",
      status: "running",
      final_accuracy: null,
      created_by: 1,
      created_at: Date.now() - 120000,
      metrics: clone(runningScript.slice(0, 2)),
      metrics_script: clone(runningScript)
    }
  ];
}

function buildInitialState() {
  return {
    nextUserId: 6,
    nextRunId: 3,
    users: [
      {
        id: 1,
        first_name: "Admin",
        last_name: "One",
        username: "admin1",
        password: "admin123",
        is_admin: true
      },
      {
        id: 2,
        first_name: "Admin",
        last_name: "Two",
        username: "admin2",
        password: "admin123",
        is_admin: true
      },
      {
        id: 3,
        first_name: "User",
        last_name: "One",
        username: "user1",
        password: "user123",
        is_admin: false
      },
      {
        id: 4,
        first_name: "User",
        last_name: "Two",
        username: "user2",
        password: "user123",
        is_admin: false
      },
      {
        id: 5,
        first_name: "User",
        last_name: "Three",
        username: "user3",
        password: "user123",
        is_admin: false
      }
    ],
    runs: createSeedRuns()
  };
}

function ensureState() {
  const existing = localStorage.getItem(STATE_KEY);

  if (!existing) {
    const initialState = buildInitialState();
    localStorage.setItem(STATE_KEY, JSON.stringify(initialState));
  }
}

function readState() {
  ensureState();
  return JSON.parse(localStorage.getItem(STATE_KEY));
}

function writeState(state) {
  localStorage.setItem(STATE_KEY, JSON.stringify(state));
}

function getAuthenticatedUser(token, state) {
  const userId = parseToken(token);
  const user = state.users.find((item) => item.id === userId);

  if (!user) {
    throw makeError("Utilisateur introuvable", 401);
  }

  return user;
}

function sanitizeRun(run) {
  return {
    id: run.id,
    framework: run.framework,
    dataset_name: run.dataset_name,
    status: run.status,
    final_accuracy: run.final_accuracy,
    created_by: run.created_by,
    created_at: run.created_at
  };
}

function visibleMetrics(metrics, isAdmin) {
  if (isAdmin) {
    return clone(metrics);
  }

  return metrics.map((metric) => ({
    epoch: metric.epoch,
    accuracy: metric.accuracy,
    execution_speed_seconds: metric.execution_speed_seconds,
    cpu_usage_percent: 0,
    ram_usage_percent: 0
  }));
}

function advanceRun(run) {
  if (run.status !== "running") {
    return;
  }

  const currentCount = run.metrics.length;
  const totalCount = run.metrics_script.length;

  if (currentCount < totalCount) {
    run.metrics.push(clone(run.metrics_script[currentCount]));
  }

  if (run.metrics.length >= totalCount) {
    run.status = "finished";
    run.final_accuracy = run.metrics[run.metrics.length - 1].accuracy;
  }
}

export async function registerUser(payload) {
  await delay();

  const state = readState();

  const username = payload.username?.trim();
  const firstName = payload.first_name?.trim();
  const lastName = payload.last_name?.trim();
  const password = payload.password ?? "";

  if (!username || !firstName || !lastName || !password) {
    throw makeError("Tous les champs sont requis", 400);
  }

  const exists = state.users.some(
    (user) => user.username.toLowerCase() === username.toLowerCase()
  );

  if (exists) {
    throw makeError("Username déjà utilisé", 400);
  }

  const user = {
    id: state.nextUserId,
    first_name: firstName,
    last_name: lastName,
    username,
    password,
    is_admin: false
  };

  state.nextUserId += 1;
  state.users.push(user);
  writeState(state);

  return publicUser(user);
}

export async function loginUser(payload) {
  await delay();

  const state = readState();

  const username = payload.username?.trim();
  const password = payload.password ?? "";

  const user = state.users.find(
    (item) => item.username === username && item.password === password
  );

  if (!user) {
    throw makeError("Identifiants invalides", 401);
  }

  return {
    access_token: createToken(user.id),
    token_type: "bearer",
    user: publicUser(user)
  };
}

export async function getMe(token) {
  await delay(150);

  const state = readState();
  const user = getAuthenticatedUser(token, state);
  return publicUser(user);
}

export async function getTrainings(token) {
  await delay(150);

  const state = readState();
  getAuthenticatedUser(token, state);

  return state.runs
    .slice()
    .sort((a, b) => b.id - a.id)
    .map(sanitizeRun);
}

export async function getTrainingDetails(token, trainingId) {
  await delay(150);

  const state = readState();
  getAuthenticatedUser(token, state);

  const run = state.runs.find((item) => String(item.id) === String(trainingId));

  if (!run) {
    throw makeError("Run introuvable", 404);
  }

  return sanitizeRun(run);
}

export async function getTrainingMetrics(token, trainingId) {
  await delay(150);

  const state = readState();
  const user = getAuthenticatedUser(token, state);

  const run = state.runs.find((item) => String(item.id) === String(trainingId));

  if (!run) {
    throw makeError("Run introuvable", 404);
  }

  advanceRun(run);
  writeState(state);

  return visibleMetrics(run.metrics, user.is_admin);
}

export async function createTraining(token, payload) {
  await delay(250);

  const state = readState();
  const user = getAuthenticatedUser(token, state);

  if (!user.is_admin) {
    throw makeError("Réservé aux admins", 403);
  }

  const framework = payload.framework || "pytorch";
  const datasetName = payload.dataset_name || "fashion_mnist";

  const run = {
    id: state.nextRunId,
    framework,
    dataset_name: datasetName,
    status: "running",
    final_accuracy: null,
    created_by: user.id,
    created_at: Date.now(),
    metrics: [],
    metrics_script: buildMetricScript(framework, datasetName)
  };

  state.nextRunId += 1;
  state.runs.push(run);
  writeState(state);

  return sanitizeRun(run);
}