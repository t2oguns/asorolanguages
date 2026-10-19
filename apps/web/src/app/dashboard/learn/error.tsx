"use client";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Failed to load units.</h2>
      <button onClick={() => reset()}>
        Try again
      </button>
    </div>
  );
}