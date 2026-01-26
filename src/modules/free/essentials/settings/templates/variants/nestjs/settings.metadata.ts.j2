import { SettingsSnapshot } from "./settings.service";

export interface SettingsMetadata {
  module: string;
  version: string;
  environment: string;
  project: string;
  configFiles: string[];
  hotReloadEnabled: boolean;
  hotReloadAllowlist: string[];
  vaultUrl: string | null;
  awsRegion: string | null;
}

export interface SettingsStatusSummary {
  module: string;
  status: "ok" | "error";
  refreshedAt: string;
  environment: string;
}

export function buildSettingsMetadata(snapshot: SettingsSnapshot): SettingsMetadata {
  return {
    module: snapshot.module,
    version: snapshot.version,
    environment: snapshot.environment,
    project: snapshot.metadata.project_name,
    configFiles: [...snapshot.config_files],
    hotReloadEnabled: snapshot.metadata.hot_reload_enabled ?? true,
    hotReloadAllowlist: snapshot.metadata.hot_reload_allowlist ?? [],
    vaultUrl: snapshot.metadata.vault_url,
    awsRegion: snapshot.metadata.aws_region,
  };
}

export function buildStatusSummary(snapshot: SettingsSnapshot): SettingsStatusSummary {
  return {
    module: snapshot.module,
    status: "ok",
    refreshedAt: new Date().toISOString(),
    environment: snapshot.environment,
  };
}
