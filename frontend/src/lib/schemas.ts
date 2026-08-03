/**
 * src/lib/schemas.ts
 *
 * Zod validation schemas for all forms in the application.
 * PRD §Phase 2: React Hook Form + Zod for all form validation.
 */

import { z } from 'zod'

// ── Login ─────────────────────────────────────────────────────────────────────
export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required.')
    .email('Please enter a valid email address.'),
  password: z
    .string()
    .min(1, 'Password is required.'),
})

export type LoginFormData = z.infer<typeof loginSchema>

// ── Register ──────────────────────────────────────────────────────────────────
export const registerSchema = z
  .object({
    full_name: z
      .string()
      .min(2, 'Full name must be at least 2 characters.')
      .max(100, 'Full name must be under 100 characters.'),
    organization: z
      .string()
      .min(2, 'Organization name must be at least 2 characters.')
      .max(100, 'Organization name must be under 100 characters.'),
    email: z
      .string()
      .min(1, 'Work email is required.')
      .email('Please enter a valid email address.'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters.')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter.')
      .regex(/[0-9]/, 'Password must contain at least one number.'),
    confirm_password: z
      .string()
      .min(1, 'Please confirm your password.'),
    role: z.enum(['engineer', 'consultant', 'org_admin'], {
      required_error: 'Please select a role.',
    }),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: 'Passwords do not match.',
    path: ['confirm_password'],
  })

export type RegisterFormData = z.infer<typeof registerSchema>

// ── Project Setup (Step 1) — used in Phase 5 ─────────────────────────────────
export const projectSetupSchema = z.object({
  product_name:           z.string().min(2, 'Product name is required.'),
  sku:                    z.string().optional(),
  cpc_code:               z.string().optional(),
  manufacturer:           z.string().min(2, 'Manufacturer name is required.'),
  manufacturer_country:   z.string().min(1, 'Please select a country.'),
  company_description:    z.string().min(10, 'Please provide a brief company description.'),
  product_narrative:      z.string().min(10, 'Please provide a product narrative.'),
  standard:               z.enum(['EN_15804_A2', 'ISO_21930', 'ISO_14025']),
  program_operator:       z.string().min(1, 'Please select a program operator.'),
  pcr_id:                 z.string().optional(),
  pcr_version:            z.string().optional(),
  functional_unit_qty:    z.coerce.number().positive('Quantity must be positive.'),
  functional_unit_unit:   z.string().min(1, 'Unit is required.'),
  functional_unit_desc:   z.string().optional(),
  rsl_value:              z.coerce.number().positive('RSL must be positive.'),
  rsl_unit:               z.enum(['years', 'cycles']),
})

export type ProjectSetupFormData = z.infer<typeof projectSetupSchema>
