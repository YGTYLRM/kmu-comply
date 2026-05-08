import { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const variants = {
  primary:
    "bg-brand-600 text-white shadow-glow-blue-sm hover:bg-brand-500 hover:shadow-glow-blue active:bg-brand-700 focus-visible:ring-brand-500",
  secondary:
    "bg-white/8 text-slate-200 border border-white/10 hover:bg-white/12 hover:text-white active:bg-white/6 focus-visible:ring-slate-500",
  outline:
    "border border-white/15 bg-transparent text-slate-300 hover:bg-white/8 hover:border-white/25 hover:text-white focus-visible:ring-slate-500",
  ghost:
    "text-slate-400 hover:bg-white/6 hover:text-white focus-visible:ring-slate-500",
  danger:
    "bg-red-600 text-white hover:bg-red-500 focus-visible:ring-red-500",
};

const sizes = {
  sm:  "h-8  px-3   text-xs  gap-1.5 rounded-lg",
  md:  "h-9  px-4   text-sm  gap-2   rounded-lg",
  lg:  "h-11 px-6   text-sm  gap-2   rounded-xl",
  xl:  "h-12 px-8   text-base gap-2.5 rounded-xl",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
}

export function Button({ variant = "primary", size = "md", className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-950",
        "disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none",
        "select-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
