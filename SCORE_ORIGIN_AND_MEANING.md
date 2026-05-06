# Les Scores dans le Path Agent - Explication Complète

## TL;DR - Réponse Rapide

| Question | Réponse |
|----------|---------|
| **D'où vient le score ?** | Table PostgreSQL `student_learning_profile` (analytics-service) |
| **Qui l'écrit ?** | assessment-service + exam_scorer_service (Python) |
| **Quand il est écrit ?** | Lors de la correction d'un examen (automatique ou LLM) |
| **Que représente-t-il ?** | Performance numérique [0.0 - 1.0] de l'étudiant dans un chapitre |
| **Format ?** | `Dict[chapter_id: float]` ex: `{"ch_001": 0.85, "ch_002": 0.40}` |

---

## 1. Flux Complet : De l'Examen au Path Agent

```
┌──────────────────────┐
│  Student prend exam  │
│  (chapitre X)        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  ExamController.submitAttempt()  │
│  (assessment-service)            │
│  Calcule score automatiquement:  │
│  QCM_SINGLE/MULTIPLE: 0 ou 100% │
│  TRUE_FALSE: 0 ou 100%           │
│  OPEN: 0 (en attente LLM)        │
└──────┬───────────────────────────┘
       │ Sauvegarde dans:
       │ - exam_attempt.score
       │ - exam_answer.points_awarded
       │
       ▼
┌──────────────────────────────────┐
│  exam.correction.requested       │
│  (Kafka topic)                   │
│  Pour les questions OPEN         │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  exam_scorer_service (Python)    │
│  Scoring LLM des questions OPEN  │
│  (via LangChain + Groq/Gemini)   │
│  Retourne score [0.0 - 1.0]      │
└──────┬───────────────────────────┘
       │ Publie sur:
       │ exam.scored (Kafka)
       │
       ▼
┌──────────────────────────────────┐
│  ExamScoredKafkaConsumer (Java)  │
│  Met à jour:                     │
│  - exam_answer.points_awarded    │
│  - exam_attempt.score (recalc)   │
│  - exam_attempt.status = GRADED  │
└──────┬───────────────────────────┘
       │ Déclenche probablement:
       │ (Kafka event ou HTTP POST)
       │
       ▼
┌──────────────────────────────────┐
│  Analytics Service API           │
│  PUT /students/{id}/chapters/{id}│
│  Sauvegarde score dans:          │
│  student_learning_profile        │
│  .scoresJson = {"ch_X": 0.85}    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  PostgreSQL (analytics-service)  │
│  Table: student_learning_profile │
│  Colonne: scores_json (TEXT)     │
│  {"chapter_001": 0.85,           │
│   "chapter_002": 0.40, ...}      │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  Frontend → GET /path/recommend/ │
│             {student_id}         │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  path.py (Backend-IA)            │
│  fetch_student_profile()         │
│  → HTTP GET Analytics API        │
└──────┬───────────────────────────┘
       │ Récupère StudentProfile:
       │ {
       │   "scores": {"ch_001": 0.85,
       │              "ch_002": 0.40}
       │ }
       │
       ▼
┌──────────────────────────────────┐
│  path_agent.recommend_learning_  │
│             path(profile)        │
│                                  │
│  Utilise scores pour:            │
│  1. Assigner priorités           │
│  2. Trier chapitres (worst first)│
│  3. Générer raisons explicatives │
└──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│  LearningPathResponse             │
│  recommended_steps (max 5)        │
│  sorted by priority + score      │
└──────────────────────────────────┘
```

---

## 2. Signification du Score - Détails

### Qu'est-ce qu'un Score ?

**Définition:** Performance numérique entre 0.0 et 1.0 représentant le % de réussite de l'étudiant dans un chapitre/examen.

**Format:** 
```
0.0  ← 0% correct
0.25 ← 25% correct
0.50 ← 50% correct
0.75 ← 75% correct
0.85 ← 85% correct
1.0  ← 100% correct
```

### Comment est-il Calculé ?

**Cas 1 : Questions QCM / Vrai-Faux / Appariement (Auto-scoring)**
```java
totalScore = 0;
for (Question q : questions) {
    if (answer == correct) {
        totalScore += q.getPoints();  // Ajouter points de la question
    }
}
percentageScore = totalScore / maxPoints;  // Normaliser [0.0 - 1.0]
```

