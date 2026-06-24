import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

const PrivateRoute = () => {
  const token = localStorage.getItem('token');

  // If token exists, allow access to requested component; else, redirect to Login
  return token ? <Outlet /> : <Navigate to="/login" replace />;
};

export default PrivateRoute;
