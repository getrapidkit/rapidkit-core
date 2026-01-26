import { Test } from "@nestjs/testing";

import { OauthModule } from "../../src/modules/free/auth/oauth/oauth.module";
import { OauthService } from "../../src/modules/free/auth/oauth/oauth.service";

const GOOGLE_ID = "google-id";
const GOOGLE_SECRET = "google-secret";
const GITHUB_ID = "github-id";
const GITHUB_SECRET = "github-secret";

const ENV_VARS: Record<string, string> = {
  GOOGLE_OAUTH_CLIENT_ID: GOOGLE_ID,
  GOOGLE_OAUTH_CLIENT_SECRET: GOOGLE_SECRET,
  GITHUB_OAUTH_CLIENT_ID: GITHUB_ID,
  GITHUB_OAUTH_CLIENT_SECRET: GITHUB_SECRET,
};

describe("OauthModule", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    for (const [key, value] of Object.entries(ENV_VARS)) {
      process.env[key] = value;
    }
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("registers the OauthService", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [OauthModule],
    }).compile();

    const service = moduleRef.get(OauthService);
    expect(service).toBeDefined();
  });

  it("lists configured providers", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [OauthModule],
    }).compile();

    const service = moduleRef.get(OauthService);
    const providers = service.listProviders();

    expect(Object.keys(providers).length).toBeGreaterThan(0);
    expect(providers.google.authorizeUrl).toContain("google");
  });

  it("produces metadata and health snapshots", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [OauthModule],
    }).compile();

    const service = moduleRef.get(OauthService);
    const metadata = service.metadata();
    const health = service.health();

    expect(metadata.module).toBe("oauth");
    expect(metadata.providerCount).toBeGreaterThan(0);
    expect(health.status).toBe("ok");
    expect(health.metadata.redirectBaseUrl).toContain("/oauth");
  });
});
