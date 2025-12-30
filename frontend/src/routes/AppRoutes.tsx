import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Dashboard />} />
      </Route>

      {/* Catch all - redirect to dashboard (which will redirect to login if needed) */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}