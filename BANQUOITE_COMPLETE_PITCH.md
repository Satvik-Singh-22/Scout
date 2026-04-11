# BANQUOITE — COMPLETE PITCH
## Read this aloud. Every word is meant to be spoken.

---

## OPENING — SET THE SCENE

Let me start by painting a picture of the problem.

Imagine you are a manager at NatWest. You need to answer one question — something as straightforward as "Why did our transaction failure rate spike last Tuesday?" You know the answer is sitting somewhere in the data. But to get it, you have to raise a ticket with the data team, wait two or three days, get back a spreadsheet you cannot fully read, and by the time you have your answer, the problem has already cost the bank money and the moment to act has passed.

Now imagine the data team is not slow because they are incompetent. They are slow because this is genuinely hard. NatWest has dozens of internal teams — Payments, Operations, Risk, Customer, Finance — and each team's data is intentionally segregated from the others. A payments analyst cannot see the operations team's logs. A risk analyst cannot see the customer team's accounts. The walls are there for compliance reasons, for regulatory reasons, for good reasons. But those walls also mean that getting a cross-domain answer — "Did the API latency spike on Tuesday cause the payment failures on Tuesday?" — requires coordinating across multiple teams, multiple data owners, multiple approval chains.

The result is that most business questions that could be answered in seconds take days. And questions that require data from more than one team sometimes never get answered at all.

That is the problem we are solving.

---

## THE PRODUCT — WHAT IS BANQUOITE?

We built **Banquoite**. It is an enterprise AI portal designed specifically for NatWest's internal banking teams.

The core idea is simple: any employee, regardless of their technical skill level, should be able to type a question in plain English and get a trustworthy, instant answer — drawn from the actual enterprise data that is relevant to their role.

A non-technical manager types: *"What is our transaction failure rate this week compared to last week, broken down by region?"* They get back a clean, readable English answer with a bar chart. No SQL. No spreadsheets. No waiting.

A developer types: *"Show me API gateway error rates by service for the past seven days."* They get back the same answer, but with the SQL that was executed, the exact tables that were queried, and the reasoning the AI used — so they can verify every step.

And critically — a senior enterprise analyst who has been granted access to multiple teams' data can ask a question that spans both the Payments domain and the Operations domain simultaneously and get a single synthesized answer that joins both data streams together. That has never been possible before without a week of coordination.

That is Banquoite.

---

## THE THREE PILLARS — HOW WE ADDRESS NATWEST'S JUDGING CRITERIA

NatWest judged this challenge on three criteria. Let me address each directly.

**Pillar one: Clarity.**
Every answer Banquoite gives is tailored to who is asking. We have two modes — Manager mode and Developer mode. A Manager gets a plain English explanation, a chart, and a one-sentence summary. A Developer gets the SQL that was executed, the table names, the row counts, and the agent's reasoning chain. The same underlying answer, delivered in the language that person actually needs. No one is ever shown a raw database dump and asked to interpret it themselves.

**Pillar two: Trust.**
This is where we go further than any generic AI product. Every single answer Banquoite gives is accompanied by what we call the Chain of Thought panel. It shows the user exactly which data sources were considered, exactly which tables were actually used, exactly what SQL was executed against those tables, how many rows came back, and which parts of the answer came from structured data versus unstructured text. Nothing is hidden. Nothing is a black box. The user can see, step by step, how the AI arrived at its answer and decide whether to trust it.

Beyond that, the entire system is built on a governance model. Data Owners — one per team — control which of their tables the AI is even allowed to access. They register their tables through a self-service interface, write human-readable descriptions of what each table contains, and can toggle any table on or off at any moment. If a table is toggled off, the AI immediately stops using it. No redeployment. No code change. Instant.

Above the Data Owners sits a Platform Administrator who has a bird's-eye view of all 40 data tables across all five teams and makes the explicit decision about which team gets access to which tables. This is how NatWest actually governs data internally — and we built that governance model directly into the product.

