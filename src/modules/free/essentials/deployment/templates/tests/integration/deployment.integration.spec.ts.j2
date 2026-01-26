import { Test } from '@nestjs/testing';
import request from 'supertest';

import { DeploymentModule } from '../../../../../src/modules/free/essentials/deployment/deployment.module';

describe('DeploymentModule (Integration)', () => {
  it('exposes deployment plan metadata', async () => {
    const moduleRef = await Test.createTestingModule({
      imports: [DeploymentModule],
    }).compile();

    const app = moduleRef.createNestApplication();
    await app.init();

    const server = app.getHttpServer();
    const response = await request(server).get('/deployment/plan');

    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('assets');
    expect(Array.isArray(response.body.assets)).toBe(true);
    expect(response.body).toHaveProperty('module');

    await app.close();
  });
});
