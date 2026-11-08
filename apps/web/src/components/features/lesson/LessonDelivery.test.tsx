import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import LessonPlayer from './LessonPlayer';
import { exerciseFixture } from './lib/exercise.fixture';
import { submitLesson, startLesson } from './lib/api';
import type { LessonDelivery, Receipt } from './types';

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock('next/navigation', () => ({ useRouter: () => router }));
vi.mock('./lib/api', () => ({ startLesson: vi.fn(), submitLesson: vi.fn() }));
const fixture: LessonDelivery = {
  lesson_attempt_id: '00000000-0000-4000-8000-000000000001', learner_id: '1',
  lesson: { id: 1, title: 'Greetings', code: 'greeting', description: '' }, submitted: false,
  exercises: [exerciseFixture({ instruction: 'Pick the greeting', prompt_blocks: [], options: [
    { id: 'yes', position: 0, text: 'Hello', media: null, is_correct: true },
    { id: 'no', position: 1, text: 'Goodbye', media: null, is_correct: false },
  ] })],
};
const receipt: Receipt = { lesson_attempt_id: fixture.lesson_attempt_id, submitted: true };

beforeEach(() => {
  localStorage.clear(); vi.clearAllMocks();
  vi.mocked(startLesson).mockResolvedValue(structuredClone(fixture));
  vi.mocked(submitLesson).mockResolvedValue(receipt);
});

