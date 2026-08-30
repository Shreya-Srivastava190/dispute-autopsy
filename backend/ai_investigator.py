import json
import os

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError


load_dotenv()


def build_fallback_report(dispute: dict, analysis: dict) -> dict:
    """
    Local fallback used when the Groq API key is missing or the API
    is unavailable. Deterministic, not AI-generated — so this can't do
    genuine free-text contradiction analysis the way the AI path does.
    It falls back to matching the structured evidence signals instead.
    """

    score = analysis["evidence_score"]
    recommendation = analysis["recommendation"]
    customer_note = dispute.get("support", {}).get("conversation", "")

    if recommendation == "CONTEST":
        summary = (
            "The dispute is strongly contradicted by the available evidence. "
            "The payment was captured, the order was fulfilled, and delivery "
            "was confirmed."
        )

        customer_claim_assessment = (
            "The customer's ITEM_NOT_RECEIVED claim is not supported by the "
            "available transaction and delivery evidence."
        )

        recommended_action = (
            "Contest the dispute using the payment, fulfillment, delivery, "
            "address-match, and signature evidence."
        )

    elif recommendation == "REVIEW":
        summary = (
            "The dispute has meaningful supporting evidence, but additional "
            "review is recommended."
        )

        customer_claim_assessment = (
            "The customer's claim cannot be conclusively confirmed or rejected "
            "using the current evidence."
        )

        recommended_action = (
            "Review the available evidence and gather additional documentation "
            "before responding to the dispute."
        )

    else:
        summary = (
            "The available evidence does not strongly support contesting "
            "the dispute."
        )

        customer_claim_assessment = (
            "The customer's claim remains plausible based on the available "
            "evidence."
        )

        recommended_action = (
            "Accept the dispute or perform additional investigation before "
            "taking action."
        )

    key_findings = [
        item["finding"]
        for item in analysis.get("evidence", [])
    ]

    delivered = dispute.get("delivery", {}).get("status") == "delivered"
    signed = dispute.get("delivery", {}).get("signature_available")
    refund_issued = dispute.get("refund", {}).get("issued")
    reason = dispute.get("reason", "")

    # This branches on the ACTUAL context (refund status, dispute reason)
    # instead of blindly asserting a "non-receipt" contradiction from
    # delivery/signature alone — that was wrong whenever the real issue
    # was something else (e.g. a refund already settling the case).
    if refund_issued:
        supporting_evidence = (
            "A refund was already issued for this order before the dispute "
            "was filed."
        )
        contradiction = (
            "No contradiction analysis is needed here — the refund already "
            "resolves the underlying claim, which is why this case is "
            "recommended for ACCEPT regardless of delivery evidence."
        )
    elif reason == "ITEM_NOT_RECEIVED" and delivered and signed:
        supporting_evidence = "Delivery confirmed with signature on file."
        contradiction = (
            "The delivery and signature record conflicts with a claim of "
            "non-receipt."
        )
    elif reason == "ITEM_NOT_RECEIVED" and delivered:
        supporting_evidence = (
            "Delivery confirmed, though no signature was captured."
        )
        contradiction = (
            "Delivery is confirmed but unsigned, so the contradiction with "
            "a non-receipt claim is present but weaker than a signed record "
            "would provide."
        )
    elif reason == "ITEM_NOT_RECEIVED":
        supporting_evidence = "No confirmed delivery on file."
        contradiction = (
            "Delivery is unconfirmed, so no contradiction can be "
            "established from the record alone — the claim may well be "
            "accurate."
        )
    else:
        # Reason is something other than non-receipt (e.g. damaged, not
        # as described) — the delivery/signature checks don't actually
        # speak to those claims, so don't force a non-receipt-style
        # contradiction onto them.
        supporting_evidence = (
            "Delivery and payment records are on file, but this dispute "
            f"reason ({reason.replace('_', ' ').lower()}) isn't directly "
            "addressed by delivery confirmation alone."
        )
        contradiction = (
            "The available structured evidence doesn't directly speak to "
            f"a {reason.replace('_', ' ').lower()} claim — a fuller "
            "assessment would need product-condition or listing evidence "
            "not captured in this dataset."
        )

    claim_vs_evidence = {
        "customer_claim": customer_note or "No customer statement on file.",
        "supporting_evidence": supporting_evidence,
        "contradiction": contradiction,
    }

    return {
        "summary": summary,
        "key_findings": key_findings,
        "customer_claim_assessment": customer_claim_assessment,
        "claim_vs_evidence": claim_vs_evidence,
        "recommended_action": recommended_action,
        "investigation_notes": (
            f"Deterministic evidence analysis produced a score of {score}/100 "
            f"and recommendation {recommendation}. "
            "This report was generated locally because the AI provider "
            "was unavailable, so it could not perform free-text contradiction "
            "analysis."
        ),
    }


