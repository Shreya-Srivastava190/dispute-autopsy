"use client";

import { useEffect, useState } from "react";

type Dispute = {
  dispute_id: string;
  amount: number;
  currency: string;
  reason: string;
};

type Evidence = {
  type: string;
  finding: string;
  strength: string;
};

type TimelineEvent = {
  timestamp: string;
  event: string;
  source: string;
};

type ClaimVsEvidence = {
  customer_claim: string;
  supporting_evidence: string;
  contradiction: string;
};

type AIReport = {
  summary: string;
  key_findings: string[];
  customer_claim_assessment: string;
  claim_vs_evidence?: ClaimVsEvidence;
  recommended_action: string;
  investigation_notes: string;
};

type NetworkRiskFlag = {
  type: string;
  finding: string;
};

type NetworkRisk = {
  risk_level: string;
  customer_dispute_count: number;
  merchant_dispute_count: number;
  distinct_merchants_disputed?: number;
  flags: NetworkRiskFlag[];
};

type CourierRiskFlag = {
  type: string;
  finding: string;
};

type CourierRisk = {
  courier: string | null;
  risk_level: string;
  courier_dispute_count: number;
  non_delivery_count: number;
  confidence?: string;
  flags: CourierRiskFlag[];
};

type InvestigationStage = {
  day: number;
  timestamp: string;
  title: string;
  description: string;
};

type Autopsy = {
  dispute_id: string;
  amount: number;
  currency: string;
  reason: string;
  evidence_score: number;
  recommendation: string;
  override_reason?: string | null;
  timeline: TimelineEvent[];
  evidence: Evidence[];
  network_risk?: NetworkRisk;
  courier_risk?: CourierRisk;
  urgency?: Urgency | null;
  merchant_spike?: MerchantSpike;
  risk_graph?: RiskGraph | null;
  ai_report?: AIReport;
};

type DashboardRow = {
  dispute_id: string;
  amount: number;
  currency: string;
  evidence_score: number;
  recommendation: string;
  risk_level: string;
};

type CourierBreakdownRow = {
  courier: string;
  dispute_count: number;
  non_delivery_count: number;
  failure_rate_pct: number;
  confidence?: string;
  flagged: boolean;
};

type FlaggedCustomer = {
  customer_id: string;
  dispute_ids: string[];
  distinct_merchants: number;
};

type MerchantSpikeSummary = {
  merchant_id: string;
  dispute_count: number;
  window_days: number;
};

type MerchantSpike = {
  is_spike: boolean;
  window_days: number | null;
  dispute_count: number;
  confidence?: string;
  finding?: string;
};

type GraphNode = {
  id: string;
  type: "customer" | "merchant";
  label: string;
};

type GraphEdge = {
  source: string;
  target: string;
  dispute_id: string;
  reason: string;
  filed_at?: string;
  amount?: number;
  is_current: boolean;
};

type RiskGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

type PlatformRiskSignals = {
  flagged_customers: FlaggedCustomer[];
  flagged_couriers: CourierBreakdownRow[];
  merchant_spikes: MerchantSpikeSummary[];
};

type Dashboard = {
  total_disputes: number;
  total_amount: number;
  currency: string;
  by_recommendation: Record<string, number>;
  flagged_risk_count: number;
  disputes: DashboardRow[];
  courier_breakdown: CourierBreakdownRow[];
  platform_risk_signals: PlatformRiskSignals;
};

type TriageRow = {
  dispute_id: string;
  amount: number;
  currency: string;
  evidence_score: number;
  recommendation: string;
  urgency_level: string;
  hours_remaining: number | null;
  priority_score: number;
};

type TriageQueue = {
  queue: TriageRow[];
};

type Urgency = {
  hours_remaining: number;
  level: string;
};

type SimulatedDispute = {
  dispute_id: string;
  reason: string;
  amount: number;
  customer_id: string;
  merchant_id: string;
};

