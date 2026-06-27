/*
 * Button (doc 06 §6.5 #1) — a typed wrapper over a native <button>.
 *
 * Plain English: pick a `variant` and it styles itself per the design system;
 * every normal button prop (onClick, disabled, type, aria-*) still works
 * because we spread `...rest` onto the real element.
 */
import type { ButtonHTMLAttributes } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({
  variant = "primary",
  className,
  ...rest
}: ButtonProps) {
  const classes = [styles.btn, styles[variant], className]
    .filter(Boolean)
    .join(" ");
  return <button className={classes} {...rest} />;
}
