# Path Agent Workflow - Complete Documentation

## Overview
The Path Agent is a **heuristic-based learning path recommendation engine** that analyzes a student's learning history and generates personalized chapter recommendations ranked by priority.

**Architecture Type:** Pure heuristic scoring (not LangGraph)
**Provider:** Backend-IA FastAPI service
**Endpoints:** 
- `GET /path/recommend/{student_id}` — fetch profile from Analytics Service
- `POST /path/recommend` — accept StudentProfile directly

---

## 1. Data Flow Entry Points

### Endpoint 1: GET /path/recommend/{student_id}
```
Frontend/Analytics → [path.py] → [learning_profile_service.py] → [Analytics Service]
                         ↓
                  StudentProfile fetched
                         ↓
                  [path_agent.py] → Recommendations
```

**Flow:**
1. API receives `student_id` (UUID) and optional `course_id`
2. Calls `fetch_student_profile(student_id, course_id)` via HTTP to Analytics Service
3. Validates response as dict
4. Converts to `StudentProfile` pydantic model
5. Passes to `recommend_learning_path()`

**Error Handling:**
- HTTP 400: Analytics Service returns 4xx status
- HTTP 502: Analytics Service unreachable (RuntimeError)
- HTTP 500: JSON parsing fails or unexpected response format

**Audit Trail:**
- Records event type: `path.recommend.by_student`
- Captures: duration_ms, source="analytics-service", recommended_steps count

---

### Endpoint 2: POST /path/recommend
```
Frontend → [Request Body: StudentProfile] → [path_agent.py] → Recommendations
```

**Flow:**
1. API receives `StudentProfile` JSON body
2. Validates against pydantic schema
3. Passes directly to `recommend_learning_path()`

**Audit Trail:**
- Records event type: `path.recommend`
- Captures: duration_ms, recommended_steps count

---

## 2. StudentProfile Input Schema

**Source:** Analytics Service API or direct POST body

```python
StudentProfile {
    student_id: UUID              # e.g., "550e8400-e29b-41d4-a716-446655440000"
    course_id: UUID               # e.g., "660e8400-e29b-41d4-a716-446655440001"
    completed_chapters: [UUID]    # Chapters already finished
    scores: Dict[str, float]      # {"chapter_id": 0.85, "chapter_id": 0.40}
    weak_topics: [str]            # Explicitly marked weak areas by student/system
}
```

**Example:**
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "660e8400-e29b-41d4-a716-446655440001",
  "completed_chapters": ["ch_001", "ch_002", "ch_003"],
  "scores": {
    "ch_001": 0.92,
    "ch_002": 0.45,
    "ch_003": 0.75,
    "ch_004": 0.30
  },
  "weak_topics": ["calculus", "derivatives"]
}
```

---

## 3. Path Agent Algorithm

### Step 1: Profile Validation
```python
validated_profile = StudentProfile.model_validate(profile)
```
Pydantic ensures all fields match schema and UUIDs are valid.

---

### Step 2: Build Candidate Set
Merge three sources of information into unique chapters:

```
Candidates = UNION(
    weak_topics,
    completed_chapters, 
    chapters_with_scores
)
```

**Logic:**
- Iterate through weak_topics → add all
- Iterate through completed_chapters → add all
- Iterate through scores.keys() → add all chapters with scores
- Skip any chapter with NO metadata (no score, not completed, not weak)
- Maintain insertion order

**Data Structure:**
```python
candidates: List[(chapter_id, score, is_completed, is_weak)]
```

Example from above:
```
[
  ("ch_001", 0.92, True,  False),   # completed + scored
  ("ch_002", 0.45, True,  False),   # completed but low score
  ("ch_003", 0.75, True,  False),   # completed
  ("ch_004", 0.30, False, False),   # low score, not completed
  ("calculus", None, False, True),  # weak but no score
  ("derivatives", None, False, True) # weak but no score
]
```

---

### Step 3: Assign Priority Labels

Priority is determined by **four factors**:

| Factor | Impact | Priority |
|--------|--------|----------|
| Is weak topic? | YES → Priority **1** | urgence |
| Score < 0.60 (60%)? | YES → Priority **1** | urgence |
| Score 0.60-0.80? | YES → Priority **2** | consolidation |
| Not yet completed? | YES → Priority **2** | progression |
| Completed + score ≥ 0.80? | YES → Priority **3** | approfondissement |

**Decision Tree:**
```
if weak_topic OR score < 0.60:
    priority = 1 ("urgence")
