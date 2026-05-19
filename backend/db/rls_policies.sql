-- Supabase Row Level Security (RLS) policies for Complio
-- Run this in the Supabase SQL Editor after creating your tables.
-- The backend uses service_role (bypasses RLS) — these policies protect
-- any direct Supabase client access from the frontend or external tools.

-- ─────────────────────────────────────────────────────────────────────────────
-- Enable RLS on all user-data tables
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.profiles             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gap_items            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_items         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_completions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expert_review_requests ENABLE ROW LEVEL SECURITY;

-- Jobs and rate_limit_events are internal — no direct client access
ALTER TABLE public.jobs                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rate_limit_events    ENABLE ROW LEVEL SECURITY;

-- Admin-only table — no user access
ALTER TABLE public.pending_regulation_updates ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────────────────────────────────────
-- profiles — users can read and update only their own row
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "profiles: own row only"
    ON public.profiles
    FOR ALL
    USING (id = auth.uid()::text)
    WITH CHECK (id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- companies — users can CRUD only their own companies
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "companies: own rows only"
    ON public.companies
    FOR ALL
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- reports — readable only through user's own companies
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "reports: via own companies"
    ON public.reports
    FOR SELECT
    USING (
        company_id IN (
            SELECT id FROM public.companies WHERE user_id = auth.uid()::text
        )
    );

-- ─────────────────────────────────────────────────────────────────────────────
-- gap_items — readable only through user's own reports
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "gap_items: via own reports"
    ON public.gap_items
    FOR SELECT
    USING (
        report_id IN (
            SELECT r.id FROM public.reports r
            JOIN public.companies c ON r.company_id = c.id
            WHERE c.user_id = auth.uid()::text
        )
    );

-- ─────────────────────────────────────────────────────────────────────────────
-- action_items — owned via company
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "action_items: via own companies"
    ON public.action_items
    FOR ALL
    USING (
        company_id IN (
            SELECT id FROM public.companies WHERE user_id = auth.uid()::text
        )
    )
    WITH CHECK (
        company_id IN (
            SELECT id FROM public.companies WHERE user_id = auth.uid()::text
        )
    );

-- ─────────────────────────────────────────────────────────────────────────────
-- notifications — own rows only
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "notifications: own rows only"
    ON public.notifications
    FOR ALL
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- subscriptions — own row only
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "subscriptions: own row only"
    ON public.subscriptions
    FOR SELECT
    USING (user_id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- action_completions — own rows only
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "action_completions: own rows only"
    ON public.action_completions
    FOR ALL
    USING (user_id = auth.uid()::text)
    WITH CHECK (user_id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- expert_review_requests — own rows only
-- ─────────────────────────────────────────────────────────────────────────────

CREATE POLICY "expert_review_requests: own rows only"
    ON public.expert_review_requests
    FOR SELECT
    USING (user_id = auth.uid()::text);

-- ─────────────────────────────────────────────────────────────────────────────
-- Internal tables — no direct client access (service_role only)
-- No SELECT/INSERT/UPDATE/DELETE policies = only service_role can access
-- ─────────────────────────────────────────────────────────────────────────────

-- jobs, rate_limit_events, pending_regulation_updates: no policies added
-- (RLS enabled but no USING clause = all client requests denied by default)
