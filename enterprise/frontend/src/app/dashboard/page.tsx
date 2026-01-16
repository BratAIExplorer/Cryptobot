'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useBotStore } from '@/lib/store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { formatCurrency, formatPercentage, formatUptime, getPnlColor } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuthStore();
  const { status, loadStatus, startBot, stopBot, restartBot, isLoading: botLoading } = useBotStore();

  const [portfolio, setPortfolio] = useState<any>(null);
  const [recentTrades, setRecentTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
      // Refresh every 30 seconds
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      await loadStatus();
      const [portfolioData, tradesData] = await Promise.all([
        api.getPortfolio(),
        api.getRecentTrades(24),
      ]);
      setPortfolio(portfolioData);
      setRecentTrades(tradesData.slice(0, 10)); // Last 10 trades
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                🤖 CryptoBot Enterprise
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Welcome back, {user?.full_name || user?.username}!
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Role: <span className="font-semibold">{user?.role}</span>
              </span>
              <Button onClick={handleLogout} variant="outline" size="sm">
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Bot Status Section */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Bot Status</CardTitle>
              <CardDescription>Current trading bot status and controls</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Status Info */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      status?.is_running
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
                    }`}>
                      {status?.is_running ? 'Running' : 'Stopped'}
                    </span>
                  </div>

                  {status?.is_running && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">PID:</span>
                        <span className="text-sm font-mono">{status.pid}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Uptime:</span>
                        <span className="text-sm font-mono">{formatUptime(status.uptime_seconds)}</span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Mode:</span>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          status.mode === 'live'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        }`}>
                          {status.mode.toUpperCase()}
                        </span>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Active Strategies:</span>
                        <span className="text-sm font-semibold">{status.strategies_active}</span>
                      </div>
                    </>
                  )}
                </div>

                {/* Bot Controls */}
                <div className="flex flex-col justify-center gap-3">
                  {status?.is_running ? (
                    <>
                      <Button
                        onClick={stopBot}
                        disabled={botLoading}
                        variant="destructive"
                        className="w-full"
                      >
                        {botLoading ? 'Stopping...' : '⏹️ Stop Bot'}
                      </Button>
                      <Button
                        onClick={restartBot}
                        disabled={botLoading}
                        variant="secondary"
                        className="w-full"
                      >
                        {botLoading ? 'Restarting...' : '🔄 Restart Bot'}
                      </Button>
                    </>
                  ) : (
                    <Button
                      onClick={startBot}
                      disabled={botLoading}
                      className="w-full"
                    >
                      {botLoading ? 'Starting...' : '▶️ Start Bot'}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Portfolio Summary */}
        {portfolio && (
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Total P&L</CardDescription>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getPnlColor(portfolio.total_pnl)}`}>
                  {formatCurrency(portfolio.total_pnl)}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Total Trades</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{portfolio.total_trades}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Win Rate</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatPercentage(portfolio.win_rate)}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardDescription>Active Positions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{portfolio.active_positions}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Strategy Performance */}
        {portfolio?.strategies && portfolio.strategies.length > 0 && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Strategy Performance</CardTitle>
              <CardDescription>Performance breakdown by strategy</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {portfolio.strategies.map((strategy: any, index: number) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div>
                      <div className="font-semibold">{strategy.name}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {strategy.trades} trades
                      </div>
                    </div>
                    <div className={`text-lg font-bold ${getPnlColor(strategy.pnl)}`}>
                      {formatCurrency(strategy.pnl)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Trades */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Trades</CardTitle>
            <CardDescription>Last 10 trades from the past 24 hours</CardDescription>
          </CardHeader>
          <CardContent>
            {recentTrades.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Time</th>
                      <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Symbol</th>
                      <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Side</th>
                      <th className="text-right py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Price</th>
                      <th className="text-right py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Amount</th>
                      <th className="text-left py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">Strategy</th>
                      <th className="text-right py-3 px-2 text-sm font-medium text-gray-600 dark:text-gray-400">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTrades.map((trade: any, index: number) => (
                      <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                        <td className="py-3 px-2 text-sm">
                          {new Date(trade.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-3 px-2 text-sm font-medium">{trade.symbol}</td>
                        <td className="py-3 px-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.side === 'buy'
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {trade.side.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-2 text-sm text-right font-mono">
                          ${trade.price.toFixed(2)}
                        </td>
                        <td className="py-3 px-2 text-sm text-right font-mono">
                          {trade.amount.toFixed(4)}
                        </td>
                        <td className="py-3 px-2 text-sm">{trade.strategy}</td>
                        <td className={`py-3 px-2 text-sm text-right font-mono ${
                          trade.pnl !== null ? getPnlColor(trade.pnl) : ''
                        }`}>
                          {trade.pnl !== null ? formatCurrency(trade.pnl) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No trades in the last 24 hours
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