**Exemple:**
```
Question 1 (QCM): 10 points ✓ correct  → +10
Question 2 (QCM): 10 points ✗ faux     → +0
Question 3 (V/F):  5 points ✓ correct  → +5
Total: 15 / 25 = 0.60 (60%)
```

**Cas 2 : Questions OPEN (LLM Scoring)**
```python
# exam_scorer_service.py
prompt = f"""
Chapitre: {chapter}
Rubrique: {rubric}
Réponse étudiant: "{student_answer}"

Évaluer sur 0-100 points basé sur rubrique.
"""
llm_score = groq.invoke(prompt)  # ex: 85 points
percentageScore = llm_score / 100  # 0.85
```

**Exemple Rubrique:**
```
Rubrique Maths - Calcul de Dérivée (100 pts total)
- Identification correcte de f'(x) : 20 pts
- Simplification correcte : 30 pts
- Notation mathématique : 20 pts
- Explication étapes : 30 pts

Réponse: "f'(x) = 2x + 1"
LLM donne: 35/100 (identification bonne, explication manquante)
→ Score = 0.35
```

### Cas 3 : Score Recalculé (Après All Answers Scored)

```java
// Dans ExamScoredKafkaConsumer
double totalScore = 0;
for (ExamAnswer answer : exam.getAnswers()) {
    totalScore += answer.getPointsAwarded();  // Points LLM + auto
}
double maxScore = exam.getMaxScore();
attempt.setScore(totalScore / maxScore);  // Re-normaliser
```

---

## 3. Où sont Stockés les Scores

### Base de Données (PostgreSQL)

**Table:** `student_learning_profile`

| Colonne | Type | Contenu |
|---------|------|---------|
| student_id | UUID | `550e8400-e29b-41d4-a716-446655440000` |
| course_id | UUID | `660e8400-e29b-41d4-a716-446655440001` |
| scores_json | TEXT | `{"chapter_001": 0.85, "chapter_002": 0.40}` |
| completed_chapters_json | TEXT | `["chapter_001", "chapter_002"]` |
| weak_topics_json | TEXT | `["calculus", "derivatives"]` |
| interactions_count | INTEGER | 15 |
| last_interaction_at | TIMESTAMP | 2026-05-03 14:30:00 |
| updated_at | TIMESTAMP | 2026-05-03 14:30:00 |

**Exemple Complet:**
```json
{
  "student_id": "550e8400-e29b-41d4-a716-446655440000",
  "course_id": "660e8400-e29b-41d4-a716-446655440001",
  "scores_json": "{\"chapter_001\": 0.92, \"chapter_002\": 0.45, \"chapter_003\": 0.75, \"chapter_004\": 0.30}",
  "completed_chapters_json": "[\"chapter_001\", \"chapter_002\", \"chapter_003\"]",
  "weak_topics_json": "[\"calculus\", \"derivatives\"]",
  "interactions_count": 42,
  "last_interaction_at": "2026-05-03T14:30:00"
}
```

### En Mémoire (API Response)

```python
# StudentProfile reçu par le Path Agent
StudentProfile(
    student_id="550e8400-e29b-41d4-a716-446655440000",
    course_id="660e8400-e29b-41d4-a716-446655440001",
    completed_chapters=["chapter_001", "chapter_002", "chapter_003"],
    scores={
        "chapter_001": 0.92,
        "chapter_002": 0.45,
        "chapter_003": 0.75,
        "chapter_004": 0.30
    },
    weak_topics=["calculus", "derivatives"]
)
```

---

## 4. Utilisation dans le Path Agent

### Règles de Priorité (basées sur le score)

```python
LOW_SCORE_THRESHOLD = 0.60
CONSOLIDATION_THRESHOLD = 0.80

def _priority_label(score, completed, weak_topic):
    # Score < 0.60 = URGENT
    if weak_topic or (score and score < 0.60):
        return 1, "urgence"
    
    # Score 0.60-0.80 = CONSOLIDATION
    if score and score < 0.80:
        return 2, "consolidation"
    
    # Pas complété = PROGRESSION
    if not completed:
        return 2, "progression"
    
    # Complété + score ≥ 0.80 = DEEPENING
    return 3, "approfondissement"
```

### Exemple Concret