elif score < 0.80:
    priority = 2 ("consolidation")
elif not completed:
    priority = 2 ("progression")
else:
    priority = 3 ("approfondissement")
```

**Example Assignments:**
| Chapter | Score | Completed | Weak | Priority | Label |
|---------|-------|-----------|------|----------|-------|
| ch_001 | 0.92 | ✓ | ✗ | 3 | approfondissement |
| ch_002 | 0.45 | ✓ | ✗ | 1 | urgence |
| ch_003 | 0.75 | ✓ | ✗ | 2 | consolidation |
| ch_004 | 0.30 | ✗ | ✗ | 1 | urgence |
| calculus | None | ✗ | ✓ | 1 | urgence |
| derivatives | None | ✗ | ✓ | 1 | urgence |

---

### Step 4: Rank Candidates

Sorting key has **three tiers**:

```python
sort_key = (
    priority_number,          # Tier 1: 1 < 2 < 3
    1.0 if score is None else score,  # Tier 2: None (1.0) > low scores
    chapter_id                # Tier 3: Alphabetical (tiebreaker)
)
```

**Interpretation:**
1. **Tier 1:** Urgence (1) → Consolidation (2) → Deepening (3)
2. **Tier 2:** Within same priority, no-score chapters (1.0) come first, then by score ascending (worst first)
3. **Tier 3:** Alphabetical for identical (priority, score)

**Example Ranking:**
```
Rank  Priority  Score   Chapter          Reason
---   --------  -----   -------          ------
1     1 (urgen) 0.30    ch_004           urgent + lowest score
2     1 (urgen) 1.0     calculus         urgent + no score (weak)
3     1 (urgen) 1.0     derivatives      urgent + no score (weak)
4     2 (cons)  0.45    ch_002           consolidation + low score
5     2 (cons)  None    (not present)    -
6     3 (deep)  0.92    ch_001           already mastered
```

---

### Step 5: Build Reasons & Steps

For each ranked candidate, generate human-readable explanation:

```python
def _build_reason(chapter_id, score, completed, weak_topic) -> str:
    parts = []
    if weak_topic:
        parts.append("faiblesse signalee dans l'historique")
    if score is not None:
        parts.append(f"score actuel {score:.0%}")
    if completed:
        parts.append("deja traite")
    else:
        parts.append("pas encore termine")
    return f"{chapter_id}: " + ", ".join(parts)
