import { Injectable } from "@nestjs/common";
import { ConfigService } from "@nestjs/config";

import {
  SETTINGS_CONFIG_KEY,
  type SettingsConfig,
  getSettings,
  refreshSettings,
  SETTINGS_VENDOR_MODULE,
  SETTINGS_VENDOR_VERSION,
} from "./configuration";
import {
  buildSettingsMetadata,
  buildStatusSummary,
  type SettingsMetadata,
  type SettingsStatusSummary,
} from "./settings.metadata";

export type { SettingsMetadata, SettingsStatusSummary } from "./settings.metadata";

export interface SettingsSnapshotMetadata extends Record<string, unknown> {
  project_name: string;
  vault_url: string | null;
  aws_region: string | null;
  hot_reload_enabled: boolean;
  hot_reload_allowlist: string[];
}

export interface SettingsSnapshot extends Record<string, unknown> {
  module: string;
  environment: string;
  version: string;
  debug: boolean;
  allowed_hosts: string[];
  config_files: string[];
  metadata: SettingsSnapshotMetadata;
}

export interface SettingsHealthPayload extends SettingsSnapshot {
  status: "ok" | "error";
  checked_at: string;
  checks: {
    secret_placeholder: boolean;
    [key: string]: unknown;
  };
  module_version: string;
}

@Injectable()
export class SettingsService {
  private cache: SettingsConfig | null = null;

  constructor(
    private readonly configService: ConfigService<Record<string, unknown>, true>,
  ) {}

  get settings(): SettingsConfig {
    if (this.cache) {
      return this.cache;
    }
    const registered = this.configService.get<SettingsConfig>(SETTINGS_CONFIG_KEY);
    this.cache = registered ?? getSettings();
    return this.cache;
  }

  refresh(): SettingsConfig {
    this.cache = refreshSettings();
    return this.cache;
  }

  snapshot(): SettingsSnapshot {
    return SettingsService.toSnapshot(this.settings);
  }

  refreshSnapshot(): SettingsSnapshot {
    return SettingsService.toSnapshot(this.refresh());
  }

  getMetadata(): SettingsMetadata {
    return buildSettingsMetadata(this.snapshot());
  }

  refreshMetadata(): SettingsMetadata {
    return buildSettingsMetadata(this.refreshSnapshot());
  }

  getStatus(): SettingsStatusSummary {
    return buildStatusSummary(this.snapshot());
  }

  getHealth(): SettingsHealthPayload {
    return SettingsService.toHealthPayload(this.snapshot());
  }

  refreshHealth(): SettingsHealthPayload {
    return SettingsService.toHealthPayload(this.refreshSnapshot());
  }

  getHealthPayload(): SettingsHealthPayload {
    return this.getHealth();
  }

  value<K extends keyof SettingsConfig>(key: K, fallback?: SettingsConfig[K]) {
    const resolved = this.settings[key];
    if (resolved === undefined) {
      return fallback as SettingsConfig[K];
    }
    return resolved;
  }

  private static toSnapshot(settings: SettingsConfig): SettingsSnapshot {
    const metadata: SettingsSnapshotMetadata = {
      project_name: settings.PROJECT_NAME,
      vault_url: settings.VAULT_URL ?? null,
      aws_region: settings.AWS_REGION ?? null,
      hot_reload_enabled: Boolean(settings.HOT_RELOAD_ENABLED),
      hot_reload_allowlist: Array.isArray(settings.HOT_RELOAD_ENV_ALLOWLIST)
        ? settings.HOT_RELOAD_ENV_ALLOWLIST.map((entry: string) => `${entry}`)
        : [],
    };

    return {
      module: SETTINGS_VENDOR_MODULE,
      environment: settings.ENV,
      version: settings.VERSION,
      debug: settings.DEBUG,
      allowed_hosts: [...settings.ALLOWED_HOSTS],
      config_files: [...settings.CONFIG_FILES],
      metadata,
    };
  }

  private static toHealthPayload(snapshot: SettingsSnapshot): SettingsHealthPayload {
    const statusSummary = buildStatusSummary(snapshot);
    const vaultUrl = snapshot.metadata?.vault_url ?? null;
    return {
      ...snapshot,
      status: statusSummary.status,
      checked_at: statusSummary.refreshedAt,
      checks: {
        secret_placeholder: vaultUrl !== null,
      },
      module_version: SETTINGS_VENDOR_VERSION,
    };
  }
}
