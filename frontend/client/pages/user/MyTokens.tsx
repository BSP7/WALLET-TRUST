import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Key, Plus, Search, Copy, CheckCircle2, Clock, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";

interface Token {
  id: string;
  token: string;
  createdAt: string;
  expiresAt: string;
  status: "active" | "expired" | "used";
  usedBy?: string;
}

function formatEpochSeconds(epochSeconds?: number) {
  if (!epochSeconds) return "";
  const date = new Date(epochSeconds * 1000);
  return date.toISOString().replace("T", " ").slice(0, 16);
}

export default function MyTokens() {
  const { user } = useAuth();
  const [tokens, setTokens] = useState<Token[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const load = async () => {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        setTokens([]);
        return;
      }

      const response = await fetch("/api/users/tokens", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        setTokens([]);
        return;
      }

      const data = await response.json();
      const items = (data?.tokens ?? []) as any[];
      const mapped: Token[] = items.map((t) => {
        const tokenId = t?.token_id ?? "";
        return {
          id: String(t.id ?? tokenId),
          token: tokenId !== "" ? String(tokenId) : String(t.tx_hash ?? ""),
          createdAt: formatEpochSeconds(t.created_at),
          expiresAt: "",
          status: "active",
        };
      });
      setTokens(mapped);
    };

    load().catch(() => setTokens([]));
  }, [user?.userId]);

  const filteredTokens = tokens.filter(token =>
    token.token.toLowerCase().includes(searchQuery.toLowerCase()) ||
    token.usedBy?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const copyToken = (token: string) => {
    navigator.clipboard.writeText(token);
    toast({
      title: "Token Copied",
      description: "Token has been copied to your clipboard.",
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return <Badge className="bg-emerald-100 text-emerald-700 border-none">Active</Badge>;
      case "expired":
        return <Badge className="bg-slate-100 text-slate-600 border-none">Expired</Badge>;
      case "used":
        return <Badge className="bg-blue-100 text-blue-700 border-none">Used</Badge>;
      default:
        return null;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <Clock className="w-4 h-4 text-emerald-600" />;
      case "expired":
        return <XCircle className="w-4 h-4 text-slate-600" />;
      case "used":
        return <CheckCircle2 className="w-4 h-4 text-blue-600" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">My Tokens</h1>
              <p className="text-slate-500">Manage your identity verification tokens.</p>
            </div>
            <Link to="/user/tokens/generate">
              <Button className="flex items-center gap-2">
                <Plus className="w-5 h-5" />
                Generate New Token
              </Button>
            </Link>
          </div>

          {/* Search */}
          <Card className="border-border shadow-sm">
            <CardContent className="pt-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  type="text"
                  placeholder="Search tokens or companies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-11"
                />
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <Clock className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {tokens.filter(t => t.status === "active").length}
                    </p>
                    <p className="text-sm text-slate-500">Active Tokens</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {tokens.filter(t => t.status === "used").length}
                    </p>
                    <p className="text-sm text-slate-500">Used Tokens</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center">
                    <XCircle className="w-6 h-6 text-slate-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {tokens.filter(t => t.status === "expired").length}
                    </p>
                    <p className="text-sm text-slate-500">Expired Tokens</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Token List */}
          <Card className="border-border shadow-sm">
            <CardHeader>
              <CardTitle>Token History</CardTitle>
              <CardDescription>
                All verification tokens you've generated, past and present.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {filteredTokens.length === 0 ? (
                  <div className="p-12 text-center">
                    <Key className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No tokens found.</p>
                  </div>
                ) : (
                  filteredTokens.map((token) => (
                    <div key={token.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                            {getStatusIcon(token.status)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                              <p className="font-mono font-bold text-lg text-slate-900">
                                {token.token}
                              </p>
                              {getStatusBadge(token.status)}
                            </div>
                            <div className="flex flex-wrap gap-4 text-sm text-slate-500">
                              <span>Created: {token.createdAt}</span>
                              <span>Expires: {token.expiresAt}</span>
                              {token.usedBy && <span>Used by: {token.usedBy}</span>}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToken(token.token)}
                          className="flex items-center gap-2"
                        >
                          <Copy className="w-4 h-4" />
                          Copy
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
