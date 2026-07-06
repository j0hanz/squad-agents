# ponytail: local reference, frontmatter deferred until a cross-skill consumer appears

# Reference: Feedback Loop Patterns

## 1. CLI Tools

- **Strategy:** File I/O comparison.
- **Setup:** Write fixture input -> Run CLI -> Output to file.
- **Assertion:** `diff expected.txt actual.txt`.
- **Determinism:** Pin RNG seeds and system time (`TZ=UTC`).

## 2. API / HTTP Services

- **Strategy:** Polling & Load.
- **Setup:** Bash `while` loop on `/health` endpoint to warm up.
- **Assertion:** Bash `for` loop with `curl`, grep for HTTP status codes.
- **Concurrency:** Background curl tasks (`&`) and `wait` to surface race conditions.

## 3. Databases / SQL

- **Strategy:** Execution plan & timing.
- **Correctness_Loop:** Pipe static `.sql` to CLI (`sqlite3`, `psql`), diff output.
- **Performance_Loop:** Prepend `EXPLAIN`, or wrap query in bash `date +%s%N` timing blocks.

## 4. Node.js / JavaScript

- **Strategy:** Programmatic test runner.
- **Sync_Crash:** `expect(() => fn()).toThrow()`.
- **Async_Bug:** `await fn()`, assert on return or catch block.
- **Race_Condition:** Spawn 100 concurrent Promises (`Promise.all`), assert final shared state.

## 5. Frontend / Browser

- **Strategy:** Headless automation.
- **Setup:** Playwright/Puppeteer script.
- **Assertion:** Navigate -> Interact -> `expect(locator).toBeVisible()`.
- **Determinism:** Avoid `setTimeout`; use DOM state watchers (`waitForSelector`).

## 6. System Concurrency (General)

- **Strategy:** Data race detection & stress.
- **C/C++:** Compile with `-fsanitize=thread`.
- **Python/Java:** Launch N threads each performing M iterations of the target operation. Assert final array length or counter.

## 7. Memory Leaks

- **Strategy:** Garbage Collection diffing.
- **Node.js:** Expose GC (`--expose-gc`).
- **Loop:** Record heap -> Run operation 10000x -> `global.gc()` -> Record heap.
- **Assertion:** Final heap - Initial heap < Threshold (e.g., 50MB).

## 8. Flaky Tests

- **Strategy:** Brute force repetition.
- **Setup:** Bash loop running the test command 50 times.
- **Assertion:** Count passes vs fails. Fail script if fails > 0.
- **Diagnosis:** Force serial execution, fix RNG seeds, inspect timestamps.

## 9. Full Stack Integration

- **Strategy:** Containerized ephemerality.
- **Setup:** `docker-compose up -d` with test database.
- **Execution:** Wait for healthcheck -> run test suite -> `docker-compose down`.

## 10. Post-Fix Regression Locking

- **Strategy:** Hardcode the failure state.
- **Naming:** Include bug ID (e.g., `describe("Bug #123: ...")`).
- **Implementation:** Replicate exact concurrency, load, and data inputs that caused the original crash.
