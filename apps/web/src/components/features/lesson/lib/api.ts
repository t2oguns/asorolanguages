import { api } from '@/lib/api/api';
import type { components } from '@/lib/api/api-schema';
import type { BatchResponse } from '../types';

export const startLesson = (code: string) => api('/api/v1/courses/lesson/{code}/sessions/', {
  method: 'post', params: { path: { code } }, cache: 'no-store', body: JSON.stringify({}),
});
export const submitLesson = (code: string, sessionId: string, responses: BatchResponse[]) => api('/api/v1/courses/lesson/{code}/sessions/{session_id}/submit/', {
  method: 'post', params: { path: { code, session_id: sessionId } }, cache: 'no-store', body: JSON.stringify({ responses } satisfies components['schemas']['LessonBatchSubmit']),
});
