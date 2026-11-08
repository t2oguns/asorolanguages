import { http, HttpResponse } from 'msw';
import { server } from '../../../../../test/server';
import { startLesson, submitLesson } from './api';

it('uses the generated lesson endpoints through the shared cookie/CSRF API client', async () => {
  document.cookie = 'csrftoken=lesson-token';
  const received: { url: string; method: string; csrf: string | null; credentials: string; body: unknown }[] = [];
  server.use(http.post('http://api.test/api/v1/courses/lesson/greeting/sessions/*', async ({ request }) => {
    received.push({ url: request.url, method: request.method, csrf: request.headers.get('x-csrftoken'), credentials: request.credentials, body: await request.json() });
    return HttpResponse.json(request.url.endsWith('/submit/') ? { submitted: true, lesson_attempt_id: 'delivery-id' } : { lesson_attempt_id: 'delivery-id' });
  }));
  await startLesson('greeting');
  const responses = [{ exercise_id: 'exercise-id', response: ['option-id'] }];
  await submitLesson('greeting', 'delivery-id', responses);
  expect(received).toEqual([
    { url: 'http://api.test/api/v1/courses/lesson/greeting/sessions/', method: 'POST', csrf: 'lesson-token', credentials: 'include', body: {} },
    { url: 'http://api.test/api/v1/courses/lesson/greeting/sessions/delivery-id/submit/', method: 'POST', csrf: 'lesson-token', credentials: 'include', body: { responses } },
  ]);
});
