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
        <label className="text-sm font-medium text-slate-700">
          {label}
          {required && <span className="ml-1 text-red-500">*</span>}
        </label>
      )}
      <RadixSelect.Root value={value} onValueChange={onValueChange} disabled={disabled}>
        <RadixSelect.Trigger
          className={cn(
            "flex items-center justify-between rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white",
            "focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent",
            "data-[placeholder]:text-slate-400",
            "disabled:bg-slate-50 disabled:cursor-not-allowed",
            error && "border-red-400"
          )}
        >
          <RadixSelect.Value placeholder={placeholder ?? "Select…"} />
          <ChevronDown className="h-4 w-4 text-slate-400 ml-2 flex-shrink-0" />
        </RadixSelect.Trigger>
        <RadixSelect.Portal>
          <RadixSelect.Content
            className="z-50 min-w-[8rem] overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg"
            position="popper"
            sideOffset={4}
          >
            <RadixSelect.Viewport className="p-1">
              {options.map((opt) => (
                <RadixSelect.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    "relative flex cursor-pointer select-none items-center rounded px-3 py-2 pr-8 text-sm text-slate-700",
                    "outline-none data-[highlighted]:bg-brand-50 data-[highlighted]:text-brand-700"
                  )}
                >
                  <RadixSelect.ItemText>{opt.label}</RadixSelect.ItemText>
                  <RadixSelect.ItemIndicator className="absolute right-2">
                    <Check className="h-4 w-4" />
                  </RadixSelect.ItemIndicator>
                </RadixSelect.Item>
              ))}
            </RadixSelect.Viewport>
          </RadixSelect.Content>
        </RadixSelect.Portal>
      </RadixSelect.Root>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
