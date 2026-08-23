"use client";

import * as RadixSelect from "@radix-ui/react-select";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  required?: boolean;
}

export function Select({
  value,
  onValueChange,
  placeholder,
  label,
  error,
  options,
  disabled,
  required,
}: SelectProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="text-sm font-medium text-slate-300">
          {label}
          {required && <span className="ml-1 text-red-400">*</span>}
        </label>
      )}
      <RadixSelect.Root value={value} onValueChange={onValueChange} disabled={disabled}>
        <RadixSelect.Trigger
          className={cn(
            "flex items-center justify-between rounded-lg border border-white/12 bg-white/5 px-3 py-2 text-sm text-white",
            "focus:outline-none focus:ring-2 focus:ring-brand-500/70 focus:border-brand-500/50",
            "data-[placeholder]:text-slate-600",
            "disabled:opacity-40 disabled:cursor-not-allowed",
            "transition-all duration-200",
            error && "border-red-500/50"
          )}
        >
          <RadixSelect.Value placeholder={placeholder ?? "Auswählen…"} />
          <ChevronDown className="h-4 w-4 text-slate-500 ml-2 flex-shrink-0" />
        </RadixSelect.Trigger>
        <RadixSelect.Portal>
          <RadixSelect.Content
            className="z-50 min-w-[8rem] overflow-hidden rounded-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.7)]"
            style={{ background: "rgba(10,22,40,0.97)", backdropFilter: "blur(16px)" }}
            position="popper"
            sideOffset={4}
          >
            <RadixSelect.Viewport className="p-1.5">
              {options.map((opt) => (
                <RadixSelect.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    "relative flex cursor-pointer select-none items-center rounded-lg px-3 py-2 pr-8 text-sm text-slate-300",
                    "outline-none data-[highlighted]:bg-brand-500/15 data-[highlighted]:text-white",
                    "transition-colors duration-100"
                  )}
                >
                  <RadixSelect.ItemText>{opt.label}</RadixSelect.ItemText>
                  <RadixSelect.ItemIndicator className="absolute right-2">
                    <Check className="h-4 w-4 text-brand-400" />
                  </RadixSelect.ItemIndicator>
                </RadixSelect.Item>
              ))}
            </RadixSelect.Viewport>
          </RadixSelect.Content>
        </RadixSelect.Portal>
      </RadixSelect.Root>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