```

**Example Reasons:**
- `"ch_004: pas encore termine, score actuel 30%"`
- `"calculus: faiblesse signalee dans l'historique, pas encore termine"`
- `"ch_002: score actuel 45%, deja traite"`

---

### Step 6: Cap at MAX_RECOMMENDED_STEPS

**Limit:** `MAX_RECOMMENDED_STEPS = 5` steps maximum

Build `RecommendedStep` objects up to limit:

```python
RecommendedStep {
    chapter_id: str,
    reason: str,
    priority: int (1-3)
}
```

---

### Step 7: Generate Summary

Count recommendations by priority:

```python
gap_count = sum(step.priority == 1 for step in steps)
consolidation_count = sum(step.priority == 2 for step in steps)
mastery_count = sum(step.priority == 3 for step in steps)
```

**Summary Template Selection:**

| Condition | Template |
|-----------|----------|
| gap_count > 0 | `"Parcours centre sur {gap_count} lacune(s) prioritaire(s) et {consolidation_count} chapitre(s) a consolider."` |
| consolidation_count > 0 | `"Parcours de consolidation avec {consolidation_count} chapitre(s) a renforcer et {mastery_count} suggestion(s) d'approfondissement."` |
| else | `"Parcours d'approfondissement: {mastery_count} chapitre(s) deja maitris(es) sont proposes pour aller plus loin."` |

**Example Summaries:**
- `"Parcours centre sur 2 lacune(s) prioritaire(s) et 1 chapitre(s) a consolider."`
- `"Parcours de consolidation avec 1 chapitre(s) a renforcer et 1 suggestion(s) d'approfondissement."`
- `"Parcours d'approfondissement: 1 chapitre(s) deja maitris(es) sont proposes pour aller plus loin."`

---

### Step 8: Fallback Path

**Condition:** No candidates found (empty profile)

**Behavior:**
```python
fallback_step = RecommendedStep(
    chapter_id=completed_chapters[-1] OR "onboarding",
    reason="Aucun signal d'historique exploitable; proposer une reprise generale.",
    priority=2
)
summary = (
    "Parcours de reprise generalise: aucune lacune explicite detectee, "
    "le plan demarre par une consolidation large."
)
```

---

## 4. Output Format

```python
LearningPathResponse {
    student_id: UUID,
    course_id: UUID,
    recommended_steps: List[RecommendedStep],  # 1-5 steps
    summary: str,                               # Human-readable explanation
    provider: "heuristic"                       # Algorithm identifier
}
```

**JSON Example:**
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "660e8400-e29b-41d4-a716-446655440001",
  "recommended_steps": [
    {
      "chapter_id": "ch_004",
      "reason": "ch_004: pas encore termine, score actuel 30%",
      "priority": 1
    },
    {
      "chapter_id": "calculus",
      "reason": "calculus: faiblesse signalee dans l'historique, pas encore termine",
      "priority": 1
    },
    {
      "chapter_id": "ch_002",
      "reason": "ch_002: score actuel 45%, deja traite",
      "priority": 2
    }
  ],
  "summary": "Parcours centre sur 2 lacune(s) prioritaire(s) et 1 chapitre(s) a consolider.",
  "provider": "heuristic"
}
```

---

## 5. Configuration Parameters

**Hardcoded in [path_agent.py](Backend-IA/app/agents/path_agent.py):**

```python
LOW_SCORE_THRESHOLD = 0.60         # Priority 1 if score < 60%
CONSOLIDATION_THRESHOLD = 0.80     # Priority 2 if score < 80%
MAX_RECOMMENDED_STEPS = 5          # Return max 5 recommendations
```

**Key Insight:** These are tuning parameters for learning path prioritization.
- Lowering `LOW_SCORE_THRESHOLD` makes more chapters "urgent"
- Raising `CONSOLIDATION_THRESHOLD` reduces consolidation priority assignments
- `MAX_RECOMMENDED_STEPS` controls cognitive load (5 is typical sweet spot)

---

## 6. Integration Points

### Analytics Service API
**URL Template:** `{ANALYTICS_SERVICE_BASE_URL}/students/{student_id}/profile?courseId={course_id}`

**Timeout:** `ANALYTICS_SERVICE_TIMEOUT_SECONDS` (from settings)

**Expected Response:**
```json
{
  "student_id": "...",
  "course_id": "...",
  "completed_chapters": [...],
  "scores": {...},
  "weak_topics": [...]
}
```

**Failure Modes:**
- HTTP 4xx → Catch HTTPError, log details, return 400
- Connection timeout → Catch URLError, return 502
- Invalid JSON → Catch JSONDecodeError, return 500

---

## 7. Logging & Monitoring

### Log Lines Emitted

**Normal Path (with candidates):**
```
[PathAgent] student=<id> course=<id> completed=<n> weak=<n> scores=<n> steps=<n>
```

**Fallback Path (no candidates):**
```
[PathAgent] student=<id> course=<id> -> fallback path
```

### Audit Events Recorded

**Event Type 1: `path.recommend.by_student` (GET endpoint)**
```python
{
    "event_type": "path.recommend.by_student",
    "endpoint": "/path/recommend/{student_id}",
    "status_code": 200 | 400 | 502 | 500,
    "success": True | False,
    "duration_ms": int,
    "provider": "heuristic",
    "course_id": UUID,
    "payload_hash": sha256(student_id + course_id),
    "details": {
        "recommended_steps": int,
        "source": "analytics-service"
    },
    "error": str (if failed)
}
```

