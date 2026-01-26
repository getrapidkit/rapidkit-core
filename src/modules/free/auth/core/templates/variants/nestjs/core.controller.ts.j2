import { Controller, Get } from "@nestjs/common";

import { AuthCoreHealthPayload, AuthCoreService } from "./auth-core.service";

const FEATURE_FLAGS = [
  "password_hashing",
  "token_signing",
  "peppered_digests",
  "policy_enforcement",
] as const;

type Feature = (typeof FEATURE_FLAGS)[number];

@Controller("auth/core")
export class AuthCoreController {
  constructor(private readonly authCoreService: AuthCoreService) {}

  @Get("metadata")
  getMetadata(): Record<string, unknown> {
    return {
      status: "ok",
      ...this.authCoreService.metadata(),
      features: [...FEATURE_FLAGS],
    };
  }

  @Get("features")
  getFeatures(): { features: Feature[] } {
    return { features: [...FEATURE_FLAGS] };
  }

  @Get("health")
  getHealth(): AuthCoreHealthPayload {
    return this.authCoreService.health();
  }
}
