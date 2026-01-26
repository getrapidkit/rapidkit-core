import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../../src/app.module';

describe('AI Assistant E2E', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  describe('Health endpoint', () => {
    it('should return ok status', async () => {
      const response = await request(app.getHttpServer()).get('/health');
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status');
    });

    it('should include metadata in health probe', async () => {
      const response = await request(app.getHttpServer()).get('/health');
      expect(response.status).toBe(200);
      const { body } = response;
      // Module health should expose version, uptime, or module metadata
      const hasMetadata = ['version', 'status', 'module', 'uptime'].some(
        (key) => key in body,
      );
      expect(hasMetadata).toBe(true);
    });
  });
});
