"use client";

import * as RadixProgress from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  className?: string;
  indicatorClassName?: string;
}

export function Progress({ value, className, indicatorClassName }: ProgressProps) {
  return (
    <RadixProgress.Root
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-slate-100", className)}
      value={value}
    >
      <RadixProgress.Indicator
        className={cn("h-full w-full bg-brand-600 transition-all duration-300", indicatorClassName)}
        style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
      />
    </RadixProgress.Root>
  );
}
