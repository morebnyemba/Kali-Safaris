// Filename: src/pages/Dashboard.jsx
// Main dashboard page - Enhanced with dynamic data fetching, chart integration, and robustness improvements

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FiUsers, FiMessageCircle, FiBarChart2, FiActivity, FiAlertCircle,
  FiCheckCircle, FiSettings, FiZap, FiHardDrive, FiTrendingUp, FiCpu, FiList, FiLoader, FiAlertTriangle
} from 'react-icons/fi';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

// --- Import your chart components ---
// Ensure these files exist and export components correctly
import ConversationTrendChart from '@/components/charts/ConversationTrendChat';
import BotPerformanceDisplay from '@/components/charts/BotPerfomanceDisplay';

// --- Import custom hook for dashboard data ---
import { useDashboardData } from '@/hooks/useDashboardData';

// --- API Configuration & Helper ---
import { API_BASE_URL } from '@/lib/api';

// Activity icons map for WebSocket updates
const activityIcons = {
  FiUsers,
  FiZap,
  FiMessageCircle,
  FiSettings,
  FiCheckCircle,
  FiAlertCircle,
  default: FiActivity,
};

const getCardStyles = (colorScheme) => {
  switch (colorScheme) {
    case "green": return { bgColor: "bg-green-50 dark:bg-green-900/40", borderColor: "border-green-500/60 dark:border-green-600", textColor: "text-green-700 dark:text-green-300", iconColor: "text-green-600 dark:text-green-400" };
    case "emerald": return { bgColor: "bg-emerald-50 dark:bg-emerald-900/40", borderColor: "border-emerald-500/60 dark:border-emerald-600", textColor: "text-emerald-700 dark:text-emerald-300", iconColor: "text-emerald-600 dark:text-emerald-400" };
    case "lime": return { bgColor: "bg-lime-50 dark:bg-lime-900/40", borderColor: "border-lime-500/60 dark:border-lime-600", textColor: "text-lime-700 dark:text-lime-300", iconColor: "text-lime-600 dark:text-lime-400" };
    case "teal": return { bgColor: "bg-teal-50 dark:bg-teal-900/40", borderColor: "border-teal-500/60 dark:border-teal-600", textColor: "text-teal-700 dark:text-teal-300", iconColor: "text-teal-600 dark:text-teal-400" };
    case "red": return { bgColor: "bg-red-50 dark:bg-red-900/40", borderColor: "border-red-500/60 dark:border-red-600", textColor: "text-red-700 dark:text-red-300", iconColor: "text-red-600 dark:text-red-400" };
    default: return { bgColor: "bg-gray-50 dark:bg-gray-900/40", borderColor: "border-gray-500/60 dark:border-gray-600", textColor: "text-gray-700 dark:text-gray-300", iconColor: "text-gray-600 dark:text-gray-400" };
  }
};

