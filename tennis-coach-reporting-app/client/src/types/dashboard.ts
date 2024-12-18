export interface DashboardData {
    periods: any[];
    selectedPeriodId: number | null;
    programmePlayersData: any[];
    reportMap: Record<string, any>;
    currentGroups: Record<string, number>;
    recommendedGroups: Record<string, number>;
    coachSummaries: Record<string, any>;
    isAdmin: boolean;
    allReportsCompleted: boolean;
  }
  
  declare global {
    interface Window {
      INITIAL_DATA: DashboardData;
    }
  }