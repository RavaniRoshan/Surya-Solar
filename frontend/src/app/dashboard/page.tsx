'use client'

import { useAuth } from '@/contexts/AuthContext'

export const dynamic = 'force-dynamic'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Welcome to ZERO-COMP Dashboard
          </h2>
          <p className="text-gray-600 mb-6">
            Solar Weather Prediction System
          </p>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              User Information
            </h3>
            <p className="text-sm text-gray-600">
              Email: {user?.email}
            </p>
            <p className="text-sm text-gray-600">
              User ID: {user?.id}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}