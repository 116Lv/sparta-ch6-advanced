# Popular Menu Cache Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve Redis-first popular-menu reads without trusting partial, stale, or concurrently overwritten daily rankings.

**Architecture:** Daily completeness markers gate Redis reads. Date-scoped locking and absolute MySQL-derived scores make rebuild and post-commit cache updates converge, while incomplete cache states fall back to MySQL and rebuild every requested date.

**Tech Stack:** Java, Spring Boot, Spring Data JPA, Spring Data Redis, Redisson, MySQL, Redis, JUnit 5, Mockito, Testcontainers.

## Global Constraints

- MySQL `daily_menu_sales` remains the durable source.
- Redis daily keys retain a 14-day TTL; temporary keys retain a 1-minute safety TTL and are deleted after use.
- API accepts only `days=7` and `limit=3`.
- No product command may run unless it is VERIFIED in `ai/command-registry.json`.
- Do not weaken or delete existing tests and contracts.

---

### Task 1: Completeness-aware query and cache protocol

**Files:**
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/service/PopularMenuQueryService.java`
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/service/MenuSalesRecorder.java`
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/service/RankingRebuildService.java`
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/repository/RedisPopularMenuRepository.java`
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/repository/DailyMenuSalesRepository.java`
- Modify: canonical ranking docs and ADR-003 where the protocol changes their contract
- Test: focused ranking unit and MySQL/Redis integration tests under `src/test/java/com/ch6/cafe/domain/ranking/`

**Interfaces:**
- `RedisPopularMenuRepository.findComplete(LocalDate to, int days)` returns a cache miss unless every daily marker exists.
- `RedisPopularMenuRepository.replaceDate(LocalDate date, Map<Long, Long> counts)` replaces one complete daily generation, including an empty date.
- `DailyMenuSalesRepository` exposes exact per-date/member durable counts required for absolute cache assignment.
- `MenuSalesRecorder.recordCache` updates a member under the same date lock used by rebuild and never marks an incomplete date complete.

- [ ] **Step 1: Write failing focused tests** for full-marker cache hit, one missing marker, empty-date stale cleanup, absolute update/rebuild interleaving, Redis failure fallback, missing-menu fallback, exact 7/3 validation, fixed `Clock`, inclusive seven-day aggregation, tie order, TTL, and temporary-key cleanup. Every test must assert returned counts/order and relevant Redis/MySQL state.
- [ ] **Step 2: Record RED as NOT RUN/BLOCKED** because no VERIFIED product test command exists; do not claim execution.
- [ ] **Step 3: Implement the minimal completeness protocol** with date-scoped Redisson locking, full-range rebuild, atomic live-key replacement, marker TTL, absolute durable score updates, injected `Clock`, durable fallback, and exact 7/3 validation.
- [ ] **Step 4: Align docs and schema/API terminology** without weakening MySQL authority or post-commit failure behavior.
- [ ] **Step 5: Run static verification** using `git diff --check`, targeted `rg`, import/dependency inspection, and schema/entity/doc comparison. Record runtime verification as NOT RUN/BLOCKED.
- [ ] **Step 6: Commit the cohesive correction** and submit the exact commit range to a fresh spec-compliance and code-quality reviewer. Fix all Critical/Important findings and re-review.

## Self-review

- The task covers every Task 4 Important finding: partial loss, empty-date stale keys, rebuild/update overlap, noncanonical parameters, missing menus, missing verification, and shared `Clock`.
- No placeholder or deferred implementation step is present.
- Interface names are implementation targets; the implementer may choose equivalent focused names while preserving the stated behavior.
