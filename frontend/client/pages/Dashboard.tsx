import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, Plus, FileText, CheckCircle2, Copy, Key, Search, RefreshCw, LogOut, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import { cn } from "@/lib/utils";

type UiDocument = {
  id: string;
  type: string;
  name: string;
  hash: string;
  date: string;
  status: "Verified" | "Pending" | "Failed";
};

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

function mapBlockchainStatus(status?: string): UiDocument["status"] {
  if (status === "success") return "Verified";
  if (status === "failed") return "Failed";
  return "Pending";
}

export default function Dashboard() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<UiDocument[]>([]);
  const [generatedToken, setGeneratedToken] = useState("");
  const [validationResult, setValidationResult] = useState<{ valid: boolean, message: string } | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [newDoc, setNewDoc] = useState({
    type: "",
    name: user?.fullName || "",
  });

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileUpload = (file: File) => {
    setSelectedFile(file);
    toast({
      title: "File Ready",
      description: `"${file.name}" has been staged for blockchain hashing.`,
    });

    // Set a default type if not already selected
    if (!newDoc.type) {
      setNewDoc(prev => ({ ...prev, type: "passport" }));
    }
  };

  const loadDocuments = async () => {
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
    const mapped: UiDocument[] = docs.map((doc) => {
      const meta = doc?.metadata ?? {};
      const docType = meta?.doc_type || "id";
      const status = mapBlockchainStatus(meta?.blockchain_status);
      return {
        id: String(doc.id),
        type: DOC_TYPE_LABELS[docType] ?? String(docType),
        name: meta?.title || user?.fullName || "",
        hash: doc.file_hash ? String(doc.file_hash).slice(0, 10) + "..." : "",
        date: toIsoDateFromEpochSeconds(doc.created_at) || "",
        status,
      };
    });
    setDocuments(mapped);
  };

  const loadTokens = async () => {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) return;

    const response = await fetch("/api/users/tokens", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      if (data.tokens && data.tokens.length > 0) {
        // Get latest token ID/hash
        const latest = data.tokens[data.tokens.length - 1];
        const displayToken = latest.token_id ? String(latest.token_id) : latest.id?.substring(0, 8).toUpperCase();
        setGeneratedToken(displayToken || "");
      }
    }
  };

  useEffect(() => {
    loadDocuments().catch(() => { });
    loadTokens().catch(() => { });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.userId]);

  const handleGenerateToken = async () => {
    try {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken || !user?.userId) {
        toast({
          title: "Authentication Required",
          description: "Please log in to generate a token.",
          variant: "destructive",
        });
        return;
      }

      const governmentIdNumber = localStorage.getItem("government_id_number");

      const response = await fetch("/api/blockchain/token/generate", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: user.userId,
          government_id_number: governmentIdNumber || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        const displayToken = data.token_id ? String(data.token_id) : data.tx_hash?.substring(0, 8).toUpperCase();
        setGeneratedToken(displayToken || "");
        toast({
          title: "Token Generated on Blockchain",
          description: `Your token ${displayToken} has been created and stored on the blockchain.`,
        });
      } else {
        toast({
          title: "Generation Failed",
          description: data.revert_reason || data.details || data.error || "You may already have an active token.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Token generation error:", error);
      toast({
        title: "Error",
        description: "Failed to connect to backend. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleValidateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    const inputToken = (e.target as any).token.value;
    try {
      const response = await fetch("/api/blockchain/token/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: inputToken }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setValidationResult({
          valid: false,
          message: data.error || data.details || "Token verification failed.",
        });
        return;
      }

      if (data.valid) {
        setValidationResult({
          valid: true,
          message: `Token #${data.token_id} is valid on-chain.`,
        });
      } else {
        setValidationResult({
          valid: false,
          message: data.error || `Token #${data.token_id} is not valid.`,
        });
      }
    } catch {
      setValidationResult({ valid: false, message: "Failed to reach verification service." });
    }
  };

  const handleAddDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDoc.type) {
      toast({
        title: "Missing Information",
        description: "Please select a document type.",
        variant: "destructive",
      });
      return;
    }

    if (!selectedFile) {
      toast({
        title: "Missing File",
        description: "Please attach a document file.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);

    try {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        throw new Error("Not authenticated");
      }

      const formData = new FormData();
      formData.append("title", newDoc.name);
      formData.append("doc_type", newDoc.type);
      formData.append("file", selectedFile);

      const response = await fetch("/api/documents/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }

      const txHash = data.blockchain?.transaction_hash;
      toast({
        title: "Document Added",
        description: (
          <div className="space-y-2">
            <p>{DOC_TYPE_LABELS[newDoc.type] || newDoc.type} has been uploaded and hashed.</p>
            {txHash && (
              <a
                href={`https://sepolia.etherscan.io/tx/${txHash}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-mono text-primary underline block break-all"
              >
                View Transaction: {txHash.substring(0, 16)}...
              </a>
            )}
          </div>
        ) as any,
      });

      setSelectedFile(null);
      setIsDialogOpen(false);
      setNewDoc({ type: "", name: user?.fullName || "" });
      await loadDocuments();
    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload document.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">My Dashboard</h1>
            <p className="text-slate-500">Manage your secure identity documents and tokens.</p>
          </div>

          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="flex items-center gap-2 h-11">
                <Plus className="w-5 h-5" />
                Add New Document
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Add New Document</DialogTitle>
                <DialogDescription>
                  Upload your document to generate a cryptographic hash and secure it on the blockchain.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddDocument} className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="docName">Full Name on Document</Label>
                  <Input
                    id="docName"
                    value={newDoc.name}
                    onChange={(e) => setNewDoc(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter full name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="docType">Document Type</Label>
                  <Select onValueChange={(val) => setNewDoc(prev => ({ ...prev, type: val }))} required>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="passport">Passport</SelectItem>
                      <SelectItem value="driver_license">Driver's License</SelectItem>
                      <SelectItem value="national_id">National ID</SelectItem>
                      <SelectItem value="id">Voter ID</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div
                  className={cn(
                    "p-8 border-2 border-dashed rounded-xl text-center space-y-4 transition-all duration-300",
                    isDragging ? "bg-primary/5 border-primary scale-[1.02] shadow-md" : "bg-slate-50 border-slate-200"
                  )}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className={cn(
                    "w-12 h-12 rounded-full mx-auto flex items-center justify-center transition-colors",
                    isDragging ? "bg-primary text-white" : "bg-slate-200 text-slate-400"
                  )}>
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-slate-900">
                      {isDragging ? "Drop your file now" : "Drag and drop file here"}
                    </p>
                    <p className="text-xs text-slate-500">
                      PDF, JPG or PNG up to 5MB
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileUpload(file);
                    }}
                  />
                  <Button
                    variant="outline"
                    type="button"
                    size="sm"
                    className="bg-white"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Browse Locally
                  </Button>
                </div>
                <DialogFooter>
                  <Button type="submit" className="w-full" disabled={isUploading}>
                    {isUploading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Hashing & Uploading...
                      </>
                    ) : "Secure on Blockchain"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Section - Documents */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-border shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xl font-bold">Verified Documents</CardTitle>
                <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                  <ShieldCheck className="w-3 h-3 mr-1" />
                  Blockchain Secured
                </Badge>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {documents.map((doc) => (
                    <div key={doc.id} className="p-6 flex items-center justify-between hover:bg-slate-50 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                          <FileText className="w-6 h-6" />
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{doc.type}</p>
                          <p className="text-sm text-slate-500 font-mono">Hash: {doc.hash}</p>
                        </div>
                      </div>
                      <div className="text-right flex flex-col items-end gap-2">
                        <Badge
                          className={cn(
                            "hover:bg-emerald-100 border-none",
                            doc.status === "Verified"
                              ? "bg-emerald-100 text-emerald-700"
                              : doc.status === "Pending"
                                ? "bg-amber-100 text-amber-700 hover:bg-amber-100"
                                : "bg-rose-100 text-rose-700 hover:bg-rose-100"
                          )}
                        >
                          {doc.status}
                        </Badge>
                        <p className="text-xs text-slate-400">Added on {doc.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
              <CardFooter className="bg-slate-50 p-4 justify-center">
                <Link to="/user/documents">
                  <Button variant="ghost" className="text-primary text-sm font-semibold">
                    View All Documents
                  </Button>
                </Link>
              </CardFooter>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Key className="w-5 h-5 text-primary" />
                    Token Generator
                  </CardTitle>
                  <CardDescription>
                    Create a secure verification token for third-party authentication.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-slate-900 rounded-lg text-center">
                    <p className="text-xs text-slate-500 uppercase font-bold mb-1">Generated Token</p>
                    <p className="text-3xl font-mono text-white tracking-widest">{generatedToken || "--------"}</p>
                  </div>
                  <Button
                    onClick={handleGenerateToken}
                    className="w-full h-11 bg-primary hover:bg-primary/90"
                    disabled={!!generatedToken}
                  >
                    < RefreshCw className="w-4 h-4 mr-2" />
                    {generatedToken ? "Token Active" : "Generate New Token"}
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Search className="w-5 h-5 text-primary" />
                    Token Validator
                  </CardTitle>
                  <CardDescription>
                    Validate a token to verify identity against blockchain records.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleValidateToken} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="token">Enter Token Code</Label>
                      <Input id="token" placeholder="E.G. AX39B2" className="h-11 font-mono uppercase" required />
                    </div>
                    <Button type="submit" variant="secondary" className="w-full h-11 border border-primary/20">
                      Validate Token
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Sidebar Section */}
          <div className="space-y-6">
            <Card className="border-primary/20 bg-primary/5 shadow-none overflow-hidden relative">
              <ShieldCheck className="w-32 h-32 text-primary/10 absolute -right-8 -top-8" />
              <CardHeader>
                <CardTitle className="text-lg font-bold">Identity Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1">
                  <p className="text-xs text-slate-500 font-bold uppercase">System Name</p>
                  <p className="text-lg font-bold">{user?.fullName || "Not set"}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-500 font-bold uppercase">Email Address</p>
                  <p className="text-sm font-medium text-slate-700">{user?.email || "Not set"}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-500 font-bold uppercase">Verified Documents</p>
                  <p className="text-lg font-bold">{documents.length} Documents</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-slate-500 font-bold uppercase">Last Verification</p>
                  <p className="text-sm font-medium">Today at 14:32</p>
                </div>
              </CardContent>
              <CardFooter className="pt-0">
                <Link to="/profile" className="w-full">
                  <Button variant="outline" className="w-full bg-white">View Full Profile</Button>
                </Link>
              </CardFooter>
            </Card>

            {validationResult && (
              <div className={`p-4 rounded-xl border animate-in zoom-in duration-300 ${validationResult.valid ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'}`}>
                <div className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${validationResult.valid ? 'bg-emerald-200' : 'bg-rose-200'}`}>
                    {validationResult.valid ? <CheckCircle2 className="w-4 h-4" /> : <LogOut className="w-4 h-4" />}
                  </div>
                  <div>
                    <p className="font-bold">{validationResult.valid ? "Verification Successful" : "Verification Failed"}</p>
                    <p className="text-sm mt-1">{validationResult.message}</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-4 w-full h-8 text-xs hover:bg-white/50"
                  onClick={() => setValidationResult(null)}
                >
                  Clear Result
                </Button>
              </div>
            )}

            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-md">Recent Activity</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="px-6 pb-6 space-y-4">
                  <div className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-primary mt-1.5 shrink-0" />
                    <div>
                      <p className="font-medium">Token created for Third-Party App</p>
                      <p className="text-slate-400 text-xs">2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    <div>
                      <p className="font-medium">Driver's License successfully hashed</p>
                      <p className="text-slate-400 text-xs">Yesterday</p>
                    </div>
                  </div>
                  <div className="flex gap-3 text-sm">
                    <div className="w-2 h-2 rounded-full bg-slate-200 mt-1.5 shrink-0" />
                    <div>
                      <p className="font-medium">Account created via Blockchain Node</p>
                      <p className="text-slate-400 text-xs">Feb 10, 2024</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
