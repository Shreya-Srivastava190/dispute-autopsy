# 🔎 Dispute Autopsy

### Evidence determines the case. Patterns determine where to look. AI helps humans understand and act.

**Dispute Autopsy** is an AI-assisted dispute investigation system built for payment platforms.

Instead of treating every dispute as an isolated event, it investigates the **evidence behind the individual case**, detects **platform-wide patterns invisible to a single merchant**, and helps investigators take an explainable action.

🌐 **Live Demo:** https://dispute-autopsy.vercel.app/  
⚙️ **Backend API:** https://dispute-autopsy-backend.onrender.com  

---

## 🚨 The Problem

When a merchant receives a dispute, they can only see:

- Their transaction
- Their customer
- Their order and delivery data

But they cannot see what is happening across the platform.

For example:

- The same customer disputes multiple merchants.
- A merchant suddenly experiences a spike in disputes.
- Multiple customers report issues involving the same courier.

Each individual case may look isolated.

A payment platform can see the bigger picture.

---

## 💡 The Solution

Dispute Autopsy investigates disputes in three layers:

```text
CASE EVIDENCE
     ↓
CONTEST / ACCEPT
     ↓
PLATFORM INTELLIGENCE
     ↓
AI INVESTIGATION & RESPONSE
````

### 1. Evidence-Based Investigation

The system analyzes:

* Payment status
* Order fulfillment
* Delivery confirmation
* Address match
* Delivery signature
* Refund history
* Support interactions

This produces an **Evidence Score** and an explainable recommendation:

> **CONTEST or ACCEPT**

---

### 2. Platform Intelligence

The system looks beyond the individual dispute to identify:

* Repeat customer disputes
* Cross-merchant patterns
* Merchant dispute spikes
* Courier-related patterns
* Connected dispute relationships

The purpose is **not to automatically judge a customer**.

It answers:

> **"Is this an isolated incident, or should we investigate something bigger?"**

For example, if multiple customers report *"Item not received"* but all shipments involve the same courier, the problem may be operational rather than customer fraud.

> **A single dispute tells us what happened in one case. Patterns help us understand what might be happening across the ecosystem.**

---

## 🧠 Key Design Decision

Platform patterns **never override the evidence-based decision**.

```text
CASE EVIDENCE
     ↓
CONTEST / ACCEPT


PLATFORM PATTERNS
     ↓
INVESTIGATE DEEPER
```

This prevents suspicion from becoming an automatic financial judgment.

### Evidence determines the case.

### Patterns determine where to look.

---

## 🤖 AI Investigator

AI is used to help investigators understand structured evidence.

It provides:

* Claim vs Evidence analysis
* Supporting evidence
* Contradictions
* Evidence strength
* Decision drivers
* Investigation summaries
* Submission-ready evidence responses

Instead of simply saying:

> **Risk Score: 87%**

Dispute Autopsy explains:

> **What happened. Why we believe it. What pattern exists. What remains uncertain. And what to do next.**

---

## ✨ Features

* 🔍 Evidence-based dispute investigation
* 📊 Explainable Evidence Score
* ⚖️ CONTEST / ACCEPT recommendation
* 🌐 Cross-merchant pattern detection
* 📈 Merchant dispute spike detection
* 🚚 Courier risk analysis
* 🕸️ Dispute relationship graph
* 🧠 AI Claim vs Evidence analysis
* 📅 Evidence timeline
* 📄 Submission-ready evidence response

---

## 🏗️ Architecture

```text
                    DISPUTE
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
     CASE EVIDENCE          PLATFORM INTELLIGENCE
          │                         │
          ▼                         ▼
   CONTEST / ACCEPT         INVESTIGATE DEEPER
          │                         │
          └────────────┬────────────┘
                       ▼
                AI INVESTIGATOR
                       │
                       ▼
              EVIDENCE RESPONSE
                       │
                       ▼
                  HUMAN ACTION
```

---

## 🛠️ Tech Stack

### Frontend

* Next.js
* React
* TypeScript

### Backend

* Python
* FastAPI
* Uvicorn

### AI

* Groq API

### Deployment

* Frontend: Vercel
* Backend: Render

---

## 🎯 Why Dispute Autopsy?

Traditional fraud systems primarily ask:

> **"Is this suspicious?"**

Dispute Autopsy asks:

> **"What does the evidence prove, is this part of a larger pattern, and what should we do next?"**

It combines:

**Case Evidence** → Understand what happened
**Platform Patterns** → Understand whether something bigger is happening
**AI Investigation** → Help humans understand the evidence
**Evidence Response** → Help investigators take action

---

# Our Principle

## **Evidence determines the case.**

## **Patterns determine where to look.**

## **AI helps humans understand and act.**

> **A merchant can investigate one dispute. A payment platform can investigate the pattern behind it.**


This is the version I'd recommend submitting with your project: **clean, short, technically clear, and focused on your unique differentiator**.
```
