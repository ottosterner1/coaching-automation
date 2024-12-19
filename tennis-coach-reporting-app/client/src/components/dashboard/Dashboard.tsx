import { useState, useEffect } from 'react';
import { DashboardStats } from './DashboardStats';
import { TeachingPeriod, DashboardMetrics } from '../../types/dashboard';

const Dashboard = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [periods, setPeriods] = useState<TeachingPeriod[]>([]);
  const [stats, setStats] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`/api/dashboard/stats${selectedPeriod ? `?period=${selectedPeriod}` : ''}`);
        
        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`API error: ${errorData}`);
        }

        const data = await response.json();
        setPeriods(data.periods);
        setStats(data.stats);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError(error instanceof Error ? error.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedPeriod]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  if (!stats) {
    return <div>No data available</div>;
  }

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Tennis Reports Dashboard</h1>
        <select
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          value={selectedPeriod || ''}
          onChange={(e) => setSelectedPeriod(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">All Periods</option>
          {periods.map((period) => (
            <option key={period.id} value={period.id}>{period.name}</option>
          ))}
        </select>
      </div>

      <DashboardStats stats={stats} />

      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Group Distribution</h2>
        <div className="space-y-2">
          {stats.currentGroups.map((group) => (
            <div key={group.name} className="flex justify-between items-center">
              <span className="text-gray-600">{group.name}</span>
              <span className="font-medium">{group.count} students</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;