type SimulationResult = {
  dispute: SimulatedDispute;
  network_risk: NetworkRisk;
  merchant_spike: MerchantSpike;
  total_simulated: number;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [view, setView] = useState<
    "inbox" | "dashboard" | "triage" | "simulate"
  >(
    "inbox"
  );

  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [disputesLoading, setDisputesLoading] = useState(true);
  const [disputesError, setDisputesError] = useState("");

  const [selected, setSelected] = useState<string | null>(null);
  const [autopsy, setAutopsy] = useState<Autopsy | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState("");

  useEffect(() => {
    async function loadDisputes() {
      setDisputesLoading(true);
      setDisputesError("");

      try {
        const response = await fetch(`${API}/disputes`);

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data: Dispute[] = await response.json();
        setDisputes(data);
      } catch (err) {
        console.error(err);
        setDisputesError(
          "Could not load disputes. Make sure the backend is running on port 8000."
        );
      } finally {
        setDisputesLoading(false);
      }
    }

    loadDisputes();
  }, []);

  useEffect(() => {
    if (view !== "dashboard" || dashboard) {
      return;
    }

    async function loadDashboard() {
      setDashboardLoading(true);
      setDashboardError("");

      try {
        const response = await fetch(`${API}/dashboard`);

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data: Dashboard = await response.json();
        setDashboard(data);
      } catch (err) {
        console.error(err);
        setDashboardError(
          "Could not load dashboard. Make sure the backend is running on port 8000."
        );
      } finally {
        setDashboardLoading(false);
      }
    }

    loadDashboard();
  }, [view, dashboard]);

  const [triage, setTriage] = useState<TriageQueue | null>(null);
  const [triageLoading, setTriageLoading] = useState(false);
  const [triageError, setTriageError] = useState("");

  useEffect(() => {
    if (view !== "triage" || triage) {
      return;
    }

    async function loadTriage() {
      setTriageLoading(true);
      setTriageError("");

      try {
        const response = await fetch(`${API}/triage`);

        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data: TriageQueue = await response.json();
        setTriage(data);
      } catch (err) {
        console.error(err);
        setTriageError(
          "Could not load triage queue. Make sure the backend is running on port 8000."
        );
      } finally {
        setTriageLoading(false);
      }
    }

    loadTriage();
  }, [view, triage]);


  async function investigate(disputeId: string) {
    setSelected(disputeId);
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API}/autopsy/${disputeId}`);

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data: Autopsy = await response.json();
      setAutopsy(data);
    } catch (err) {
      console.error(err);
      setError(
        "Could not connect to FastAPI. Make sure the backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatMoney(amount: number, currency: string) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  function generateEvidenceResponse(autopsy: Autopsy): string {
    const lines: string[] = [];

    // Build a natural, flowing paragraph from the strong evidence
    // findings — reads like something a merchant could paste directly,
    // not a bulleted internal report.
    const strongFindings = autopsy.evidence
      .filter((item) => item.strength === "strong")
      .map((item) => item.finding.replace(/\.$/, ""));

    const weakFindings = autopsy.evidence
      .filter((item) => item.strength === "weak")
      .map((item) => item.finding.replace(/\.$/, ""));

    let narrative = "";
    if (strongFindings.length > 0) {
      narrative += strongFindings.join(". ") + ".";
    }
    if (weakFindings.length > 0) {
      narrative +=
        (narrative ? " " : "") +
        "While " +
        weakFindings.join(", ").toLowerCase() +
        ", ";
    } else {
      narrative += " ";
    }

    const contradiction = autopsy.ai_report?.claim_vs_evidence?.contradiction;
    if (contradiction) {
      narrative += contradiction;
    } else if (autopsy.recommendation === "CONTEST") {
      narrative +=
        "the available evidence collectively contradicts the customer's claim.";
    } else if (autopsy.recommendation === "ACCEPT") {
      narrative +=
        "the available evidence does not sufficiently support contesting this dispute.";
    } else {
      narrative += "the available evidence is inconclusive on its own.";
    }

    lines.push(`Dispute ${autopsy.dispute_id} — ${formatMoney(autopsy.amount, autopsy.currency)}`);
    lines.push("");
    lines.push(narrative.trim());
    lines.push("");
    lines.push(`Recommended action: ${autopsy.recommendation}`);

    if (autopsy.override_reason) {
      lines.push(autopsy.override_reason);
    }

    if (
      autopsy.network_risk &&
      autopsy.network_risk.risk_level !== "low"
    ) {
      lines.push("");
      lines.push(
        "Platform Intelligence note: separate investigation context " +
          `identified ${autopsy.network_risk.flags
            .map((f) => f.type.replaceAll("_", " "))
            .join(" and ")} involving this customer or merchant. This ` +
          "signal does not affect the evidence-based recommendation above."
      );
    }

    lines.push("");
    lines.push("--- Full evidence record ---");
    autopsy.evidence.forEach((item, index) => {
      lines.push(`${index + 1}. [${item.strength}] ${item.finding}`);
    });
    lines.push("");
    lines.push("Timeline:");
    autopsy.timeline.forEach((event) => {
      const formatted = new Date(event.timestamp).toLocaleString("en-IN");
      lines.push(`- ${formatted}: ${event.event}`);
    });
    lines.push("");
    lines.push(
      `Evidence score: ${autopsy.evidence_score}/100 (deterministic, evidence-based scoring)`
    );

    return lines.join("\n");
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      {/* HEADER */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-5">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Dispute Autopsy
            </h1>

            <p className="text-sm text-slate-500">
              AI-powered payment dispute investigation
            </p>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex rounded-xl border bg-slate-50 p-1">
              <button
                onClick={() => setView("inbox")}
                className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
                  view === "inbox"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Inbox
              </button>

              <button
                onClick={() => setView("dashboard")}
                className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
                  view === "dashboard"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Dashboard
              </button>

              <button
                onClick={() => setView("triage")}
                className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
                  view === "triage"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Action Queue
              </button>

              <button
                onClick={() => setView("simulate")}
                className={`rounded-lg px-4 py-1.5 text-sm font-semibold transition ${
                  view === "simulate"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500"
                }`}
              >
                Scenario Lab
              </button>
            </div>

            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
              Investigation Engine Online
            </div>
          </div>
        </div>
      </header>

      {view === "dashboard" ? (
        <DashboardView
          dashboard={dashboard}
          loading={dashboardLoading}
          error={dashboardError}
          formatMoney={formatMoney}
        />
      ) : view === "triage" ? (
        <TriageView
          triage={triage}
          loading={triageLoading}
          error={triageError}
          formatMoney={formatMoney}
        />
      ) : view === "simulate" ? (
        <SimulateView formatMoney={formatMoney} />
      ) : (
      <>
      {/* BODY */}
      <div className="mx-auto grid max-w-7xl grid-cols-[320px_1fr] gap-6 px-8 py-8">
        {/* DISPUTE INBOX */}
        <aside className="h-fit overflow-hidden rounded-2xl border bg-white shadow-sm">
          <div className="border-b px-5 py-5">
            <h2 className="font-semibold">Dispute Inbox</h2>

            <p className="mt-1 text-sm text-slate-500">
              {disputesLoading
                ? "Loading disputes..."
                : `${disputes.length} dispute${
                    disputes.length === 1 ? "" : "s"
                  } requiring review`}
            </p>
          </div>

          <div className="p-3">
            {disputesError && (
              <div className="m-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {disputesError}
              </div>
            )}

            {disputes.map((dispute) => (
              <button
                key={dispute.dispute_id}
                onClick={() => investigate(dispute.dispute_id)}
                className={`w-full rounded-xl p-4 text-left transition ${
                  selected === dispute.dispute_id
                    ? "bg-slate-900 text-white"
                    : "hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">
                    {dispute.dispute_id}
                  </span>

                  <span
                    className={`rounded-full px-2 py-1 text-xs ${
                      selected === dispute.dispute_id
                        ? "bg-white/10 text-white"
                        : "bg-red-50 text-red-600"
                    }`}
                  >
                    New
                  </span>
                </div>

                <p
                  className={`mt-2 text-sm ${
                    selected === dispute.dispute_id
                      ? "text-slate-300"
                      : "text-slate-500"
                  }`}
                >
                  {dispute.reason.replaceAll("_", " ")}
                </p>

                <p className="mt-3 font-semibold">
                  {formatMoney(dispute.amount, dispute.currency)}
                </p>
              </button>
            ))}
          </div>
        </aside>

        {/* AUTOPSY */}
        <section>
          {error && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {!autopsy && !loading && (
            <div className="flex min-h-[600px] items-center justify-center rounded-2xl border bg-white shadow-sm">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-2xl">
                  🔍
                </div>

                <h2 className="text-xl font-semibold">
                  Select a dispute
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  Select a dispute from the inbox to run an autopsy.
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex min-h-[600px] items-center justify-center rounded-2xl border bg-white shadow-sm">
              <div className="text-center">
                <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />

                <h2 className="font-semibold">
                  Investigating dispute...
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  Checking payment, order, delivery and support evidence.
                </p>
              </div>
            </div>
          )}

          {autopsy && !loading && (
            <AutopsyView
              autopsy={autopsy}
              formatMoney={formatMoney}
              generateEvidenceResponse={generateEvidenceResponse}
            />
          )}
        </section>
      </div>
      </>
      )}
    </main>
  );
}

