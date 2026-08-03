import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-surface-soft flex items-center justify-center">
      <div className="text-center">
        <p className="text-caption-md text-primary uppercase mb-md">404</p>
        <h1 className="text-display-xl mb-xl">Page Not Found</h1>
        <p className="text-body-md text-mute mb-xxl">
          The page you're looking for doesn't exist.
        </p>
        <Link to="/" className="btn-primary">Return Home</Link>
      </div>
    </div>
  )
}