**Pillar three: Speed.**
Answers appear in real time, word by word, streamed directly to the screen. The AI pipeline runs its SQL generation and its document retrieval in parallel, not sequentially, which cuts latency significantly. Under normal conditions, a user starts seeing an answer within two to three seconds of pressing send. The entire response, including a chart, is complete in under ten seconds for most queries.

---

## THE GOVERNANCE MODEL — THE DIFFERENTIATOR

Let me spend a moment on the governance model because this is the thing that separates us from every other chatbot demo you will see today.

Most AI tools treat data access as a binary: you either have access to everything or you do not. We built a four-tier access hierarchy that mirrors how a real bank actually operates.

**Tier one: ANALYST.** This is the default role. An Analyst belongs to one team and can only query that team's assigned tables. If they are on the Payments team, they see payment data. They cannot see operations logs, risk flags, or customer records. The wall is enforced at the AI pipeline level, not just at the UI level — the AI literally does not know those other tables exist for that user.

**Tier two: DATA_OWNER.** One per team. They can register their team's database tables through a self-service onboarding wizard — no developer involvement required. They write the semantic definitions that tell the AI what each table means in plain English. And they can revoke access to any table at any time.

**Tier three: ENTERPRISE_ANALYST.** This is the role you would give to a senior manager or a Head of Business Intelligence — someone whose decisions require synthesizing data from multiple domains. The Platform Admin explicitly grants them access to, say, Team A's payment data and Team B's operations data. When that person asks a question, the AI pulls from both domains simultaneously, writes SQL that joins across those domains if needed, and gives a single unified answer. No one else on either team can do that. It is explicitly granted, explicitly controlled, and instantly revocable.

**Tier four: PLATFORM_ADMIN.** This person sits above all teams. They see all 40 tables in the system. They decide which tables each team can access. They decide who gets cross-team access. They can revoke any permission from any user in real time. This is the Data Governance function that enterprise banks actually have — we just made it a live, interactive part of the product.

---

## THE TECHNICAL ARCHITECTURE — HOW IT WORKS

Let me walk you through what actually happens when a user sends a message.

The user types a question. That question goes to our backend, which is a Python application built on FastAPI. From there it enters our AI pipeline, which we built using LangGraph — a framework for building stateful, multi-step AI workflows. The pipeline is a graph of seven specialized agents, each with a single responsibility.

**Agent one: the Orchestrator.** It reads the question and decides what kind of question it is. Is this a question that needs to query the database? Is it a question about customer sentiment that needs to search through text? Or is it both? It makes that routing decision and passes it forward.

**Agent two: the Relevancy Agent.** It looks at all the tables this particular user is allowed to access — which is controlled by the governance model we just described — and selects only the tables that are relevant to this specific question. A question about payment failures does not need the customer segmentation table. A question about API latency does not need the FX conversion table. The relevancy agent narrows the scope before any SQL is written, which dramatically improves accuracy.

**Agent three: the SQL Generation Agent.** It takes the relevant tables, their column definitions, and the user's question, and writes the SQL query. It knows today's date, so when a user says "last week" or "this month," it resolves that correctly. It handles GROUP BY, date ranges, aggregations, JOINs across tables — everything needed for real enterprise analytics questions.

**Agent four: the RAG Agent.** This runs in parallel with the SQL agent. RAG stands for Retrieval-Augmented Generation. We have embedded thousands of customer complaints and support tickets into a vector database. When a question has a qualitative component — "What are customers saying about payment failures?" — the RAG agent retrieves the most semantically relevant pieces of that text and feeds them into the answer.

**Agent five: the Execution Agent.** It runs the SQL against the actual database, gets back the rows, and formats them for the next stage.

**Agent six: the Synthesis Agent.** It takes the SQL results, the retrieved text chunks, and weaves them into a single coherent narrative context.

