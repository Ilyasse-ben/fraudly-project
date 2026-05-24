# Student Score Calculation & Database Write Audit

## Overview
Student scores are calculated in **two stages**:
1. **Automatic Multiple Choice Scoring** (Java) - calculated immediately upon submission
2. **LLM-Based Open Answer Scoring** (Python) - asynchronous scoring via Kafka

---

## 1. AUTOMATIC SCORING (Java Backend)

### Location: `Backend-Spring/assessment-service`

#### A. REST Endpoint to Submit Answers
**Class:** `ExamController.java`
**Endpoint:** `POST /api/exams/attempts/submit`

```java
@PostMapping("/attempts/submit")
public ResponseEntity<ExamAttemptResponse> submitAttempt(@RequestBody SubmitAttemptRequest request) {
    return ResponseEntity.ok(examAttemptService.submitAttempt(request));
}
```

#### B. Score Calculation & Storage Logic
**Class:** `ExamAttemptServiceImpl.java`
**Method:** `submitAttempt(SubmitAttemptRequest request)`

**Score Calculation Algorithm:**
```java
double totalScore = 0;
double maxScore = 0;

for (SubmitAnswerRequest answerReq : request.getAnswers()) {
    ExamQuestion question = examQuestionRepository.findById(answerReq.getQuestionId());
    maxScore += question.getPoints();

    if (question.getType() == QuestionType.QCM_MULTIPLE) {
        // Multiple choice: All correct choices must be selected = full points
        long correctSelected = answerReq.getSelectedChoiceIds().stream()
            .filter(id -> questionChoiceRepository.findById(id)
                .map(QuestionChoice::getIsCorrect).orElse(false))
            .count();
        long totalCorrect = questionChoiceRepository.findByQuestionId(question.getId())
            .stream().filter(QuestionChoice::getIsCorrect).count();
        
        if (totalCorrect > 0 && correctSelected == totalCorrect) {
            points = question.getPoints();  // Full credit if all correct choices selected
        }
        answer.setPointsAwarded(points);
        totalScore += points;
        
    } else if (question.getType() == QuestionType.QCM_SINGLE || QuestionType.TRUE_FALSE) {
        // Single choice or True/False: Binary scoring
        boolean isCorrect = questionChoiceRepository.findById(answerReq.getSelectedChoiceId())
            .map(QuestionChoice::getIsCorrect).orElse(false);
        
        answer.setPointsAwarded(isCorrect ? question.getPoints() : 0.0);
        if (isCorrect) totalScore += question.getPoints();
        
    } else if (question.getType() == QuestionType.OPEN) {
        // Open questions: Not graded immediately (requires human/AI review)
        answer.setAnswerText(answerReq.getAnswerText());
        answer.setIsGraded(false);
        answer.setPointsAwarded(0.0);
    }
    
    examAnswerRepository.save(answer);
}

// Update attempt with calculated scores
attempt.setStatus(AttemptStatus.SUBMITTED);
attempt.setSubmittedAt(LocalDateTime.now());
attempt.setScore(totalScore);          // Total points earned
attempt.setMaxScore(maxScore);         // Total possible points
attempt = examAttemptRepository.save(attempt);
```

**Database Tables Affected:**
- `exam_attempt` - stores `score` and `max_score` fields
- `exam_answer` - stores `points_awarded` and `is_graded` fields for each answer

---

## 2. OPEN QUESTION SCORING (Python LLM-Based)

### Location: `Backend-IA/app/services/exam_scorer_service.py`

#### A. Kafka Consumer for Correction Requests
**Class:** `ExamScorerConsumer`
**Topic:** `exam.correction.requested`
**Consumer Group:** `fraudly-ia-service-exam-scorer`

```python
class ExamScorerConsumer:
    def __init__(self):
        self._consumer = KafkaConsumer(
            settings.KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"{settings.KAFKA_GROUP_ID}-exam-scorer",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            max_poll_records=10,
        )
```

**Expected Input Format (from Java):**
```json
{
  "exam_id": "uuid",
  "course_id": "uuid",
  "requested_at": "iso-string",
  "submissions": [
    {
      "student_id": "uuid",
      "open_answers": [
        {
          "question_id": "uuid",
          "student_answer": "student's text response",
          "correct_answer": "expected answer",
          "explanation": "rubric/explanation",
          "max_score": 20
        }
      ]
    }
  ]
}
```

