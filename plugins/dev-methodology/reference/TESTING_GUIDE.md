# Testing Guide

> Guidelines for testing practices in this project.

---

## Philosophy

1. **Feature flows include testing instructions** - Follow them to verify features work
2. **Manual integration testing > automated tests** - For complex user journeys
3. **Automate when it saves time** - Repeated testing, regression prevention
4. **Test at the right level** - Unit for logic, integration for flows, E2E sparingly

---

## Test Tiers

### Tier 1: Smoke Tests (Fast)
**Duration**: ~1 minute
**Purpose**: Quick validation that nothing is catastrophically broken

### Tier 2: Core Tests (Standard)
**Duration**: ~5 minutes
**Purpose**: Comprehensive validation of core functionality

### Tier 3: Full Suite (Comprehensive)
**Duration**: ~15+ minutes
**Purpose**: Complete validation including slow integration tests

---

## Quality Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Pass Rate | >90% | 75-90% | <75% |
| Failures | 0 | 1-5 | >5 |
| Coverage | >80% | 60-80% | <60% |

---

## When to Write Tests

### Always Write Tests For:
- Bug fixes (regression prevention)
- Complex business logic
- Critical user paths
- Edge cases that have bitten you

### Consider Not Testing:
- Simple CRUD operations (covered by framework)
- UI styling
- Third-party library behavior
- One-off scripts

---

## Feature Flow Testing

Each feature flow document (`docs/memory/feature-flows/*.md`) should include a Testing section with:
- Prerequisites
- Step-by-step test instructions
- Expected results
- Edge cases
- Status tracking

---

## Best Practices

### DO
- Write descriptive test names
- Test one thing per test
- Clean up after tests
- Run tests frequently

### DON'T
- Test implementation details
- Share state between tests
- Skip flaky tests indefinitely
- Mock everything
