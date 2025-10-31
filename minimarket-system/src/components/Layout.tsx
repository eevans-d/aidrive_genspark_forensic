import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Package, Warehouse, CheckSquare, ShoppingCart, Users, LogOut, User as UserIcon } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { user, signOut } = useAuth()

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/deposito', icon: Warehouse, label: 'Depósito' },
    { path: '/stock', icon: Package, label: 'Stock' },
    { path: '/tareas', icon: CheckSquare, label: 'Tareas' },
    { path: '/productos', icon: ShoppingCart, label: 'Productos' },
    { path: '/proveedores', icon: Users, label: 'Proveedores' },
  ]

  async function handleSignOut() {
    try {
      await signOut()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl sm:text-2xl font-bold text-blue-600">Mini Market System</h1>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-gray-700">
                <UserIcon className="w-5 h-5" />
                <span className="hidden sm:inline text-sm">
                  {user?.user_metadata?.nombre || user?.email}
                </span>
              </div>
              <button
                onClick={handleSignOut}
                className="flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Cerrar Sesión"
              >
                <LogOut className="w-5 h-5" />
                <span className="hidden sm:inline text-sm">Salir</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex flex-col md:flex-row">
        {/* Sidebar - Oculto en móvil, visible en desktop */}
        <aside className="hidden md:block md:w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)]">
          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </aside>

        {/* Bottom Navigation - Solo en móvil */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-50">
          <div className="grid grid-cols-6 gap-1 p-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex flex-col items-center justify-center py-2 px-1 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5 mb-1" />
                  <span className="text-xs">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 md:p-8 pb-20 md:pb-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