#### B. Score Calculation via LLM
**Class:** `ExamScorerConsumer`
**Method:** `_score_open_answer()`

**Scoring Algorithm:**
```python
def _score_open_answer(
    self,
    student_answer: str,
    correct_answer: str,
    explanation: str,
    max_score: float,
) -> ScoreResult:
    prompt = (
        "Tu es un correcteur d'examen strict et juste.\n"
        "Evalue la reponse et retourne UNIQUEMENT un JSON valide.\n"
        "Schema JSON attendu:\n"
        "{\n"
        '  "score": number,\n'
        '  "feedback": string,\n'
        '  "rubric_justification": string\n'
        "}\n"
        "Contraintes:\n"
        f"- score entre 0 et {max_score}\n"
        "- feedback court, actionnable\n"
        "- justification basee explicitement sur la reponse correcte et l'explication\n\n"
        f"Reponse correcte:\n{correct_answer}\n\n"
        f"Explication attendue:\n{explanation}\n\n"
        f"Reponse etudiant:\n{student_answer}\n"
    )

    llm_result = invoke_with_fallback(prompt)
    
    # Parse JSON response from LLM
    parsed = json.loads(llm_result.answer)
    score = float(parsed.get("score", 0.0))
    feedback = str(parsed.get("feedback", "")).strip()
    justification = str(parsed.get("rubric_justification", "")).strip()
    
    # Clamp score between 0 and max_score
    score = max(0.0, min(score, max_score))
    
    return ScoreResult(
        score=score,
        max_score=max_score,
        feedback=feedback,
        rubric_justification=justification,
        provider=llm_result.provider,
        fallback_used=llm_result.fallback_used,
    )
```

**Provider:** Supports LLM routing with fallback (via `llm_router.py`)

#### C. Publish Scores Back to Java
**Topic:** `exam.scored`

**Output Format:**
```python
output_event = {
    "exam_id": exam_id,
    "course_id": event.get("course_id"),
    "requested_at": requested_at,
    "student_id": student_id,
    "student_name": student_name,
    "question_id": question_id,
    "score": result.score,              # Awarded score
    "max_score": result.max_score,      # Max possible score
    "feedback": result.feedback,
    "scored_at": datetime.now(timezone.utc).isoformat(),
    "rubric_justification": result.rubric_justification,
    "provider": result.provider,        # Which LLM provider scored this
    "fallback_used": result.fallback_used,
}
```

**Consumer Loop:**
```python
async def run_exam_scorer_loop() -> None:
    consumer = get_exam_scorer_consumer()
    if not consumer.start():
        return
    
    try:
        logger.info("[ExamScorer] Loop demarree")
        while True:
            consumer.poll_once()          # Check for new correction requests
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        consumer.stop()
```

---

## 3. SCORE PERSISTENCE TO DATABASE (Java)

### Location: `Backend-Spring/assessment-service`

#### A. Kafka Consumer for Scored Answers
**Class:** `ExamScoredKafkaConsumer.java`
**Topic:** `exam.scored`
**Consumer Group:** `fraudly-assessment-service`

