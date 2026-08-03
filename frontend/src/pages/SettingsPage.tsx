/**
 * src/pages/SettingsPage.tsx
 *
 * Basic organization settings page.
 */

import { AppLayout } from '@/components/organisms/AppLayout'
import { TextInput } from '@/components/atoms/TextInput'
import { ButtonPrimary, Button } from '@/components/atoms/Button'
import { useAppSelector } from '@/store'

export default function SettingsPage() {
  const { user } = useAppSelector(s => s.auth)

  const breadcrumbs = [
    { label: 'Settings' }
  ]

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      <div className="w-full max-w-[600px] mx-auto px-hero-h py-section">
        
        <h1 className="text-heading-lg text-ink mb-md">Account Settings</h1>
        
        <div className="bg-white border border-hairline p-xl rounded-sm flex flex-col gap-lg mb-xl">
          <h2 className="text-heading-sm text-ink border-b border-hairline pb-sm">User Profile</h2>
          <div className="grid grid-cols-1 tablet:grid-cols-2 gap-md">
            <TextInput label="Display Name" defaultValue={user?.display_name} />
            <TextInput label="Email Address" defaultValue={user?.email} disabled />
            <TextInput label="Role" defaultValue={user?.role} disabled />
          </div>
          <div>
            <ButtonPrimary>Save Profile</ButtonPrimary>
          </div>
        </div>

        <div className="bg-white border border-hairline p-xl rounded-sm flex flex-col gap-lg">
          <h2 className="text-heading-sm text-ink border-b border-hairline pb-sm">Organization</h2>
          <div className="grid grid-cols-1 gap-md">
            <TextInput label="Organization Name" defaultValue={user?.organization} />
            <TextInput label="Default EPD Program Operator" defaultValue="EPD International" />
          </div>
          <div>
            <Button>Update Organization</Button>
          </div>
        </div>

      </div>
    </AppLayout>
  )
}