**Input:**
```python
profile = StudentProfile(
    student_id="550e8400-e29b-41d4-a716-446655440000",
    course_id="660e8400-e29b-41d4-a716-446655440001",
    completed_chapters=["ch_001", "ch_002", "ch_003"],
    scores={
        "ch_001": 0.92,      # Excellent, complété
        "ch_002": 0.45,      # Mauvais score, complété
        "ch_003": 0.75,      # Moyen, complété
        "ch_004": 0.30       # Très mauvais, NON complété
    },
    weak_topics=["calculus"]
)
```

**Analyse du Path Agent:**

| Chapter | Score | Completed | Weak | Priority | Reason |
|---------|-------|-----------|------|----------|--------|
| ch_004 | 0.30 | ✗ | ✗ | **1 (urgent)** | "`ch_004: pas encore termine, score actuel 30%`" |
| calculus | None | ✗ | ✓ | **1 (urgent)** | "`calculus: faiblesse signalee dans l'historique, pas encore termine`" |
| ch_002 | 0.45 | ✓ | ✗ | **1 (urgent)** | "`ch_002: score actuel 45%, deja traite`" |
| ch_003 | 0.75 | ✓ | ✗ | **2 (consol)** | "`ch_003: score actuel 75%, deja traite`" |
| ch_001 | 0.92 | ✓ | ✗ | **3 (deep)** | "`ch_001: score actuel 92%, deja traite`" |

**Output Recommendations (max 5):**
```json
{
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
      "priority": 1
    },
    {
      "chapter_id": "ch_003",
      "reason": "ch_003: score actuel 75%, deja traite",
      "priority": 2
    }
  ],
  "summary": "Parcours centre sur 3 lacune(s) prioritaire(s) et 1 chapitre(s) a consolider."
}
```

---

## 5. Interprétation des Seuils

### LOW_SCORE_THRESHOLD (0.60)
- **Meaning:** Score inférieur à 60% = compression **immédiate** requise
- **Use Case:** Si étudiant a 45% dans une matière, c'est critique
- **Tuning:** 
  - Baisser à 0.50 = plus tolérant (seul très faible = urgent)
  - Augmenter à 0.70 = plus strict (70% = urgent)

### CONSOLIDATION_THRESHOLD (0.80)
- **Meaning:** Score entre 60-80% = matière à **consolider**
- **Use Case:** Si étudiant a 75%, il sait ce chapitre mais doit l'améliorer
- **Tuning:**
  - Baisser à 0.70 = moins de chapitres "à consolider"
  - Augmenter à 0.90 = plus de chapitres "à consolider"

