import { useState, useEffect } from "react";
import { Activity, Users, Building2, FileCheck, Server, AlertTriangle, CheckCircle, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import Navbar from "@/components/Navbar";

export default function SystemMonitor() {
  const [blockchainStatus, setBlockchainStatus] = useState({
    status: "operational",
    blockHeight: 1234567,
    difficulty: "18.5T",
    hashRate: "342.5 EH/s",
    avgBlockTime: "9.8 min",
  });

  const [systemMetrics, setSystemMetrics] = useState({
    cpuUsage: 45,
    memoryUsage: 62,
    diskUsage: 38,
    networkLatency: 12,
  });

  const [stats, setStats] = useState({
    totalUsers: 1247,
    totalCompanies: 89,
    totalDocuments: 3589,
    totalValidations: 12456,
    activeToday: 342,
  });

  const [recentActivity, setRecentActivity] = useState([]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemMetrics((prev) => ({
        cpuUsage: Math.min(100, Math.max(20, prev.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.min(100, Math.max(30, prev.memoryUsage + (Math.random() - 0.5) * 5)),
        diskUsage: prev.diskUsage,
        networkLatency: Math.min(50, Math.max(5, prev.networkLatency + (Math.random() - 0.5) * 5)),
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "operational":
        return <Badge className="bg-emerald-100 text-emerald-700 border-none">Operational</Badge>;
      case "warning":
        return <Badge className="bg-amber-100 text-amber-700 border-none">Warning</Badge>;
      case "error":
        return <Badge className="bg-rose-100 text-rose-700 border-none">Error</Badge>;
      default:
        return null;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "user":
        return <Users className="w-4 h-4" />;
      case "company":
        return <Building2 className="w-4 h-4" />;
      case "document":
        return <FileCheck className="w-4 h-4" />;
      case "blockchain":
        return <Server className="w-4 h-4" />;
      case "system":
        return <Activity className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">System Monitor</h1>
              <p className="text-slate-500">Real-time blockchain and system status</p>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge(blockchainStatus.status)}
              <Button variant="outline" size="sm">
                <Activity className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Platform Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.totalUsers.toLocaleString()}</p>
                    <p className="text-sm text-slate-500">Users</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.totalCompanies}</p>
                    <p className="text-sm text-slate-500">Companies</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <FileCheck className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.totalDocuments.toLocaleString()}</p>
                    <p className="text-sm text-slate-500">Documents</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.totalValidations.toLocaleString()}</p>
                    <p className="text-sm text-slate-500">Validations</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.activeToday}</p>
                    <p className="text-sm text-slate-500">Active Today</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Blockchain Status */}
            <div className="lg:col-span-2 space-y-6">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Server className="w-5 h-5 text-primary" />
                      Blockchain Status
                    </CardTitle>
                    {getStatusBadge(blockchainStatus.status)}
                  </div>
                  <CardDescription>Real-time blockchain network metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-1">
                      <p className="text-sm text-slate-500">Block Height</p>
                      <p className="text-2xl font-bold text-slate-900">
                        {blockchainStatus.blockHeight.toLocaleString()}
                      </p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-slate-500">Network Difficulty</p>
                      <p className="text-2xl font-bold text-slate-900">{blockchainStatus.difficulty}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-slate-500">Hash Rate</p>
                      <p className="text-2xl font-bold text-slate-900">{blockchainStatus.hashRate}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-slate-500">Avg Block Time</p>
                      <p className="text-2xl font-bold text-slate-900">{blockchainStatus.avgBlockTime}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* System Performance */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    System Performance
                  </CardTitle>
                  <CardDescription>Server resource utilization</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">CPU Usage</span>
                      <span className="text-sm font-bold text-slate-900">
                        {systemMetrics.cpuUsage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={systemMetrics.cpuUsage} className="h-2" />
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">Memory Usage</span>
                      <span className="text-sm font-bold text-slate-900">
                        {systemMetrics.memoryUsage.toFixed(1)}%
                      </span>
                    </div>
                    <Progress value={systemMetrics.memoryUsage} className="h-2" />
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">Disk Usage</span>
                      <span className="text-sm font-bold text-slate-900">
                        {systemMetrics.diskUsage}%
                      </span>
                    </div>
                    <Progress value={systemMetrics.diskUsage} className="h-2" />
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-700">Network Latency</span>
                      <span className="text-sm font-bold text-slate-900">
                        {systemMetrics.networkLatency.toFixed(1)} ms
                      </span>
                    </div>
                    <Progress value={(systemMetrics.networkLatency / 50) * 100} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <div className="space-y-6">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">Recent Activity</CardTitle>
                  <CardDescription>Latest system events</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y divide-border">
                    {recentActivity.map((activity, index) => (
                      <div key={index} className="p-4 hover:bg-slate-50 transition-colors">
                        <div className="flex gap-3">
                          <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center shrink-0 text-primary">
                            {getActivityIcon(activity.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-slate-900">{activity.message}</p>
                            <p className="text-xs text-slate-400 mt-1">{activity.time}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* System Health */}
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg">System Health</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                      <span className="text-sm font-medium text-slate-900">API Services</span>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 border-none">Online</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                      <span className="text-sm font-medium text-slate-900">Database</span>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 border-none">Online</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-emerald-600" />
                      <span className="text-sm font-medium text-slate-900">Blockchain Node</span>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 border-none">Synced</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                      <span className="text-sm font-medium text-slate-900">Storage</span>
                    </div>
                    <Badge className="bg-amber-100 text-amber-700 border-none">62% Full</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
