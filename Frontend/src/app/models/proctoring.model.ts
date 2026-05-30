export enum FraudEventType {
  TAB_SWITCH = 'TAB_SWITCH',
  DEVICE_MISMATCH = 'DEVICE_MISMATCH',
  FACE_ABSENT = 'FACE_ABSENT',
  MULTI_FACE = 'MULTI_FACE',
  PHONE_DETECTED = 'PHONE_DETECTED',
}

export interface StartSessionRequest {
  studentId: string;
  examId: string;
  attemptId: string;
  deviceFingerprint?: string;
}

export interface FraudEventRequest {
  sessionId: string;
  eventType: FraudEventType;
  confidenceScore: number;
  details?: string;
}

export interface ProctoringSessionResponse {
  id: string;
  studentId: string;
  examId: string;
  attemptId: string;
  status: string;
  fraudScore: number;
  deviceFingerprint: string | null;
  startedAt: string;
  endedAt: string | null;
}

export interface FraudEventResponse {
  id: string;
  sessionId: string;
  studentId: string;
  examId: string;
  eventType: FraudEventType;
  confidenceScore: number;
  details: string | null;
  detectedAt: string;
}
