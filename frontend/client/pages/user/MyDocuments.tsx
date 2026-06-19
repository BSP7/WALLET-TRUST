import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText, Plus, Search, Download, Eye, Trash2, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";

interface Document {
  id: string;
  type: string;
  name: string;
  hash: string;
  date: string;
  status: "verified" | "pending" | "rejected";
  fileSize?: string;
}

const DOC_TYPE_LABELS: Record<string, string> = {
  passport: "Passport",
  driver_license: "Driver's License",
  national_id: "National ID",
  id: "ID",
};

function toIsoDateFromEpochSeconds(epochSeconds?: number) {
  if (!epochSeconds) return "";
  const date = new Date(epochSeconds * 1000);
  return date.toISOString().split("T")[0];
}

function mapStatus(status?: string): Document["status"] {
  if (status === "success") return "verified";
  if (status === "failed") return "rejected";
  return "pending";
}

export default function MyDocuments() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const load = async () => {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        setDocuments([]);
        return;
      }

      const response = await fetch("/api/users/documents", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        setDocuments([]);
        return;
      }

      const data = await response.json();
      const docs = (data?.documents ?? []) as any[];
      const mapped: Document[] = docs.map((doc) => {
        const meta = doc?.metadata ?? {};
        const docType = meta?.doc_type || "id";
        return {
          id: String(doc.id),
          type: DOC_TYPE_LABELS[docType] ?? String(docType),
          name: meta?.title || user?.fullName || "",
          hash: doc.file_hash ? String(doc.file_hash) : "",
          date: toIsoDateFromEpochSeconds(doc.created_at) || "",
          status: mapStatus(meta?.blockchain_status),
          fileSize: doc.file_size ? `${(Number(doc.file_size) / (1024 * 1024)).toFixed(2)} MB` : undefined,
        };
      });
      setDocuments(mapped);
    };

    load().catch(() => {
      setDocuments([]);
    });
  }, [user?.userId, user?.fullName]);

  const filteredDocuments = documents.filter(doc =>
    doc.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.hash.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "verified":
        return <Badge className="bg-emerald-100 text-emerald-700 border-none">Verified</Badge>;
      case "pending":
        return <Badge className="bg-amber-100 text-amber-700 border-none">Pending</Badge>;
      case "rejected":
        return <Badge className="bg-rose-100 text-rose-700 border-none">Rejected</Badge>;
      default:
        return null;
    }
  };

  const handleDelete = (docId: string) => {
    toast({
      title: "Document Deleted",
      description: "Document has been removed from the blockchain.",
      variant: "destructive",
    });
    setDocuments(documents.filter(d => d.id !== docId));
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">My Documents</h1>
              <p className="text-slate-500">Manage your blockchain-verified identity documents.</p>
            </div>
            <Link to="/user/documents/scan">
              <Button className="flex items-center gap-2">
                <Plus className="w-5 h-5" />
                Upload New Document
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
                  placeholder="Search by document type or hash..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-11"
                />
              </div>
            </CardContent>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">{documents.length}</p>
                    <p className="text-sm text-slate-500">Total Documents</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <Shield className="w-6 h-6 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {documents.filter(d => d.status === "verified").length}
                    </p>
                    <p className="text-sm text-slate-500">Verified</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                    <FileText className="w-6 h-6 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {documents.filter(d => d.status === "pending").length}
                    </p>
                    <p className="text-sm text-slate-500">Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border shadow-sm">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Download className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {documents.reduce((acc, doc) => {
                        const size = parseFloat(doc.fileSize || "0");
                        return acc + size;
                      }, 0).toFixed(1)}
                    </p>
                    <p className="text-sm text-slate-500">MB Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Document List */}
          <Card className="border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Document Archive</CardTitle>
                  <CardDescription>
                    All your uploaded and verified identity documents.
                  </CardDescription>
                </div>
                <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                  <Shield className="w-3 h-3 mr-1" />
                  Blockchain Secured
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {filteredDocuments.length === 0 ? (
                  <div className="p-12 text-center">
                    <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No documents found.</p>
                  </div>
                ) : (
                  filteredDocuments.map((doc) => (
                    <div key={doc.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center">
                            <FileText className="w-7 h-7 text-primary" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                              <h3 className="font-bold text-lg text-slate-900">{doc.type}</h3>
                              {getStatusBadge(doc.status)}
                            </div>
                            <div className="space-y-1">
                              <p className="text-sm text-slate-600">{doc.name}</p>
                              <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                                <span className="font-mono">Hash: {doc.hash}</span>
                                <span>Added: {doc.date}</span>
                                {doc.fileSize && <span>Size: {doc.fileSize}</span>}
                              </div>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm" className="flex items-center gap-2">
                            <Eye className="w-4 h-4" />
                            View
                          </Button>
                          <Button variant="outline" size="sm" className="flex items-center gap-2">
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(doc.id)}
                            className="text-destructive hover:bg-destructive/5"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
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
