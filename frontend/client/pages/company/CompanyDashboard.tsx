import { useState } from "react";
import { Link } from "react-router-dom";
import { Building2, Search, ShieldCheck, Clock, XCircle, TrendingUp, Users, FileCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";
import Navbar from "@/components/Navbar";

interface Validation {
  id: string;
  token: string;
  userName: string;
  timestamp: string;
  status: "success" | "failed" | "pending";
  documentHash?: string;
}

export default function CompanyDashboard() {
  const companyData = JSON.parse(localStorage.getItem("companyUser") || "{}");
  const companyName = companyData.companyName || "COMPANY";

  const [tokenInput, setTokenInput] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [validations, setValidations] = useState<Validation[]>([]);

  const handleValidateToken = (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput) return;

    setIsValidating(true);

    setTimeout(() => {
      const isValid = Math.random() > 0.3;
      const newValidation: Validation = {
        id: Date.now().toString(),
        token: tokenInput,
        userName: isValid ? "User " + Math.floor(Math.random() * 1000) : "Unknown",
        timestamp: new Date().toLocaleString(),
        status: isValid ? "success" : "failed",
        documentHash: isValid ? "0x" + Math.random().toString(16).substring(2, 12) : undefined,
      };

      setValidations([newValidation, ...validations]);
      setIsValidating(false);
      setTokenInput("");

      toast({
        title: isValid ? "Token Valid" : "Token Invalid",
        description: isValid
          ? "Identity verified successfully on blockchain."
          : "Token not found or expired.",
        variant: isValid ? "default" : "destructive",
      });
    }, 1000);
  };

  const stats = {
    total: validations.length,
    success: validations.filter((v) => v.status === "success").length,
    failed: validations.filter((v) => v.status === "failed").length,
    today: validations.filter((v) => v.timestamp.includes("2024-02-27")).length,
  };

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

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Company Dashboard</h1>
              <p className="text-slate-500">Welcome, {companyName}</p>
            </div>
            <Link to="/company/validations">
              <Button variant="outline" className="flex items-center gap-2">
                <FileCheck className="w-5 h-5" />
                View All Validations
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                    <p className="text-sm text-slate-500">Total Validations</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <ShieldCheck className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.success}</p>
                    <p className="text-sm text-slate-500">Successful</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-rose-100 rounded-xl flex items-center justify-center">
                    <XCircle className="w-6 h-6 text-rose-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.failed}</p>
                    <p className="text-sm text-slate-500">Failed</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{stats.today}</p>
                    <p className="text-sm text-slate-500">Today</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Token Validator */}
            <div className="lg:col-span-1">
              <Card className="border-border shadow-sm sticky top-24">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    Validate Token
                  </CardTitle>
                  <CardDescription>
                    Enter a user's verification token to check their identity
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleValidateToken} className="space-y-4">
                    <Input
                      placeholder="Enter token code (e.g., AX39B2F8)"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value.toUpperCase())}
                      className="h-12 font-mono text-center text-lg"
                      maxLength={8}
                    />
                    <Button
                      type="submit"
                      disabled={isValidating || !tokenInput}
                      className="w-full h-11"
                    >
                      {isValidating ? "Validating..." : "Verify Identity"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            {/* Recent Validations */}
            <div className="lg:col-span-2">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Recent Validations</CardTitle>
                  <CardDescription>Latest identity verification attempts</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y divide-border">
                    {validations.slice(0, 10).map((validation) => (
                      <div key={validation.id} className="p-6 hover:bg-slate-50 transition-colors">
                        <div className="flex items-center justify-between gap-4">
                          <div className="flex items-center gap-4 flex-1">
                            <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center">
                              {getStatusIcon(validation.status)}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-1">
                                <p className="font-bold text-slate-900">{validation.userName}</p>
                                {getStatusBadge(validation.status)}
                              </div>
                              <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                                <span className="font-mono">Token: {validation.token}</span>
                                <span>{validation.timestamp}</span>
                              </div>
                              {validation.documentHash && (
                                <p className="text-xs text-slate-400 font-mono mt-1">
                                  Hash: {validation.documentHash}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
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
