"use strict";

const normalizeBoolean = (value, fallback) => {
  if (value === undefined || value === null) {
    return fallback;
  }
  return ["1", "true", "yes", "on"].includes(String(value).toLowerCase());
};

const normalizeSinks = (value) => {
  if (!value) {
    return ["stderr"];
  }
  return String(value)
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
};

function loadConfiguration() {
  return {
    module: "logging",
    level: process.env.LOG_LEVEL ?? "info",
    format: process.env.LOG_FORMAT ?? "json",
    sinks: normalizeSinks(process.env.LOG_SINKS),
    asyncQueue: normalizeBoolean(process.env.LOG_ASYNC_QUEUE, true),
    filePath: process.env.LOG_FILE_PATH ?? "logs/app.log",
    samplingRate: Number(process.env.LOG_SAMPLING_RATE ?? "1"),
  };
}

module.exports = {
  loadConfiguration,
};
