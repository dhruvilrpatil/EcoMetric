/**
 * src/pages/PortfolioPage.tsx
 *
 * PRD §6.11 Portfolio Dashboard
 *   - Stats header (4-up)
 *   - Regulatory deadline calendar
 *   - Sortable/filterable product catalog table
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AppLayout } from '@/components/organisms/AppLayout'
import { CalloutStat } from '@/components/molecules/CalloutStat'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { ButtonGhost } from '@/components/atoms/Button'
import { useProjects, useDeleteProject, type ProjectSummary } from '@/hooks/useProjects'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTrash, faTriangleExclamation } from '@fortawesome/free-solid-svg-icons'

const DEADLINES = [
  { name: 'ESPR Battery Directive', date: '2027-01-01', days: 156 },
  { name: 'CPR Updates (Construction)', date: '2029-06-01', days: 1068 },
]

export default function PortfolioPage() {
  const { data: projects = [], isLoading, error } = useProjects()
  const deleteProjectMutation = useDeleteProject()

  const [filter, setFilter] = useState<'ALL' | 'PUBLISHED' | 'IN PROGRESS' | 'DRAFT'>('ALL')
  const [projectToDelete, setProjectToDelete] = useState<ProjectSummary | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const breadcrumbs = [
    { label: 'Portfolio' }
  ]

  const totalPublished = projects.filter(p => p.status === 'published').length
  const totalInProgress = projects.filter(p => p.status === 'in_progress' || p.status === 'draft').length
  const gwpProjects = projects.filter(p => p.gwp_total != null)
  const avgGwp = gwpProjects.length > 0
    ? (gwpProjects.reduce((s, p) => s + (p.gwp_total || 0), 0) / gwpProjects.length).toFixed(1)
    : '—'

  const STATS = [
    { label: 'Total Declarations', value: String(projects.length), caption: 'Across active workspace' },
    { label: 'Published EPDs', value: String(totalPublished), caption: 'Third-party verified', color: 'primary' as const },
    { label: 'In Progress', value: String(totalInProgress), caption: 'Pending verification', color: 'warning' as const },
    { label: 'Avg Portfolio GWP', value: avgGwp, caption: 'kg CO2e / unit' },
  ]

  const filteredProjects = projects.filter(p => {
    if (filter === 'ALL') return true
    if (filter === 'PUBLISHED') return p.status === 'published'
    if (filter === 'IN PROGRESS') return p.status === 'in_progress'
    if (filter === 'DRAFT') return p.status === 'draft'
    return true
  })

  async function handleConfirmDelete() {
    if (!projectToDelete) return
    setDeleteError(null)
    try {
      await deleteProjectMutation.mutateAsync(projectToDelete.id)
      setProjectToDelete(null)
    } catch (err: any) {
      setDeleteError(err?.message || 'Failed to delete project. Please try again.')
    }
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">
        
        <div className="mb-xl">
          <h1 className="text-heading-lg text-ink">Portfolio Overview</h1>
          <p className="text-body-md text-mute">Manage enterprise-wide compliance and EPD lifecycle events.</p>
        </div>

        {/* 4-up Stats */}
        <div className="grid grid-cols-1 mobile:grid-cols-2 desktop-small:grid-cols-4 gap-lg mb-xxl">
          {STATS.map((stat, idx) => (
            <CalloutStat
              key={idx}
              value={stat.value}
              caption={stat.caption}
              eyebrow={stat.label}
              valueColor={stat.color}
            />
          ))}
        </div>

        <div className="flex flex-col desktop-small:flex-row gap-xxl mb-xxl">
          
          {/* Main Table */}
          <div className="flex-[2] bg-white border border-hairline rounded-sm flex flex-col">
            <div className="p-md border-b border-hairline bg-surface-soft flex justify-between items-center">
              <h2 className="text-heading-sm text-ink">Product Catalog</h2>
              <div className="flex gap-xs">
                {['ALL', 'PUBLISHED', 'IN PROGRESS', 'DRAFT'].map(f => (
                  <button 
                    key={f}
                    onClick={() => setFilter(f as any)}
                    className={`px-sm py-xxs rounded-sm text-caption-xs font-bold transition-colors ${
                      filter === f ? 'bg-ink text-white' : 'bg-transparent text-mute hover:text-ink'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-hairline bg-white">
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Product</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Standard</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">GWP-total</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Status</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Created</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={6} className="p-xl text-center text-mute text-body-sm">
                        Loading portfolio projects...
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td colSpan={6} className="p-xl text-center text-error text-body-sm">
                        Could not load portfolio catalog.
                      </td>
                    </tr>
                  ) : filteredProjects.map((p) => (
                    <tr key={p.id} className="border-b border-hairline hover:bg-surface-soft transition-colors">
                      <td className="p-md text-body-strong text-ink">{p.product_name}</td>
                      <td className="p-md text-body-sm text-mute">{(p.epd_standard || '').replace(/_/g, ' ')}</td>
                      <td className="p-md text-body-sm text-ink font-mono">
                        {p.gwp_total != null ? `${Number(p.gwp_total).toFixed(2)} kg CO₂e` : '—'}
                      </td>
                      <td className="p-md">
                        <BadgeTag color={p.status === 'published' ? 'success' : p.status === 'in_progress' ? 'info' : 'default'}>
                          {(p.status || 'draft').toUpperCase().replace(/_/g, ' ')}
                        </BadgeTag>
                      </td>
                      <td className="p-md text-body-sm text-mute">
                        {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="p-md text-right">
                        <div className="flex items-center justify-end gap-sm">
                          <Link to={`/projects/${p.id}/inventory`} className="text-link-blue hover:underline text-body-sm font-medium">
                            Manage
                          </Link>
                          <button
                            onClick={() => setProjectToDelete(p)}
                            title="Delete project"
                            className="text-mute hover:text-error transition-colors p-1"
                          >
                            <FontAwesomeIcon icon={faTrash} className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!isLoading && filteredProjects.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-xl text-center text-mute text-body-sm">
                        No projects match the selected filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Rail: Deadlines */}
          <div className="flex-[1] flex flex-col gap-lg">
            <div className="bg-white border border-hairline rounded-sm p-xl">
              <h2 className="text-heading-sm text-ink mb-md">Regulatory Deadlines</h2>
              <div className="flex flex-col gap-md">
                {DEADLINES.map((d, i) => (
                  <div key={i} className="border border-hairline p-md rounded-sm flex flex-col gap-xs">
                    <div className="flex justify-between items-start">
                      <BadgeTag color="warning">REGULATION</BadgeTag>
                      <span className="text-caption-sm font-bold text-warning">{d.days} Days</span>
                    </div>
                    <h3 className="text-body-strong text-ink">{d.name}</h3>
                    <p className="text-caption-sm text-mute">Effective: {d.date}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>

        {/* Delete Confirmation Modal */}
        {projectToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-md animate-fade-in">
            <div className="bg-white border border-hairline rounded-sm shadow-xl max-w-md w-full p-xl flex flex-col gap-lg">
              <div className="flex items-start gap-md">
                <div className="w-10 h-10 rounded-full bg-error-surface/30 text-error flex items-center justify-center flex-shrink-0">
                  <FontAwesomeIcon icon={faTriangleExclamation} className="text-body-lg" />
                </div>
                <div className="flex flex-col gap-xxs">
                  <h3 className="text-heading-sm text-ink">Delete Declaration?</h3>
                  <p className="text-body-sm text-mute">
                    Are you sure you want to delete <strong className="text-ink">{projectToDelete.product_name}</strong>? All associated BOM entries, parameters, transportation data, and LCA calculation results will be permanently removed.
                  </p>
                </div>
              </div>

              {deleteError && (
                <div className="p-sm bg-error-surface/20 border border-error/30 text-error text-caption-sm rounded-sm">
                  {deleteError}
                </div>
              )}

              <div className="flex justify-end items-center gap-sm pt-sm border-t border-hairline">
                <ButtonGhost
                  onClick={() => {
                    setProjectToDelete(null)
                    setDeleteError(null)
                  }}
                  disabled={deleteProjectMutation.isPending}
                >
                  Cancel
                </ButtonGhost>
                <button
                  onClick={handleConfirmDelete}
                  disabled={deleteProjectMutation.isPending}
                  className="px-md py-sm bg-error text-white text-body-sm font-semibold rounded-sm hover:bg-error/90 transition-colors flex items-center gap-xs disabled:opacity-50"
                >
                  <FontAwesomeIcon icon={faTrash} className="text-caption-sm" />
                  {deleteProjectMutation.isPending ? 'Deleting...' : 'Delete Project'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  )
}
