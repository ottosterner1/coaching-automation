// src/types/dashboard.ts
export interface TeachingPeriod {
  id: number;
  name: string;
}

export interface DashboardMetrics {  // Renamed from DashboardStats
  totalStudents: number;
  totalReports: number;
  reportCompletion: number;
  currentGroups: {
    name: string;
    count: number;
  }[];
}