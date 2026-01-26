import { registerAs } from '@nestjs/config';

type SettingsArray = string[];

type Nullable<T> = T | null;

export interface SettingsConfig {
  ENV: string;
  DEBUG: boolean;
  PROJECT_NAME: string;
  SECRET_KEY: string;
  VERSION: string;
  ALLOWED_HOSTS: SettingsArray;
  CONFIG_FILES: SettingsArray;
  CONFIG_REFRESH_INTERVAL: number;
  VAULT_URL: Nullable<string>;
  AWS_REGION: Nullable<string>;
  HOT_RELOAD_ENABLED: boolean;
  HOT_RELOAD_ENV_ALLOWLIST: SettingsArray;
  [key: string]: unknown;
}

const SETTINGS_CONFIG_KEY = 'settings';
export const SETTINGS_VENDOR_MODULE = 'settings';
export const SETTINGS_VENDOR_VERSION = '1.0.43';

function toList(raw: string | undefined, fallback: string): SettingsArray {
  return (raw ?? fallback)
    .split(',')
    .map((entry: string) => entry.trim())
    .filter((entry: string) => entry.length > 0);
}

function buildSettings(): SettingsConfig {
  return {
    ENV: process.env.NODE_ENV ?? 'development',
    DEBUG: process.env.DEBUG === '1' || process.env.DEBUG?.toLowerCase() === 'true',
    PROJECT_NAME: process.env.APP_NAME ?? 'RapidKit Service',
    SECRET_KEY: process.env.SECRET_KEY ?? 'rapidkit-default-generated-secret',
    VERSION: process.env.APP_VERSION ?? '0.0.1',
    ALLOWED_HOSTS: toList(process.env.ALLOWED_HOSTS, '*'),
    CONFIG_FILES: [],
    CONFIG_REFRESH_INTERVAL: Number.parseInt(process.env.CONFIG_REFRESH_INTERVAL ?? '60', 10),
    VAULT_URL: process.env.VAULT_URL ?? null,
    AWS_REGION: process.env.AWS_REGION ?? null,
    HOT_RELOAD_ENABLED:
      process.env.HOT_RELOAD_ENABLED === '1' ||
      process.env.HOT_RELOAD_ENABLED?.toLowerCase() === 'true',
    HOT_RELOAD_ENV_ALLOWLIST: toList(process.env.HOT_RELOAD_ENV_ALLOWLIST, ''),
  };
}

export const settingsConfiguration = registerAs(SETTINGS_CONFIG_KEY, buildSettings);

export const getSettings = (): SettingsConfig => buildSettings();

export const refreshSettings = (): SettingsConfig => buildSettings();

export const loadSettings = (): SettingsConfig => buildSettings();

export { SETTINGS_CONFIG_KEY };
