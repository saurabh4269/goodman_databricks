Bharat Bricks Hackathon: IIT Bombay


Day 1: Friday, March 27, 2026

Day 2: Saturday, March 28, 2026

# Participant Guide

[Welcome](https://bharatbricks.org/guide/iit-bombay?referrer=luma#welcome) [Overview](https://bharatbricks.org/guide/iit-bombay?referrer=luma#overview) [Schedule](https://bharatbricks.org/guide/iit-bombay?referrer=luma#schedule) [Know Before You Go](https://bharatbricks.org/guide/iit-bombay?referrer=luma#know-before) [Free Edition Constraints](https://bharatbricks.org/guide/iit-bombay?referrer=luma#constraints) [Preparation](https://bharatbricks.org/guide/iit-bombay?referrer=luma#prep) [Data Sources](https://bharatbricks.org/guide/iit-bombay?referrer=luma#data-sources) [Sample Apps](https://bharatbricks.org/guide/iit-bombay?referrer=luma#sample-apps) [What to Expect](https://bharatbricks.org/guide/iit-bombay?referrer=luma#what-to-expect) [Tracks](https://bharatbricks.org/guide/iit-bombay?referrer=luma#tracks) [Requirements](https://bharatbricks.org/guide/iit-bombay?referrer=luma#requirements) [Resources](https://bharatbricks.org/guide/iit-bombay?referrer=luma#resources) [Team Formation](https://bharatbricks.org/guide/iit-bombay?referrer=luma#teams) [Mentor Support](https://bharatbricks.org/guide/iit-bombay?referrer=luma#mentors) [Judging](https://bharatbricks.org/guide/iit-bombay?referrer=luma#judging) [Submission](https://bharatbricks.org/guide/iit-bombay?referrer=luma#submission) [Presentation](https://bharatbricks.org/guide/iit-bombay?referrer=luma#presentation) [Starter Kit](https://bharatbricks.org/guide/iit-bombay?referrer=luma#starter-kit) [Overnight](https://bharatbricks.org/guide/iit-bombay?referrer=luma#overnight) [Prizes](https://bharatbricks.org/guide/iit-bombay?referrer=luma#prizes) [Code of Conduct](https://bharatbricks.org/guide/iit-bombay?referrer=luma#conduct) [Contact](https://bharatbricks.org/guide/iit-bombay?referrer=luma#contact)

## Welcome, Future Builder! 🚀

You're about to be part of something big: a 2-day hackathon where you'll build AI solutions on Databricks, collaborate with brilliant minds, and compete for prizes. This guide has everything you need to hit the ground running. Read it, prep your tools, and come ready to build!

## Event Overview

A 2-day campus event combining a hands-on Databricks workshop with a competitive hackathon as part of the Bharat Bricks Hacks 2026 program. Day 1 includes a 1.5-hour introductory workshop, team formation, and hackathon tracks overview. Day 2 is a full-day hackathon where teams build solutions on Databricks, followed by presentations and judging. Submissions from the top 2 teams are sent forward for national-level judging.

## Schedule

### Day 1 (11:00 AM – 6:00 PM)

| Time | Activity | Details |
| --- | --- | --- |
| 11:00 AM | **Check-In for Approved Participants** | Arrive, setup and networking with Databricks team |
| 12:00 PM | **Databricks Hands-on Workshop** | Hands-on Databricks workshop — get up to speed with the platform |
| 1:30 PM | **Lunch (Provided at Venue) & Team Formation** | Grab lunch, network, and form your hackathon teams |
| 2:15 PM | **Hackathon Tracks Overview** | Tracks, datasets, and starter kits are shared. |
| 3:00 PM | **Hacking Begins** | Start building! Mentors available until 6:00 PM |
| 6:00 PM | **Day 1 Wraps Up** | Mentors sign off — continue hacking remotely with your team overnight |

### Day 2 (9:00 AM – 6:00 PM)

| Time | Activity | Details |
| --- | --- | --- |
| 9:00 AM | **Day 2 Begins** | Resume hacking at the venue |
| 1:00 PM | **Lunch** | Lunch break — recharge before the final stretch |
| 3:00 PM | **Code Freeze & Submissions** | Submit your project — GitHub repo, demo, and architecture diagram |
| 3:30 PM | **Presentations & Judging** | 5-minute pitches to the judging panel |
| 5:30 PM | **Results & Prize Ceremony** | Winners announced and prizes awarded |
| 6:00 PM | **Event Concludes** |  |

## Know Before You Go ✅

- Bring your laptop and charger, fully charged
- Use a modern browser (Chrome, Firefox, or Edge)
- No prior Databricks experience required
- Dress code: casual. Wear what's comfortable.
- Arrive on time. Check-in opens at the scheduled start.

## Free Edition: Know Your Constraints 💡

Databricks Free Edition is powerful, but resource-aware design is key. If your solution only works on an A100, it does not work in India. Build smart.

| Resource | Constraint | Strategy |
| --- | --- | --- |
| **Compute** | CPU-only, no GPU | Use quantised models (GGUF/ONNX). Prefer smaller models that run well on CPU. |
| **Memory** | ~15 GB RAM | Stream data, avoid loading full datasets into memory. Use Delta Lake for efficient reads. |
| **Storage** | Limited DBFS | Clean up temp files. Use Delta tables for structured storage. |
| **Model Serving** | No dedicated endpoints | Use in-notebook inference or Databricks Apps for serving. |

## Prepare Ahead 🛠️

Set up your tools before the event. It saves time on Day 1 and lets you focus on building.

- **[Sign up for Databricks Free Edition](https://bharatbricks.org/free-edition)**: Do this before the event. No credit card needed. Your workspace is ready in minutes.
- **[Add your teammates to your workspace](https://www.youtube.com/watch?v=eA1SZvKiCfk)**: Once signed up, follow this walkthrough to invite your hackathon teammates to your Free Edition workspace.
- **[Watch: Hackathon Starter Playlist](https://www.youtube.com/playlist?list=PLxuESJxgW6ce9YPX7GFgM3J4GDOs3ohC-)**: Covers data ingestion, SQL, notebooks, AI, and building apps on Databricks.

## Find Public Data for Your Project 📊

India has rich open datasets you can use as the foundation for your hackathon project. Start exploring early. The best projects pick a focused dataset and build a sharp solution around it.

- **[data.gov.in: India's Open Government Data](https://www.data.gov.in/)**: Thousands of datasets across agriculture, finance, health, transport, and governance, published by central and state agencies.
- **[AI Kosh: IndiaAI Dataset Repository](https://aikosh.indiaai.gov.in/)**: Curated AI-ready datasets from India's national AI mission, including text, image, and domain-specific collections.

## Sample Apps & Templates 🧩

Don't start from scratch. Use these references to understand what's possible on Databricks, then build your own.

- **[Nyaya Dhwani: Legal AI Assistant (End-to-End Sample)](https://github.com/shwethab/nyaya-dhwani-hackathon/tree/main)**: A complete sample app built on Databricks Free Edition using data ingestion, vector search, and the Llama Maverick model. Includes a developer guide with step-by-step instructions to deploy on Free Edition.
- **[Databricks Apps Cookbook](https://apps-cookbook.dev/)**: Browse working examples of Databricks Apps. See patterns for dashboards, ML pipelines, and data apps.
- **[dbdemos: End-to-End Demos](https://github.com/databricks-demos/dbdemos)**: Production-style demo notebooks covering lakehouse, ML, GenAI, and data engineering. Ready to run.
- **[Databricks App Templates](https://github.com/databricks/app-templates)**: Starter templates for building Databricks Apps. Clone, customise, and deploy.
- **[Watch: Build & Deploy a Databricks App](https://m.youtube.com/watch?v=6V43f_E3AG8)**: Step-by-step video walkthrough of building and deploying an app on Databricks.

## What to Expect 🎯

- Hands-on workshop with guided exercises on Databricks
- Mentorship from Databricks engineers and domain experts
- Networking with fellow students and professionals
- Databricks swag for participants

## Hackathon Tracks 🏁

Choose your track wisely. This is where your hackathon journey begins! You'll pick one track and build a solution around it. Here's what's on the table:

### Nyaya-Sahayak: Governance & Access to Justice

Build AI that makes Indian law accessible. India recently transitioned from the colonial IPC to the Bharatiya Nyaya Sanhita (BNS). Help citizens and junior lawyers navigate this new legal framework and discover government schemes.

**Datasets:** BNS 2023 (full text), Constitution of India, gov\_myscheme (government schemes), BhashaBench-Legal

**Starter Ideas:**

- BNS explainer chatbot in Hindi/English
- Scheme eligibility checker for rural users
- Legal clause comparison tool (IPC → BNS)

_Technical Hook: RAG pipeline + IndicTrans2 for multilingual legal Q&A_

### Rail-Drishti: Critical Infrastructure & Logistics

Add intelligence to India's transport backbone: Rail, Metro, or Bus. Predict train delays, build a passenger rulebook bot, or design route optimisation dashboards using open data.

**Datasets:** Railways Running History (data.gov.in), Railway General Rules PDF, Air Quality / Weather data

**Starter Ideas:**

- Train delay predictor using historical data
- Passenger rights chatbot
- Route optimisation dashboard

_Technical Hook: Time-series forecasting on Spark + Delta Lake for historical patterns_

### Digital-Artha: Economy & Financial Inclusion

Secure and democratise financial access. Detect UPI fraud patterns, explain RBI circulars in local languages, or build loan eligibility tools for rural users.

**Datasets:** Synthetic UPI Transactions, RBI Circulars (scraped), BhashaBench-Finance

**Starter Ideas:**

- UPI fraud detection pipeline
- RBI circular explainer in regional languages
- Loan eligibility tool for rural users

_Technical Hook: Anomaly detection with Spark MLlib + multilingual summarisation_

### Swatantra: Open / Any Indic AI Use Case

Got a strong original idea that doesn't fit the defined themes? Agriculture advisory, healthcare triaging, education tools, accessibility aids. Surprise us. The only constraints are the mandatory requirements.

**Starter Ideas:**

- Agriculture advisory bot
- Healthcare triage assistant
- Education accessibility tool

_Technical Hook: Any Databricks stack. Show us creative platform usage._

_Detailed track information, curated datasets, and starter ideas will be shared on Day 1 after the workshop session._

## Mandatory Requirements (All Tracks) ⚙️

| Requirement | Details |
| --- | --- |
| **Databricks as core** | Your project must run on Databricks. Delta Lake, Spark, or Lakehouse architecture must be meaningfully used, not just for file storage. |
| **AI must be central** | AI/ML must drive the core value of your project, not be a decorative add-on. |
| **Prefer models made in India** | We encourage using at least one model built in India (e.g., Param-1, Airavata, Sarvam, IndicTrans2). This is not mandatory but strongly preferred. |
| **Working demo required** | Judges will attempt to reproduce your demo. If it doesn't run, it doesn't count. |
| **Databricks App or Notebook UI** | Your solution must have a user-facing component: a Databricks App, notebook with widgets, or Gradio/Streamlit front-end deployed on Databricks. |

**⚠️ Submissions missing any mandatory requirement will not be judged. No exceptions.**

### Databricks Tech You Can Use

- Delta Lake: structured storage and versioned data tables
- Apache Spark / PySpark: data processing and ML training
- Databricks Lakehouse: unified data + AI architecture
- Vector Search / FAISS on DBFS: semantic retrieval for RAG pipelines
- MLflow (via Databricks): experiment tracking and model logging
- Spark MLlib: distributed ML model training
- Model Serving / Inference: serving quantized models

### Guardrails

- No coding before the event opens (ideation and dataset review beforehand is fine)
- Open-source models and datasets only. No proprietary data.
- Preferably use models built in India (encouraged, not mandatory)

## Self-Serve Resources 🧠

Models, benchmarks, and datasets for your hackathon project.

| Name | Type | Capability |
| --- | --- | --- |
| **[Param-1 (2.9B)](https://huggingface.co/bharatgenai/Param-1-2.9B-Instruct)** | Model | Indic multilingual LLM. Good for Hindi, Marathi, Tamil, Telugu, and more. Runs quantised on CPU. |
| **[Airavata (7B)](https://huggingface.co/ai4bharat/Airavata)** | Model | Hindi instruction-tuned LLM based on OpenHathi. Strong for Hindi Q&A and summarisation. |
| **[IndicTrans2](https://github.com/AI4Bharat/IndicTrans2)** | Model | State-of-the-art translation across 22 Indian languages. Use for multilingual pipelines. |
| **[Sarvam-m](https://huggingface.co/sarvamai/sarvam-m)** | Model | Compact multilingual model optimised for Indian languages. Fast inference on CPU. |
| **[BhashaBench](https://bharatgen-iitb-tih.github.io/bhashabenchv1/)** | Benchmark | Evaluate your model across Indian language tasks: translation, QA, summarisation, and more. |
| **[BNS 2023 Full Text](https://www.kaggle.com/datasets/nandr39/bharatiya-nyaya-sanhita-dataset-bns)** | Data | Complete Bharatiya Nyaya Sanhita text for legal AI applications. |
| **[Railways Running History](https://www.kaggle.com/datasets/sripaadsrinivasan/indian-railways-dataset)** | Data | Historical train schedules and delays from data.gov.in. |
| **[Synthetic UPI Transactions](https://www.kaggle.com/datasets/skullagos5246/upi-transactions-2024-dataset)** | Data | Simulated UPI transaction data for fraud detection and financial analysis. |

## Team Formation 👥

- Teams of 2–4 members
- You can come with a pre-formed team or form one during Day 1
- Cross-department teams are encouraged
- Each team picks one hackathon track

## Mentor Support 🧑‍🏫

Databricks engineers and domain experts are available throughout the hackathon. Here's how mentorship works:

### Day 1: Workshop & Hacking Kickoff (11:00 AM – 6:00 PM)

Mentors circulate between teams after the workshop session. Ask for help with architecture decisions, debugging, dataset issues, or Databricks platform questions.

**Mentors will:**

- Help debug Databricks-specific issues
- Advise on architecture and data pipeline design
- Suggest relevant models, datasets, and techniques
- Review your approach and give honest feedback

**Mentors won't:**

- Write code for you
- Make decisions for your team
- Give scoring hints

### Day 2: Hackathon & Presentations (9:00 AM – 6:00 PM)

Mentors continue supporting teams in the morning, then shift to evaluation mode in the afternoon. Treat every interaction after 2 PM as a pre-judging conversation. Be ready to explain your choices.

**Mentors will:**

- Continue technical support (morning)
- Ask probing questions about your architecture
- Provide final feedback before submissions close

**Mentors won't:**

- Help with new feature development after lunch
- Debug code during afternoon judging phase

## Judging Criteria 🏆

| Criteria | Weight | Description |
| --- | --- | --- |
| **Databricks Usage** | 30% | Depth and correctness of platform usage. Is Delta Lake/Spark actually doing work, or just present? Bonus for creative use of multiple components. |
| **Accuracy & Effectiveness** | 25% | Does the AI actually work? Are the techniques sound and the results verifiable? |
| **Innovation** | 25% | Is the problem well-chosen? Is the solution novel? Does it address a real Indian context in a non-obvious way? |
| **Presentation & Demo** | 20% | Can you explain what you built, why you built it, and how it works, clearly and confidently in under 5 minutes? |

_Total: 100 points. Common scoring rubric across all tracks. Teams compete within their chosen track._

## Submission Requirements 📋

- A public GitHub repo with an architecture diagram showing how Databricks components connect. Must remain public for at least 30 days. README must include: what it does (1-2 sentences), architecture diagram, how to run (exact commands), and demo steps (what to click / what prompt to run).
- A project write-up: up to 500 characters describing what you built and why.
- Which Databricks technologies and open-source models you have used.
- A demo video: up to 2 minutes showing the solution in action.
- A link to a deployed prototype.

**⚠️ Judges will attempt to reproduce your demo from the GitHub repo. If it doesn't run, it doesn't score.**

### Optional / Bonus

- BhashaBench evaluation scores
- MLflow experiment logs
- Quantitative accuracy metrics

## Presentation 🎤

Teams selected for presentations will be announced after Round 1 judging. Prepare a 5-minute pitch covering: problem, solution, architecture, demo, and impact.

### Pitch Structure (5 minutes)

| Segment | Duration | Focus |
| --- | --- | --- |
| **Problem Statement** | 30 seconds | What problem are you solving and for whom? |
| **Architecture & Approach** | 2 minutes | How does your solution work? Show the Databricks components and data flow. |
| **Live Demo** | 1.5 minutes | Show it working. Judges will try to reproduce this. |
| **Results & Impact** | 1 minute | What did you achieve? Metrics, accuracy, user impact. |

## Bharat-Bricks Starter Kit 🧰

Every team receives this kit at the start. It contains everything you need to hit the ground running on Databricks Free Edition.

- **[Data Ingestion Notebook](https://gist.github.com/harsharobo/a3e2c7f8d9b1e4f5a6c7d8e9f0a1b2c3)**: Pre-configured notebook for ingesting CSV/JSON data into Delta Lake tables.
- **[RAG Pipeline Notebook](https://github.com/shwethab/nyaya-dhwani-hackathon/blob/main/build_rag_index.ipynb)**: Build a retrieval-augmented generation index with vector search on Free Edition.
- **[Vector Search Setup](https://github.com/shwethab/nyaya-dhwani-hackathon/blob/main/vector_search.py)**: FAISS-based vector search on DBFS for semantic retrieval.
- **[IndicTrans2 Translation Wrapper](https://github.com/shwethab/nyaya-dhwani-hackathon/blob/main/translation.py)**: Ready-to-use wrapper for multilingual query handling across 22 Indian languages.
- **[Secrets & Environment Setup Guide](https://github.com/shwethab/nyaya-dhwani-hackathon/blob/main/DEVELOPER_GUIDE.md)**: How to configure secrets, environment variables, and API keys in your Databricks workspace.

## Overnight Hacking (Day 1 to Day 2) 🌙

- After Day 1 ends, continue hacking remotely with your team.
- Use your team's communication channel (WhatsApp/Discord) to coordinate.
- Code freeze is at 3 PM on Day 2. Plan your time accordingly.
- Get some rest. Day 2 is a full day of building and presenting!
- Join the [Discord server](https://discord.gg/7Q9nbSHP) for real-time help from mentors and other participants in the **#26-iitb-hack** channel.

## Social Media Contest 📸

Share your hackathon experience on LinkedIn and win a special prize!

- Post on LinkedIn with the hashtag #BharatBricksHacks.
- Share what you learned, your experience, or your project journey.
- Attach at least one picture from the hackathon.
- Post must be published by 4:30 PM on Day 2.
- One winner will be selected for a special prize.

## Prizes

| Award | Details |
| --- | --- |
| 🥇 1st Place | ₹1,25,000 + premium swag + Databricks blog recognition |
| 🥈 2nd Place | ₹75,000 + premium swag |
| 🥉 3rd Place | ₹50,000 + premium swag |
| 🎁 All Successful Submissions | Databricks swag per team member |

## Code of Conduct 🤝

- Be respectful to all participants, mentors, and organizers
- Collaborate openly and help fellow participants when possible
- Follow all venue rules and guidelines
- Report any concerns to the organizing team immediately

## Contact & Support

Discord: **[#26-iitb-hack](https://discord.gg/7Q9nbSHP)**

Email: **bharatbricks@databricks.com**

Website: [bharatbricks.org](https://bharatbricks.org/)