**Agent seven: the Persona Agent.** It takes that narrative and formats the final answer based on who is asking. Manager mode: plain English, chart data, no jargon. Developer mode: full SQL, table names, row counts, technical detail. It also builds the complete Chain of Thought object that appears in the transparency panel.

That entire pipeline — all seven agents — runs in under ten seconds for most queries.

---

## THE DATA LAYER

We are not demoing against a toy dataset with ten rows. We built a realistic mock enterprise dataset with approximately one million rows across forty tables, covering five distinct business domains.

The Payments domain has twelve tables — transactions, failed transactions, payment events, refunds, chargebacks, FX conversions, recurring payments, and more. Two hundred and fifty thousand transaction rows, with a deliberately seeded anomaly: two days ago, between two and four in the afternoon, the transaction failure rate spiked from fifteen percent to thirty-five percent. That is the event our demo queries are designed to find and explain.

The Operations domain has ten tables — API gateway logs, system health metrics, service latency logs, error logs, deployment events, audit trails, and more. One hundred thousand API log rows, with a matching latency spike in the same time window as the payment failures. That is the cross-domain correlation the Enterprise Analyst demo is designed to surface.

The Risk domain has six tables — KYC records, customer complaints, support tickets, churn events, fraud cases, and compliance flags. The Risk and Customer domains together contain over one hundred and fifty thousand rows.

The Finance domain has six tables — products, loan applications, monthly revenue, cost centres, branch performance, and regulatory reports.

All forty tables are registered in our governance system, assigned to their respective teams, with full semantic definitions that tell the AI what each table means and what each column contains.

---

## THE PROACTIVE FEATURES

Beyond answering questions, Banquoite also monitors your data proactively.

We have an anomaly detection system that runs on a schedule using APScheduler. It checks key metrics — transaction failure rates, API latency percentiles — against configured thresholds. When a threshold is breached, it generates an alert automatically. The Alert Center in the UI shows these pre-detected anomalies so a manager sees them the moment they log in, without having to ask.

We also have a scheduled query feature. A user can set up a recurring query — for example, "Send me a daily transaction summary every morning at nine." The system runs that query on schedule, saves the result, and either delivers it to the user's dashboard or sends it by email. This means the data comes to the user instead of the user having to remember to ask.

---

## THE DEMO — THREE BEATS

Let me describe exactly what we will show you.

**Beat one: Data isolation.** We log in as a standard analyst on the Payments team. We ask: "What is the total payment volume this week?" The answer comes back instantly, drawn only from the Payments team's tables. The Chain of Thought panel on the right shows exactly which tables were used, what SQL was executed, how many rows came back. Nothing from the Operations team, the Risk team, or any other team appears anywhere in the answer — not because we filtered it out at the display layer, but because the AI literally does not see those tables for this user.

**Beat two: Cross-domain synthesis.** We log in as the Enterprise Analyst, who has been explicitly granted access to both the Payments domain and the Operations domain. We ask: "Did the spike in API errors last Tuesday cause the increase in payment failures?" The pipeline now queries both domains simultaneously. It pulls latency data from the operations logs, payment failure data from the transactions table, compares the time windows, and synthesizes a single answer that draws from both. This is the answer that would have taken a week of cross-team coordination to produce manually. We get it in eight seconds.

**Beat three: Governance in real time.** We log in as the Platform Administrator. We navigate to the governance panel. We find the Enterprise Analyst user and revoke their access to the Operations team's data — one click. We log back in as the Enterprise Analyst and run the same query. The answer now only reflects the Payments data. The operations logs are gone. The boundary is enforced instantly, with no code change, no redeployment, no delay. That is live, demonstrable enterprise data governance.

---

## THE TECH STACK — WHAT WE BUILT WITH

Everything we used is open source, freely licensed, and deployable on free-tier infrastructure. There are no credit card requirements, no proprietary licenses, nothing that would prevent NatWest from taking this and running with it.

The frontend is built with Next.js 14, styled with Tailwind CSS and shadcn/ui components, with charts rendered by Recharts. It is deployed on Vercel.

