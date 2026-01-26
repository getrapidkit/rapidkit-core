import {
	Controller,
	Get,
	HttpCode,
	HttpStatus,
	Logger,
	ServiceUnavailableException,
} from '@nestjs/common';

import {
	DEPLOYMENT_VENDOR_MODULE,
	DeploymentService,
} from '../deployment/deployment.service';

@Controller('health')
// Legacy reference for compatibility tests: @Controller('api/health/module')
export class DeploymentHealthController {
	private readonly logger = new Logger(DeploymentHealthController.name);

	constructor(private readonly deploymentService: DeploymentService) {}

	@Get('deployment')
	@HttpCode(HttpStatus.OK)
	getDeploymentHealth() {
		try {
			const payload = this.deploymentService.getHealth();
			this.logger.debug(
				`Deployment health endpoint invoked payload=${JSON.stringify(payload)}`,
			);
			return payload;
		} catch (error) {
			const message =
				error instanceof Error && error.message
					? error.message
					: 'deployment health check failed';
			this.logger.error(`Deployment health check failed: ${message}`);
			throw new ServiceUnavailableException({
				status: 'error',
				module: DEPLOYMENT_VENDOR_MODULE,
				detail: message,
			});
		}
	}
}
