import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  steps: string[];
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <div className="flex items-center">
      {steps.map((label, i) => {
        const num  = i + 1;
        const done = num < current;
        const active = num === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all duration-300",
                  done   && "bg-brand-600 text-white shadow-glow-blue-sm",
                  active && "bg-brand-600 text-white ring-4 ring-brand-500/25 shadow-glow-blue-sm",
                  !done && !active && "bg-white/8 text-slate-500 border border-white/10"
                )}
              >
                {done ? <Check className="h-4 w-4" /> : num}
              </div>
              <span
                className={cn(
                  "hidden sm:block text-[11px] font-semibold whitespace-nowrap",
                  active  ? "text-brand-400" : done ? "text-slate-500" : "text-slate-600"
                )}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={cn(
                  "h-px w-8 sm:w-14 mx-2 mb-5 transition-colors duration-300",
                  done ? "bg-brand-600" : "bg-white/10"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
