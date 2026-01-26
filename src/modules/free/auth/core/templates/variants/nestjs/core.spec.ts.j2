import { Test } from "@nestjs/testing";

import { AuthCoreModule } from "../../../../../src/modules/free/auth/core/auth-core.module";
import { AuthCoreService } from "../../../../../src/modules/free/auth/core/auth-core.service";

const TEST_PEPPER = "integration-test-pepper";

describe("AuthCoreModule", () => {
  beforeEach(() => {
    process.env.RAPIDKIT_AUTH_CORE_PEPPER = TEST_PEPPER;
  });

  afterEach(() => {
    delete process.env.RAPIDKIT_AUTH_CORE_PEPPER;
  });

  it("registers the AuthCoreService", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AuthCoreModule.forRoot()],
    }).compile();

    const service = moduleRef.get(AuthCoreService);
    expect(service).toBeDefined();
  });

  it("hashes and verifies passwords", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AuthCoreModule.forRoot()],
    }).compile();

    const service = moduleRef.get(AuthCoreService);
    const encoded = service.hashPassword("ValidPassword123!");

    expect(encoded).toContain("$");
    expect(service.verifyPassword("ValidPassword123!", encoded)).toBe(true);
    expect(service.verifyPassword("invalid", encoded)).toBe(false);
  });

  it("issues signed tokens", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AuthCoreModule.forRoot()],
    }).compile();

    const service = moduleRef.get(AuthCoreService);

    const token = service.issueToken("user-123", {
      audience: "api",
      scopes: ["read"],
      ttlSeconds: 10,
      customClaims: { role: "admin" },
    });

    const payload = service.verifyToken(token);
    expect(payload.sub).toBe("user-123");
    expect(payload.aud).toBe("api");
    expect(payload.scopes).toEqual(["read"]);
    expect(payload.role).toBe("admin");
  });

  it("reports health metadata", async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [AuthCoreModule.forRoot()],
    }).compile();

    const service = moduleRef.get(AuthCoreService);
    const metadata = service.metadata();

    expect(metadata.module).toBe("auth_core");
    expect(typeof metadata.pepper_configured).toBe("boolean");
    expect(metadata.iterations).toBeGreaterThan(0);
  });
});
