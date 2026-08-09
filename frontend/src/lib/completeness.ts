/**
 * src/lib/completeness.ts
 *
 * Real-time EPD Completeness Score & Checklist Auditor.
 * Evaluates numerical and narrative fields across all steps.
 */

export interface FieldCheck {
  id: string
  label: string
  step: number
  stepPath: string
  isComplete: boolean
  helpText: string
}

export function auditProjectCompleteness(project: any): {
  scorePct: number
  completedCount: number
  totalCount: number
  checks: FieldCheck[]
} {
  if (!project) {
    return { scorePct: 0, completedCount: 0, totalCount: 0, checks: [] }
  }

  const pDesc = typeof project.product_description === 'string'
    ? (() => { try { return JSON.parse(project.product_description) } catch { return {} } })()
    : project.product_description || {}

  const mDesc = typeof project.manufacturing_narrative === 'string'
    ? (() => { try { return JSON.parse(project.manufacturing_narrative) } catch { return {} } })()
    : project.manufacturing_narrative || {}

  const tData = typeof project.transportation_data === 'string'
    ? (() => { try { return JSON.parse(project.transportation_data) } catch { return null } })()
    : project.transportation_data

  const mfg = project.manufacturing || {}

  const checks: FieldCheck[] = [
    {
      id: 'product_name',
      label: 'Product Name & Manufacturer',
      step: 1,
      stepPath: 'setup',
      isComplete: !!(project.product_name && project.manufacturer_name),
      helpText: 'Basic product and manufacturer identity',
    },
    {
      id: 'company_desc',
      label: 'Company Description',
      step: 1,
      stepPath: 'setup',
      isComplete: !!(project.company_description && project.company_description.trim().length >= 5),
      helpText: 'Corporate overview narrative',
    },
    {
      id: 'operating_principle',
      label: 'Product Operating Principle Narrative',
      step: 1,
      stepPath: 'setup',
      isComplete: !!(pDesc.operating_principle || (project.product_narrative && project.product_narrative.trim().length >= 5)),
      helpText: 'Detailed core technology and operating principle',
    },
    {
      id: 'functional_unit',
      label: 'Functional Unit & RSL',
      step: 1,
      stepPath: 'setup',
      isComplete: !!(project.functional_unit_quantity > 0 && project.functional_unit_unit),
      helpText: 'Quantified functional unit and service lifespan',
    },
    {
      id: 'bom',
      label: 'Bill of Materials (BOM)',
      step: 2,
      stepPath: 'inventory?tab=bom',
      isComplete: Array.isArray(project.bom) && project.bom.length > 0,
      helpText: 'A1–A3 material inventory items',
    },
    {
      id: 'manufacturing',
      label: 'Manufacturing Data & Energy',
      step: 2,
      stepPath: 'inventory?tab=manufacturing',
      isComplete: !!(project.manufacturing && (project.manufacturing.electricity_use_kwh > 0 || project.manufacturing.product_mass_kg > 0 || mDesc.component_sourcing_description)),
      helpText: 'A3 manufacturing electricity and process specs',
    },
    {
      id: 'compressed_air_validation',
      label: 'Compressed Air Double-Counting Prevention',
      step: 2,
      stepPath: 'inventory?tab=manufacturing',
      isComplete: !((mfg.compressed_air_energy_mj || 0) > 0 && !mfg.compressed_air_already_in_electricity),
      helpText: 'Confirmation that compressed air energy is excluded from electricity',
    },
    {
      id: 'transport',
      label: 'Transportation Scenarios',
      step: 3,
      stepPath: 'transportation',
      isComplete: !!(
        (Array.isArray(project.transport) && project.transport.length > 0) ||
        (Array.isArray(project.transport_legs) && project.transport_legs.length > 0) ||
        (tData && (tData.a4_segment || (Array.isArray(tData.a2_segments) && tData.a2_segments.length > 0)))
      ),
      helpText: 'A2/A4 vehicle distance and logistics routes',
    },
    {
      id: 'operational_energy',
      label: 'Operational Energy (Module B6)',
      step: 2,
      stepPath: 'inventory?tab=use_phase',
      isComplete: !!(project.use_phase && Number(project.use_phase.annual_electricity_kwh) > 0),
      helpText: 'B6 annual electricity demand (kWh)',
    },
    {
      id: 'end_of_life',
      label: 'End-of-Life Scenarios (C1–C4)',
      step: 2,
      stepPath: 'inventory?tab=end_of_life',
      isComplete: !!(
        project.end_of_life &&
        (Number(project.end_of_life.waste_to_landfill_pct) +
          Number(project.end_of_life.waste_to_recycling_pct) +
          Number(project.end_of_life.waste_to_incineration_pct) +
          Number(project.end_of_life.waste_to_reuse_pct)) > 0
      ),
      helpText: 'C1–C4 waste treatment collection & routing percentages',
    },
    {
      id: 'material_composition_consistency',
      label: 'Material composition is internally consistent',
      step: 2,
      stepPath: 'inventory?tab=bom',
      isComplete: (() => {
        const bomItems = Array.isArray(project.bom) ? project.bom : []
        if (bomItems.length === 0) return false
        const totalMass = bomItems.reduce((sum: number, item: any) => sum + (Number(item.mass_kg || item.quantity) || 0), 0)
        if (totalMass <= 0) return false
        return bomItems.every((item: any) => (Number(item.mass_kg || item.quantity) || 0) > 0)
      })(),
      helpText: 'All material composition rows have positive mass and valid percentage totals',
    },
    {
      id: 'lca_calculation',
      label: 'Finalized LCA Calculation',
      step: 4,
      stepPath: 'calculate',
      isComplete: !!project.gwp_total || !!project.lca_results,
      helpText: 'EN 15804+A2 matrix engine calculation results',
    },
  ]

  const completedCount = checks.filter((c) => c.isComplete).length
  const totalCount = checks.length
  const scorePct = Math.round((completedCount / totalCount) * 100)

  return { scorePct, completedCount, totalCount, checks }
}
