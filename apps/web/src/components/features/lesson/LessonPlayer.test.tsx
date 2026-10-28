import { render, screen, within } from '@testing-library/react';
import userEvent, { UserEvent } from '@testing-library/user-event';
import { useRouter } from 'next/router';
import { vi, describe, it, expect } from 'vitest';
import LessonPlayer from './LessonPlayer';
import { Exercise } from './types';

const { push } = vi.hoisted(() => ({ push: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: ()=> ({ push }) }));


beforeEach(()=>{
    push.mockClear();
});


afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// Couple of mocked exercises
const intro: Exercise = { id: 'i1', type: 'intro', term: 'el gato', translation: 'the cat' };
const choice: Exercise = {
  id: 'c1',
  type: 'choice',
  prompt: 'el gato',
  options: ['the cat', 'the dog'],
  answer: 0,
};

const footer = () => screen.getByRole('contentinfo');


// A utility function to be able to render whatever lesson with whatever exercises we want
function renderLesson(exercises: Exercise[], props: Partial<React.ComponentProps<typeof LessonPlayer>> = {}) {
    return render(<LessonPlayer exercises={exercises} {...props} />);
}


describe('lesson flow',()=>{
    let user: UserEvent;

    beforeEach(()=>{
        user = userEvent.setup();
    })

    it("renders its exercises", async ()=>{

        const intro2: Exercise = { id: 'i1', type: 'intro', term: 'el perro', translation: 'the dog' };
        const intro3: Exercise = { id: 'i1', type: 'intro', term: 'el leche', translation: 'the milk' };

        renderLesson([intro, intro2, intro3]);
        
        expect(screen.getByText('el gato')).toBeVisible();
        await user.click(screen.getByRole("button", {name: "Continue"}));
        
        expect(screen.getByText('el perro')).toBeVisible();
        await user.click(screen.getByRole("button", {name: "Continue"}));
        
        expect(screen.getByText('el leche')).toBeVisible();
        await user.click(screen.getByRole("button", {name: "Continue"}));

    })

    it("keeps Check disabled until an answer is picked, then marks it correct", async ()=>{
        renderLesson([choice]);

        await user.click(screen.getByRole("button", {name: "Check"}));
        expect(screen.getByRole("button", { name: "Check" })).toBeDisabled();

        await user.click(screen.getByRole("radio", { name: "the cat" }));
        expect(screen.getByRole("button", { name: "Check" })).not.toBeDisabled();
        await user.click(screen.getByRole("button", {name: "Check"}));        

        expect(screen.getByText("Correct")).toBeVisible();

        expect(footer()).toHaveAttribute('data-status', 'correct');
        expect(within(footer()).getByText('Correct')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument();

    })

    it("goes to next exercise when clicking continue", async ()=>{
        renderLesson([intro, choice]);
        
        expect(screen.getByText('el gato')).toBeVisible();
        await user.click(screen.getByRole("button", {name: "Continue"}));
        
        expect(screen.getByRole("radio", { name: "the dog" })).toBeVisible();
    })

    it("locks the options after checking", async ()=>{
        renderLesson([choice]);

        await user.click(screen.getByRole("radio", { name: "the dog" }));
        await user.click(screen.getByRole("button", { name: "Check" }));
        
        expect(screen.getByRole("radio", { name: "the dog" })).toBeDisabled();
        expect(screen.getByRole("radio", { name: "the cat" })).toBeDisabled();
    })

    it("updates the progress bar as exercises are completed", async ()=>{
        renderLesson([choice, { ...choice, id: 'c2' }]);
 
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
        await user.click(screen.getByRole('radio', { name: 'the cat' }));
        await user.click(screen.getByRole('button', { name: 'Check' }));
        await user.click(screen.getByRole('button', { name: 'Continue' }));
    
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50');
    })

    it('brings a missed exercise back before finishing', async () => {
        const onComplete = vi.fn();
        renderLesson([choice], { onComplete });
    
        await user.click(screen.getByRole('radio', { name: 'the dog' }));
        await user.click(screen.getByRole('button', { name: 'Check' }));
        await user.click(screen.getByRole('button', { name: 'Continue' }));
    
        // Same exercise again, with a fresh selection.
        expect(screen.getByRole('radio', { name: 'the cat' })).toBeEnabled();
        expect(screen.getByRole('button', { name: 'Check' })).toBeDisabled();
    
        await user.click(screen.getByRole('radio', { name: 'the cat' }));
        await user.click(screen.getByRole('button', { name: 'Check' }));
        await user.click(screen.getByRole('button', { name: 'Continue' }));
    
        expect(screen.getByText('Lesson complete')).toBeInTheDocument();
        expect(screen.getByText('0 of 1')).toBeInTheDocument();
        expect(screen.getByText('0%')).toBeInTheDocument();
        expect(onComplete).toHaveBeenCalledTimes(1);
        expect(onComplete).toHaveBeenCalledWith({
        total: 1,
        firstTryCorrect: 0,
        missedIds: ['c1'],
        accuracy: 0,
        });
    })

    it("finishes with a score, calls onComplete once, and navigates on Finish", async ()=>{
        const onComplete = vi.fn();
        renderLesson([choice], { onComplete, exitHref: '/dashboard/learn' });
    
        await user.click(screen.getByRole('radio', { name: 'the cat' }));
        await user.click(screen.getByRole('button', { name: 'Check' }));
        await user.click(screen.getByRole('button', { name: 'Continue' }));
    
        expect(screen.getByText('Lesson complete')).toBeInTheDocument();
        expect(screen.getByText('1 of 1')).toBeInTheDocument();
        expect(screen.getByText('100%')).toBeInTheDocument();
        expect(onComplete).toHaveBeenCalledTimes(1);
        expect(onComplete).toHaveBeenCalledWith(
            expect.objectContaining({ total: 1, firstTryCorrect: 1, accuracy: 1 }),
        );
    
        await user.click(screen.getByRole('button', { name: 'Finish' }));
        expect(push).toHaveBeenCalledWith('/dashboard/learn');
    })    
})

describe('exiting', () => {
    let user: UserEvent;

    beforeEach(()=>{
        user = userEvent.setup();
    })

    it("leaves immediately if no progress has been made",async ()=>{
        const confirm = vi.spyOn(window, 'confirm');
        renderLesson([intro, choice]);
    
        await user.click(screen.getByRole('button', { name: 'Exit lesson' }));
    
        expect(confirm).not.toHaveBeenCalled();
        expect(push).toHaveBeenCalledWith('/dashboard/learn');
    })

    it("asks user to confirm if progress has been made", async ()=>{
        const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
        
        renderLesson([choice, intro]);

        await user.click(screen.getByRole("radio", { name: "the cat" }));
        await user.click(screen.getByRole("button", { name: "Check" }));
        await user.click(screen.getByRole("button", { name: "Continue" }));



        await user.click(screen.getByRole('button', { name: 'Exit lesson' }));
        expect(confirm).toHaveBeenCalled();
        expect(push).toHaveBeenCalledWith("/dashboard/learn")

        confirm.mockRestore();
    })

    it("sends lesson complete at the end of the lesson", async ()=>{
        const onComplete = vi.fn();

        renderLesson([choice], { onComplete });

        await user.click(screen.getByRole("radio", { name: "the cat" }));
        await user.click(screen.getByRole("button", { name: "Check" }));
        await user.click(screen.getByRole("button", { name: "Continue" }));


        expect(onComplete).toHaveBeenCalledTimes(1);
        expect(screen.getByText("Lesson complete")).toBeInTheDocument();
        expect(screen.getByText("100%")).toBeInTheDocument();


        expect(onComplete).toHaveBeenCalledWith(
            expect.objectContaining({ total: 1, firstTryCorrect: 1, missedIds: [], accuracy: 1 })
        )

        await user.click(screen.getByRole("button", {name: "Finish"}));
        expect(push).toHaveBeenCalledWith("/dashboard/learn");
    })

});


describe('word bank', () => {
    it("test all the rest of the exercises", ()=>{

    })
})