The backend is Python 3.11 with FastAPI for the API layer, SQLAlchemy for the database ORM, and Alembic for migrations. It is deployed on Render.

The AI pipeline uses LangGraph for the multi-agent graph orchestration, LangChain Core for prompt templates and output parsers, and the Groq API to access the Llama 3.1 70-billion parameter model — which is currently the fastest publicly available LLM inference, with a generous free tier of over fourteen thousand requests per day.

The vector store for RAG uses ChromaDB with the sentence-transformers all-MiniLM-L6-v2 embedding model — local, free, Apache 2.0 licensed, no external API calls required.

The database is PostgreSQL hosted on Neon.tech, which is a serverless Postgres provider with a free tier that requires no credit card.

The entire system — frontend, backend, AI pipeline, vector store, database — is fully deployed, live, and accessible right now.

---

## THE BIGGER PICTURE — WHY THIS MATTERS

What we built in forty-eight hours is a proof of concept, but the proof of concept demonstrates something important: that enterprise data governance and conversational AI are not in tension with each other. You do not have to choose between giving people access to data and maintaining control over that access. You can have both simultaneously.

The governance model we built — the four-tier role hierarchy, the master configuration table as the security boundary, the real-time revocation of access — is not a demo trick. It is a real architecture that scales. In production, you would add encryption for the database connection strings, a semantic caching layer to avoid redundant queries, and a configuration UI for alert thresholds. Those are the next steps. The foundation is already production-grade.

And the core user experience — type a question, get a trustworthy, transparent, instant answer — is exactly what NatWest's employees need to make faster, better decisions without depending on a data team queue that moves at the speed of a ticket system.

That is Banquoite. Thank you.

---

## ANTICIPATED QUESTIONS — AND HOW TO ANSWER THEM

**"How do you handle hallucination? How do you know the AI answer is correct?"**
The Chain of Thought panel shows every source used and every SQL query executed. The user can see the row count that came back from the database. If the SQL returned zero rows, the answer says so. If the AI could not find a relevant table, the Chain of Thought says that too. We do not ask users to trust the answer blindly — we show them the evidence and let them verify. That is what the transparency layer is for.

**"What stops someone from asking a question that accesses data they should not see?"**
The security boundary is enforced at the pipeline level, not the UI level. The Relevancy Agent — the second step in the pipeline — only queries the `master_config` table filtered by the teams this specific user is allowed to access. That filter is a database query, not a JavaScript check. Even if someone found a way to manipulate the UI, the backend would still only return data from their permitted tables. There is no route around the data boundary.

**"What happens if the AI writes wrong SQL?"**
The Execution Agent has error handling. If the SQL fails, the pipeline catches the error and returns a graceful failure message rather than a stack trace. In the Chain of Thought, the user sees that the SQL execution failed and what the error was. We never silently return incorrect data — we return either correct data or a clear failure.

**"Is this using any of NatWest's real data?"**
No. The entire dataset is synthetically generated using the Faker library. It is realistic in structure and volume — one million rows across forty tables — but every customer name, transaction, account number, and log entry is procedurally generated with a fixed random seed. No real customer data was used at any point.

**"Could this work with NatWest's actual databases?"**
Yes, that is the design intent. The Data Owner onboarding flow allows any database — currently PostgreSQL and MySQL — to be registered by providing a connection string. NatWest's real teams would use that same flow to register their real tables, write semantic definitions in plain English describing what those tables contain, and the AI pipeline would immediately be able to query them. The mock data exists only because we needed something to demo against.

**"What is the cost to run this at scale?"**
For the hackathon, the entire stack runs on free tiers. In production, the primary cost would be the LLM API calls. At Groq's current pricing, a typical enterprise query costs fractions of a penny. The database, vector store, and background scheduler add minimal cost. The architecture is designed to be economically viable from day one.

---

*End of pitch. Everything above can be read aloud as written or used as talking points.*
