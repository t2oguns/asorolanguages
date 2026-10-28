import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import Lesson from './Lesson';
import { useRouter } from "next/navigation";
import userEvent from "@testing-library/user-event";


vi.mock("next/navigation", () => ({
  useRouter: vi.fn(),
}));

const push = vi.fn();

const mockLesson = {
    id: 1,
    code: "math101",
    title: "Introduction to Math",
    description: "Learn the basics of mathematics",
    difficulty:1,
    order: 3,
    module: 1,
};

describe('Lesson', () => {
    beforeEach(() => {
        vi.clearAllMocks();

        vi.mocked(useRouter).mockReturnValue(
            { push } as unknown as ReturnType<typeof useRouter>
        );
    });

    it("renders the Start Lesson button", () => {
        render(<Lesson lesson={mockLesson} />);

        expect(
        screen.getByRole("button", { name: "Start Lesson" })
        ).toBeInTheDocument();
    });


    it("navigates to the correct lesson when clicked", async () => {
        const user = userEvent.setup();

        render(<Lesson lesson={mockLesson} />);

        await user.click(
            screen.getByRole("button", { name: "Start Lesson" })
        );

        expect(push).toHaveBeenCalledOnce();
        expect(push).toHaveBeenCalledWith("/lesson/math101/");
    });

    it("does not trigger the parent click handler", async () => {
        const user = userEvent.setup();
        const parentClick = vi.fn();

        render(
            <div onClick={parentClick}>
                <Lesson lesson={mockLesson} />
            </div>
        );

        await user.click(
            screen.getByRole("button", { name: "Start Lesson" })
        );

        expect(parentClick).not.toHaveBeenCalled();
        expect(push).toHaveBeenCalledWith("/lesson/math101/");
    });
})