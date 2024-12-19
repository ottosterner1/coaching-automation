import { useState, useEffect } from 'react';
import { DashboardStats } from './DashboardStats';
import { 
  TeachingPeriod, 
  DashboardMetrics, 
  ProgrammePlayer,
  User 
} from '../../types/dashboard';

const Dashboard = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [periods, setPeriods] = useState<TeachingPeriod[]>([]);
  const [stats, setStats] = useState<DashboardMetrics | null>(null);
  const [players, setPlayers] = useState<ProgrammePlayer[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch user data first
        const userResponse = await fetch('/api/current-user');
        if (!userResponse.ok) {
          throw new Error('Failed to fetch user data');
        }
        const userData = await userResponse.json();
        setCurrentUser(userData);

        // Fetch dashboard stats
        const statsResponse = await fetch(`/api/dashboard/stats${selectedPeriod ? `?period=${selectedPeriod}` : ''}`);
        if (!statsResponse.ok) {
          throw new Error('Failed to fetch dashboard stats');
        }
        const statsData = await statsResponse.json();
        setPeriods(statsData.periods);
        setStats(statsData.stats);

        // Fetch programme players
        const playersResponse = await fetch(`/api/programme-players${selectedPeriod ? `?period=${selectedPeriod}` : ''}`);
        if (!playersResponse.ok) {
          throw new Error('Failed to fetch programme players');
        }
        const playersData = await playersResponse.json();
        setPlayers(playersData);

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

  if (!stats || !currentUser) {
    return <div>No data available</div>;
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
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

      {/* Admin Analytics Section - Only shown to admins */}
      {(currentUser.is_admin || currentUser.is_super_admin) && stats.coachSummaries && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Club Analytics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Group Progress */}
            <div>
              <h3 className="text-lg font-medium mb-4">Group Progress</h3>
              <div className="space-y-2">
                {stats.currentGroups.map((group) => (
                  <div key={group.name} className="flex justify-between items-center">
                    <span className="text-gray-600">{group.name}</span>
                    <div className="text-right">
                      <span className="font-medium">{group.count} students</span>
                      <div className="text-sm text-gray-500">
                        {((group.reports_completed / group.count) * 100).toFixed(1)}% complete
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Coach Performance */}
            <div>
              <h3 className="text-lg font-medium mb-4">Coach Performance</h3>
              <div className="space-y-2">
                {stats.coachSummaries.map((coach) => (
                  <div key={coach.id} className="flex justify-between items-center">
                    <span className="text-gray-600">{coach.name}</span>
                    <div className="text-right">
                      <span className="font-medium">
                        {coach.reports_completed}/{coach.total_assigned}
                      </span>
                      <div className="text-sm text-gray-500">
                        {((coach.reports_completed / coach.total_assigned) * 100).toFixed(1)}% complete
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reports Management Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          {currentUser.is_admin || currentUser.is_super_admin ? 'All Reports' : 'Reports'}
        </h2>
        {players.length === 0 ? (
          <p className="text-gray-500">No reports available for this period.</p>
        ) : (
          <div className="divide-y">
            {players.map((player) => (
              <div key={player.id} className="py-4 flex justify-between items-center">
                <div>
                  <h3 className="font-medium">{player.student_name}</h3>
                  <p className="text-sm text-gray-500">Group: {player.group_name}</p>
                </div>
                <div className="space-x-2">
                  {player.report_submitted ? (
                    <>
                      <a 
                        href={`/report/${player.report_id}`}
                        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                      >
                        View
                      </a>
                      {player.can_edit && (
                        <a 
                          href={`/report/${player.report_id}/edit?period=${selectedPeriod}`}
                          className="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50"
                        >
                          Edit
                        </a>
                      )}
                    </>
                  ) : (
                    player.can_edit && (
                      <a 
                        href={`/report/create/${player.id}?period=${selectedPeriod}`}
                        className="inline-flex items-center px-3 py-2 border border-green-300 shadow-sm text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50"
                      >
                        Create Report
                      </a>
                    )
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;