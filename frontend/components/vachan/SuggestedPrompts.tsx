import styles from "./SuggestedPrompts.module.css";

const PROMPTS = [
  "Reply to a client like me",
  "Write a polite email to a vendor",
  "Say no without sounding rude",
  "Switch to pure Hindi",
];

export function SuggestedPrompts({ onPrompt }: { onPrompt: (text: string) => void }) {
  return (
    <div
      className={styles.wrap}
      role="list"
      aria-label="Suggested prompts"
    >
      {PROMPTS.map((text) => (
        <button
          key={text}
          type="button"
          className={styles.prompt}
          onClick={() => onPrompt(text)}
        >
          {text}
        </button>
      ))}
    </div>
  );
}
