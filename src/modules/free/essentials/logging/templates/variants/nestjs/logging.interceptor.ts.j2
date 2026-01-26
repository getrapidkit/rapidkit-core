import { CallHandler, ExecutionContext, Injectable, NestInterceptor } from '@nestjs/common';
import type { Observable } from 'rxjs';
import { randomUUID } from 'crypto';
import type { Request } from 'express';

import { LoggingService, type LoggingContext } from './logging.service';

const REQUEST_ID_HEADER = 'x-request-id';
const USER_ID_HEADER = 'x-user-id';

function resolveHeaderValue(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) {
    return value.find((candidate) => !!candidate);
  }
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

@Injectable()
export class LoggingContextInterceptor implements NestInterceptor {
  constructor(private readonly logging: LoggingService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    if (!this.logging.contextEnabled) {
      return next.handle();
    }

    const httpContext = context.switchToHttp();
    const request = httpContext.getRequest<Request | undefined>();
    const fallbackRequestId = randomUUID();
    const requestId = resolveHeaderValue(request?.headers?.[REQUEST_ID_HEADER]) ?? fallbackRequestId;

    const userIdHeader = resolveHeaderValue(request?.headers?.[USER_ID_HEADER]);
    const userId = typeof userIdHeader === 'string' ? userIdHeader : undefined;

    const contextPayload: LoggingContext = {
      requestId,
      userId,
    };

    return this.logging.runWithContext(contextPayload, () => next.handle());
  }
}
