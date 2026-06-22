import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, Download, Filter, ShieldCheck, XCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import Navbar from "@/components/Navbar";

interface Validation {
  id: string;
  token: string;
  userName: string;
  timestamp: string;
  status: "success" | "failed" | "pending";
  documentHash?: string;
  documentType?: string;
}

export default function ValidationHistory() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [validations, setValidations] = useState<Validation[]>([]);

  useEffect(() => {
    const fetchValidations = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;
        const res = await fetch("/api/company/validations", {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          const mapped = data.validations.map((v: any) => ({
            id: v.id,
            token: v.token,
            userName: v.user_address || "User",
            timestamp: new Date(v.timestamp * 1000).toLocaleString(),
            status: v.is_valid ? "success" : "failed",
            documentHash: v.tx_hash,
            documentType: "Blockchain Token",
          }));
          mapped.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
          setValidations(mapped);
        }
      } catch (err) {
        console.error("Error fetching validations:", err);
      }
    };
    fetchValidations();
  }, []);

  const filteredValidations = validations.filter((validation) => {
    const matchesSearch =
      validation.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      validation.token.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === "all" || validation.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return <Badge className="bg-emerald-100 text-emerald-700 border-none">Verified</Badge>;
      case "failed":
        return <Badge className="bg-rose-100 text-rose-700 border-none">Failed</Badge>;
      case "pending":
        return <Badge className="bg-amber-100 text-amber-700 border-none">Pending</Badge>;
      default:
        return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <ShieldCheck className="w-5 h-5 text-emerald-600" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-rose-600" />;
      case "pending":
        return <Clock className="w-5 h-5 text-amber-600" />;
      default:
        return null;
    }
  };

  const stats = {
    total: validations.length,
    success: validations.filter((v) => v.status === "success").length,
    failed: validations.filter((v) => v.status === "failed").length,
    pending: validations.filter((v) => v.status === "pending").length,
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <Link
                to="/company/dashboard"
                className="inline-flex items-center text-sm text-slate-500 hover:text-primary transition-colors mb-2"
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back to Dashboard
              </Link>
              <h1 className="text-3xl font-bold text-slate-900">Validation History</h1>
              <p className="text-slate-500">Complete record of all identity verifications</p>
            </div>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-5 h-5" />
              Export Report
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-slate-900">{stats.total}</p>
                  <p className="text-sm text-slate-500 mt-1">Total Validations</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-emerald-600">{stats.success}</p>
                  <p className="text-sm text-slate-500 mt-1">Successful</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-rose-600">{stats.failed}</p>
                  <p className="text-sm text-slate-500 mt-1">Failed</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-3xl font-bold text-amber-600">{stats.pending}</p>
                  <p className="text-sm text-slate-500 mt-1">Pending</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card className="border-border shadow-sm">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative">
                  <Input
                    type="text"
                    placeholder="Search by name or token..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="h-11 pl-4"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-slate-400" />
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="Filter by status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="success">Verified</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Validation List */}
          <Card className="border-border shadow-sm">
            <CardHeader>
              <CardTitle>All Validations ({filteredValidations.length})</CardTitle>
              <CardDescription>
                Detailed history of identity verification requests
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {filteredValidations.length === 0 ? (
                  <div className="p-12 text-center">
                    <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No validations found.</p>
                  </div>
                ) : (
                  filteredValidations.map((validation) => (
                    <div key={validation.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-14 h-14 bg-slate-100 rounded-xl flex items-center justify-center">
                            {getStatusIcon(validation.status)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                              <h3 className="font-bold text-lg text-slate-900">
                                {validation.userName}
                              </h3>
                              {getStatusBadge(validation.status)}
                            </div>
                            <div className="space-y-1">
                              <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                                <span className="font-mono">Token: {validation.token}</span>
                                <span>{validation.timestamp}</span>
                                {validation.documentType && (
                                  <span>Document: {validation.documentType}</span>
                                )}
                              </div>
                              {validation.documentHash && (
                                <p className="text-xs text-slate-400 font-mono">
                                  Blockchain Hash: {validation.documentHash}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
