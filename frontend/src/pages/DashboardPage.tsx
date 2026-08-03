/**
 * src/pages/DashboardPage.tsx
 *
 * PRD §6.3 Dashboard — fetches projects from FastAPI /api/v1/projects (AWS RDS).
 */

import { Link, useNavigate } from 'react-router-dom'
import { useProjects } from '@/hooks/useProjects'
import { useAppSelector } from '@/store'

import { AppLayout } from '@/components/organisms/AppLayout'
import { CalloutStat } from '@/components/molecules/CalloutStat'
import { ProductCard } from '@/components/molecules/ProductCard'
import { ButtonPrimary } from '@/components/atoms/Button'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faPlus } from '@fortawesome/free-solid-svg-icons'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAppSelector((s) => s.auth)
  const { data: projects = [], isLoading, error } = useProjects()

  // Derive stats from real data
  const totalDeclarations = projects.length
  const inProgress = projects.filter(p => p.status === 'draft' || p.status === 'in_progress').length
  const published = projects.filter(p => p.status === 'published').length
  const avgGwp =
    projects.filter(p => p.gwp_total != null).length > 0
      ? (
          projects
            .filter(p => p.gwp_total != null)
            .reduce((sum, p) => sum + (p.gwp_total || 0), 0) /
          projects.filter(p => p.gwp_total != null).length
        ).toFixed(1)
      : '—'

  const STATS = [
    { label: 'Total Declarations', value: String(totalDeclarations), caption: 'All projects' },
    { label: 'In Progress', value: String(inProgress), caption: 'Pending completion', color: 'warning' as const },
    { label: 'Published (EPD)', value: String(published), caption: 'Verified and active', color: 'primary' as const },
    { label: 'Avg. GWP', value: avgGwp === '—' ? '—' : `${avgGwp}`, caption: 'kg CO₂e (total)', color: undefined },
  ]

  const breadcrumbs = [{ label: 'Projects' }]

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        {/* Header row */}
        <div className="flex flex-col mobile:flex-row mobile:items-end justify-between gap-md mb-xl">
          <div>
            <h1 className="text-heading-lg text-ink">Dashboard</h1>
            <p className="text-body-md text-mute mt-xxs">
              Welcome back, {user?.display_name?.split(' ')[0] ?? 'there'}
            </p>
          </div>

          <Link to="/projects/new">
            <ButtonPrimary iconLeft={faPlus} aria-label="Create new declaration">
              New Declaration
            </ButtonPrimary>
          </Link>
        </div>

        {/* 4-up Stats Grid */}
        <div className="grid grid-cols-1 mobile:grid-cols-2 desktop-small:grid-cols-4 gap-lg mb-xxl">
          {STATS.map((stat) => (
            <CalloutStat
              key={stat.label}
              value={stat.value}
              caption={stat.caption}
              eyebrow={stat.label}
              valueColor={stat.color}
            />
          ))}
        </div>

        {/* Projects Section */}
        <div className="border-t border-hairline pt-xl">
          <h2 className="text-heading-md text-ink mb-lg">Recent Projects</h2>

          {isLoading ? (
            <div className="flex justify-center py-xxl text-mute">Loading projects...</div>
          ) : error ? (
            <div className="flex justify-center py-xxl text-error text-body-sm">
              Could not load projects. Is the backend running?
            </div>
          ) : projects.length > 0 ? (
            <div className="grid grid-cols-1 tablet:grid-cols-2 desktop-small:grid-cols-3 gap-lg">
              {projects.map((proj) => (
                <ProductCard
                  key={proj.id}
                  projectName={proj.product_name}
                  standard={(proj.epd_standard || '').replace(/_/g, ' ')}
                  functionalUnit={`${proj.functional_unit_quantity} ${proj.functional_unit_unit}`}
                  lastEdited={proj.created_at ? new Date(proj.created_at).toLocaleDateString() : 'Just now'}
                  status={proj.status as any}
                  currentStep={1}
                  onOpen={() => navigate(`/projects/${proj.id}/inventory`)}
                />
              ))}
            </div>
          ) : (
            /* Empty State */
            <div className="bg-white border border-hairline border-dashed rounded-sm p-xxl text-center flex flex-col items-center gap-md">
              <div className="w-[64px] h-[64px] bg-surface-soft rounded-full flex items-center justify-center mb-sm">
                <FontAwesomeIcon icon={faPlus} className="text-mute text-heading-md" />
              </div>
              <h3 className="text-heading-sm text-ink">No projects yet</h3>
              <p className="text-body-sm text-mute max-w-[400px]">
                Start your first LCA calculation to generate an audit-ready Environmental Product Declaration.
              </p>
              <Link to="/projects/new" className="mt-sm">
                <ButtonPrimary>Create First Project</ButtonPrimary>
              </Link>
            </div>
          )}
        </div>

      </div>
    </AppLayout>
  )
}
