'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useBotStore } from '@/lib/store';
import {
  Wallet,
  TrendingUp,
  Activity,
  BarChart3,
  Power,
  Settings,
  TrendingDown,
  CheckCircle,
  Zap
} from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Area, AreaChart } from 'recharts';
import { formatCurrency, formatPercentage, formatRelativeTime, formatUptime, getPnlColor } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const {
    botStatus,
    portfolio,
    recentTrades,
    strategyPerformance,
    fetchBotStatus,
    fetchPortfolio,
    fetchRecentTrades,
    fetchStrategyPerformance,
    startBot,
    stopBot,
    restartBot,
    isLoading: botLoading
  } = useBotStore();

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  // Fetch data on mount and set interval
  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 30000); // Refresh every 30s
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const fetchData = async () => {
    try {
      await Promise.all([
        fetchBotStatus(),
        fetchPortfolio(),
        fetchRecentTrades(24),
        fetchStrategyPerformance()
      ]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const handleBotAction = async (action: 'start' | 'stop' | 'restart') => {
    setActionLoading(action);
    try {
      if (action === 'start') await startBot();
      else if (action === 'stop') await stopBot();
      else if (action === 'restart') await restartBot();

      await fetchBotStatus();
    } catch (error) {
      console.error(`Error ${action}ing bot:`, error);
    } finally {
      setActionLoading(null);
    }
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  // Mock portfolio chart data (replace with real data later)
  const portfolioChartData = [
    { date: 'Jan 10', value: 10000 },
    { date: 'Jan 11', value: 10200 },
    { date: 'Jan 12', value: 10500 },
    { date: 'Jan 13', value: 10800 },
    { date: 'Jan 14', value: 11200 },
    { date: 'Jan 15', value: 11800 },
    { date: 'Jan 16', value: portfolio?.total_pnl ? 10000 + portfolio.total_pnl : 12315 },
  ];

  // Asset distribution data (mock - replace with real data)
  const assetData = [
    { name: 'BTC', value: 5200, color: '#3B82F6' },
    { name: 'ETH', value: 3100, color: '#10B981' },
    { name: 'BNB', value: 1800, color: '#F59E0B' },
    { name: 'SOL', value: 1200, color: '#EF4444' },
    { name: 'USDT', value: 1015, color: '#8B5CF6' },
  ];

  const totalAssetValue = assetData.reduce((sum, asset) => sum + asset.value, 0);

  // Bot configurations (use real data if available, otherwise mock)
  const bots = strategyPerformance.length > 0 ? strategyPerformance.map(s => ({
    name: s.strategy,
    type: s.strategy,
    status: 'active',
    pnl: s.total_pnl,
    pnlPercent: (s.total_pnl / 10000 * 100), // Assuming $10k base
    trades: s.total_trades,
    winRate: s.win_rate
  })) : [
    {
      name: 'Grid Bot BTC',
      type: 'Grid Trading',
      status: botStatus?.is_running ? 'active' : 'paused',
      pnl: 1547.32,
      pnlPercent: 15.47,
      trades: 124,
      winRate: 68
    },
    {
      name: 'Grid Bot ETH',
      type: 'Grid Trading',
      status: botStatus?.is_running ? 'active' : 'paused',
      pnl: 892.15,
      pnlPercent: 8.92,
      trades: 256,
      winRate: 72
    },
    {
      name: 'Buy-the-Dip',
      type: 'Opportunistic',
      status: 'paused',
      pnl: -124.50,
      pnlPercent: -1.24,
      trades: 48,
      winRate: 45
    }
  ];

  // Recent activity from trades
  const activities = recentTrades.slice(0, 4).map(trade => ({
    type: trade.side === 'buy' ? 'buy' : 'sell',
    title: `${trade.side === 'buy' ? 'Buy' : 'Sell'} Order Executed`,
    description: `${trade.strategy} ${trade.side} ${trade.symbol}`,
    details: `${trade.amount.toFixed(4)} @ ${formatCurrency(trade.price)}`,
    time: formatRelativeTime(trade.timestamp)
  }));

  return (
    <div className="min-h-screen bg-[#0F172A]">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#1E293B]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Crypto Trading Dashboard</h1>
              <p className="text-sm text-gray-400">AI-Powered Trading Bots</p>
            </div>
          </div>
          <button
            onClick={() => useAuthStore.getState().logout()}
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Portfolio */}
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase">Total Portfolio</h3>
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Wallet className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-white">
                {portfolio ? formatCurrency(10000 + portfolio.total_pnl) : '$12,315'}
              </p>
              <p className="text-sm text-green-400 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                23.15%
              </p>
            </div>
          </div>

          {/* Total P&L */}
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase">Total P&L</h3>
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="space-y-1">
              <p className={`text-3xl font-bold ${portfolio ? getPnlColor(portfolio.total_pnl) : 'text-white'}`}>
                {portfolio ? formatCurrency(portfolio.total_pnl) : '$2,315'}
              </p>
              <p className="text-sm text-green-400 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                Last 7 days
              </p>
            </div>
          </div>

          {/* Active Bots */}
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase">Active Bots</h3>
              <div className="w-12 h-12 bg-pink-600 rounded-full flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-white">
                {botStatus?.strategies_active || 2}
              </p>
              <p className="text-sm text-green-400 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                3 total
              </p>
            </div>
          </div>

          {/* Total Trades */}
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase">Total Trades</h3>
              <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-3xl font-bold text-white">
                {portfolio?.total_trades || 428}
              </p>
              <p className="text-sm text-green-400 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                All time
              </p>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Portfolio Value Chart */}
          <div className="lg:col-span-2 bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-white mb-6">Portfolio Value</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={portfolioChartData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  stroke="#6B7280"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#6B7280"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: any) => [`$${value.toLocaleString()}`, 'Value']}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  fill="url(#colorValue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Asset Distribution */}
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
            <h3 className="text-lg font-semibold text-white mb-6">Asset Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={assetData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {assetData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                  formatter={(value: any) => [`$${value.toLocaleString()}`, '']}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 space-y-2">
              {assetData.map((asset) => (
                <div key={asset.name} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: asset.color }}
                    />
                    <span className="text-sm text-gray-400">{asset.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-white">
                      ${asset.value.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">
                      {((asset.value / totalAssetValue) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Trading Bots Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Trading Bots</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {bots.map((bot, index) => (
              <div key={index} className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{bot.name}</h3>
                    <p className="text-sm text-gray-400">{bot.type}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${bot.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                    <span className={`text-sm ${bot.status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                      {bot.status === 'active' ? 'Active' : 'Paused'}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-400 mb-1">P&L</p>
                    <p className={`text-xl font-bold ${bot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {bot.pnl >= 0 ? '+' : ''}{bot.pnl.toFixed(2)}
                    </p>
                    <p className={`text-xs flex items-center ${bot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {bot.pnl >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                      {bot.pnlPercent >= 0 ? '+' : ''}{bot.pnlPercent.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400 mb-1">Trades</p>
                    <p className="text-xl font-bold text-white">{bot.trades}</p>
                    <p className="text-xs text-blue-400">{bot.winRate.toFixed(0)}% win</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition flex items-center justify-center">
                    <Zap className="w-4 h-4 mr-2" />
                    Details
                  </button>
                  <button className="w-10 h-10 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg flex items-center justify-center transition">
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleBotAction(bot.status === 'active' ? 'stop' : 'start')}
                    disabled={actionLoading !== null}
                    className="w-10 h-10 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg flex items-center justify-center transition"
                  >
                    <Power className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
          <h2 className="text-2xl font-bold text-white mb-6">Recent Activity</h2>
          <div className="space-y-4">
            {activities.length > 0 ? activities.map((activity, index) => (
              <div
                key={index}
                className={`flex items-start space-x-4 p-4 rounded-lg border-l-4 ${
                  activity.type === 'buy' ? 'bg-green-950/20 border-green-500' :
                  activity.type === 'sell' ? 'bg-red-950/20 border-red-500' :
                  'bg-blue-950/20 border-blue-500'
                }`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  activity.type === 'buy' ? 'bg-green-600' :
                  activity.type === 'sell' ? 'bg-red-600' :
                  'bg-blue-600'
                }`}>
                  {activity.type === 'buy' ? <TrendingUp className="w-5 h-5 text-white" /> :
                   activity.type === 'sell' ? <TrendingDown className="w-5 h-5 text-white" /> :
                   <CheckCircle className="w-5 h-5 text-white" />}
                </div>
                <div className="flex-1">
                  <h4 className="text-white font-medium">{activity.title}</h4>
                  <p className="text-sm text-gray-400">{activity.description}</p>
                  <p className="text-sm font-medium text-gray-300 mt-1">{activity.details}</p>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap">{activity.time}</span>
              </div>
            )) : (
              <div className="text-center py-8 text-gray-500">
                No recent activity
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