**Event Type 2: `path.recommend` (POST endpoint)**
```python
{
    "event_type": "path.recommend",
    "endpoint": "/path/recommend",
    "status_code": 200 | 400 | 500,
    "success": True | False,
    "duration_ms": int,
    "provider": "heuristic",
    "course_id": UUID,
    "payload_hash": sha256(student_id + course_id + completed_count + weak_count),
    "details": {
        "recommended_steps": int
    },
    "error": str (if failed)
}
```

---

## 8. Performance Characteristics

### Computational Complexity
- **Time:** O(n log n) where n = candidates count
  - Candidate building: O(n)
  - Sorting: O(n log n)
  - Summary generation: O(n)

- **Space:** O(n) for candidate list and recommendations

### Typical Performance
| Input Size | Operation | Time |
|------------|-----------|------|
| 50 chapters | Recommendation | <10ms |
| 100 chapters | Recommendation | <10ms |
| 200 chapters | Recommendation | <20ms |

**Bottleneck:** Network call to Analytics Service (100-500ms typical)

---

## 9. Error Scenarios & Handling

| Scenario | Error Type | HTTP Response | Recovery |
|----------|-----------|---------------|----------|
| Invalid student_id format | ValueError (validation) | 400 | Client retries with valid UUID |
| Analytics Service offline | RuntimeError (URLError) | 502 | Retry with backoff, fallback to cached profile |
| Malformed Analytics response | RuntimeError (JSONDecodeError) | 500 | Log error, alert ops team |
| Empty student profile (no chapters) | (none - fallback) | 200 | Return generic consolidation path |
| Negative or >1.0 score | _coerce_score clamps | 200 | Scores normalized to [0.0, 1.0] |

---

## 10. Future Enhancement Opportunities

### Current Limitations
1. **Heuristic-only:** No machine learning or adaptive personalization
2. **Single model:** Same algorithm for all students (no clustering/segmentation)
3. **Static thresholds:** No tuning based on course difficulty
4. **No prerequisites:** Ignores chapter dependencies
5. **No time constraints:** Assumes unlimited learning time

### Proposed Enhancements
1. **LangGraph Agent:** Integrate with other agents (Assessment, Tutor) for context-aware recommendations
2. **ML-based Scoring:** Train model on completion rate, assessment results, time-to-complete
3. **Prerequisite Graph:** Model chapter dependencies as DAG, respect ordering
4. **Time Budgeting:** Estimate effort and distribute recommendations across weeks
5. **Difficulty Adaptation:** Adjust thresholds based on course/chapter difficulty ratings
6. **A/B Testing:** Measure completion rates for different recommendation strategies

---

## 11. Request-Response Lifecycle Example

### Request 1: GET /path/recommend/{student_id}

**Input:**
```
GET /path/recommend/550e8400-e29b-41d4-a716-446655440000?courseId=660e8400-e29b-41d4-a716-446655440001
```

**Internal Flow:**
```
1. Parse student_id, course_id from URL
2. Call fetch_student_profile(student_id, course_id)
   ├─ Build HTTP URL: {ANALYTICS_BASE_URL}/students/550e8400-.../profile?courseId=660e8400-...
   ├─ Execute HTTP GET (timeout: settings.ANALYTICS_SERVICE_TIMEOUT_SECONDS)
   ├─ Decode JSON response
   └─ Return dict
3. Validate as StudentProfile
4. Call recommend_learning_path(profile)
   ├─ Build candidates: [weak_topics, completed, scores]
   ├─ Rank by (priority, score, chapter_id)
   ├─ Generate RecommendedStep objects (max 5)
   ├─ Count gaps/consolidation/mastery
   └─ Generate summary text
5. Record audit event (type: path.recommend.by_student)
6. Return LearningPathResponse (HTTP 200)
```

