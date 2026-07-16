# ADR-004: Use Domain Packages with a Three-Layer Structure

## Status

Accepted

## Context

The previous plans mixed `api`, `application`, `domain`, and `infrastructure` as top-level concepts inside every feature. For this assignment, those boundaries add naming and navigation overhead without independent modules or ports-and-adapters contracts to justify them.

The project needs one structure that keeps related feature code together, makes transaction ownership obvious, and remains simple enough for the current scope.

## Decision

Use domain-first packaging with a three-layer dependency direction inside each domain:

```txt
com.ch6.cafe
├─ global
│  ├─ config
│  ├─ exception
│  ├─ response
│  └─ lock
└─ domain
   ├─ menu
   ├─ point
   ├─ order
   ├─ ranking
   └─ outbox
```

Create only the subpackages required by implemented classes. A normal domain may use:

```txt
controller
service
repository
entity
dto/request
dto/response
exception
```

The dependency direction is:

```txt
controller -> service -> repository
```

- Controllers map and validate HTTP input and output. They do not own business rules.
- Services own business rules, use-case orchestration, distributed-lock orchestration, and transaction boundaries.
- Repositories own persistence access. Entities and DTOs are used by the layer that needs them without introducing an additional architectural layer.
- Cross-domain infrastructure configuration, shared error responses, and distributed-lock utilities belong under `global`.
- Kafka publishing belongs in `domain/outbox/publisher`.
- Payment belongs inside `domain/order` because it has no independent lifecycle in the current scope.

Do not create empty packages, package-info placeholders, `.gitkeep` files, or placeholder classes merely to mirror the tree.

## Alternatives Considered

- Package by technical layer across the whole application: simple layer visibility, but scatters each feature across the repository and increases cross-feature coupling.
- Domain packages with `api/application/domain/infrastructure`: useful when enforcing ports and adapters or a richer domain model, but unnecessary indirection for the current assignment.
- Separate payment domain: appropriate when payment gains its own lifecycle, external provider integration, refunds, or independent policies; not justified now.

## Consequences

### Positive

- Feature code is colocated and easier to navigate.
- Controller, service, and repository responsibilities are explicit.
- Business rules and transactions have one clear owner: the service layer.
- The structure can add subpackages incrementally without empty scaffolding.

### Negative

- Domain entities can remain aware of JPA because there is no separate persistence adapter layer.
- Cross-domain service calls require discipline to avoid cycles.
- A future move to ports and adapters would require an explicit migration rather than only renaming packages.

### Neutral / Trade-offs

- This ADR decides package and dependency boundaries, not the number of classes in each domain.
- If payment later gains an independent lifecycle, a new ADR may extract it from `order`.

## Follow-up

- Keep feature plans aligned with the decided paths.
- Add package dependency checks when production code exists and a supported static workflow can enforce them.