const StatCard = ({ linkTo, title, value, trend, trendType, icon, colorScheme, isLoading, valueSuffix = "" }) => {
  const styles = getCardStyles(colorScheme);
  const content = (
    <div className={`p-4 sm:p-5 rounded-xl shadow-lg border-l-4 ${styles.borderColor} ${styles.bgColor} flex flex-col justify-between min-h-[140px] md:min-h-[150px] h-full transition-transform hover:scale-[1.02] ${linkTo ? 'cursor-pointer' : ''}`}>
      <div>
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-xs sm:text-sm font-semibold text-gray-600 dark:text-gray-300 truncate" title={title}>{title}</h3>
          {React.cloneElement(icon, { className: `h-6 w-6 opacity-70 ${styles.iconColor}` })}
        </div>
        <p className={`text-2xl sm:text-3xl md:text-4xl font-bold ${styles.textColor}`}>
          {isLoading ? <FiLoader className="animate-spin h-8 w-8 inline-block opacity-70" /> : `${value}${valueSuffix}`}
        </p>
      </div>
      {trend && (
        <div className={`text-xs mt-1.5 ${trendType === 'positive' ? 'text-green-600 dark:text-green-400' : trendType === 'negative' ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>
          {isLoading ? <Skeleton className="h-3 w-20 inline-block dark:bg-slate-700 rounded" /> : trend}
        </div>
      )}
    </div>
  );

  return linkTo ? <Link to={linkTo} className="block h-full hover:shadow-2xl transition-shadow duration-300">{content}</Link> : <div className="block h-full">{content}</div>;
};

const FlowInsightsCard = ({ insights, isLoading, onNavigate }) => (
  <Card className="lg:col-span-1 dark:bg-slate-800 dark:border-slate-700 shadow-lg">
    <CardHeader><CardTitle className="text-lg font-semibold dark:text-slate-100 flex items-center"><FiZap className="mr-2 text-purple-500"/>Flow Insights</CardTitle></CardHeader>
    <CardContent className="space-y-3">
      {[
        { label: "Active Flows", value: insights.activeFlows, icon: <FiZap className="text-purple-500"/>, link: "/flows" },
        { label: "Completions Today", value: insights.completedToday, icon: <FiCheckCircle className="text-emerald-500"/>, link: null },
        { label: "Avg. Steps/Flow", value: insights.avgSteps, icon: <FiList className="text-teal-500"/>, link: null },
      ].map(item => (
        <div key={item.label} className={`flex justify-between items-center p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 ${item.link ? 'hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer' : ''} transition-colors`}
             onClick={item.link && !isLoading ? () => onNavigate(item.link) : undefined}
        >
          <div className="flex items-center">
            {React.cloneElement(item.icon, {className: "h-5 w-5 mr-3 opacity-90"})}
            <p className="text-sm text-slate-700 dark:text-slate-300 font-medium">{item.label}</p>
          </div>
          <p className="text-lg font-bold text-slate-800 dark:text-slate-100">{isLoading && item.value === "..." ? <FiLoader className="animate-spin h-5 w-5 inline text-slate-500"/> : item.value}</p>
        </div>
      ))}
    </CardContent>
  </Card>
);

const RecentActivityCard = ({ activities, isLoading }) => (
  <Card className="lg:col-span-2 dark:bg-slate-800 dark:border-slate-700 shadow-lg">
    <CardHeader><CardTitle className="text-lg font-semibold dark:text-slate-100 flex items-center"><FiActivity className="mr-2 text-blue-500"/>Recent Activity</CardTitle></CardHeader>
    <CardContent>
      <div className="space-y-2 max-h-72 overflow-y-auto pr-2 custom-scrollbar">
        {isLoading && activities.length === 0 ? ([...Array(3)].map((_, i) => <Skeleton key={i} className="h-12 w-full dark:bg-slate-700 rounded-lg mb-2" />))
         : activities.length === 0 ? (<p className="text-sm text-slate-500 dark:text-slate-400 italic p-3 text-center">No recent activity.</p>)
         : (activities.map((activity) => (
            <div key={activity.id} className="flex items-start space-x-3 p-2.5 bg-slate-50 dark:bg-slate-700/60 rounded-lg">
              <span className="flex-shrink-0 mt-1 text-slate-500 dark:text-slate-400">{React.isValidElement(activity.icon) ? activity.icon : <FiActivity className="text-gray-500"/>}</span>
              <div><p className="text-sm text-slate-700 dark:text-slate-300 leading-snug">{activity.text}</p><p className="text-xs text-slate-400 dark:text-slate-500">{activity.timestamp ? new Date(activity.timestamp).toLocaleString() : 'N/A'}</p></div>
            </div>)))}
      </div>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  // Use the custom hook for dashboard data
  const { 
    statsCardsData: hookStatsCardsData, 
    recentActivities: hookRecentActivities, 
    flowInsights: hookFlowInsights, 
    conversationTrendsData: hookConversationTrendsData, 
    botPerformanceData: hookBotPerformanceData, 
    systemStatus, 
    isLoading: isLoadingData, 
    error: loadingError, 
    refetch: fetchData 
  } = useDashboardData();
  
  // Local state for WebSocket-updated data (initialized from hook)
  const [statsCardsData, setStatsCardsData] = useState(hookStatsCardsData);
  const [recentActivities, setRecentActivities] = useState(hookRecentActivities);
  const [conversationTrendsData, setConversationTrendsData] = useState(hookConversationTrendsData);
  const [botPerformanceData, setBotPerformanceData] = useState(hookBotPerformanceData);
  
  const navigate = useNavigate();
  const { accessToken, isLoadingAuth } = useAuth();

  // Sync local state with hook data when it changes
  useEffect(() => {
    setStatsCardsData(hookStatsCardsData);
    setRecentActivities(hookRecentActivities);
    setConversationTrendsData(hookConversationTrendsData);
    setBotPerformanceData(hookBotPerformanceData);
  }, [hookStatsCardsData, hookRecentActivities, hookConversationTrendsData, hookBotPerformanceData]);

  // --- WebSocket Setup ---
  const getSocketUrl = useCallback(() => {
    if (accessToken) {
      return `${API_BASE_URL.replace(/^http/, 'ws')}/ws/stats/dashboard/?token=${accessToken}`;
    }
    return null; // Don't connect if no token
  }, [accessToken]);

  const { lastJsonMessage, readyState } = useWebSocket(getSocketUrl, { shouldReconnect: () => true });

  // --- WebSocket Message Handling ---
  useEffect(() => {
    if (lastJsonMessage) {
      const { type, payload } = lastJsonMessage;

      switch (type) {
        case 'stats_update':
          if (payload) {
            setStatsCardsData(prevData =>
              prevData.map(card =>
                payload[card.id] !== undefined ? { ...card, value: payload[card.id].toString() } : card
              )
            );
          }
          break;
        case 'activity_log_add':
          if (payload) {
            const IconComponent = activityIcons[payload.iconName] || activityIcons.default;
            const newActivity = {
              ...payload,
              icon: <IconComponent className={`${payload.iconColor || "text-gray-500"} h-5 w-5`} />
            };
            setRecentActivities(prev => [newActivity, ...prev].slice(0, 10));
          }
          break;
        case 'chart_update_conversation_trends':
          if (payload) setConversationTrendsData(payload);
          break;
        case 'chart_update_bot_performance':
          if (payload) setBotPerformanceData(prev => ({ ...prev, ...payload }));
          break;
        case 'human_intervention_needed':
          if (payload) {
            toast.warning(payload.message, {
              description: `Click to view conversation with ${payload.name}.`,
              duration: 20000,
              icon: <FiAlertTriangle className="h-5 w-5" />,
              action: {
                label: 'View Conversation',
                onClick: () => navigate(`/conversation/${payload.contact_id}`),
              },
              id: `intervention-${payload.contact_id}`
            });
          }
          break;
        default:
          // Unhandled WebSocket message type
          break;
      }
    }
  }, [lastJsonMessage, navigate]);

  const connectionStatus = {
    [ReadyState.CONNECTING]: { text: 'Connecting...', color: 'text-yellow-500', icon: <FiLoader className="animate-spin" /> },
    [ReadyState.OPEN]: { text: 'Live', color: 'text-green-500', icon: <FiCheckCircle /> },
    [ReadyState.CLOSING]: { text: 'Closing...', color: 'text-orange-500', icon: <FiAlertCircle /> },
    [ReadyState.CLOSED]: { text: 'Disconnected', color: 'text-red-500', icon: <FiAlertCircle /> },
    [ReadyState.UNINSTANTIATED]: { text: 'Uninstantiated', color: 'text-gray-500', icon: <FiAlertCircle /> },
  }[readyState];

  return (
    <div className="space-y-6 md:space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 dark:text-gray-100">Dashboard Overview</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Welcome! Here's a real-time summary of your CRM activity.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 py-1.5 px-3 rounded-full text-xs font-medium ${connectionStatus.color}`}>
            {connectionStatus.icon && React.cloneElement(connectionStatus.icon, { className: "h-4 w-4"})}
            <span>Live Feed: {connectionStatus.text}</span>
          </div>
          <div className={`flex items-center gap-2 py-1.5 px-3 rounded-full text-xs font-medium ${systemStatus.color}`}>
            {systemStatus.icon && React.isValidElement(systemStatus.icon) ? React.cloneElement(systemStatus.icon, { className: "h-4 w-4"}) : <FiActivity className="h-4 w-4"/>}
            <span>System: {systemStatus.status}</span>
          </div>
        </div>
      </div>

      {loadingError && (
        <Card className="border-orange-500/70 dark:border-orange-600/70 bg-orange-50 dark:bg-orange-900/20">
            <CardContent className="p-4 text-sm text-orange-700 dark:text-orange-300 flex items-center gap-3">
                <FiAlertCircle className="h-6 w-6 flex-shrink-0"/>
                <div><span className="font-semibold">Data Loading Issue(s):</span> {loadingError.replace(/\(toasted\)/gi, '').replace(/;/g, '; ')} Some data might be unavailable.</div>
            </CardContent>
        </Card>
      )}

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 gap-4 md:gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {statsCardsData.map((stat) => {
          // Defensive: Ensure defaultIcon is a valid React element
          const defaultIconElement = React.isValidElement(stat.defaultIcon) 
            ? stat.defaultIcon 
            : <FiActivity />;

          return (
            <StatCard
              key={stat.id}
              linkTo={stat.linkTo}
              title={stat.title}
              value={stat.value}
              trend={stat.trend}
              trendType={stat.trendType}
              icon={defaultIconElement}
              colorScheme={stat.colorScheme}
              isLoading={isLoadingData && stat.value === "..."}
              valueSuffix={stat.valueSuffix}
            />
          );
        })}
      </div>

      {/* Flow Insights & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
        <FlowInsightsCard insights={hookFlowInsights} isLoading={isLoadingData} onNavigate={navigate} />
        <RecentActivityCard activities={recentActivities} isLoading={isLoadingData} />
      </div>
      
      {/* Chart Sections - Using imported components */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8 mt-6 md:mt-8">
          <Card className="dark:bg-slate-800 dark:border-slate-700 shadow-lg">
              <CardHeader><CardTitle className="text-lg font-semibold dark:text-slate-100 flex items-center"><FiBarChart2 className="mr-2 text-indigo-500"/>Conversation Trends</CardTitle></CardHeader>
              <CardContent className="h-80 bg-slate-50 dark:bg-slate-700/50 rounded-md p-4">
                  { ConversationTrendChart ? <ConversationTrendChart data={conversationTrendsData} isLoading={isLoadingData} /> : <p className="text-center text-sm text-slate-500 dark:text-slate-400">Chart component not loaded.</p> }
              </CardContent>
          </Card>
           <Card className="dark:bg-slate-800 dark:border-slate-700 shadow-lg">
              <CardHeader><CardTitle className="text-lg font-semibold dark:text-slate-100 flex items-center"><FiCpu className="mr-2 text-rose-500"/>Bot Performance</CardTitle></CardHeader>
              <CardContent className="h-80 bg-slate-50 dark:bg-slate-700/50 rounded-md p-4">
                  { BotPerformanceDisplay ? <BotPerformanceDisplay data={botPerformanceData} isLoading={isLoadingData} /> : <p className="text-center text-sm text-slate-500 dark:text-slate-400">Performance display not loaded.</p> }
              </CardContent>
          </Card>
      </div>
    </div>
  );
}