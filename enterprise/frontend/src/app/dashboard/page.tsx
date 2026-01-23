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
  Zap,
  X
} from 'lucide-react';
import { LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Area, AreaChart } from 'recharts';
import { formatCurrency, formatPercentage, formatRelativeTime, formatUptime, getPnlColor } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const {
    botStatus,
    portfolio,
    botConfigs,
    recentTrades,
    strategyPerformance,
    fetchBotStatus,
    fetchPortfolio,
    fetchBotConfigs,
    fetchRecentTrades,
    fetchStrategyPerformance,
    updateBotConfig,
    startBot,
    stopBot,
    restartBot,
    isLoading: botLoading
  } = useBotStore();

  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedBot, setSelectedBot] = useState<any | null>(null);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

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
        fetchBotConfigs(),
        fetchRecentTrades(24),
        fetchStrategyPerformance()
      ]);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const handleUpdateConfig = async (id: number, data: any) => {
    setActionLoading(`config-${id}`);
    try {
      await updateBotConfig(id, data);
      await fetchBotConfigs();
      setShowSettingsModal(false);
    } catch (error) {
      console.error('Error updating config:', error);
    } finally {
      setActionLoading(null);
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
    { date: 'Jan 10', value: 1000 },
    { date: 'Jan 11', value: 1050 },
    { date: 'Jan 12', value: 1100 },
    { date: 'Jan 13', value: 1200 },
    { date: 'Jan 14', value: 1350 },
    { date: 'Jan 15', value: 1450 },
    { date: 'Jan 16', value: portfolio?.total_value_usd ? portfolio.total_value_usd : 1500 },
  ];

  // Asset distribution data (mock - replace with real data)
  const assetData = [
    { name: 'BTC', value: 250, color: '#3B82F6' },
    { name: 'ETH', value: 200, color: '#10B981' },
    { name: 'BNB', value: 333, color: '#F59E0B' },
    { name: 'SOL', value: 333, color: '#EF4444' },
    { name: 'USDT', value: 334, color: '#8B5CF6' },
  ];

  const totalAssetValue = assetData.reduce((sum: number, asset: any) => sum + asset.value, 0);

  // Bot configurations (merge store configs with performance data)
  const bots = botConfigs.map((config: any) => {
    const perf = strategyPerformance.find((p: any) => p.strategy === config.bot_type || p.strategy === config.bot_name);
    return {
      id: config.id,
      name: config.bot_name,
      type: config.bot_type,
      status: config.is_active ? 'active' : 'paused',
      pnl: perf?.total_pnl || 0,
      pnlPercent: perf ? (perf.total_pnl / (config.config.budget || 300) * 100) : 0,
      trades: perf?.trades || 0,
      winRate: perf?.win_rate || 0,
      reinvestProfits: config.reinvest_profits,
      config: config.config
    };
  });

  // Fallback to mock if no configs (development)
  const displayBots = bots.length > 0 ? bots : [
    {
      id: 1,
      name: 'Grid Bot BTC',
      type: 'Grid Trading',
      status: botStatus?.is_running ? 'active' : 'paused',
      pnl: 154.32,
      pnlPercent: 1.54,
      trades: 124,
      winRate: 68,
      reinvestProfits: true,
      config: { grid_levels: 10, budget: 100 }
    },
    {
      id: 2,
      name: 'Grid Bot ETH',
      type: 'Grid Trading',
      status: botStatus?.is_running ? 'active' : 'paused',
      pnl: 89.15,
      pnlPercent: 0.89,
      trades: 256,
      winRate: 72,
      reinvestProfits: true,
      config: { grid_levels: 12, budget: 100 }
    }
  ];

  // Recent activity from trades
  const activities = recentTrades.slice(0, 4).map((trade: any) => ({
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
                {portfolio ? formatCurrency(portfolio.total_value_usd) : '$1,500'}
              </p>
              <p className="text-sm text-green-400 flex items-center">
                <TrendingUp className="w-4 h-4 mr-1" />
                Active
              </p>
            </div>

            {/* Wallet Usage Bar */}
            <div className="mt-4 pt-4 border-t border-gray-800">
              <div className="flex justify-between items-center mb-1 text-xs text-gray-400">
                <span>Wallet Usage</span>
                <span>{portfolio?.total_value_usd > 0 ? ((portfolio.used_balance / portfolio.total_value_usd) * 100).toFixed(1) : '25'}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-blue-500 h-full transition-all duration-500"
                  style={{ width: portfolio?.total_value_usd > 0 ? `${(portfolio.used_balance / portfolio.total_value_usd) * 100}%` : '25%' }}
                />
              </div>
              <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                <span>Used: {portfolio ? formatCurrency(portfolio.used_balance) : '$375'}</span>
                <span>Avail: {portfolio ? formatCurrency(portfolio.available_balance) : '$1,125'}</span>
              </div>
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
                {botStatus?.strategies_active || 5}
              </p>
              <p className="text-sm text-blue-400 flex items-center">
                Monitoring active
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

        {/* Trading Bots Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">Trading Bots</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayBots.map((bot, index) => (
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
                  <button
                    onClick={() => {
                      setSelectedBot(bot);
                      setShowDetailsModal(true);
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg text-sm font-medium transition flex items-center justify-center"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Details
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBot(bot);
                      setShowSettingsModal(true);
                    }}
                    className="w-10 h-10 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg flex items-center justify-center transition"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleBotAction(bot.status === 'active' ? 'stop' : 'start')}
                    disabled={actionLoading !== null}
                    className="w-10 h-10 bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg flex items-center justify-center transition"
                  >
                    <Power className={`w-4 h-4 ${bot.status === 'active' ? 'text-red-400' : 'text-green-400'}`} />
                  </button>
                </div>
              </div>
            ))}
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
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
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
                  tickFormatter={(value) => `$${(value / 1000).toFixed(1)}K`}
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

        {/* Recent Activity */}
        <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-800">
          <h2 className="text-2xl font-bold text-white mb-6">Recent Activity</h2>
          <div className="space-y-4">
            {activities.length > 0 ? activities.map((activity: any, index: number) => (
              <div
                key={index}
                className={`flex items-start space-x-4 p-4 rounded-lg border-l-4 ${activity.type === 'buy' ? 'bg-green-950/20 border-green-500' :
                  activity.type === 'sell' ? 'bg-red-950/20 border-red-500' :
                    'bg-blue-950/20 border-blue-500'
                  }`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${activity.type === 'buy' ? 'bg-green-600' :
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

      {/* Settings Modal */}
      {showSettingsModal && selectedBot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-[#1E293B] border border-gray-800 rounded-2xl w-full max-w-md overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-800">
              <h3 className="text-xl font-bold text-white">Bot Settings: {selectedBot.name}</h3>
              <button onClick={() => setShowSettingsModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">Reinvest Profits</p>
                  <p className="text-xs text-gray-400">Automatically add earnings back to capital</p>
                </div>
                <button
                  onClick={() => {
                    handleUpdateConfig(selectedBot.id, {
                      reinvest_profits: !selectedBot.reinvestProfits
                    });
                  }}
                  disabled={actionLoading !== null}
                  className={`w-12 h-6 rounded-full transition-colors relative ${selectedBot.reinvestProfits ? 'bg-blue-600' : 'bg-gray-700'} ${actionLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${selectedBot.reinvestProfits ? 'left-7' : 'left-1'}`} />
                </button>
              </div>

              <div className="space-y-2">
                <label className="text-xs text-gray-400 uppercase font-medium">Trading Budget (USD)</label>
                <div className="flex items-center space-x-2">
                  <input
                    id="bot-budget-input"
                    type="number"
                    defaultValue={selectedBot.config?.budget || 100}
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="pt-4 flex space-x-3">
                <button
                  onClick={() => setShowSettingsModal(false)}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg font-medium transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    const budgetInput = document.getElementById('bot-budget-input') as HTMLInputElement;
                    const budget = budgetInput ? parseFloat(budgetInput.value) : (selectedBot.config?.budget || 100);
                    handleUpdateConfig(selectedBot.id, {
                      config: { ...selectedBot.config, budget }
                    });
                  }}
                  disabled={actionLoading !== null}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition disabled:opacity-50"
                >
                  {actionLoading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Details Modal */}
      {showDetailsModal && selectedBot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-[#1E293B] border border-gray-800 rounded-2xl w-full max-w-lg overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-800">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                  <Activity className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedBot.name}</h3>
                  <p className="text-xs text-gray-400">{selectedBot.type}</p>
                </div>
              </div>
              <button onClick={() => setShowDetailsModal(false)} className="text-gray-400 hover:text-white">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                  <p className="text-xs text-gray-400 mb-1">Total P&L</p>
                  <p className={`text-lg font-bold ${selectedBot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedBot.pnl >= 0 ? '+' : ''}{selectedBot.pnl.toFixed(2)}
                  </p>
                </div>
                <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                  <p className="text-xs text-gray-400 mb-1">Win Rate</p>
                  <p className="text-lg font-bold text-white">{selectedBot.winRate}%</p>
                </div>
                <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
                  <p className="text-xs text-gray-400 mb-1">Active Positions</p>
                  <p className="text-lg font-bold text-white">1</p>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-white">Recent Trade Performance</h4>
                <div className="space-y-2">
                  {recentTrades.filter((t: any) => t.strategy === selectedBot.type || t.strategy === selectedBot.name).slice(0, 5).map((trade: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
                      <div className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${trade.side === 'buy' ? 'bg-green-600/20 text-green-500' : 'bg-red-600/20 text-red-500'}`}>
                          {trade.side === 'buy' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{trade.symbol} {trade.side === 'buy' ? 'Buy' : 'Sell'}</p>
                          <p className="text-[10px] text-gray-500">{formatRelativeTime(trade.timestamp)}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.pnl ? (trade.pnl >= 0 ? '+' : '') + trade.pnl.toFixed(2) : '-'}
                        </p>
                        <p className="text-[10px] text-gray-500">Completed</p>
                      </div>
                    </div>
                  ))}
                  {recentTrades.filter((t: any) => t.strategy === selectedBot.type || t.strategy === selectedBot.name).length === 0 && (
                    <p className="text-sm text-gray-500 text-center py-4">No recent trades for this bot</p>
                  )}
                </div>
              </div>

              <div className="pt-2">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-medium transition"
                >
                  Close View
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
