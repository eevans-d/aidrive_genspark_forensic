import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Deposito from './pages/Deposito'
import Stock from './pages/Stock'
import Tareas from './pages/Tareas'
import Productos from './pages/Productos'
import Proveedores from './pages/Proveedores'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route 
        path="/login" 
        element={user ? <Navigate to="/" replace /> : <Login />} 
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/deposito"
        element={
          <ProtectedRoute>
            <Layout>
              <Deposito />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/stock"
        element={
          <ProtectedRoute>
            <Layout>
              <Stock />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/tareas"
        element={
          <ProtectedRoute>
            <Layout>
              <Tareas />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/productos"
        element={
          <ProtectedRoute>
            <Layout>
              <Productos />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/proveedores"
        element={
          <ProtectedRoute>
            <Layout>
              <Proveedores />
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  )
}

export default App