**Output:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "660e8400-e29b-41d4-a716-446655440001",
  "recommended_steps": [...],
  "summary": "Parcours centre sur 2 lacune(s)...",
  "provider": "heuristic"
}
```

---

## 12. Code Locations

| Component | File | Key Functions |
|-----------|------|---|
| API Routing | [Backend-IA/app/api/path.py](Backend-IA/app/api/path.py) | `recommend_path()`, `recommend_path_by_student()` |
| Core Logic | [Backend-IA/app/agents/path_agent.py](Backend-IA/app/agents/path_agent.py) | `recommend_learning_path()`, `_build_candidates()`, `_priority_label()` |
| Data Models | [Backend-IA/app/schemas/path_schema.py](Backend-IA/app/schemas/path_schema.py) | `StudentProfile`, `RecommendedStep`, `LearningPathResponse` |
| Data Fetching | [Backend-IA/app/services/learning_profile_service.py](Backend-IA/app/services/learning_profile_service.py) | `fetch_student_profile()` |
| Audit Trail | [Backend-IA/app/db/ingestion_registry.py](Backend-IA/app/db/ingestion_registry.py) | `record_audit_event()` |

---

## 13. Configuration Dependencies

**From [Backend-IA/app/core/config.py](Backend-IA/app/core/config.py):**
```python
ANALYTICS_SERVICE_BASE_URL: str       # Where to fetch student profiles
ANALYTICS_SERVICE_TIMEOUT_SECONDS: int  # HTTP timeout (default ~10s)
```

**From [Backend-IA/.env](Backend-IA/.env):**
```bash
ANALYTICS_SERVICE_BASE_URL=http://analytics-service:8080
ANALYTICS_SERVICE_TIMEOUT_SECONDS=10
```

---

## 14. Sequence Diagram

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ GET /path/recommend/{student_id}
       │ or POST /path/recommend {StudentProfile}
       ▼
┌──────────────────────┐
│  path.py API Router  │
└──────┬───────────────┘
       │
       ├─ (if GET) fetch_student_profile()
       │           │
       │           └─ HTTP GET Analytics Service
       │               │
       │               ▼
       │           ┌──────────────────────┐
       │           │ Analytics Service    │
       │           │ /students/{id}/prof  │
       │           └──────────────────────┘
       │               │ Returns StudentProfile JSON
       │               │
       │           ┌─────────────────────────────┐
       │           │ Validate as StudentProfile  │
       │           └────────┬────────────────────┘
       │                    │
       ▼                    │
┌─────────────────────────────────────┐
│  path_agent.recommend_learning_path │
├─────────────────────────────────────┤
│ 1. Build candidates from 3 sources  │
│ 2. Assign priority (1-3)            │
│ 3. Rank by (priority, score, id)    │
│ 4. Generate RecommendedStep objects │
│ 5. Build summary text               │
│ 6. Return LearningPathResponse      │
└─────────────────────────────────────┘
       │
       ▼
┌──────────────────────┐
│ record_audit_event() │
│ (ingestion_registry) │
└──────────────────────┘
       │
       ▼
┌──────────────────────┐
│   HTTP 200 + JSON    │
│ LearningPathResponse │
└──────────────────────┘
       │
       ▼
┌─────────────┐
│   Frontend  │
│   (Display  │
│  Recommendations)
└─────────────┘
```

---

## Summary

The **Path Agent** is a deterministic heuristic-based system that:

1. ✅ Accepts student learning profiles (from Analytics or direct POST)
2. ✅ Builds a candidate set from weak topics, completed chapters, and scores
3. ✅ Assigns priority labels (urgent, consolidation, progression, deepening)
4. ✅ Ranks candidates by priority (descending) then by performance (ascending)
5. ✅ Generates 1-5 recommended steps with human-readable reasons
6. ✅ Produces a summary explaining the learning path strategy
7. ✅ Records audit trail for analytics/compliance
8. ✅ Handles errors gracefully with proper HTTP status codes

**Key Design Principle:** Simplicity and transparency — students and instructors can understand why each chapter is recommended and in what order.