describe('whole-lesson client', () => {
  it('shows local feedback, collects optional rating, and submits only at the end', async () => {
    const user = userEvent.setup();
    render(<LessonPlayer code="greeting" />);
    await user.click(await screen.findByRole('radio', { name: 'Hello' }));
    await user.click(screen.getByRole('button', { name: 'Check' }));
    expect(screen.getByText('Correct')).toBeInTheDocument();
    expect(submitLesson).not.toHaveBeenCalled();
    await user.selectOptions(screen.getByLabelText('Recall rating for hola'), '2');
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    expect(submitLesson).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Finish' }));
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(startLesson).toHaveBeenCalledTimes(1);
    expect(submitLesson).toHaveBeenCalledExactlyOnceWith('greeting', fixture.lesson_attempt_id, [{
      exercise_id: fixture.exercises[0].id, response: ['yes'], recall_ratings: { '42': 2 },
    }]);
  });

  it('records a requeued correction within the open lesson', async () => {
    const user = userEvent.setup();
    render(<LessonPlayer code="greeting" />);
    await user.click(await screen.findByRole('radio', { name: 'Goodbye' }));
    await user.click(screen.getByRole('button', { name: 'Check' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await user.click(await screen.findByRole('radio', { name: 'Hello' }));
    await user.click(screen.getByRole('button', { name: 'Check' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await user.click(screen.getByRole('button', { name: 'Finish' }));
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(submitLesson).toHaveBeenCalledWith('greeting', fixture.lesson_attempt_id, [
      { exercise_id: fixture.exercises[0].id, response: ['no'] },
      { exercise_id: fixture.exercises[0].id, response: ['yes'] },
    ]);
  });

  it('retains a failed batch and retries identical answers', async () => {
    const user = userEvent.setup();
    vi.mocked(submitLesson).mockRejectedValueOnce(new Error('offline'));
    render(<LessonPlayer code="greeting" />);
    await user.click(await screen.findByRole('radio', { name: 'Hello' }));
    await user.click(screen.getByRole('button', { name: 'Check' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await user.click(screen.getByRole('button', { name: 'Finish' }));
    await screen.findByRole('alert');
    expect(localStorage.length).toBe(0);
    await user.click(screen.getByRole('button', { name: 'Retry saving' }));
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(vi.mocked(submitLesson).mock.calls[0]).toEqual(vi.mocked(submitLesson).mock.calls[1]);
  });

  it('discards answers after leaving and starts a new attempt on return', async () => {
    const user = userEvent.setup();
    const first = render(<LessonPlayer code="greeting" />);
    await user.click(await screen.findByRole('radio', { name: 'Goodbye' }));
    await user.click(screen.getByRole('button', { name: 'Check' }));
    first.unmount();
    const freshId = '00000000-0000-4000-8000-000000000009';
    vi.mocked(startLesson).mockResolvedValue({ ...fixture, lesson_attempt_id: freshId });
    render(<LessonPlayer code="greeting" />);
    const hello = await screen.findByRole('radio', { name: 'Hello' });
    expect(hello).not.toBeChecked();
    expect(screen.queryByText('Correct answer')).not.toBeInTheDocument();
    expect(startLesson).toHaveBeenCalledTimes(2);
    expect(localStorage.length).toBe(0);
    await user.click(hello);
    await user.click(screen.getByRole('button', { name: 'Check' }));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    await user.click(screen.getByRole('button', { name: 'Finish' }));
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(submitLesson).toHaveBeenCalledExactlyOnceWith('greeting', freshId, [
      { exercise_id: fixture.exercises[0].id, response: ['yes'] },
    ]);
  });
});

it('keeps client stats unchanged when the backend returns a conflicting grade', async () => {
  const user = userEvent.setup();
  // Additional server diagnostics must never replace locally observed stats.
  vi.mocked(submitLesson).mockResolvedValue({ ...receipt, first_try_correct: 0, mean_score: 0 } as Receipt);
  render(<LessonPlayer code="greeting" />);
  await user.click(await screen.findByRole('radio', { name: 'Hello' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByText('1 of 1')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  await waitFor(() => expect(router.push).toHaveBeenCalled());
  expect(screen.getByText('1 of 1')).toBeInTheDocument();
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('starts fresh after browser back-forward cache restoration', async () => {
  const user = userEvent.setup();
  render(<LessonPlayer code="greeting" />);
  await user.click(await screen.findByRole('radio', { name: 'Hello' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  fireEvent(window, new PageTransitionEvent('pagehide', { persisted: true }));
  expect(screen.queryByText('Correct')).not.toBeInTheDocument();
  fireEvent(window, new PageTransitionEvent('pageshow', { persisted: true }));
  expect(await screen.findByRole('radio', { name: 'Hello' })).not.toBeChecked();
  expect(startLesson).toHaveBeenCalledTimes(2);
  expect(submitLesson).not.toHaveBeenCalled();
});

it('does not apply an old save acknowledgement to a fresh lesson after returning', async () => {
  let resolveSave!: (value: Receipt) => void;
  vi.mocked(submitLesson).mockReturnValueOnce(new Promise<Receipt>((resolve) => { resolveSave = resolve; }));
  const user = userEvent.setup();
  render(<LessonPlayer code="greeting" />);
  await user.click(await screen.findByRole('radio', { name: 'Hello' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  fireEvent(window, new PageTransitionEvent('pagehide', { persisted: true }));
  fireEvent(window, new PageTransitionEvent('pageshow', { persisted: true }));
  expect(await screen.findByRole('radio', { name: 'Hello' })).not.toBeChecked();
  await act(async () => { resolveSave(receipt); });
  expect(router.push).not.toHaveBeenCalled();
  expect(screen.getByRole('button', { name: 'Check' })).toBeInTheDocument();
});

it('records a wrong matching permutation before requeued practice corrects it', async () => {
  const user = userEvent.setup();
  const matching = exerciseFixture({ exercise_type: 'matching', options: [], prompt_blocks: [], matching_pairs: [
    { id: 'a', position: 0, target_id: null, left_text: 'hola', right_text: 'hello', left_media: null, right_media: null },
    { id: 'b', position: 1, target_id: null, left_text: 'mundo', right_text: 'world', left_media: null, right_media: null },
  ] });
  vi.mocked(startLesson).mockResolvedValue({ ...fixture, exercises: [matching] });
  render(<LessonPlayer code="greeting" />);
  await user.click(await screen.findByRole('button', { name: 'hola' }));
  await user.click(screen.getByRole('button', { name: 'world' }));
  await user.click(screen.getByRole('button', { name: 'mundo' }));
  await user.click(screen.getByRole('button', { name: 'hello' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  expect(screen.getByText('Review these pairs')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.click(screen.getByRole('button', { name: 'hola' }));
  await user.click(screen.getByRole('button', { name: 'hello' }));
  await user.click(screen.getByRole('button', { name: 'mundo' }));
  await user.click(screen.getByRole('button', { name: 'world' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByText('0 of 1')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  await waitFor(() => expect(router.push).toHaveBeenCalled());
  expect(submitLesson).toHaveBeenCalledWith('greeting', fixture.lesson_attempt_id, [
    { exercise_id: matching.id, response: { a: 'b', b: 'a' } },
    { exercise_id: matching.id, response: { a: 'a', b: 'b' } },
  ]);
});

it('uses code-point blank offsets and retains per-sense ratings on partial recall', async () => {
  const user = userEvent.setup();
  const blank = exerciseFixture({ exercise_type: 'fill_blank', options: [],
    targets: [fixture.exercises[0].targets[0], { id: 'target-2', sense_id: 43, lexeme_id: 'lexeme-2', label: 'mundo', meaning: 'world' }],
    prompt_blocks: [{ id: 'block', position: 0, block_type: 'text', text: '🙂 hola mundo', media: null }],
    fill_blank_slots: [
      { id: 'a', position: 0, source_block_id: 'block', target_id: 'target-1', start_offset: 2, end_offset: 6, accepted_answers: [{ id: '1', text: 'hola' }, { id: '2', text: 'buenas' }] },
      { id: 'b', position: 1, source_block_id: 'block', target_id: 'target-2', start_offset: 7, end_offset: 12, accepted_answers: [{ id: '3', text: 'mundo' }] },
    ],
  });
  vi.mocked(startLesson).mockResolvedValue({ ...fixture, exercises: [blank] });
  render(<LessonPlayer code="greeting" />);
  await user.type(await screen.findByRole('textbox', { name: 'Blank 1.1' }), 'BUENAS');
  expect(screen.getByRole('button', { name: 'Check' })).toBeDisabled();
  expect(screen.getByText('🙂')).toBeInTheDocument();
  await user.type(screen.getByRole('textbox', { name: 'Blank 1.2' }), 'wrong');
  await user.click(screen.getByRole('button', { name: 'Check' }));
  await user.selectOptions(screen.getByLabelText('Recall rating for hola'), '2');
  expect(screen.queryByLabelText('Recall rating for mundo')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.type(screen.getByRole('textbox', { name: 'Blank 1.1' }), 'hola');
  await user.type(screen.getByRole('textbox', { name: 'Blank 1.2' }), 'mundo');
  await user.click(screen.getByRole('button', { name: 'Check' }));
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  await waitFor(() => expect(router.push).toHaveBeenCalled());
  expect(submitLesson).toHaveBeenCalledWith('greeting', fixture.lesson_attempt_id, [
    { exercise_id: blank.id, response: { a: 'BUENAS', b: 'wrong' }, recall_ratings: { '42': 2 } },
    { exercise_id: blank.id, response: { a: 'hola', b: 'mundo' } },
  ]);
});

it('keeps repeated word tiles distinct and submits the supplied words', async () => {
  const { within } = await import('@testing-library/react');
  const user = userEvent.setup();
  const words = ['I', 'am', 'what', 'I', 'am'];
  const wordOrder = exerciseFixture({ exercise_type: 'word_order', options: [], accepted_answers: [{ id: '1', text: words.join(' '), is_primary: true }] });
  vi.mocked(startLesson).mockResolvedValue({ ...fixture, exercises: [wordOrder] });
  render(<LessonPlayer code="greeting" />);
  const bank = within(await screen.findByRole('group', { name: 'Word bank' }));
  for (const word of words) {
    expect(screen.getByRole('button', { name: 'Check' })).toBeDisabled();
    await user.click(bank.getAllByRole('button', { name: word }).find((button) => !button.hasAttribute('disabled'))!);
  }
  await user.click(screen.getByRole('button', { name: 'Check' }));
  expect(screen.getByText('Correct')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  await waitFor(() => expect(router.push).toHaveBeenCalled());
  expect(submitLesson).toHaveBeenCalledWith('greeting', fixture.lesson_attempt_id, [{ exercise_id: wordOrder.id, response: words }]);
});

it('uses checkboxes when more than one choice is correct', async () => {
  const user = userEvent.setup();
  const choice = exerciseFixture({ prompt_blocks: [], options: [
    { id: 'a', position: 0, text: 'hola', media: null, is_correct: true },
    { id: 'b', position: 1, text: 'buenas', media: null, is_correct: true },
    { id: 'c', position: 2, text: 'adiós', media: null, is_correct: false },
  ] });
  vi.mocked(startLesson).mockResolvedValue({ ...fixture, exercises: [choice] });
  render(<LessonPlayer code="greeting" />);
  await user.click(await screen.findByRole('checkbox', { name: 'hola' }));
  await user.click(screen.getByRole('checkbox', { name: 'buenas' }));
  await user.click(screen.getByRole('button', { name: 'Check' }));
  expect(screen.getByText('Correct')).toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: 'adiós' })).toBeDisabled();
  await user.click(screen.getByRole('button', { name: 'Continue' }));
  await user.click(screen.getByRole('button', { name: 'Finish' }));
  await waitFor(() => expect(router.push).toHaveBeenCalled());
  expect(submitLesson).toHaveBeenCalledWith('greeting', fixture.lesson_attempt_id, [{ exercise_id: choice.id, response: ['a', 'b'] }]);
});
