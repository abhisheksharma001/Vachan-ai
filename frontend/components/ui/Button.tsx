/*
 * Button (doc 06 §6.5 #1) — a typed wrapper over a native <button>.
 *
 * Variants: primary | secondary | ghost
 * Sizes:    default | sm
 * Supports loading state with an inline spinner.
 */
import type { ButtonHTMLAttributes } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "ghost";
type Size = "default" | "sm";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "default",
  loading = false,
  disabled,
  children,
  className,
  ...rest
}: ButtonProps) {
  const classes = [styles.btn, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(" ");
  const isDisabled = disabled || loading;
  return (
    <button
      className={classes}
      disabled={isDisabled}
      aria-busy={loading}
      {...rest}
    >
      {loading && (
        <span className={styles.spinner} aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray="32"
              strokeDashoffset="12"
            >
              <animateTransform
                attributeName="transform"
                type="rotate"
                from="0 12 12"
                to="360 12 12"
                dur="1s"
                repeatCount="indefinite"
              />
            </circle>
          </svg>
        </span>
      )}
      <span className={loading ? styles.faded : undefined}>{children}</span>
    </button>
  );
}