/* ------------------------------------------------ */
/* AUTOPSY VIEW */
/* ------------------------------------------------ */

function AutopsyView({
  autopsy,
  formatMoney,
  generateEvidenceResponse,
}: {
  autopsy: Autopsy;
  formatMoney: (amount: number, currency: string) => string;
  generateEvidenceResponse: (autopsy: Autopsy) => string;
}) {
  const [showResponse, setShowResponse] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [copied, setCopied] = useState(false);

  const responseText = generateEvidenceResponse(autopsy);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(responseText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Copy failed", err);
    }
  }

  const recommendationStyles: Record<string, string> = {
    CONTEST: "bg-green-100 text-green-700",
    REVIEW: "bg-yellow-100 text-yellow-700",
    ACCEPT: "bg-red-100 text-red-700",
  };

  const bannerStyles: Record<string, string> = {
    CONTEST: "border-green-200 bg-green-50",
    REVIEW: "border-yellow-200 bg-yellow-50",
    ACCEPT: "border-red-200 bg-red-50",
  };

  const badgeClass =
    recommendationStyles[autopsy.recommendation] ??
    "bg-slate-100 text-slate-700";

  const bannerClass =
    bannerStyles[autopsy.recommendation] ?? "border-slate-200 bg-slate-50";

  return (
    <div className="space-y-6">
      {/* TITLE */}
      <div>
        <div className="mb-2 flex items-center gap-2 text-sm text-slate-500">
          <span>Dispute Inbox</span>
          <span>/</span>
          <span>{autopsy.dispute_id}</span>
        </div>

        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              Dispute Autopsy
            </h2>

            <p className="mt-1 text-slate-500">
              Investigation report for {autopsy.dispute_id}
            </p>
          </div>

          <div
            className={`rounded-full px-5 py-2 text-sm font-bold ${badgeClass}`}
          >
            {autopsy.recommendation}
          </div>
        </div>
      </div>

      {/* STATS */}
      <div
        className={`grid gap-4 ${
          autopsy.urgency ? "grid-cols-4" : "grid-cols-3"
        }`}
      >
        <Stat
          label="Dispute Amount"
          value={formatMoney(autopsy.amount, autopsy.currency)}
        />

        <Stat
          label="Evidence Score"
          value={`${autopsy.evidence_score}/100`}
          highlight
        />

        <Stat
          label="Dispute Reason"
          value={autopsy.reason.replaceAll("_", " ")}
        />

        {autopsy.urgency && (
          <Stat
            label="Response Deadline"
            value={
              autopsy.urgency.hours_remaining > 0
                ? `${Math.round(autopsy.urgency.hours_remaining)}h left`
                : "Overdue"
            }
          />
        )}
      </div>

      {/* RECOMMENDATION */}
      <div className={`rounded-2xl border p-6 ${bannerClass}`}>
        <div className="flex items-start gap-4">
          <div className="text-2xl">
            {autopsy.recommendation === "CONTEST" ? "✓" : "!"}
          </div>

          <div>
            <h3 className="font-bold">
              Recommended action: {autopsy.recommendation}
            </h3>

            <p className="mt-1 text-sm leading-6 text-slate-600">
              {autopsy.ai_report?.recommended_action ||
                "Review the available evidence before responding."}
            </p>

            {autopsy.override_reason && (
              <div className="mt-3 rounded-lg bg-white/70 px-3 py-2 text-xs text-slate-600">
                <span className="font-bold uppercase tracking-wide text-slate-500">
                  Why this overrides the evidence score:
                </span>{" "}
                {autopsy.override_reason}
              </div>
            )}

            <div className="mt-3 rounded-lg bg-white/70 px-3 py-2 text-xs text-slate-600">
              <span className="font-bold uppercase tracking-wide text-slate-500">
                Why this recommendation:
              </span>{" "}
              {autopsy.evidence
                .filter((e) => e.strength === "strong")
                .slice(0, 3)
                .map((e) => e.type)
                .join(" → ") || "Evidence was weak or inconclusive"}
              {" → "}
              <span className="font-semibold">{autopsy.recommendation}</span>
            </div>

            <p className="mt-3 text-xs text-slate-500">
              This recommendation is decided by evidence alone. Platform
              Intelligence below is investigation context — it never
              changes the recommendation above.
            </p>
          </div>
        </div>
      </div>

      {/* PLATFORM INTELLIGENCE */}
      {(autopsy.network_risk?.flags.length ||
        (autopsy.courier_risk && autopsy.courier_risk.flags.length > 0) ||
        autopsy.merchant_spike?.is_spike) && (
        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-lg">🔎</span>
            <h3 className="font-bold">Platform Intelligence</h3>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Signals only visible when comparing this dispute against
            everything else on the platform — not something a single
            merchant could see on their own.
          </p>

          <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
            <span className="font-bold uppercase tracking-wide text-slate-500">
              What this is for:
            </span>{" "}
            helps investigators prioritize cases needing deeper review,
            detect repeated cross-merchant patterns, identify coordinated
            or recurring dispute behavior, and surface relationships
            invisible to any individual merchant.
          </div>

          <div className="mt-5 space-y-3">
            {autopsy.network_risk && autopsy.network_risk.flags.length > 0 && (
              <NetworkRiskCard networkRisk={autopsy.network_risk} />
            )}

            {autopsy.courier_risk && autopsy.courier_risk.flags.length > 0 && (
              <CourierRiskCard courierRisk={autopsy.courier_risk} />
            )}

            {autopsy.merchant_spike?.is_spike && (
              <div className="rounded-2xl border border-purple-200 bg-purple-50 p-6 text-purple-700">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold">Merchant Dispute Spike</h3>
                    <p className="mt-1 text-sm opacity-80">
                      A temporal clustering signal — different from
                      repeat-count checks, this looks at how tightly
                      disputes are bunched in time.
                    </p>
                  </div>
                  <div className="rounded-full bg-white/70 px-4 py-1 text-xs font-bold uppercase tracking-wide">
                    Spike detected
                  </div>
                </div>
                <p className="mt-4 rounded-lg bg-white/70 px-3 py-2 text-sm">
                  {autopsy.merchant_spike.finding}
                </p>
              </div>
            )}
          </div>

          {autopsy.risk_graph && (
            <div className="mt-4">
              <button
                onClick={() => setShowGraph((prev) => !prev)}
                className="text-sm font-semibold text-indigo-600 hover:text-indigo-800"
              >
                {showGraph ? "Hide relationships ↑" : "Explore relationships →"}
              </button>

              {showGraph && (
                <div className="mt-4">
                  <RiskGraphCard graph={autopsy.risk_graph} />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* EVIDENCE RESPONSE GENERATOR */}
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold">Evidence Response</h3>
            <p className="mt-1 text-sm text-slate-500">
              A submission-ready summary you can paste into your dispute
              response portal.
            </p>
          </div>

          <button
            onClick={() => setShowResponse((prev) => !prev)}
            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            {showResponse ? "Hide" : "Generate Evidence Response"}
          </button>
        </div>

        {showResponse && (
          <div className="mt-5">
            <div className="flex items-center justify-end">
              <button
                onClick={handleCopy}
                className="rounded-lg border px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                {copied ? "Copied ✓" : "Copy to clipboard"}
              </button>
            </div>

            <pre className="mt-2 max-h-96 overflow-y-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 font-mono text-xs leading-6 text-slate-700">
              {responseText}
            </pre>
          </div>
        )}
      </div>

      {/* AI SUMMARY */}
      {autopsy.ai_report && (
        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold text-white">
              AI
            </div>

            <div>
              <h3 className="font-bold">
                Investigator Summary
              </h3>

              <p className="text-sm text-slate-500">
                Evidence-grounded investigation
              </p>
            </div>
          </div>

          <p className="leading-7 text-slate-700">
            {autopsy.ai_report.summary}
          </p>

          {autopsy.ai_report.claim_vs_evidence && (
            <div className="mt-6">
              <h4 className="mb-3 font-semibold">Claim vs. Evidence</h4>
              <p className="mb-3 text-xs text-slate-400">
                What the customer said, in their own words, checked
                against the record.
              </p>

              <div className="space-y-2">
                <div className="rounded-xl border border-slate-200 bg-white p-3 text-sm">
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    Customer claim
                  </p>
                  <p className="mt-1 text-slate-700">
                    &ldquo;{autopsy.ai_report.claim_vs_evidence.customer_claim}
                    &rdquo;
                  </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-3 text-sm">
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    Supporting evidence
                  </p>
                  <p className="mt-1 text-slate-700">
                    {autopsy.ai_report.claim_vs_evidence.supporting_evidence}
                  </p>
                </div>

                <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm">
                  <p className="text-xs font-bold uppercase tracking-wide text-red-500">
                    Contradiction
                  </p>
                  <p className="mt-1 text-red-800">
                    {autopsy.ai_report.claim_vs_evidence.contradiction}
                  </p>
                </div>
              </div>
            </div>
          )}

          {autopsy.ai_report.key_findings &&
            autopsy.ai_report.key_findings.length > 0 && (
              <div className="mt-6">
                <h4 className="mb-3 font-semibold">Decision drivers</h4>
                <ul className="space-y-1.5 text-sm text-slate-700">
                  {autopsy.ai_report.key_findings.slice(0, 4).map(
                    (finding, index) => (
                      <li key={index} className="flex gap-2">
                        <span className="text-slate-400">•</span>
                        {finding}
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}
        </div>
      )}

      {/* TIMELINE */}
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <h3 className="font-bold">Evidence Timeline</h3>

        <div className="mt-6 space-y-6">
          {autopsy.timeline.map((event, index) => (
            <div
              key={`${event.timestamp}-${index}`}
              className="flex gap-4"
            >
              <div className="flex flex-col items-center">
                <div className="h-3 w-3 rounded-full bg-slate-900" />

                {index < autopsy.timeline.length - 1 && (
                  <div className="mt-2 h-12 w-px bg-slate-200" />
                )}
              </div>

              <div className="-mt-1">
                <p className="font-semibold">
                  {event.event}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {new Date(event.timestamp).toLocaleString(
                    "en-IN"
                  )}
                </p>

                <span className="mt-2 inline-block rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
                  {event.source}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* EVIDENCE */}
      <div className="rounded-2xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold">
              Evidence Analysis
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Evidence collected from the dispute record
            </p>
          </div>

          <div className="text-3xl font-bold">
            {autopsy.evidence_score}
            <span className="text-base font-normal text-slate-400">
              /100
            </span>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {autopsy.evidence.map((item, index) => {
            const iconStyles: Record<string, string> = {
              strong: "bg-green-100 text-green-700",
              supporting: "bg-blue-100 text-blue-700",
              weak: "bg-slate-100 text-slate-500",
              disqualifying: "bg-red-100 text-red-700",
            };

            const iconClass =
              iconStyles[item.strength] ?? "bg-slate-100 text-slate-500";

            return (
              <div
                key={`${item.type}-${index}`}
                className="flex gap-4 rounded-xl border p-4"
              >
                <div
                  className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${iconClass}`}
                >
                  {item.strength === "weak" || item.strength === "disqualifying"
                    ? "!"
                    : "✓"}
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold capitalize">
                      {item.type}
                    </p>

                    <span className="text-xs font-medium uppercase text-slate-400">
                      {item.strength}
                    </span>
                  </div>

                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    {item.finding}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}

/* ------------------------------------------------ */
/* NETWORK RISK CARD */
/* ------------------------------------------------ */

function NetworkRiskCard({ networkRisk }: { networkRisk: NetworkRisk }) {
  const levelStyles: Record<string, string> = {
    high: "border-red-200 bg-red-50 text-red-700",
    medium: "border-yellow-200 bg-yellow-50 text-yellow-700",
    low: "border-slate-200 bg-slate-50 text-slate-600",
  };

  const badgeClass = levelStyles[networkRisk.risk_level] ?? levelStyles.low;

  return (
    <div className={`rounded-2xl border p-6 ${badgeClass}`}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold">Network Risk</h3>
          <p className="mt-1 text-sm opacity-80">
            Pattern check across all disputes on file — separate from this
            dispute&apos;s own evidence.
          </p>
        </div>

        <div className="rounded-full bg-white/70 px-4 py-1 text-xs font-bold uppercase tracking-wide">
          {networkRisk.risk_level} risk
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-semibold">
            {networkRisk.customer_dispute_count}
          </span>{" "}
          dispute(s) from this customer
        </div>

        <div>
          <span className="font-semibold">
            {networkRisk.merchant_dispute_count}
          </span>{" "}
          dispute(s) against this merchant
        </div>
      </div>

      {networkRisk.flags.length > 0 && (
        <div className="mt-4 space-y-2">
          {networkRisk.flags.some(
            (f) => f.type === "cross_merchant_serial_disputer"
          ) && (
            <div className="rounded-lg border-2 border-current bg-white/70 px-3 py-2 text-sm font-semibold">
              ⚡ Cross-platform signal detected: the same customer has
              disputed multiple merchants — a pattern invisible within any
              single merchant&apos;s own data.
            </div>
          )}

          {networkRisk.flags.map((flag, index) => (
            <div
              key={`${flag.type}-${index}`}
              className="rounded-lg bg-white/70 px-3 py-2 text-sm"
            >
              {flag.finding}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------ */
/* COURIER RISK CARD */
/* ------------------------------------------------ */

function CourierRiskCard({ courierRisk }: { courierRisk: CourierRisk }) {
  return (
    <div className="rounded-2xl border border-orange-200 bg-orange-50 p-6 text-orange-700">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold">Courier Risk — {courierRisk.courier}</h3>
          <p className="mt-1 text-sm opacity-80">
            Fulfillment pattern check across merchants using this courier —
            not a fraud signal, a delivery-quality one.
          </p>
        </div>

        <div className="rounded-full bg-white/70 px-4 py-1 text-xs font-bold uppercase tracking-wide">
          {courierRisk.risk_level} risk
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="font-semibold">
            {courierRisk.courier_dispute_count}
          </span>{" "}
          dispute(s) linked to this courier
        </div>

        <div>
          <span className="font-semibold">
            {courierRisk.non_delivery_count}
          </span>{" "}
          were non-delivery
        </div>
      </div>

      {courierRisk.flags.length > 0 && (
        <div className="mt-4 space-y-2">
          {courierRisk.flags.map((flag, index) => (
            <div
              key={`${flag.type}-${index}`}
              className="rounded-lg bg-white/70 px-3 py-2 text-sm"
            >
              {flag.finding}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------ */
/* RISK GRAPH CARD */
/* ------------------------------------------------ */

function useIsNarrow(breakpoint = 480) {
  const [isNarrow, setIsNarrow] = useState(false);

  useEffect(() => {
    function check() {
      setIsNarrow(window.innerWidth < breakpoint);
    }
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, [breakpoint]);

  return isNarrow;
}

function RiskGraphCard({ graph }: { graph: RiskGraph }) {
  const merchants = graph.nodes.filter((n) => n.type === "merchant");
  const customer = graph.nodes.find((n) => n.type === "customer");
  const isNarrow = useIsNarrow();

  if (!customer || merchants.length === 0) {
    return null;
  }

  function formatShortDate(iso?: string) {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
    });
  }

  // Narrow screens: stack top-to-bottom (customer above, merchants
  // below) so labels have room instead of being squeezed sideways.
  // Wider screens: original left-to-right layout.
  const rowSpacing = isNarrow ? 110 : 90;
  const viewWidth = isNarrow ? 340 : 560;
  const height = isNarrow
    ? 110 + merchants.length * rowSpacing + 20
    : Math.max(180, merchants.length * rowSpacing + 40);

  const customerX = isNarrow ? viewWidth / 2 : 90;
  const customerY = isNarrow ? 50 : height / 2;
  const merchantX = isNarrow ? viewWidth / 2 : 460;

  const merchantPositions = merchants.map((m, i) => ({
    node: m,
    x: isNarrow ? merchantX : merchantX,
    y: isNarrow
      ? 130 + i * rowSpacing
      : 40 + i * rowSpacing + rowSpacing / 2,
  }));

  return (
    <div className="rounded-2xl border bg-white p-6 shadow-sm">
      <h3 className="font-bold">Dispute Relationship Graph</h3>
      <p className="mt-1 text-sm text-slate-500">
        Why this was flagged — this customer&apos;s disputes span more
        than one merchant. Only shown when there is more than one
        relationship to compare; a single-merchant case wouldn&apos;t
        need a graph.
      </p>

      <svg
        viewBox={`0 0 ${viewWidth} ${height}`}
        className="mt-4 w-full"
        style={{ maxHeight: isNarrow ? 420 : 320 }}
      >
        {(() => {
          // Group edges by their target merchant. When a customer has
          // MULTIPLE disputes with the SAME merchant (e.g. disp_001 and
          // disp_004 both against merch_501), those edges previously
          // resolved to the exact same line and label position and
          // rendered on top of each other, illegible. Each edge in a
          // group now gets a small perpendicular offset — proportional
          // to its position within the group — so same-merchant edges
          // fan out into parallel, readable lines instead of stacking.
          const edgesByTarget = new Map<string, typeof graph.edges>();
          for (const edge of graph.edges) {
            const list = edgesByTarget.get(edge.target) ?? [];
            list.push(edge);
            edgesByTarget.set(edge.target, list);
          }

          return graph.edges.map((edge) => {
            const target = merchantPositions.find(
              (m) => m.node.id === edge.target
            );
            if (!target) return null;

            const group = edgesByTarget.get(edge.target) ?? [edge];
            const indexInGroup = group.findIndex(
              (e) => e.dispute_id === edge.dispute_id
            );
            const groupCount = group.length;

            // Perpendicular unit vector to this line's own direction,
            // used to fan out same-target edges instead of overlapping.
            const dx = target.x - customerX;
            const dy = target.y - customerY;
            const len = Math.sqrt(dx * dx + dy * dy) || 1;
            const perpX = -dy / len;
            const perpY = dx / len;

            const OFFSET = isNarrow ? 10 : 16;
            const offset =
              groupCount > 1
                ? (indexInGroup - (groupCount - 1) / 2) * OFFSET
                : 0;

            const x1 = customerX + perpX * offset;
            const y1 = customerY + perpY * offset;
            const x2 = target.x + perpX * offset;
            const y2 = target.y + perpY * offset;

            // Position along the line closer to the merchant end (62%)
            // rather than the exact midpoint — with more than one
            // merchant, midpoints from different edges can land close
            // together; anchoring nearer each line's own destination
            // keeps labels from different edges apart.
            const t = 0.62;
            const labelBaseX = x1 + t * (x2 - x1);
            const labelBaseY = y1 + t * (y2 - y1);

            // Offset direction follows THIS line's own slope (whether it
            // heads up or down from the customer), not is_current — using
            // is_current for direction was the bug: it made the current
            // edge's label push one way and the other edge push the
            // opposite way, and depending on which merchant was "current"
            // those two directions could coincidentally converge on the
            // same point instead of naturally separating.
            const goesUp = y2 < y1;
            const idLabelX = isNarrow ? labelBaseX + 55 : labelBaseX;
            const idLabelY = isNarrow
              ? labelBaseY - 6
              : labelBaseY + (goesUp ? -14 : 18);
            const dateLabelX = idLabelX;
            const dateLabelY = isNarrow
              ? labelBaseY + 7
              : labelBaseY + (goesUp ? -1 : 31);

            return (
              <g key={edge.dispute_id}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={edge.is_current ? "#4f46e5" : "#cbd5e1"}
                  strokeWidth={edge.is_current ? 2.5 : 1.5}
                />

                {/* Edge label: dispute ID + date + amount */}
                <text
                  x={idLabelX}
                  y={idLabelY}
                  textAnchor={isNarrow ? "start" : "middle"}
                  fontSize={isNarrow ? "9" : "10"}
                  fontWeight={edge.is_current ? 700 : 600}
                  fill={edge.is_current ? "#4338ca" : "#475569"}
                >
                  {edge.dispute_id}
                  {edge.is_current ? " (current)" : ""}
                </text>
                <text
                  x={dateLabelX}
                  y={dateLabelY}
                  textAnchor={isNarrow ? "start" : "middle"}
                  fontSize={isNarrow ? "8" : "9"}
                  fontWeight="500"
                  fill={edge.is_current ? "#6366f1" : "#64748b"}
                >
                  {formatShortDate(edge.filed_at)}
                  {edge.amount ? ` · ₹${edge.amount.toLocaleString("en-IN")}` : ""}
                </text>
              </g>
            );
          });
        })()}

        <circle cx={customerX} cy={customerY} r={22} fill="#1e293b" />
        <text
          x={customerX}
          y={customerY + 40}
          textAnchor="middle"
          fontSize="11"
          fontWeight="600"
          fill="#1e293b"
        >
          {customer.label}
        </text>

        {merchantPositions.map(({ node, x, y }) => {
          const isCurrentTarget = graph.edges.some(
            (e) => e.target === node.id && e.is_current
          );
          return (
            <g key={node.id}>
              <circle
                cx={x}
                cy={y}
                r={18}
                fill={isCurrentTarget ? "#4f46e5" : "#818cf8"}
              />
              <text
                x={isNarrow ? x : x + 32}
                y={isNarrow ? y + 34 : y + 4}
                textAnchor={isNarrow ? "middle" : "start"}
                fontSize="11"
                fontWeight="600"
                fill="#334155"
              >
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-indigo-600" /> This
          dispute
        </span>
        <span className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-slate-300" /> Other
          disputes, same customer
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------ */
/* DASHBOARD VIEW */
/* ------------------------------------------------ */

function DashboardView({
  dashboard,
  loading,
  error,
  formatMoney,
}: {
  dashboard: Dashboard | null;
  loading: boolean;
  error: string;
  formatMoney: (amount: number, currency: string) => string;
}) {
  const recommendationDot: Record<string, string> = {
    CONTEST: "bg-green-500",
    REVIEW: "bg-yellow-500",
    ACCEPT: "bg-red-500",
  };

  const riskTextStyles: Record<string, string> = {
    high: "text-red-600",
    medium: "text-yellow-600",
    low: "text-slate-400",
  };

  return (
    <div className="mx-auto max-w-7xl px-8 py-8">
      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex min-h-[400px] items-center justify-center rounded-2xl border bg-white shadow-sm">
          <div className="text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
            <p className="font-semibold">Loading portfolio...</p>
          </div>
        </div>
      )}

      {dashboard && !loading && (
        <div className="space-y-6">
          {/* TOP STATS */}
          <div className="grid grid-cols-4 gap-4">
            <Stat
              label="Total Disputes"
              value={String(dashboard.total_disputes)}
            />
            <Stat
              label="Amount at Stake"
              value={formatMoney(dashboard.total_amount, dashboard.currency)}
              highlight
            />
            <Stat
              label="Flagged for Network Risk"
              value={String(dashboard.flagged_risk_count)}
            />
            <Stat
              label="Recommended to Contest"
              value={String(dashboard.by_recommendation["CONTEST"] ?? 0)}
            />
          </div>

          {/* PLATFORM RISK SIGNALS */}
          {(dashboard.platform_risk_signals.flagged_customers.length > 0 ||
            dashboard.platform_risk_signals.flagged_couriers.length > 0) && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-white shadow-sm">
              <div className="flex items-center gap-2">
                <span className="text-lg">⚡</span>
                <h3 className="font-bold">Platform Risk Signals</h3>
              </div>

              <p className="mt-1 text-sm text-slate-300">
                Patterns that only exist because we&apos;re looking across
                every merchant at once — invisible to any single merchant&apos;s
                own dashboard.
              </p>

              <div className="mt-5 grid gap-4 md:grid-cols-3">
                {dashboard.platform_risk_signals.flagged_customers.length >
                  0 && (
                  <div className="rounded-xl bg-white/10 p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-red-300">
                      Cross-merchant serial disputers
                    </p>
                    <div className="mt-3 space-y-2 text-sm">
                      {dashboard.platform_risk_signals.flagged_customers.map(
                        (c) => (
                          <div key={c.customer_id}>
                            <span className="font-semibold">
                              {c.customer_id}
                            </span>{" "}
                            — disputed {c.distinct_merchants} different
                            merchants ({c.dispute_ids.join(", ")})
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {dashboard.platform_risk_signals.flagged_couriers.length >
                  0 && (
                  <div className="rounded-xl bg-white/10 p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-orange-300">
                      Underperforming couriers
                    </p>
                    <div className="mt-3 space-y-2 text-sm">
                      {dashboard.platform_risk_signals.flagged_couriers.map(
                        (c) => (
                          <div key={c.courier}>
                            <span className="font-semibold">
                              {c.courier}
                            </span>{" "}
                            — {c.failure_rate_pct}% non-delivery rate across{" "}
                            {c.dispute_count} disputes
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

                {dashboard.platform_risk_signals.merchant_spikes.length >
                  0 && (
                  <div className="rounded-xl bg-white/10 p-4">
                    <p className="text-xs font-bold uppercase tracking-wide text-purple-300">
                      Merchant dispute spikes
                    </p>
                    <div className="mt-3 space-y-2 text-sm">
                      {dashboard.platform_risk_signals.merchant_spikes.map(
                        (m) => (
                          <div key={m.merchant_id}>
                            <span className="font-semibold">
                              {m.merchant_id}
                            </span>{" "}
                            — {m.dispute_count} disputes within{" "}
                            {m.window_days} days
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* RECOMMENDATION BREAKDOWN */}
          <div className="rounded-2xl border bg-white p-6 shadow-sm">
            <h3 className="font-bold">Recommendation Breakdown</h3>

            <div className="mt-5 space-y-3">
              {(["CONTEST", "REVIEW", "ACCEPT"] as const).map((key) => {
                const count = dashboard.by_recommendation[key] ?? 0;
                const pct =
                  dashboard.total_disputes > 0
                    ? Math.round((count / dashboard.total_disputes) * 100)
                    : 0;

                return (
                  <div key={key}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="font-medium">{key}</span>
                      <span className="text-slate-500">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={`h-full ${recommendationDot[key]}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ALL DISPUTES TABLE */}
          <div className="rounded-2xl border bg-white p-6 shadow-sm">
            <h3 className="font-bold">All Disputes</h3>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-slate-500">
                    <th className="pb-2 pr-4 font-medium">Dispute</th>
                    <th className="pb-2 pr-4 font-medium">Amount</th>
                    <th className="pb-2 pr-4 font-medium">Score</th>
                    <th className="pb-2 pr-4 font-medium">Recommendation</th>
                    <th className="pb-2 font-medium">Network Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.disputes.map((row) => (
                    <tr key={row.dispute_id} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-semibold">
                        {row.dispute_id}
                      </td>
                      <td className="py-3 pr-4">
                        {formatMoney(row.amount, row.currency)}
                      </td>
                      <td className="py-3 pr-4">{row.evidence_score}/100</td>
                      <td className="py-3 pr-4">
                        <span className="inline-flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${recommendationDot[row.recommendation]}`}
                          />
                          {row.recommendation}
                        </span>
                      </td>
                      <td
                        className={`py-3 font-semibold uppercase ${riskTextStyles[row.risk_level] ?? ""}`}
                      >
                        {row.risk_level}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* COURIER BREAKDOWN */}
          {dashboard.courier_breakdown.length > 0 && (
            <div className="rounded-2xl border bg-white p-6 shadow-sm">
              <h3 className="font-bold">Courier Breakdown</h3>
              <p className="mt-1 text-sm text-slate-500">
                Non-delivery rate per courier, compared across every
                merchant on file — a single merchant would only ever see
                their own row.
              </p>

              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b text-slate-500">
                      <th className="pb-2 pr-4 font-medium">Courier</th>
                      <th className="pb-2 pr-4 font-medium">Disputes</th>
                      <th className="pb-2 pr-4 font-medium">Non-delivery</th>
                      <th className="pb-2 font-medium">Failure Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.courier_breakdown.map((row) => (
                      <tr key={row.courier} className="border-b last:border-0">
                        <td className="py-3 pr-4 font-semibold">
                          {row.courier}
                        </td>
                        <td className="py-3 pr-4">{row.dispute_count}</td>
                        <td className="py-3 pr-4">
                          {row.non_delivery_count}
                        </td>
                        <td
                          className={`py-3 font-semibold ${
                            row.flagged ? "text-red-600" : "text-slate-600"
                          }`}
                        >
                          {row.failure_rate_pct}%
                          {row.flagged ? " ⚠" : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------ */
/* TRIAGE VIEW */
/* ------------------------------------------------ */

function TriageView({
  triage,
  loading,
  error,
  formatMoney,
}: {
  triage: TriageQueue | null;
  loading: boolean;
  error: string;
  formatMoney: (amount: number, currency: string) => string;
}) {
  const urgencyDot: Record<string, string> = {
    red: "bg-red-500",
    yellow: "bg-yellow-500",
    green: "bg-green-500",
  };

  const urgencyLabel: Record<string, string> = {
    red: "Urgent",
    yellow: "Soon",
    green: "Comfortable",
  };

  return (
    <div className="mx-auto max-w-7xl px-8 py-8">
      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex min-h-[400px] items-center justify-center rounded-2xl border bg-white shadow-sm">
          <div className="text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
            <p className="font-semibold">Building triage queue...</p>
          </div>
        </div>
      )}

      {triage && !loading && (
        <div className="space-y-6">
          <div className="rounded-2xl border bg-white p-6 shadow-sm">
            <h3 className="font-bold">Action Required</h3>
            <p className="mt-1 text-sm text-slate-500">
              Sorted by a simple, transparent heuristic — amount ×
              deadline urgency × evidence gap. This is a demo priority
              signal, not a calibrated model.
            </p>

            <div className="mt-5 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b text-slate-500">
                    <th className="pb-2 pr-4 font-medium">Priority</th>
                    <th className="pb-2 pr-4 font-medium">Dispute</th>
                    <th className="pb-2 pr-4 font-medium">Amount</th>
                    <th className="pb-2 pr-4 font-medium">Evidence</th>
                    <th className="pb-2 pr-4 font-medium">Recommendation</th>
                    <th className="pb-2 font-medium">Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {triage.queue.map((row, index) => (
                    <tr
                      key={row.dispute_id}
                      className="border-b last:border-0"
                    >
                      <td className="py-3 pr-4 font-semibold text-slate-400">
                        #{index + 1}
                      </td>
                      <td className="py-3 pr-4 font-semibold">
                        {row.dispute_id}
                      </td>
                      <td className="py-3 pr-4">
                        {formatMoney(row.amount, row.currency)}
                      </td>
                      <td className="py-3 pr-4">{row.evidence_score}/100</td>
                      <td className="py-3 pr-4">{row.recommendation}</td>
                      <td className="py-3">
                        <span className="inline-flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${urgencyDot[row.urgency_level]}`}
                          />
                          {urgencyLabel[row.urgency_level]}
                          {row.hours_remaining !== null && (
                            <span className="text-slate-400">
                              ({Math.max(0, Math.round(row.hours_remaining))}h)
                            </span>
                          )}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------ */
/* SIMULATE VIEW */
/* ------------------------------------------------ */

function SimulateView({
  formatMoney,
}: {
  formatMoney: (amount: number, currency: string) => string;
}) {
  const [customerId, setCustomerId] = useState("cust_101");
  const [merchantId, setMerchantId] = useState("merch_999");
  const [reason, setReason] = useState("ITEM_NOT_RECEIVED");
  const [amount, setAmount] = useState("15000");

  const [history, setHistory] = useState<SimulationResult[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function runSimulation(
    scenarioCustomerId: string,
    scenarioMerchantId: string,
    scenarioReason: string,
    scenarioAmount: number
  ) {
    setSubmitting(true);
    setError("");

    try {
      const response = await fetch(`${API}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: scenarioCustomerId,
          merchant_id: scenarioMerchantId,
          reason: scenarioReason,
          amount: scenarioAmount,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data: SimulationResult = await response.json();
      setHistory((prev) => [...prev, data]);
    } catch (err) {
      console.error(err);
      setError(
        "Could not run simulation. Make sure the backend is running on port 8000."
      );
    } finally {
      setSubmitting(false);
    }
  }

  function runScenario(
    scenarioCustomerId: string,
    scenarioMerchantId: string,
    scenarioReason: string,
    scenarioAmount: number
  ) {
    setCustomerId(scenarioCustomerId);
    setMerchantId(scenarioMerchantId);
    setReason(scenarioReason);
    setAmount(String(scenarioAmount));
    runSimulation(
      scenarioCustomerId,
      scenarioMerchantId,
      scenarioReason,
      scenarioAmount
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await runSimulation(customerId, merchantId, reason, Number(amount));
  }

  async function handleReset() {
    try {
      await fetch(`${API}/simulate/reset`, { method: "POST" });
      setHistory([]);
    } catch (err) {
      console.error(err);
      setError("Could not reset the simulation.");
    }
  }

  const riskBadge: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-slate-100 text-slate-600",
  };

  return (
    <div className="mx-auto max-w-7xl px-8 py-8">
      <div className="mb-6 rounded-2xl border border-indigo-200 bg-indigo-50 px-5 py-4 text-sm text-indigo-800">
        <span className="font-bold">Interactive demo environment.</span>{" "}
        This shows how Platform Intelligence signals evolve as new
        disputes enter the network — it&apos;s not a production workflow
        where investigators would manually type in customer or merchant
        IDs.
      </div>

      <div className="mb-6 rounded-2xl border bg-white p-6 shadow-sm">
        <h3 className="font-bold">Quick Scenarios</h3>
        <p className="mt-1 text-sm text-slate-500">
          One click, pre-filled with real data from the seed set — no
          typing needed for the demo.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <button
            onClick={() => runScenario("cust_102", "merch_999", "ITEM_NOT_RECEIVED", 15000)}
            disabled={submitting}
            className="rounded-xl border border-red-200 bg-red-50 p-4 text-left transition hover:bg-red-100 disabled:opacity-50"
          >
            <p className="text-xs font-bold uppercase tracking-wide text-red-600">
              Scenario 1
            </p>
            <p className="mt-1 text-sm font-semibold text-red-800">
              Repeat customer across merchants
            </p>
            <p className="mt-1 text-xs text-red-700">
              cust_102 already has 1 dispute — this adds a 2nd against a
              brand-new merchant.
            </p>
          </button>

          <button
            onClick={() => runScenario("cust_888", "merch_503", "ITEM_NOT_RECEIVED", 9500)}
            disabled={submitting}
            className="rounded-xl border border-purple-200 bg-purple-50 p-4 text-left transition hover:bg-purple-100 disabled:opacity-50"
          >
            <p className="text-xs font-bold uppercase tracking-wide text-purple-600">
              Scenario 2
            </p>
            <p className="mt-1 text-sm font-semibold text-purple-800">
              Merchant dispute spike
            </p>
            <p className="mt-1 text-xs text-purple-700">
              A 2nd dispute lands on merch_503 within the same short
              window as its last one.
            </p>
          </button>

          <button
            onClick={() => runScenario("cust_777", "merch_777", "ITEM_NOT_RECEIVED", 5000)}
            disabled={submitting}
            className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-left transition hover:bg-slate-100 disabled:opacity-50"
          >
            <p className="text-xs font-bold uppercase tracking-wide text-slate-500">
              Scenario 3
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-800">
              No platform signal
            </p>
            <p className="mt-1 text-xs text-slate-600">
              A brand-new customer and merchant — the baseline, clean
              contrast.
            </p>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[380px_1fr] gap-6">
        {/* FORM */}
        <div className="h-fit rounded-2xl border bg-white p-6 shadow-sm">
          <h3 className="font-bold">Add a Simulated Dispute</h3>
          <p className="mt-1 text-sm text-slate-500">
            Watch the network risk picture update live. This never
            touches real data — it resets when the backend restarts.
          </p>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500">
                Customer ID
              </label>
              <input
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                placeholder="cust_101"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500">
                Merchant ID
              </label>
              <input
                value={merchantId}
                onChange={(e) => setMerchantId(e.target.value)}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
                placeholder="merch_999"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500">
                Reason
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              >
                <option value="ITEM_NOT_RECEIVED">ITEM_NOT_RECEIVED</option>
                <option value="ITEM_DAMAGED">ITEM_DAMAGED</option>
                <option value="ITEM_NOT_AS_DESCRIBED">
                  ITEM_NOT_AS_DESCRIBED
                </option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500">
                Amount (INR)
              </label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mt-1 w-full rounded-lg border px-3 py-2 text-sm"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50"
            >
              {submitting ? "Simulating..." : "Add Dispute"}
            </button>

            {history.length > 0 && (
              <button
                type="button"
                onClick={handleReset}
                className="w-full rounded-xl border px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                Reset Simulation
              </button>
            )}
          </form>
        </div>

        {/* RESULTS */}
        <div className="space-y-4">
          {history.length === 0 && (
            <div className="flex min-h-[300px] items-center justify-center rounded-2xl border bg-white shadow-sm">
              <p className="text-sm text-slate-500">
                Submit a simulated dispute to see the network risk impact.
              </p>
            </div>
          )}

          {history.map((result, index) => (
            <div
              key={result.dispute.dispute_id}
              className="rounded-2xl border bg-white p-6 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-400">
                    Simulation #{index + 1} —{" "}
                    {result.dispute.dispute_id}
                  </p>
                  <p className="mt-1 font-semibold">
                    {result.dispute.customer_id} vs{" "}
                    {result.dispute.merchant_id} —{" "}
                    {formatMoney(result.dispute.amount, "INR")}
                  </p>
                </div>

                <span
                  className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${
                    riskBadge[result.network_risk.risk_level]
                  }`}
                >
                  {result.network_risk.risk_level} risk
                </span>
              </div>

              {result.network_risk.flags.length > 0 && (
                <div className="mt-4 space-y-2">
                  {result.network_risk.flags.map((flag, i) => (
                    <div
                      key={i}
                      className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600"
                    >
                      {flag.finding}
                    </div>
                  ))}
                </div>
              )}

              {result.merchant_spike?.is_spike && (
                <div className="mt-2 rounded-lg bg-purple-50 px-3 py-2 text-xs text-purple-700">
                  {result.merchant_spike.finding}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------ */
/* STAT CARD */
/* ------------------------------------------------ */

function Stat({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p
        className={`mt-2 text-2xl font-bold ${
          highlight
            ? "text-green-600"
            : "text-slate-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}