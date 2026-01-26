# Advanced Users Core Scenarios

This guide highlights extension points for teams integrating Users Core into mature production
environments.

## Custom Repository Implementations

The generated repository protocol
(`src.modules.free.users.users_core.core.users.repository.UsersRepositoryProtocol`) defines the
expected persistence contract. Replace the in-memory implementation with your datastore by creating
a class that implements the same asynchronous and synchronous methods, then register it inside your
dependency container:

```python
from src.modules.free.users.users_core.core.users.repository import (
    UsersRepositoryProtocol,
)
from src.modules.free.users.users_core.core.users.dependencies import (
    configure_users_dependencies,
)


class SQLUsersRepository(UsersRepositoryProtocol):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def get_by_id(self, user_id: str):
        with self._session_factory() as session:
            return session.get(UserModel, user_id)


configure_users_dependencies(
    repository_provider=SQLUsersRepository(sql_session_factory)
)
```

The dependency helper propagates the custom repository through the service facade, keeping the HTTP
layer unchanged.

## Event Hooks and Auditing

Enable audit logging via `RAPIDKIT_USERS_CORE_AUDIT_LOG_ENABLED=true` and supply a structured logger
that consumes the service's audit events. Extend `UsersService` to emit domain events (for example,
`UserCreated` and `UserUpdated`) and publish them to your messaging layer for downstream consumers.

```python
from src.modules.free.users.users_core.core.users.service import UsersService


class EventedUsersService(UsersService):
    def _notify_user_created(self, user):  # called internally after creation
        super()._notify_user_created(user)
        event_bus.publish("user.created", user.model_dump())
```

Register the subclass through the overrides mixin or dependency configuration to layer in the new
behaviour without patching vendor templates.

## Multi-tenant Deployments

Multi-tenant products can override defaults per tenant by extending the settings object generated in
`src.modules.free.users.users_core.core.users.settings`. Use `UsersCoreOverrides` to inject
tenant-aware defaults and load them from your configuration service. Because overrides run during
generation, sensitive logic should reside in runtime factories or middleware.

## GraphQL or gRPC Front Ends

The service facade intentionally exposes synchronous methods so alternative transport layers
(GraphQL resolvers, gRPC handlers) can wrap the same contract. When building GraphQL resolvers,
inject the facade with the same dependency helper and serialise DTOs into your schema types. For
gRPC, map DTO fields to protobuf messages and reuse the repository abstraction.
