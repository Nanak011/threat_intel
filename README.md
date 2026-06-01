# Multi-Node Global Honeypot Network & Automated Threat Intel Pipeline

An automated, cloud-native Cyber Threat Intelligence (CTI) pipeline that captures live reconnaissance traffic across multiple global edge locations, processes payloads using AI, and maps them onto a dynamic frontend dashboard.

## Live Deployment
The interactive 3D threat globe and live analysis table are deployed and streaming here:
**https://nanak011.github.io/threat_intel/**

---

## Architecture & Data Lifecycle

1. **Edge Honeypot Nodes:** Lightweight Linux droplets deployed across global regions (London, New York, Bangalore) capturing unauthorized connection payloads, scans, and exploit attempts.
2. **Central Logging Backend:** Raw TCP/UDP network telemetry is immediately streamed and cataloged inside a secure Supabase database instance.
3. **Automated AI Processing Pipeline:** A background GitHub Actions workflow triggers cron schedule to fetch unprocessed attack logs sequentially. 
4. **Threat Intelligence Extraction:** The pipeline utilizes the Gemini large language model to parse raw commands, classify the attack vectors (e.g., Credential stuffing, PHPUnit RCEs, Path Traveersals, Log4j exploits, automated web scanners, etc.), extract unique technical signatures, and deduplicate repeating botnet spam.
5. **State Synchronization:** Cleaned data structures are appended to a historical global threat ledger (`threat_feed.json`), while database records are updated to prevent reprocessing loops.

---

## Tech Stack

* **Infrastructure:** DigitalOcean (Multi-Node Droplets)
* **Database:** Supabase (PostgreSQL)
* **Automation Engine:** GitHub Actions (Python 3.11 Runtime)
* **Core CTI Engine:** Vertex AI Gemini API 
* **Frontend Visualization:** HTML5 / Tailwind CSS / Three.js (Deployed via GitHub Pages) / FreeIPAPI

---

## Security & Optimization Principles

* **Deduplication Shield:** The processing engine builds unique signature hashes based on `IP | Classification | Node Location`. Repeating brute-force or socket-flooding attacks are consolidated dynamically to keep frontend loading speeds optimized.
* **Fail-Safe Execution State:** Database sync state flags mutate *inside* the secure execution thread before repository updates commit. This eliminates duplicate token processing even during upstream network connection drops.
<img width="1919" height="973" alt="image" src="https://github.com/user-attachments/assets/b750a37c-69d2-4aed-99e6-479964b4cf28" />
