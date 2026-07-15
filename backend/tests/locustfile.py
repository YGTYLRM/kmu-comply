"""
Locust load test for Complio / kmu-comply.

Three user classes cover the main traffic shapes:

  PublicUser        — /api/health + /api/quick-check with no auth.
                      Fast, high-frequency. Stresses the threshold engine
                      and basic FastAPI routing.

  DiagnosticUser    — Full analysis pipeline as an unsubscribed user.
                      POST /api/analyze → poll /api/status → GET /api/report.
                      Exercises Celery, ChromaDB, and the OpenAI call chain.
                      Slow by design (pipeline takes 1-10 min).

  StatusPollerUser  — Simulates the frontend polling /api/status every 2-3 s
                      for a job that is already running. High concurrency.

─────────────────────────────────────────────────────────────────────────────
Setup
─────────────────────────────────────────────────────────────────────────────
  pip install locust

Obtain a Supabase JWT for authenticated scenarios:
  1. Log in to the app in the browser.
  2. Open DevTools → Application → Local Storage → supabase.auth.token
  3. Copy the access_token value.
  OR use curl:
    curl -sX POST 'https://<project>.supabase.co/auth/v1/token?grant_type=password' \\
      -H 'apikey: <anon-key>' -H 'Content-Type: application/json' \\
      -d '{"email":"you@example.com","password":"yourpassword"}' | jq .access_token

  Export it before running:
    export COMPLIO_AUTH_TOKEN=eyJ...

─────────────────────────────────────────────────────────────────────────────
Run commands
─────────────────────────────────────────────────────────────────────────────
  # Interactive UI at http://localhost:8089
  locust -f backend/tests/locustfile.py --host http://localhost:8000

  # Headless — public endpoints only, 50 users, 5/s ramp, 3 min
  locust -f backend/tests/locustfile.py --host http://localhost:8000 \\
    --headless -u 50 -r 5 --run-time 3m --class-picker PublicUser

  # Spike test — 10 concurrent analysis submissions
  locust -f backend/tests/locustfile.py --host http://localhost:8000 \\
    --headless -u 10 -r 10 --run-time 30m --class-picker DiagnosticUser

  # Status-poll concurrency — 100 users hammering status
  locust -f backend/tests/locustfile.py --host http://localhost:8000 \\
    --headless -u 100 -r 20 --run-time 5m --class-picker StatusPollerUser
"""

import logging
import os
import random
import time

from locust import HttpUser, between, events, tag, task

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────────────────────

_AUTH_TOKEN = os.environ.get("COMPLIO_AUTH_TOKEN", "")

if not _AUTH_TOKEN:
    logger.warning(
        "COMPLIO_AUTH_TOKEN not set — DiagnosticUser and StatusPollerUser "
        "will be skipped. Set the env var to a valid Supabase JWT."
    )


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_AUTH_TOKEN}"} if _AUTH_TOKEN else {}


# ── Canonical company profiles (from conftest.py) ─────────────────────────────

_PROFILES = [
    {
        "company_name": "TechBit GmbH",
        "industry": "it_software",
        "employee_count": 5,
        "annual_revenue_eur": 400_000,
        "processes_personal_data": True,
        "processes_special_category_data": False,
        "processing_is_occasional": False,
        "has_supply_chain_abroad": False,
        "has_website": True,
        "has_privacy_policy": False,
        "has_cookie_banner": False,
    },
    {
        "company_name": "MaschBau AG",
        "industry": "manufacturing",
        "employee_count": 1200,
        "annual_revenue_eur": 75_000_000,
        "balance_sheet_total_eur": 40_000_000,
        "processes_personal_data": True,
        "processes_special_category_data": False,
        "processing_is_occasional": False,
        "has_supply_chain_abroad": True,
        "supply_chain_countries": ["CN", "VN", "IN"],
        "annual_energy_consumption_mwh": 10_000,
    },
    {
        "company_name": "Konzern SE",
        "industry": "manufacturing",
        "employee_count": 1500,
        "annual_revenue_eur": 200_000_000,
        "balance_sheet_total_eur": 80_000_000,
        "processes_personal_data": True,
        "processes_special_category_data": False,
        "processing_is_occasional": False,
        "is_listed_company": True,
        "has_supply_chain_abroad": True,
        "supply_chain_countries": ["CN"],
        "annual_energy_consumption_mwh": 12_000,
    },
    {
        "company_name": "Max Mustermann Consulting",
        "industry": "consulting",
        "employee_count": 1,
        "annual_revenue_eur": 80_000,
        "processes_personal_data": True,
        "processing_is_occasional": True,
    },
    {
        "company_name": "MediCare Praxis GmbH",
        "industry": "healthcare",
        "employee_count": 50,
        "annual_revenue_eur": 3_000_000,
        "processes_personal_data": True,
        "processes_special_category_data": True,
        "processing_is_occasional": False,
    },
]