def generate_ai_report(dispute: dict, analysis: dict) -> dict:

    api_key = os.getenv("GROQ_API_KEY")

    # If there is no API key, use the local investigator.
    if not api_key:
        print("GROQ_API_KEY not found. Using local fallback.")
        return build_fallback_report(dispute, analysis)

    customer_note = dispute.get("support", {}).get("conversation", "")
    refund_issued = dispute.get("refund", {}).get("issued")
    dispute_reason = dispute.get("reason", "")

    prompt = f"""
You are an AI payment dispute investigator.

Analyze the dispute using ONLY the evidence provided below.

Do not invent facts.
Do not change the evidence score.
Do not change the recommendation.

FORMAL DISPUTE REASON: {dispute_reason}
REFUND ALREADY ISSUED: {refund_issued}

STRUCTURED FACTS:
{json.dumps(analysis, indent=2)}

UNSTRUCTURED NOTE (customer/support conversation, free text — this is
the part that needs real reading comprehension, not just restating the
structured facts above):
"{customer_note}"

Your job:
1. Identify the customer's actual claim, in your own words, based on the
   unstructured note above. The note may be about something OTHER than
   the formal dispute reason (e.g. the note might mention a refund even
   though the formal reason is non-receipt) — if so, say so explicitly
   rather than forcing them to match.
2. State what the structured evidence supports or contradicts about that
   SPECIFIC claim — be concrete, don't just restate the evidence list.
3. Name the contradiction explicitly if one genuinely exists between the
   claim and the evidence. IMPORTANT: only claim a "non-receipt
   contradiction" if the dispute reason is actually about non-receipt —
   if REFUND ALREADY ISSUED is true, or the note is about something else
   entirely, say that instead of forcing a delivery/signature
   contradiction that doesn't apply. If the evidence is genuinely
   inconclusive, say so honestly instead of forcing a contradiction that
   isn't there.
4. Summarize the most important pieces of evidence.
5. State what the merchant should do next.

Return ONLY valid JSON with this structure:

{{
  "summary": "short investigation summary",
  "key_findings": [
    "finding 1",
    "finding 2",
    "finding 3"
  ],
  "customer_claim_assessment": "assessment of the customer's claim",
  "claim_vs_evidence": {{
    "customer_claim": "the claim, restated in your own words from the note",
    "supporting_evidence": "what backs the merchant's side, if anything",
    "contradiction": "the specific conflict between claim and evidence, or an honest statement that none can be established or that none applies"
  }},
  "recommended_action": "what the merchant should do",
  "investigation_notes": "short explanation"
}}
"""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    except RateLimitError:
        print("Groq API rate limit hit. Using local fallback.")
        return build_fallback_report(dispute, analysis)

    except APIError as error:
        print(f"Groq API error: {error}")
        return build_fallback_report(dispute, analysis)

    except json.JSONDecodeError:
        print("OpenAI returned invalid JSON. Using local fallback.")
        return build_fallback_report(dispute, analysis)

    except Exception as error:
        print(f"Unexpected AI error: {error}")
        return build_fallback_report(dispute, analysis)