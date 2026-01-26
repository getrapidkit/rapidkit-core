import { INestApplication } from '@nestjs/common';
import { Test } from '@nestjs/testing';
import request from 'supertest';

import { LoggingModule } from '../../../../../src/modules/free/essentials/logging/logging.module';

describe('LoggingModule (Integration)', () => {
  let app: INestApplication;

  beforeAll(async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [LoggingModule],
    }).compile();

    app = moduleRef.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('exposes logging configuration endpoint', async () => {
    const server = app.getHttpServer();
    const response = await request(server).get('/logging');

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('level');
    expect(response.body).toHaveProperty('sinks');
  });
});