```java
@Component
@RequiredArgsConstructor
public class ExamScoredKafkaConsumer {

    private final ExamAnswerRepository examAnswerRepository;
    private final ExamAttemptRepository examAttemptRepository;
    private final ExamQuestionRepository examQuestionRepository;

    @KafkaListener(
        topics = "${kafka.topic.exam.scored}",
        groupId = "${spring.kafka.consumer.group-id}"
    )
    public void consumeExamScored(String message) {
        try {
            Map<String, Object> event = objectMapper.readValue(message, Map.class);

            UUID questionId = UUID.fromString(event.get("question_id").toString());
            UUID studentId = UUID.fromString(event.get("student_id").toString());
            UUID examId = UUID.fromString(event.get("exam_id").toString());
            double score = Double.parseDouble(event.get("score").toString());
            String feedback = event.get("feedback").toString();

            // Find the student's exam attempt
            ExamAttempt attempt = examAttemptRepository
                .findByExamIdAndStudentId(examId, studentId)
                .orElseThrow(() -> new RuntimeException("Attempt not found"));

            // Update individual answer with LLM score
            examAnswerRepository
                .findByAttemptIdAndQuestionId(attempt.getId(), questionId)
                .ifPresent(answer -> {
                    answer.setPointsAwarded(score);           // Store LLM score
                    answer.setIsGraded(true);
                    answer.setAnswerText(answer.getAnswerText() + "\n[Feedback: " + feedback + "]");
                    examAnswerRepository.save(answer);        // **DATABASE WRITE #1**
                    log.info("[Scorer] Answer updated: question={} student={} score={}", 
                        questionId, studentId, score);
                });

            // Recalculate total attempt score
            recalculateAttemptScore(attempt);

        } catch (Exception e) {
            log.error("[Scorer] Erreur consommation: {}", e.getMessage());
        }
    }

    private void recalculateAttemptScore(ExamAttempt attempt) {
        double totalScore = examAnswerRepository
            .findByAttemptId(attempt.getId())
            .stream()
            .mapToDouble(a -> a.getPointsAwarded() != null ? a.getPointsAwarded() : 0.0)
            .sum();

        attempt.setScore(totalScore);
        attempt.setStatus(AttemptStatus.GRADED);
        examAttemptRepository.save(attempt);  // **DATABASE WRITE #2**
        log.info("[Score] Attempt recalculé: id={} score={}", attempt.getId(), totalScore);
    }
}
```

**Database Tables Updated:**
- `exam_answer` - updates `points_awarded` and `is_graded` fields
- `exam_attempt` - updates `score` field and sets status to `GRADED`

---

## 4. MANUAL SCORE ADJUSTMENT BY PROFESSOR

### Location: `Backend-Spring/assessment-service`

#### A. REST Endpoint to Update Score
**Class:** `ExamController.java`
**Endpoint:** `PATCH /api/exams/answers/{answerId}/score`

```java
@PatchMapping("/answers/{answerId}/score")
public ResponseEntity<Void> updateAnswerScore(
        @PathVariable UUID answerId,
        @RequestParam Double pointsAwarded,
        @RequestParam UUID professorId) {
    examService.updateAnswerScore(answerId, pointsAwarded, professorId);
    return ResponseEntity.ok().build();
}
```

#### B. Score Update Logic
**Class:** `ExamServiceImpl.java`
**Method:** `updateAnswerScore(UUID answerId, Double pointsAwarded, UUID professorId)`

```java
@Override
public void updateAnswerScore(UUID answerId, Double pointsAwarded, UUID professorId) {
    ExamAnswer answer = examAnswerRepository.findById(answerId)
            .orElseThrow(() -> new RuntimeException("Answer not found"));

    // Save original AI score on first modification
    if (answer.getOriginalAiScore() == null) {
        answer.setOriginalAiScore(answer.getPointsAwarded());
    }

    answer.setPointsAwarded(pointsAwarded);
    answer.setModifiedByProfessor(true);
    answer.setModifiedAt(LocalDateTime.now());
    examAnswerRepository.save(answer);  // **DATABASE WRITE #3**

    // Recalculate total exam attempt score
    ExamAttempt attempt = answer.getAttempt();
    double totalScore = examAnswerRepository
            .findByAttemptId(attempt.getId())
            .stream()
            .mapToDouble(a -> a.getPointsAwarded() != null ? a.getPointsAwarded() : 0.0)
            .sum();

    attempt.setScore(totalScore);
    examAttemptRepository.save(attempt);  // **DATABASE WRITE #4**
    
    log.info("[Score] Modified by prof={}: answer={} aiScore={} newScore={}",
            professorId, answerId, answer.getOriginalAiScore(), pointsAwarded);
}
```

---

## 5. SCORE RETRIEVAL & ANALYTICS

### Location: `Backend-Spring/analytics-service`

#### A. Learning Profile Storage
**Entity:** `StudentLearningProfile.java`

```java
@Entity
@Table(name = "student_learning_profile",
    uniqueConstraints = @UniqueConstraint(columnNames = {"student_id", "course_id"})
)
public class StudentLearningProfile {
    @Id
    private UUID id;

    @Column(name = "student_id")
    private UUID studentId;

    @Column(name = "course_id")
    private UUID courseId;

    @Column(name = "scores_json", columnDefinition = "TEXT")
    private String scoresJson;                    // **Stores: {"exam_id": 85.5, "chapter_1": 92.0}**

    @Column(name = "completed_chapters_json", columnDefinition = "TEXT")
    private String completedChaptersJson;

    @Column(name = "weak_topics_json", columnDefinition = "TEXT")
    private String weakTopicsJson;

    @Column(name = "interactions_count")
    private Integer interactionsCount;

    private LocalDateTime lastInteractionAt;
}
```

