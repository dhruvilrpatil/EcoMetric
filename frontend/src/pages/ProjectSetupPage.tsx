/**
 * src/pages/ProjectSetupPage.tsx
 *
 * PRD §6.4 Step 1: Setup
 * Posts project to FastAPI /api/v1/projects (AWS RDS) instead of Firestore.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { faArrowRight } from '@fortawesome/free-solid-svg-icons'

import { useParams } from 'react-router-dom'
import { useAppSelector } from '@/store'
import { projectSetupSchema, type ProjectSetupFormData } from '@/lib/schemas'
import { useCreateProject, useProject, useUpdateProject } from '@/hooks/useProjects'
import { useEffect } from 'react'

import { AppLayout } from '@/components/organisms/AppLayout'
import { TextInput } from '@/components/atoms/TextInput'
import { ButtonPrimary } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'
import { PillTab } from '@/components/atoms/PillTab'

export default function ProjectSetupPage() {
  const { id } = useParams()
  const isNew = !id || id === 'new'
  const navigate = useNavigate()
  const { user } = useAppSelector((s) => s.auth)
  const [error, setError] = useState<string | null>(null)
  
  const { data: project, isLoading: projectLoading } = useProject(id)
  const createProject = useCreateProject()
  const updateProject = useUpdateProject(id || '')

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectSetupFormData>({
    resolver: zodResolver(projectSetupSchema),
    defaultValues: {
      standard: 'EN_15804_A2',
      functional_unit_qty: 1,
      rsl_unit: 'years',
    },
  })

  useEffect(() => {
    if (project && !isNew) {
      reset({
        product_name: project.product_name || '',
        sku: project.product_sku || '',
        manufacturer: project.manufacturer_name || '',
        manufacturer_country: project.manufacturing_country || '',
        company_description: project.company_description || '',
        product_narrative: project.product_narrative || '',
        standard: (project.epd_standard as any) || 'EN_15804_A2',
        program_operator: project.program_operator_name || '',
        functional_unit_qty: project.functional_unit_quantity || 1,
        functional_unit_unit: project.functional_unit_unit || 'unit',
        rsl_value: project.product_lifetime_years || 75,
        rsl_unit: 'years'
      })
    }
  }, [project, isNew, reset])

  async function onSubmit(data: ProjectSetupFormData) {
    if (!user) return
    setError(null)

    try {
      const pDesc = (data as any).operating_principle ? {
        operating_principle: (data as any).operating_principle || '',
        core_technology_description: (data as any).core_technology_description || '',
        heat_transfer_description: (data as any).heat_transfer_description || '',
        applications_description: (data as any).applications_description || '',
        capacity_range_description: (data as any).capacity_range_description || '',
        refrigerant_technology_notes: (data as any).refrigerant_technology_notes || '',
      } : undefined

      const mDesc = (data as any).component_sourcing_description ? {
        component_sourcing_description: (data as any).component_sourcing_description || '',
        assembly_description: (data as any).assembly_description || '',
        production_facility_locations: ((data as any).facility_locations || '').split(',').map((s: string) => s.trim()).filter(Boolean),
      } : undefined

      const certsList = ((data as any).certifications_list || '').split(',').map((s: string) => ({ standard_name: s.trim() })).filter((c: any) => c.standard_name)

      const payload = {
        product: {
          product_name: data.product_name,
          product_sku: data.sku,
          manufacturer_name: data.manufacturer,
          manufacturing_country: data.manufacturer_country,
          product_lifetime_years: Number(data.rsl_value) || 75,
          functional_unit_quantity: Number(data.functional_unit_qty) || 1,
          functional_unit_unit: data.functional_unit_unit || 'unit',
        },
        lca_config: {
          epd_standard: data.standard || 'EN_15804_A2',
          system_boundary: 'cradle_to_grave',
          lcia_method: 'EF_3_1',
          lci_database: 'ecoinvent_3.12_cutoff',
          active_modules: ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B6', 'C1', 'C2', 'C3', 'C4', 'D'],
        },
        narrative: {
          company_description: data.company_description,
          product_narrative: data.product_narrative,
          product_description: pDesc,
          manufacturing_narrative: mDesc,
          certifications_structured: certsList,
          program_operator: {
            name: data.program_operator,
            address: '',
            website: ''
          }
        },
        bom: project?.bom || [],
      }

      let targetId = id
      if (isNew) {
        const result = await createProject.mutateAsync(payload)
        targetId = result.project_id
      } else {
        await updateProject.mutateAsync(payload)
      }

      navigate(`/projects/${targetId}/inventory`)
    } catch (err: any) {
      console.error(err)
      setError(err?.message || 'Failed to save project. Please try again.')
    }
  }

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'New Declaration' },
  ]

  const projectNav = {
    projectId: isNew ? 'new' : (id as string),
    currentStep: 1 as const,
    highestCompletedStep: (isNew ? 1 : 7) as any,
  }

  if (!isNew && projectLoading) {
    return <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}><div className="p-xl">Loading...</div></AppLayout>
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-[600px] mx-auto px-hero-h py-section">

        <h1 className="text-heading-lg text-ink mb-md">Project Setup</h1>
        <p className="text-body-md text-mute mb-xl">
          Define the boundaries and metadata for your Environmental Product Declaration.
        </p>

        {error && (
          <div className="mb-xl">
            <NotificationCard variant="error" title="Setup Failed">
              {error}
            </NotificationCard>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="bg-white border border-hairline p-xl rounded-sm flex flex-col gap-xl">

          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">1. Product Information</h2>
            <TextInput
              label="Product Name"
              {...register('product_name')}
              error={errors.product_name?.message}
              required
            />
            <div className="grid grid-cols-2 gap-lg">
              <TextInput
                label="Manufacturer"
                {...register('manufacturer')}
                error={errors.manufacturer?.message}
                required
              />
              <TextInput
                label="Country of Manufacture"
                placeholder="e.g. DE, US, CH"
                {...register('manufacturer_country')}
                error={errors.manufacturer_country?.message}
                required
              />
            </div>
            
            <div className="flex flex-col gap-xs mt-sm">
              <label className="text-body-strong text-body block mb-xxs">Company Description<span className="text-error ml-xxs">*</span></label>
              <textarea
                className="text-input h-[80px]"
                placeholder="Brief description of the company..."
                {...register('company_description')}
              />
              {errors.company_description && <span className="text-error text-body-sm">{errors.company_description.message}</span>}
            </div>

            <div className="flex flex-col gap-xs mt-sm">
              <label className="text-body-strong text-body block mb-xxs">Product Narrative<span className="text-error ml-xxs">*</span></label>
              <textarea
                className="text-input h-[80px]"
                placeholder="Detailed description of the product and its applications..."
                {...register('product_narrative')}
              />
              {errors.product_narrative && <span className="text-error text-body-sm">{errors.product_narrative.message}</span>}
            </div>
          </div>

          {/* 1b. Product Description Details (Part 5.1) */}
          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">1b. Technical Product Description (ISO 14025 / EN 15804)</h2>
            
            <div className="flex flex-col gap-xs">
              <label className="text-body-strong text-body block">Operating Principle</label>
              <p className="text-caption-sm text-mute">e.g. Vapor-compression refrigeration cycle utilizing a high-efficiency centrifugal compressor.</p>
              <textarea
                className="text-input h-[60px]"
                placeholder="Operating principle..."
                {...register('operating_principle' as any)}
              />
            </div>

            <div className="flex flex-col gap-xs">
              <label className="text-body-strong text-body block">Core Technology &amp; Compressor Mechanism</label>
              <textarea
                className="text-input h-[60px]"
                placeholder="Compressor technology, bearings, motor configuration..."
                {...register('core_technology_description' as any)}
              />
            </div>

            <div className="grid grid-cols-2 gap-lg">
              <div className="flex flex-col gap-xs">
                <label className="text-body-strong text-body block">Applications</label>
                <textarea
                  className="text-input h-[50px]"
                  placeholder="Commercial buildings, data centers..."
                  {...register('applications_description' as any)}
                />
              </div>
              <div className="flex flex-col gap-xs">
                <label className="text-body-strong text-body block">Capacity Range</label>
                <textarea
                  className="text-input h-[50px]"
                  placeholder="300 to 800 kW cooling capacity..."
                  {...register('capacity_range_description' as any)}
                />
              </div>
            </div>
          </div>

          {/* 1c. Manufacturing Narrative (Part 5.2) */}
          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">1c. Manufacturing &amp; Supply Chain</h2>
            <div className="flex flex-col gap-xs">
              <label className="text-body-strong text-body block">Component Sourcing &amp; Procurement</label>
              <textarea
                className="text-input h-[50px]"
                placeholder="Global component sourcing strategy..."
                {...register('component_sourcing_description' as any)}
              />
            </div>
            <div className="flex flex-col gap-xs">
              <label className="text-body-strong text-body block">Assembly &amp; Testing Details</label>
              <textarea
                className="text-input h-[50px]"
                placeholder="Assembly process and testing protocols..."
                {...register('assembly_description' as any)}
              />
            </div>
            <TextInput
              label="Production Facility Locations"
              placeholder="e.g. Charlotte NC, Shanghai China"
              {...register('facility_locations' as any)}
            />
          </div>

          {/* 1d. Certifications (Part 5.3) */}
          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">1d. Certifications</h2>
            <TextInput
              label="Certifications (comma separated)"
              placeholder="AHRI 550/590, Eurovent Certified Performance, ISO 9001, ISO 14001"
              {...register('certifications_list' as any)}
            />
          </div>

          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">2. Functional Unit &amp; Lifespan</h2>

            <div className="flex gap-lg">
              <div className="flex-1">
                <TextInput
                  label="Quantity"
                  type="number"
                  step="any"
                  {...register('functional_unit_qty')}
                  error={errors.functional_unit_qty?.message}
                  required
                />
              </div>
              <div className="flex-1">
                <TextInput
                  label="Unit"
                  placeholder="e.g. kg, m2, piece"
                  {...register('functional_unit_unit')}
                  error={errors.functional_unit_unit?.message}
                  required
                />
              </div>
            </div>

            <div className="flex gap-lg">
              <div className="flex-1">
                <TextInput
                  label="Reference Service Life (RSL)"
                  type="number"
                  {...register('rsl_value')}
                  error={errors.rsl_value?.message}
                  required
                />
              </div>
              <div className="flex-1">
                <label className="text-body-strong text-body block mb-xxs">RSL Unit<span className="text-error ml-xxs">*</span></label>
                <Controller
                  name="rsl_unit"
                  control={control}
                  render={({ field }) => (
                    <div className="flex gap-xs">
                      <PillTab active={field.value === 'years'} onClick={() => field.onChange('years')}>Years</PillTab>
                      <PillTab active={field.value === 'cycles'} onClick={() => field.onChange('cycles')}>Cycles</PillTab>
                    </div>
                  )}
                />
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-lg border-b border-hairline pb-lg">
            <h2 className="text-heading-sm text-ink">3. Standard &amp; Compliance</h2>
            <div className="flex flex-col gap-xs">
              <label className="text-body-strong text-body block mb-xxs">EPD Standard<span className="text-error ml-xxs">*</span></label>
              <Controller
                name="standard"
                control={control}
                render={({ field }) => (
                  <select
                    className="text-input"
                    value={field.value}
                    onChange={field.onChange}
                  >
                    <option value="EN_15804_A2">EN 15804+A2 (Construction Europe)</option>
                    <option value="ISO_21930">ISO 21930 (Construction Global)</option>
                    <option value="ISO_14025">ISO 14025 (General Type III)</option>
                  </select>
                )}
              />
            </div>

            <TextInput
              label="Program Operator"
              placeholder="e.g. EPD International, IBU"
              {...register('program_operator')}
              error={errors.program_operator?.message}
              required
            />
          </div>

          <div className="flex justify-end pt-md">
            <ButtonPrimary
              type="submit"
              loading={isSubmitting || createProject.isPending || updateProject.isPending}
              disabled={isSubmitting || createProject.isPending || updateProject.isPending}
              iconRight={faArrowRight}
            >
              Save &amp; Continue to Inventory
            </ButtonPrimary>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
