import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, required, ...props }, ref) => (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-slate-300">
          {label}
          {required && <span className="ml-1 text-red-400">*</span>}
        </label>
      )}
      <input
        ref={ref}
        required={required}
        className={cn(
          "rounded-lg border border-white/12 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-600",
          "focus:outline-none focus:ring-2 focus:ring-brand-500/70 focus:border-brand-500/50 focus:bg-white/8",
          "disabled:opacity-40 disabled:cursor-not-allowed",
          "transition-all duration-200",
          error && "border-red-500/50 focus:ring-red-500/50",
          className
        )}
        {...props}
      />
      {hint && !error && <p className="text-xs text-slate-600">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
);
Input.displayName = "Input";