### Score = None (Pas d'évaluation)
- **Meaning:** Chapitre **jamais évalué** (pas d'examen fait)
- **Priority:** Si faible topic → Priority 1, sinon filtré hors recommendations
- **Interpretation:** "Pas encore évalué, à explorer"

---

## 6. Exemple Complet du Calcul de Score

### Scenario: Étudiant fait Examen Chapitre "Calcul"

**Step 1: Examen Structure**
```
Chapitre: CALCUL (100 points max)

Question 1 (QCM): Dérivée de x² = ?
  Options: a) 2x ✓ b) x c) 2
  Points: 20
  Réponse étudiant: a) 2x
  Score: 20/20 ✓

Question 2 (QCM Multiple): Intégrales de (x² + 1) ?
  Correct: (x³/3 + x), (1/3 x³ + x)
  Points: 20
  Réponse étudiant: (x³/3 + x) ✓
  Score: 20/20 ✓

Question 3 (Vrai/Faux): ln(0) = 0 ?
  Correct: Faux
  Points: 10
  Réponse étudiant: Vrai ✗
  Score: 0/10

Question 4 (OPEN): "Expliquer pourquoi d/dx(e^x) = e^x"
  Points: 50
  Réponse: "La dérivée de e^x est elle-même, c'est une fonction spéciale."
  Score: TBD (LLM) → 30/50 (incomplète)

TOTAL: 20 + 20 + 0 + 30 = 70 points
PERCENTAGE: 70 / 100 = 0.70 (70%)
```

**Step 2: Sauvegarde Immédiate (Auto-scoring)**
```java
// ExamAttemptServiceImpl.submitAttempt()
exam_attempt {
  score: 0.30  // Seulement Q1, Q2, Q3 (auto-scored)
  max_score: 1.0
  status: "SUBMITTED"
}

exam_answer[0] {
  question_id: "q1"
  points_awarded: 0.20  // 20/100
}

exam_answer[1] {
  question_id: "q2"
  points_awarded: 0.20  // 20/100
}

exam_answer[2] {
  question_id: "q3"
  points_awarded: 0.00  // 0/100
}

exam_answer[3] {
  question_id: "q4"
  points_awarded: null  // Attendant LLM
  is_graded: false
}
```

**Step 3: Scoring LLM (Asynchrone)**
```python
# exam_scorer_service.py
open_answer = {
    "text": "La dérivée de e^x est elle-même...",
    "rubric": "Explain derivative of e^x (50 pts)"
}

llm_prompt = f"""
Évaluer cette réponse sur 0-50 points.
Rubric: {open_answer['rubric']}
Réponse: {open_answer['text']}
"""

score_points = llm.invoke(llm_prompt)  # Returns: 30
```

**Step 4: Mise à Jour (Kafka Event)**
```java
// ExamScoredKafkaConsumer.consumeExamScored()
exam_answer[3] {
  points_awarded: 0.30  // 30/100
  is_graded: true
}

// Recalculate total
exam_attempt {
  score: 0.70  // (20+20+0+30)/100
  status: "GRADED"
}
```

**Step 5: Sync to Analytics**
```
Analytics Service API:
PUT /students/550e8400-e29b-41d4-a716-446655440000/chapters/calcul

Body:
{
  "score": 0.70
}

Updates student_learning_profile:
{
  "scores_json": "{\"calcul\": 0.70, ...}"
}
```

**Step 6: Path Agent sees it**
```python
profile.scores = {
    "calcul": 0.70,  # Newly updated
    ...
}

# Priority assignment
if 0.70 < 0.80:  # CONSOLIDATION
    priority = 2
    reason = "calcul: score actuel 70%, deja traite"
```

---

## 7. Diagnostic : Pourquoi un Score Peut Manquer

| Cas | Raison | Solution |
|-----|--------|----------|
| Score = None pour ch_001 | Étudiant n'a jamais passé examen ch_001 | Créer + soumettre examen |
| Score = 0.0 | Examen fait, réponses toutes fausses | Revoir le chapitre, retenter |
| Score = 0.5 | Score binaire (question autorisée/refusée) | Vérifier rubrique examen |
| scores_json = "{}" | Profil créé mais aucun examen tracé | Exécuter exam + attendre sync |
| Old score (0.45) pas à jour | Student a refait examen (0.85) non encore synced | Attendre synchronisation (Kafka lag) |

---

## 8. Fichiers Sources

| Composant | Fichier | Responsabilité |
|-----------|---------|-----------------|
| Auto-scoring | `Backend-Spring/assessment-service/ExamAttemptServiceImpl.java:60-145` | Calcule score pour QCM/V-F |
| LLM Scoring | `Backend-IA/app/services/exam_scorer_service.py` | LLM-powered OPEN answer scoring |
| Kafka Consumer | `Backend-Spring/analytics-service/ExamScoredKafkaConsumer.java` | Met à jour exam_attempt.score |
| Profile API | `Backend-Spring/analytics-service/LearningAnalyticsServiceImpl.java:107-143` | Retourne profile avec scores |
| Path Fetcher | `Backend-IA/app/services/learning_profile_service.py:fetch_student_profile()` | HTTP GET profile depuis Analytics |
| Path Agent | `Backend-IA/app/agents/path_agent.py:_priority_label()` | Utilise score pour assigner priorité |
| Path API | `Backend-IA/app/api/path.py` | REST endpoints pour recommendations |

---

## Summary

```
Score = Performance Numérique [0.0 - 1.0]
       ↓ Source: exam_attempt table (après auto-score + LLM-score)
       ↓ Stocké dans: student_learning_profile.scores_json (PostgreSQL)
       ↓ Récupéré via: Analytics Service API
       ↓ Utilisé par: Path Agent pour assigner priorités
       ↓ Affichage: Frontend reçoit ranked recommendations
       
Formule: Points_awarded / Max_points = Score [0.0 - 1.0]

Priorités (Path Agent):
  Score < 0.60 ou weak_topic → Priority 1 (URGENT)
  Score < 0.80 ou not completed → Priority 2 (CONSOLIDATION)
  Score ≥ 0.80 + completed → Priority 3 (DEEPENING)
```
