"""
Apply Supabase Row-Level Security policies to production database.

Usage:
    cd backend
    python scripts/apply_rls.py              # apply RLS
    python scripts/apply_rls.py --verify     # verify RLS is enabled
    python scripts/apply_rls.py --dry-run    # print SQL without running it

Requires DATABASE_URL in backend/.env or environment.
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RLS_SQL_PATH = Path(__file__).parent.parent / "db" / "rls_policies.sql"

VERIFY_SQL = """
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('companies', 'reports', 'jobs', 'notifications', 'subscriptions',
                    'action_completions', 'expert_review_requests', 'rate_limit_events',
                    'alembic_version')
ORDER BY tablename;
"""


def load_rls_sql() -> str:
    if not RLS_SQL_PATH.exists():
        print(f"ERROR: RLS SQL file not found at {RLS_SQL_PATH}")
        sys.exit(1)
    return RLS_SQL_PATH.read_text(encoding="utf-8")


def get_connection_string() -> str:
    from config import settings
    url = settings.database_url
    if not url:
        print("ERROR: DATABASE_URL not set in .env")
        sys.exit(1)
    # asyncpg uses postgresql+asyncpg:// — psycopg2/sync needs postgresql://
    return url.replace("postgresql+asyncpg://", "postgresql://").replace("+asyncpg", "")


def apply_rls(dry_run: bool = False) -> None:
    sql = load_rls_sql()

    if dry_run:
        print("=== DRY RUN — SQL that would be executed ===\n")
        print(sql)
        return

    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    db_url = get_connection_string()
    print("Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    print("Applying RLS policies...")
    try:
        cur.execute(sql)
        print("RLS policies applied successfully.")
    except Exception as exc:
        print(f"ERROR applying RLS: {exc}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


def verify_rls() -> None:
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    db_url = get_connection_string()
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(VERIFY_SQL)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"\n{'Table':<35} {'RLS Enabled'}")
    print("-" * 50)
    all_enabled = True
    for schema, table, rls_enabled in rows:
        status = "YES" if rls_enabled else "NO"
        if not rls_enabled:
            all_enabled = False
        print(f"{table:<35} {status}")

    print()
    if all_enabled:
        print("All tables have RLS enabled.")
    else:
        print("WARNING: Some tables do not have RLS enabled. Run: python scripts/apply_rls.py")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply or verify Supabase RLS policies")
    parser.add_argument("--verify", action="store_true", help="Verify RLS is enabled without applying")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    args = parser.parse_args()

    if args.verify:
        verify_rls()
    else:
        apply_rls(dry_run=args.dry_run)
