"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Trash2, AlertTriangle, Shield, Database, User, Lock, CheckCircle2, Loader2, Smartphone, X } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiDelete(path: string, token: string) {
  const res = await fetch(`${API}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

function Section({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 mb-6">
      {children}
    </div>
  );
}

function SectionHeader({ icon, title, sub }: { icon: React.ReactNode; title: string; sub?: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500/10">
        {icon}
      </div>
      <div>
        <p className="text-sm font-semibold text-white">{title}</p>
        {sub && <p className="text-xs text-slate-500">{sub}</p>}
      </div>
    </div>
  );
}

export default function AccountSettingsPage() {
  const router = useRouter();

  // Profile state
  const [email, setEmail]             = useState("");
  const [currentName, setCurrentName] = useState("");
  const [name, setName]               = useState("");
  const [nameLoading, setNameLoading] = useState(false);
  const [nameSuccess, setNameSuccess] = useState(false);
  const [nameError, setNameError]     = useState<string | null>(null);

  // Password state
  const [newPassword, setNewPassword]   = useState("");
  const [confirmPw, setConfirmPw]       = useState("");
  const [pwLoading, setPwLoading]       = useState(false);
  const [pwSuccess, setPwSuccess]       = useState(false);
  const [pwError, setPwError]           = useState<string | null>(null);

  // Delete state
  const [confirm, setConfirm]     = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError]     = useState<string | null>(null);

  // MFA state
  const [factors, setFactors]             = useState<{ id: string; status: string }[]>([]);
  const [factorsLoading, setFactorsLoading] = useState(true);
  const [enrolling, setEnrolling]         = useState(false);
  const [qrCode, setQrCode]               = useState<string | null>(null);
  const [secret, setSecret]               = useState<string | null>(null);
  const [pendingFactorId, setPendingFactorId] = useState<string | null>(null);
  const [mfaCode, setMfaCode]             = useState("");
  const [mfaLoading, setMfaLoading]       = useState(false);
  const [mfaError, setMfaError]           = useState<string | null>(null);
  const [mfaSuccess, setMfaSuccess]       = useState(false);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      setEmail(user?.email ?? "");
      const n = user?.user_metadata?.name ?? "";
      setCurrentName(n);
      setName(n);
    });
  }, []);

  const loadFactors = async () => {
    const supabase = createClient();
    const { data } = await supabase.auth.mfa.listFactors();
    setFactors(data?.totp ?? []);
    setFactorsLoading(false);
  };

  useEffect(() => {
    loadFactors();
  }, []);

  const handleStartEnroll = async () => {
    setMfaError(null);
    setMfaLoading(true);
    try {
      const supabase = createClient();
      const { data: list } = await supabase.auth.mfa.listFactors();
      const unverified = list?.totp.find((f) => (f.status as string) === "unverified");
      if (unverified) {
        await supabase.auth.mfa.unenroll({ factorId: unverified.id });
      }
      const { data, error } = await supabase.auth.mfa.enroll({ factorType: "totp", issuer: "Complio" });
      if (error) throw error;
      setQrCode(data.totp.qr_code);
      setSecret(data.totp.secret);
      setPendingFactorId(data.id);
      setEnrolling(true);
    } catch (e: unknown) {
      setMfaError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setMfaLoading(false);
    }
  };

  const handleCancelEnroll = async () => {
    if (pendingFactorId) {
      const supabase = createClient();
      await supabase.auth.mfa.unenroll({ factorId: pendingFactorId }).catch(() => {});
    }
    setEnrolling(false);
    setQrCode(null);
    setSecret(null);
    setPendingFactorId(null);
    setMfaCode("");
    setMfaError(null);
  };

  const handleConfirmEnroll = async (e: FormEvent) => {
    e.preventDefault();
    if (mfaCode.length !== 6 || !pendingFactorId) return;
    setMfaLoading(true);
    setMfaError(null);
    try {
      const supabase = createClient();
      const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({ factorId: pendingFactorId });
      if (challengeError) throw challengeError;
      const { error: verifyError } = await supabase.auth.mfa.verify({
        factorId: pendingFactorId,
        challengeId: challenge.id,
        code: mfaCode,
      });
      if (verifyError) throw verifyError;
      setEnrolling(false);
      setQrCode(null);
      setSecret(null);
      setPendingFactorId(null);
      setMfaCode("");
      setMfaSuccess(true);
      setTimeout(() => setMfaSuccess(false), 4000);
      await loadFactors();
    } catch {
      setMfaError("Code ungültig. Bitte erneut versuchen.");
    } finally {
      setMfaLoading(false);
    }
  };

  const handleUnenroll = async (factorId: string) => {
    setMfaLoading(true);
    setMfaError(null);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.mfa.unenroll({ factorId });
      if (error) throw error;
      await loadFactors();
    } catch (e: unknown) {
      setMfaError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setMfaLoading(false);
    }
  };

  const getToken = async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error("Nicht angemeldet");
    return session.access_token;
  };

  const handleSaveName = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setNameLoading(true);
    setNameError(null);
    setNameSuccess(false);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({ data: { name: name.trim() } });
      if (error) throw error;
      setCurrentName(name.trim());
      setNameSuccess(true);
      setTimeout(() => setNameSuccess(false), 3000);
    } catch (e: unknown) {
      setNameError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) { setPwError("Mindestens 8 Zeichen erforderlich."); return; }
    if (newPassword !== confirmPw) { setPwError("Passwörter stimmen nicht überein."); return; }
    setPwLoading(true);
    setPwError(null);
    setPwSuccess(false);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw error;
      setNewPassword("");
      setConfirmPw("");
      setPwSuccess(true);
      setTimeout(() => setPwSuccess(false), 4000);
    } catch (e: unknown) {
      setPwError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setPwLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (confirm !== "mein konto löschen") return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      const token = await getToken();
      await apiDelete("/api/account", token);
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push("/");
    } catch (e: unknown) {
      setDeleteError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-2xl font-bold text-white mb-2">Kontoeinstellungen</h1>
        <p className="text-sm text-slate-500 mb-10">Profil, Passwort und Datenschutz verwalten.</p>

        {/* Name */}
        <Section>
          <SectionHeader icon={<User className="h-4 w-4 text-brand-400" />} title="Profil" sub="Ihre Kontodaten" />
          <div className="flex flex-col gap-1.5 mb-4">
            <label className="text-xs text-slate-500">E-Mail-Adresse</label>
            <input
              type="email"
              value={email}
              readOnly
              className="w-full rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-2.5 text-sm text-slate-400 outline-none cursor-default select-all"
            />
            <p className="text-xs text-slate-600">Ihre Anmelde-E-Mail-Adresse kann nicht geändert werden.</p>
          </div>
          <form onSubmit={handleSaveName} className="flex flex-col gap-3">
            <label className="text-xs text-slate-500 -mb-1">Anzeigename</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ihr Name"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
            />
            {nameError && (
              <p className="text-xs text-red-400">{nameError}</p>
            )}
            {nameSuccess && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" /> Name gespeichert
              </div>
            )}
            <button
              type="submit"
              disabled={nameLoading || !name.trim() || name.trim() === currentName}
              className="self-start rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {nameLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {nameLoading ? "Wird gespeichert…" : "Speichern"}
            </button>
          </form>
        </Section>

        {/* Password */}
        <Section>
          <SectionHeader icon={<Lock className="h-4 w-4 text-brand-400" />} title="Passwort ändern" sub="Mindestens 8 Zeichen" />
          <form onSubmit={handleChangePassword} className="flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-slate-500">Neues Passwort</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Mind. 8 Zeichen"
                autoComplete="new-password"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-slate-500">Passwort bestätigen</label>
              <input
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                placeholder="Passwort wiederholen"
                autoComplete="new-password"
                className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
              />
            </div>
            {pwError && <p className="text-xs text-red-400">{pwError}</p>}
            {pwSuccess && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle2 className="h-3.5 w-3.5" /> Passwort erfolgreich geändert
              </div>
            )}
            <button
              type="submit"
              disabled={pwLoading || !newPassword || !confirmPw}
              className="self-start rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {pwLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {pwLoading ? "Wird gespeichert…" : "Passwort ändern"}
            </button>
          </form>
        </Section>

        {/* Two-factor authentication */}
        <Section>
          <SectionHeader
            icon={<Smartphone className="h-4 w-4 text-cyan-400" />}
            title="Zwei-Faktor-Authentifizierung"
            sub="Zusätzlicher Schutz für Ihr Konto"
          />

          {mfaError && <p className="text-xs text-red-400 mb-3">{mfaError}</p>}
          {mfaSuccess && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 mb-3">
              <CheckCircle2 className="h-3.5 w-3.5" /> Zwei-Faktor-Authentifizierung aktiviert
            </div>
          )}

          {!factorsLoading && !enrolling && (
            <div className="flex flex-col gap-3">
              {factors.filter((f) => f.status === "verified").map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between rounded-xl border border-white/[0.05] bg-white/[0.02] px-4 py-3"
                >
                  <div className="flex items-center gap-2 text-sm text-slate-300">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Authenticator-App aktiv
                  </div>
                  <button
                    type="button"
                    onClick={() => handleUnenroll(f.id)}
                    disabled={mfaLoading}
                    className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors disabled:opacity-40"
                  >
                    <X className="h-3.5 w-3.5" /> Deaktivieren
                  </button>
                </div>
              ))}
              {factors.filter((f) => f.status === "verified").length === 0 && (
                <button
                  type="button"
                  onClick={handleStartEnroll}
                  disabled={mfaLoading}
                  className="self-start rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {mfaLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Zwei-Faktor-Authentifizierung aktivieren
                </button>
              )}
            </div>
          )}

          {enrolling && qrCode && (
            <form onSubmit={handleConfirmEnroll} className="flex flex-col gap-4">
              <p className="text-xs text-slate-500">
                Scannen Sie den QR-Code mit einer Authenticator-App (z. B. Google Authenticator, Authy)
                und geben Sie den 6-stelligen Code ein.
              </p>
              <img
                src={`data:image/svg+xml;utf8,${encodeURIComponent(qrCode)}`}
                alt="QR-Code für Authenticator-App"
                className="h-40 w-40 rounded-lg bg-white p-2"
              />
              {secret && (
                <p className="text-xs text-slate-600">
                  Manuelle Eingabe: <span className="font-mono text-slate-400 select-all">{secret}</span>
                </p>
              )}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-slate-500">Bestätigungscode</label>
                <input
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ""))}
                  placeholder="000000"
                  className="w-full max-w-[140px] rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white tracking-widest placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={mfaLoading || mfaCode.length !== 6}
                  className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {mfaLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Bestätigen
                </button>
                <button
                  type="button"
                  onClick={handleCancelEnroll}
                  disabled={mfaLoading}
                  className="rounded-xl px-5 py-2.5 text-sm font-semibold text-slate-400 hover:text-slate-300 transition-colors disabled:opacity-40"
                >
                  Abbrechen
                </button>
              </div>
            </form>
          )}
        </Section>

        {/* GDPR rights */}
        <Section>
          <SectionHeader icon={<Shield className="h-4 w-4 text-blue-400" />} title="Ihre Datenschutzrechte (DSGVO)" sub="Art. 15–17 DSGVO" />
          <div className="grid sm:grid-cols-2 gap-3 text-xs text-slate-400">
            {[
              { right: "Auskunft (Art. 15)", desc: "Welche Daten wir über Sie speichern" },
              { right: "Berichtigung (Art. 16)", desc: "Unrichtige Daten korrigieren lassen" },
              { right: "Löschung (Art. 17)", desc: "Ihre Daten vollständig löschen" },
              { right: "Datenübertragbarkeit (Art. 20)", desc: "Ihre Daten im maschinenlesbaren Format" },
            ].map(({ right, desc }) => (
              <div key={right} className="rounded-lg border border-white/[0.05] bg-white/[0.02] p-3">
                <p className="font-semibold text-slate-300 mb-0.5">{right}</p>
                <p className="text-slate-600">{desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-600">
            Für Auskunft oder Datenübertragbarkeit wenden Sie sich an:{" "}
            <a href="mailto:datenschutz@complio.de" className="text-brand-400 hover:text-brand-300">datenschutz@complio.de</a>
          </p>
        </Section>

        {/* Data overview */}
        <Section>
          <SectionHeader icon={<Database className="h-4 w-4 text-purple-400" />} title="Gespeicherte Daten" />
          <div className="space-y-2 text-xs text-slate-400">
            {[
              { label: "Unternehmensprofile",    retention: "Bis zur manuellen Löschung" },
              { label: "Compliance-Berichte",    retention: "Bis zur manuellen Löschung" },
              { label: "Hochgeladene Dokumente", retention: "7 Tage, dann automatische Löschung" },
              { label: "Rechnungsdaten",         retention: "10 Jahre (§ 147 AO)" },
              { label: "Server-Logs",            retention: "30 Tage" },
            ].map(({ label, retention }) => (
              <div key={label} className="flex justify-between items-start gap-4 rounded-lg border border-white/[0.04] px-3 py-2">
                <span className="text-slate-300">{label}</span>
                <span className="text-slate-600 text-right flex-shrink-0">{retention}</span>
              </div>
            ))}
          </div>
        </Section>

        {/* Danger zone */}
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/10">
              <Trash2 className="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-red-400">Konto löschen</p>
              <p className="text-xs text-slate-500">Nicht rückgängig zu machen</p>
            </div>
          </div>

          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 mb-5 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-300/80">
              Hiermit werden Ihr Konto, alle Unternehmensprofile, alle Compliance-Berichte und alle Benachrichtigungen
              dauerhaft gelöscht. Rechnungsdaten werden gemäß gesetzlicher Aufbewahrungspflichten (§ 147 AO, 10 Jahre) aufbewahrt.
            </p>
          </div>

          {deleteError && (
            <div className="rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-2.5 mb-4 text-xs text-red-400">
              {deleteError}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">
                Zum Bestätigen eingeben: <span className="font-mono text-slate-300">mein konto löschen</span>
              </label>
              <input
                type="text"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="mein konto löschen"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:border-red-500/50 focus:outline-none focus:ring-1 focus:ring-red-500/30"
              />
            </div>
            <button
              type="button"
              disabled={confirm !== "mein konto löschen" || deleteLoading}
              onClick={handleDeleteAccount}
              className="w-full rounded-xl bg-red-600/80 py-2.5 text-sm font-semibold text-white hover:bg-red-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {deleteLoading && <Loader2 className="h-4 w-4 animate-spin" />}
              {deleteLoading ? "Wird gelöscht…" : "Konto und alle Daten dauerhaft löschen"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