#### B. REST Endpoint to Get Student Profile
**Class:** `LearningAnalyticsController.java`
**Endpoint:** `GET /api/analytics/students/{studentId}/profile`

```java
@GetMapping("/students/{studentId}/profile")
public ResponseEntity<Map<String, Object>> getStudentProfile(
        @PathVariable UUID studentId,
        @RequestParam(required = false) UUID courseId) {
    return ResponseEntity.ok(
            learningAnalyticsService.getStudentProfile(studentId, courseId)
    );
}
```

#### C. Profile Synchronization Service
**Class:** `LearningAnalyticsServiceImpl.java`
**Method:** `syncStudentProfile(UUID studentId, UUID courseId)`

```java
private void syncStudentProfile(UUID studentId, UUID courseId) {
    StudentLearningProfile profile = studentLearningProfileRepository
            .findByStudentIdAndCourseId(studentId, courseId)
            .orElseGet(() -> StudentLearningProfile.builder()
                    .studentId(studentId)
                    .courseId(courseId)
                    .completedChaptersJson("[]")
                    .scoresJson("{}")
                    .weakTopicsJson("[]")
                    .interactionsCount(0)
                    .build());

    profile.setInteractionsCount(
        (profile.getInteractionsCount() == null ? 0 : profile.getInteractionsCount()) + 1
    );
    profile.setLastInteractionAt(LocalDateTime.now());
    profile.setWeakTopicsJson(writeAsJson(getWeakTopics(studentId, courseId, 3)));
    
    // Initialize JSON fields if empty
    if (profile.getCompletedChaptersJson() == null || profile.getCompletedChaptersJson().isBlank()) {
        profile.setCompletedChaptersJson("[]");
    }
    if (profile.getScoresJson() == null || profile.getScoresJson().isBlank()) {
        profile.setScoresJson("{}");
    }

    studentLearningProfileRepository.save(profile);  // **DATABASE WRITE #5**
}
```

**Repository Interface:**
```java
public interface StudentLearningProfileRepository extends JpaRepository<StudentLearningProfile, UUID> {
    Optional<StudentLearningProfile> findByStudentIdAndCourseId(UUID studentId, UUID courseId);
    Optional<StudentLearningProfile> findTopByStudentIdOrderByUpdatedAtDesc(UUID studentId);
}
```

---

## 6. SCORE CALCULATION WORKFLOW SUMMARY

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: IMMEDIATE SCORING (Multiple Choice/True-False)            │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Student submits exam via: POST /api/exams/attempts/submit       │
│ 2. ExamAttemptServiceImpl.submitAttempt() calculates scores:         │
│    - QCM_SINGLE/TRUE_FALSE: Binary (0 or full points)              │
│    - QCM_MULTIPLE: All correct choices = full points               │
│    - OPEN: Score = 0, isGraded = false                             │
│ 3. Saves to: exam_attempt.score, exam_answer.points_awarded       │
│ 4. Sets attempt status: SUBMITTED                                   │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: REQUEST CORRECTION FOR OPEN QUESTIONS                     │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Professor calls: POST /api/exams/{examId}/correction            │
│ 2. ExamServiceImpl.launchCorrection() publishes event:              │
│    - Topic: exam.correction.requested                               │
│    - Contains all open answers needing scoring                      │
│ 3. Sets exam status: GRADING                                        │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: LLM SCORING (Python Backend)                              │
├─────────────────────────────────────────────────────────────────────┤
│ 1. ExamScorerConsumer listens on: exam.correction.requested        │
│ 2. For each open answer:                                            │
│    - Constructs prompt with: student_answer, correct_answer, rubric│
│    - Calls LLM (with fallback support)                              │
│    - Parses JSON response: {"score": X, "feedback": "...", ...}   │
│    - Clamps score: 0 ≤ score ≤ max_score                           │
│ 3. Publishes result to: exam.scored topic                          │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: PERSIST SCORES (Java Consumer)                            │
├─────────────────────────────────────────────────────────────────────┤
│ 1. ExamScoredKafkaConsumer listens on: exam.scored                │
│ 2. Updates exam_answer: points_awarded = LLM score                  │
│ 3. Recalculates: exam_attempt.score = SUM(all answer scores)      │
│ 4. Sets attempt status: GRADED                                      │
│ 5. Stores feedback in: exam_answer.answer_text                     │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: OPTIONAL PROFESSOR ADJUSTMENT                             │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Professor calls: PATCH /api/exams/answers/{answerId}/score     │
│ 2. ExamServiceImpl.updateAnswerScore():                             │
│    - Saves original AI score (if first modification)               │
│    - Updates points_awarded with new score                         │
│    - Sets modifiedByProfessor = true                               │
│ 3. Recalculates: exam_attempt.score = SUM(all answer scores)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. KEY CONFIGURATION

