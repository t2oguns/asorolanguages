/** Optional seed keeps exercise markup stable across server/client rendering. */
export function shuffle<T>(arr: T[], seed?: string): T[] {
  const result = [...arr];
  let state = seed === undefined ? 0 : Array.from(seed).reduce((value, char) => Math.imul(value ^ char.codePointAt(0)!, 16777619), 2166136261);
  for (let index = result.length - 1; index > 0; index--) {
    state = Math.imul(state ^ (state >>> 16), 2246822507);
    const other = seed === undefined ? Math.floor(Math.random() * (index + 1)) : (state >>> 0) % (index + 1);
    [result[index], result[other]] = [result[other], result[index]];
  }
  return result;
}
