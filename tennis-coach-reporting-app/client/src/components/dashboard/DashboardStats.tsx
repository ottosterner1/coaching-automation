// src/components/dashboard/DashboardStats.tsx
import React from 'react';
import { DashboardMetrics } from '../../types/dashboard';  // Updated import

interface DashboardStatsProps {
  stats: DashboardMetrics;  // Updated type
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900">Total Students</h3>
        <p className="text-3xl font-bold text-blue-600">{stats.totalStudents}</p>
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900">Reports Completed</h3>
        <p className="text-3xl font-bold text-green-600">{stats.totalReports}</p>
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900">Completion Rate</h3>
        <p className="text-3xl font-bold text-purple-600">{stats.reportCompletion}%</p>
      </div>
    </div>
  );
};