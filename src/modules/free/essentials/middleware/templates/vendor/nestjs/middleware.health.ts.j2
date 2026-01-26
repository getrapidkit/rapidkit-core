import { Injectable } from '@nestjs/common';
import { HealthIndicator, HealthIndicatorResult } from '@nestjs/terminus';

import { MiddlewareService } from '../modules/free/essentials/middleware/service';

@Injectable()
export class MiddlewareHealthIndicator extends HealthIndicator {
  constructor(private readonly middlewareService: MiddlewareService) {
    super();
  }

  public async isHealthy(): Promise<HealthIndicatorResult> {
    const status = this.middlewareService.getStatus();
    const healthy = status.status === 'ok';
    return this.getStatus('middleware', healthy, {
      enabled: status.enabled,
    });
  }
}
