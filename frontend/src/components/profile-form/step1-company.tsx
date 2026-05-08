"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { ProfileFormData } from "@/app/analyze/page";

const INDUSTRIES = [
  { value: "it_software", label: "IT / Software" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "healthcare", label: "Healthcare" },
  { value: "retail", label: "Retail" },
  { value: "finance", label: "Finance" },
  { value: "logistics", label: "Logistics" },
  { value: "construction", label: "Construction" },
  { value: "energy", label: "Energy" },
  { value: "food_beverage", label: "Food & Beverage" },
  { value: "consulting", label: "Consulting" },
  { value: "other", label: "Other" },
];

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step1Company({ form }: Props) {
  const { register, control, formState: { errors } } = form;
  return (
    <div className="flex flex-col gap-5">
      <Input
        label="Company name"
        required
        placeholder="Muster GmbH"
        error={errors.company_name?.message}
        {...register("company_name")}
      />
      <Controller
        control={control}
        name="industry"
        render={({ field }) => (
          <Select
            label="Industry"
            required
            options={INDUSTRIES}
            value={field.value}
            onValueChange={field.onChange}
            error={errors.industry?.message}
          />
        )}
      />
      <Input
        label="Country"
        placeholder="Germany"
        hint="Leave blank if Germany"
        {...register("country")}
      />
      <Input
        label="Number of employees"
        required
        type="number"
        min={1}
        placeholder="50"
        error={errors.employee_count?.message}
        {...register("employee_count")}
      />
    </div>
  );
}
