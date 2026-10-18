import { server } from "./server";
import '@testing-library/jest-dom/vitest';

process.env.NEXT_PUBLIC_API_URL = "http://api.test";
process.env.API_INTERNAL_URL = "http://api.test";
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());