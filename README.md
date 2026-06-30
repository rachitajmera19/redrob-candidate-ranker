# Redrob Candidate Discovery & Ranking Challenge

This repository contains the winning candidate discovery and ranking system developed for the**Redrob AI**.

## System Architecture

Our ranking pipeline uses a highly optimized, deterministic rules-based scoring engine designed to identify the top 100 best-fit candidates from a pool of 100,000 candidates in under 15 seconds.

### Key Components

1. **Honeypot Filter**: Explicitly removes synthetic "honeypot" and trap profiles using logical integrity checks (e.g. working at a company before its founding year, impossible job durations, experience-duration mismatches, education-degree contradictions, and expert skills with zero months of usage).
2. **Consulting Firm Filter**: Screens out candidates whose entire career history consists exclusively of IT consulting giants (e.g. TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini), prioritizing product engineering experience per the JD.
3. **Location Matcher**: Weights candidates located near Redrob's hybrid hubs (Pune/Noida) or other Indian Tier-1 tech hubs.
4. **Experience Scorer**: Optimizes for the core 5-9 years of experience band.
5. **Skills Scorer**: Performs lexical matching against target NLP, vector search, embeddings, information retrieval, and LLM skills, weighted by proficiency, duration, and endorsement counts.
6. **Title Matcher**: Identifies candidate titles matching targeted engineering archetypes (AI/ML Engineer, Search/NLP Engineer, Data Scientist).
7. **Behavioral Signals Multiplier**: Enhances or dampens the match score using real-time Redrob platform engagement signals (response rate, last active date, notice period, and application activity).

## How to Reproduce

### Dependencies
No external packages are required! The system runs on raw Python 3.

### Running the Ranker
Execute the following command to process the candidate dataset and output the ranked CSV:

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

The script will complete in ~10 seconds.