# Quick-check payloads mirror the profile shapes but only include the fields
# accepted by /api/quick-check (a subset of CompanyProfile).
_QUICK_CHECK_PAYLOADS = [
    {
        "employee_count": 5,
        "industry": "it_software",
        "annual_revenue_eur": 400_000,
        "processes_personal_data": True,
        "has_website": True,
        "processing_is_occasional": False,
        "processes_special_category_data": False,
    },
    {
        "employee_count": 1200,
        "industry": "manufacturing",
        "annual_revenue_eur": 75_000_000,
        "balance_sheet_total_eur": 40_000_000,
        "processes_personal_data": True,
        "has_supply_chain_abroad": True,
        "supply_chain_countries": ["CN", "VN"],
        "annual_energy_consumption_mwh": 10_000,
    },
    {
        "employee_count": 50,
        "industry": "healthcare",
        "annual_revenue_eur": 3_000_000,
        "processes_personal_data": True,
        "processes_special_category_data": True,
        "processing_is_occasional": False,
    },
    {
        "employee_count": 300,
        "industry": "logistics",
        "annual_revenue_eur": 25_000_000,
        "processes_personal_data": True,
        "has_supply_chain_abroad": True,
        "is_critical_infrastructure_sector": True,
    },
    {
        "employee_count": 1,
        "industry": "consulting",
        "annual_revenue_eur": 80_000,
        "processes_personal_data": True,
        "processing_is_occasional": True,
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _poll_until_done(
    user: HttpUser,
    job_id: str,
    *,
    poll_interval: float = 3.0,
    timeout: float = 900.0,  # 15 min max — gpt-4o can be slow under load
) -> bool:
    """Poll /api/status/{job_id} until the job is completed or failed.

    Returns True if completed successfully, False otherwise.
    Each poll is recorded as a separate Locust request so the status-poll
    latency distribution appears in the report separately from the submit call.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        with user.client.get(
            f"/api/status/{job_id}",
            headers=_auth_headers(),
            name="/api/status/[job_id]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "")
                if status == "completed":
                    resp.success()
                    return True
                if status in ("failed", "partial"):
                    resp.failure(f"Job {job_id} ended with status={status}")
                    return False
                resp.success()  # still running — mark as success, keep polling
            elif resp.status_code == 404:
                resp.failure(f"Job {job_id} not found")
                return False
            else:
                resp.failure(f"Unexpected status code: {resp.status_code}")

        time.sleep(poll_interval)

    logger.warning("Job %s did not complete within %.0f s", job_id, timeout)
    return False


# ── User classes ──────────────────────────────────────────────────────────────

class PublicUser(HttpUser):
    """
    No authentication required. Models anonymous traffic and top-of-funnel usage.

    Weight: 60 — most real traffic will be public visitors.
    """

    weight = 60
    wait_time = between(1, 4)

    @task(3)
    @tag("public", "health")
    def health_check(self):
        with self.client.get(
            "/api/health", name="/api/health", catch_response=True
        ) as resp:
            if resp.status_code == 200:
                body = resp.json()
                if body.get("status") not in ("ok", "degraded"):
                    resp.failure("Unexpected health status: " + str(body))
                else:
                    resp.success()
            else:
                resp.failure(f"Health check returned {resp.status_code}")

    @task(5)
    @tag("public", "quick-check")
    def quick_check(self):
        """
        /api/quick-check runs only the deterministic threshold engine — no LLM,
        no DB. This is the cheapest endpoint and should handle the highest load.
        """
        payload = random.choice(_QUICK_CHECK_PAYLOADS)
        with self.client.post(
            "/api/quick-check",
            json=payload,
            name="/api/quick-check",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "applicable" not in data:
                    resp.failure("Response missing 'applicable' key")
                else:
                    resp.success()
            elif resp.status_code == 429:
                resp.success()  # rate-limited is expected behaviour, not a failure
            else:
                resp.failure(f"quick-check returned {resp.status_code}: {resp.text[:200]}")

    @task(1)
    @tag("public", "plans")
    def list_plans(self):
        self.client.get("/api/plans", name="/api/plans")

    @task(1)
    @tag("public", "regulations")
    def list_regulations(self):
        self.client.get("/api/regulations", name="/api/regulations")


class DiagnosticUser(HttpUser):
    """
    Authenticated user with no subscription.
    Runs the full pipeline end-to-end and receives the diagnostic-only report.

    Requires COMPLIO_AUTH_TOKEN. Skipped (abstract=True) when not set.

    Weight: 5
    """

    weight = 5
    abstract = not bool(_AUTH_TOKEN)
    # Long wait between tasks — each analysis takes 1-10 min.
    wait_time = between(30, 120)

    def on_start(self):
        if not _AUTH_TOKEN:
            logger.warning(
                "DiagnosticUser: COMPLIO_AUTH_TOKEN not set — tasks will be no-ops."
            )

    @task
    @tag("auth", "pipeline", "expensive")
    def full_pipeline(self):
        if not _AUTH_TOKEN:
            return

        profile = random.choice(_PROFILES).copy()
        # Randomise company name so jobs are unique and don't hit the idempotency cache
        profile["company_name"] = f"{profile['company_name']} Load-{random.randint(1000, 9999)}"

        # 1. Submit analysis
        with self.client.post(
            "/api/analyze",
            json={"profile": profile},
            headers=_auth_headers(),
            name="/api/analyze",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                job_id = resp.json().get("job_id")
                if not job_id:
                    resp.failure("No job_id in response")
                    return
                resp.success()
            elif resp.status_code == 402:
                # Stripe/subscription gate — expected in production without a sub
                resp.success()
                return
            elif resp.status_code == 429:
                resp.success()  # rate-limited — expected, not a bug
                return
            else:
                resp.failure(f"analyze returned {resp.status_code}: {resp.text[:300]}")
                return

        # 2. Poll until done
        completed = _poll_until_done(self, job_id)
        if not completed:
            return

        # 3. Fetch the (diagnostic-only) report
        with self.client.get(
            f"/api/report/{job_id}",
            headers=_auth_headers(),
            name="/api/report/[job_id]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                # Validate diagnostic stripping: unsubscribed users should get empty lists
                if data.get("diagnostic_only"):
                    if data.get("gap_analysis") or data.get("action_plan"):
                        resp.failure(
                            "diagnostic_only=True but gap_analysis/action_plan not stripped"
                        )
                    else:
                        resp.success()
                else:
                    # Subscribed user or Stripe disabled — full report expected
                    resp.success()
            else:
                resp.failure(f"get_report returned {resp.status_code}: {resp.text[:300]}")


class StatusPollerUser(HttpUser):
    """
    Simulates the frontend polling /api/status every 2-3 seconds during
    an active analysis. Models the thundering-herd problem when many users
    start an analysis at the same time and all begin polling simultaneously.

    Requires COMPLIO_AUTH_TOKEN. Skipped (abstract=True) when not set.

    Weight: 35
    """

    weight = 35
    abstract = not bool(_AUTH_TOKEN)
    wait_time = between(2, 4)

    # Shared seed job_id — all StatusPollerUsers hit the same job.
    _seed_job_id: str = os.environ.get("COMPLIO_POLL_JOB_ID", "")

    def on_start(self):
        if not _AUTH_TOKEN:
            logger.warning(
                "StatusPollerUser: COMPLIO_AUTH_TOKEN not set — tasks will be no-ops."
            )
        if not self._seed_job_id:
            logger.warning(
                "StatusPollerUser: COMPLIO_POLL_JOB_ID not set. "
                "Set it to a valid job_id for meaningful results. "
                "The 404 responses will be recorded as failures."
            )

    @task
    @tag("auth", "polling")
    def poll_status(self):
        if not _AUTH_TOKEN:
            return

        job_id = self._seed_job_id or "nonexistent-job-for-baseline"
        with self.client.get(
            f"/api/status/{job_id}",
            headers=_auth_headers(),
            name="/api/status/[job_id]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 202):
                resp.success()
            elif resp.status_code == 404 and not self._seed_job_id:
                # No seed job set — 404 is expected, don't count as failure
                resp.success()
            else:
                resp.failure(f"poll_status returned {resp.status_code}")


# ── Event hooks ───────────────────────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    sep = "=" * 60
    token_info = ("set (" + _AUTH_TOKEN[:12] + "...)") if _AUTH_TOKEN else "NOT SET - auth tasks skipped"
    poll_info   = StatusPollerUser._seed_job_id or "NOT SET - StatusPollerUser will 404"
    print(f"\n{sep}")
    print("  Complio Load Test")
    print(sep)
    print(f"  Host:        {environment.host}")
    print(f"  Auth token:  {token_info}")
    print(f"  Poll job id: {poll_info}")
    print(sep)
    print("  User classes:")
    print("  PublicUser (weight=60)       - health, quick-check, plans, regulations")
    print("  DiagnosticUser (weight=5)    - full pipeline: analyze -> poll -> report [EXPENSIVE]")
    print("  StatusPollerUser (weight=35) - concurrent status polling")
    print("  Tag filters (--tags): public | expensive | polling")
    print(sep + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats
    total = stats.total
    print("\n" + "=" * 60)
    print("  Test complete")
    print("=" * 60)
    print(f"  Total requests:  {total.num_requests}")
    print(f"  Failures:        {total.num_failures}  ({100 * total.fail_ratio:.1f}%)")
    print(f"  Median RPS:      {total.current_rps:.1f}")
    print(f"  p50 latency:     {total.get_response_time_percentile(0.5):.0f} ms")
    print(f"  p95 latency:     {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  p99 latency:     {total.get_response_time_percentile(0.99):.0f} ms")
    print("=" * 60 + "\n")
