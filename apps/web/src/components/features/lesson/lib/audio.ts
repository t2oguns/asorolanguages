/** Speak text with the browser's built-in voices. No-op where unsupported. */
export function speakText(text: string, locale: string) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = locale;
  window.speechSynthesis.speak(u);
}