'use strict';

const path = require('path');

const DEFAULT_DATA_DIR = path.join(__dirname, '..', 'data');

function present(value) {
  return typeof value === 'string' ? !!value.trim() : !!value;
}

/* Render's application filesystem is replaceable. Setting LEON_DATA_DIR to a
   mounted persistent-disk directory moves every JSONL operational record off
   that replaceable layer without baking a host-specific path into the app. */
function dataDir(env = process.env) {
  const configured = String(env.LEON_DATA_DIR || '').trim();
  return configured ? path.resolve(configured) : DEFAULT_DATA_DIR;
}

function dataFile(filename, explicitEnvName, env = process.env) {
  const explicit = explicitEnvName && String(env[explicitEnvName] || '').trim();
  return explicit ? path.resolve(explicit) : path.join(dataDir(env), filename);
}

function storageConfig(env = process.env) {
  const localDurableConfigured = present(env.LEON_DATA_DIR);
  return {
    localMode: localDurableConfigured ? 'configured-persistent-path' : 'application-filesystem',
    localDurableConfigured
  };
}

module.exports = { dataDir, dataFile, storageConfig };
