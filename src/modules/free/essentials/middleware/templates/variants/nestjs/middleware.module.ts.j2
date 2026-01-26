import { MiddlewareConsumer, Module, NestModule } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

import { MiddlewareController } from './controller';
import middlewareConfiguration from './configuration';
import { MiddlewareHealthIndicator } from '../../../../health/middleware.health';
import { MiddlewareService } from './service';

@Module({
  imports: [ConfigModule.forFeature(middlewareConfiguration)],
  controllers: [MiddlewareController],
  providers: [MiddlewareService, MiddlewareHealthIndicator],
  exports: [MiddlewareService, MiddlewareHealthIndicator],
})
export class MiddlewareModule implements NestModule {
  constructor(private readonly middlewareService: MiddlewareService) {}

  configure(consumer: MiddlewareConsumer) {
    const handlers = this.middlewareService.getHandlers();
    if (handlers.length === 0) {
      return;
    }

    consumer.apply(...handlers).forRoutes('*');
  }
}
