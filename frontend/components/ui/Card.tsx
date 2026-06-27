/*
 * Card / Surface (doc 06 §6.5 #2). Pass `interactive` to get the hover lift
 * (use only when the whole card is clickable).
 */
import type { HTMLAttributes } from "react";
import styles from "./Card.module.css";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export function Card({ interactive, className, ...rest }: CardProps) {
  const classes = [styles.card, interactive && styles.interactive, className]
    .filter(Boolean)
    .join(" ");
  return <div className={classes} {...rest} />;
}