### Kafka Topics
```properties
# Backend-Spring/assessment-service/src/main/resources/application.properties
kafka.topic.exam.correction.requested=exam.correction.requested
kafka.topic.exam.scored=exam.scored

# Backend-IA/app/core/config.py
KAFKA_TOPIC_EXAM_CORRECTION_REQUESTED = "exam.correction.requested"
KAFKA_TOPIC_EXAM_SCORED = "exam.scored"
```

### Consumer Groups
- Assessment Service: `fraudly-assessment-service`
- Analytics Service: `fraudly-analytics-service`
- Python IA Service: `fraudly-ia-service-exam-scorer`

---

## 8. DATABASE SCHEMA

### Primary Tables
```sql
-- Exam Attempt (stores overall score)
CREATE TABLE exam_attempt (
    id UUID PRIMARY KEY,
    exam_id UUID NOT NULL,
    student_id UUID NOT NULL,
    status VARCHAR(20),  -- STARTED, SUBMITTED, GRADED
    score DOUBLE,        -- Total points earned
    max_score DOUBLE,    -- Total possible points
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exam(id)
);

-- Exam Answer (stores individual question answers & scores)
CREATE TABLE exam_answer (
    id UUID PRIMARY KEY,
    attempt_id UUID NOT NULL,
    question_id UUID NOT NULL,
    answer_text TEXT,
    selected_choice_id UUID,
    points_awarded DOUBLE,       -- Score for this answer
    is_graded BOOLEAN,
    is_correct BOOLEAN,
    original_ai_score DOUBLE,    -- Original LLM score (before professor adjustment)
    modified_by_professor BOOLEAN,
    modified_at TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempt(id),
    FOREIGN KEY (question_id) REFERENCES exam_question(id)
);

-- Student Learning Profile (analytics aggregation)
CREATE TABLE student_learning_profile (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    scores_json TEXT,                -- JSON map: {"exam_id": score, ...}
    completed_chapters_json TEXT,    -- JSON array: ["ch1", "ch2", ...]
    weak_topics_json TEXT,           -- JSON array: ["topic1", "topic2", ...]
    interactions_count INT,
    last_interaction_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(student_id, course_id)
);
```

---

## 9. SUMMARY OF DATABASE WRITE LOCATIONS

| **Location** | **Class** | **Method** | **Table** | **Field** | **Score Source** |
|---|---|---|---|---|---|
| Java | `ExamAttemptServiceImpl` | `submitAttempt()` | `exam_attempt` | `score`, `max_score` | Automatic (MC) |
| Java | `ExamAttemptServiceImpl` | `submitAttempt()` | `exam_answer` | `points_awarded` | Automatic (MC) |
| Java | `ExamScoredKafkaConsumer` | `consumeExamScored()` | `exam_answer` | `points_awarded` | LLM (Open Q) |
| Java | `ExamScoredKafkaConsumer` | `recalculateAttemptScore()` | `exam_attempt` | `score` | Sum of answers |
| Java | `ExamServiceImpl` | `updateAnswerScore()` | `exam_answer` | `points_awarded` | Professor |
| Java | `ExamServiceImpl` | `updateAnswerScore()` | `exam_attempt` | `score` | Sum of answers |
| Java | `LearningAnalyticsServiceImpl` | `syncStudentProfile()` | `student_learning_profile` | `scores_json` | Aggregated |

