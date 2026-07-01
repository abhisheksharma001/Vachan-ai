"use client";

import type { InputHTMLAttributes } from "react";
import styles from "./Slider.module.css";

interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  min?: number;
  max?: number;
}

export function Slider({ className, min = 0, max = 100, value, ...props }: SliderProps) {
  const numValue = typeof value === "number" ? value : Number(value ?? min);
  const pct = max === min ? 0 : ((numValue - min) / (max - min)) * 100;

  const classes = [styles.slider, className].filter(Boolean).join(" ");

  return (
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      className={classes}
      style={{ ["--pct" as string]: `${pct}%` }}
      {...props}
    />
  );
}
