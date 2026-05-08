import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  steps: string[];
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((label, i) => {
        const num = i + 1;
        const done = num < current;
        const active = num === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors",
                  done && "border-brand-600 bg-brand-600 text-white",
                  active && "border-brand-600 bg-white text-brand-600",
                  !done && !active && "border-slate-300 bg-white text-slate-400"
                )}
              >
                {done ? <Check className="h-4 w-4" /> : num}
              </div>
              <span
                className={cn(
                  "hidden sm:block text-xs font-medium",
                  active ? "text-brand-600" : done ? "text-slate-500" : "text-slate-400"
                )}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={cn(
                  "h-0.5 w-10 sm:w-16 mx-1 mb-5 transition-colors",
                  done ? "bg-brand-600" : "bg-slate-200"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
