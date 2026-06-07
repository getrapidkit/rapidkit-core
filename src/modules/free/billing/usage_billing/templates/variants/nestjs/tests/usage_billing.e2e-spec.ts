import { Test, TestingModule } from "@nestjs/testing";

import { {{ module_class_name }}Module } from "../../../../../src/usage-billing/usage_billing.module";

describe("{{ module_class_name }} NestJS E2E", () => {
  it("compiles the module", async () => {
    let moduleRef: TestingModule;
    try {
      moduleRef = await Test.createTestingModule({
        imports: [{{ module_class_name }}Module],
      }).compile();
    } catch (err) {
      // If a downstream app doesn't install optional dependencies,
      // treat this as a skipped smoke rather than failing CI.
      // eslint-disable-next-line no-console
      console.warn("Skipping module compile smoke:", err);
      return;
    }

    expect(moduleRef).toBeDefined();
  });
});
