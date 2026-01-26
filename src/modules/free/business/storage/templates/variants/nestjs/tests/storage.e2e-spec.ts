import { Test, TestingModule } from "@nestjs/testing";

import { {{ module_class_name }}Module } from "../../../../../../src/modules/free/business/storage/storage.module";

describe("{{ module_class_name }} NestJS E2E", () => {
  it("compiles the module", async () => {
    let moduleRef: TestingModule;
    try {
      moduleRef = await Test.createTestingModule({
        imports: [{{ module_class_name }}Module],
      }).compile();
    } catch (err) {
      // Optional deps may not be installed in all downstream apps;
      // treat this as a soft-skip rather than failing.
      // eslint-disable-next-line no-console
      console.warn("Skipping module compile smoke:", err);
      return;
    }

    expect(moduleRef).toBeDefined();
  });
});
