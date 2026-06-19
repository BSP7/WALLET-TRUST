import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { User, ShieldCheck, Mail, Calendar, CreditCard, ChevronLeft, Lock, Camera, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
  const { user: currentUser } = useAuth();
  const [isDragging, setIsDragging] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const [profile, setProfile] = useState<{
    name: string;
    email: string;
    dob?: string | null;
    createdAt?: number;
    verifiedHash?: string;
    documentType?: string;
  } | null>(null);

  useEffect(() => {
    const load = async () => {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) {
        setProfile(null);
        return;
      }

      const response = await fetch("/api/users/profile", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        setProfile(null);
        return;
      }

      const data = await response.json();
      setProfile({
        name: data?.name ?? "",
        email: data?.email ?? "",
        dob: data?.dob ?? null,
        createdAt: data?.created_at,
        verifiedHash: data?.tokens && data.tokens.length > 0 ? data.tokens[data.tokens.length - 1] : undefined,
      });
    };

    load().catch(() => setProfile(null));
  }, [currentUser?.userId]);

  const user = {
    name: profile?.name || currentUser?.fullName || "",
    email: profile?.email || currentUser?.email || "",
    dob: profile?.dob || "",
    documentType: profile?.documentType || "",
    verifiedHash: profile?.verifiedHash || "",
    joinedDate: profile?.createdAt
      ? new Date(profile.createdAt * 1000).toISOString().split("T")[0]
      : "",
  };

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
    if (!file.type.startsWith('image/')) {
      toast({
        title: "Invalid File Type",
        description: "Please upload an image for your profile picture.",
        variant: "destructive",
      });
      return;
    }

    setIsUpdating(true);

    // Simulate upload and blockchain verification
    setTimeout(() => {
      setIsUpdating(false);
      toast({
        title: "Profile Updated",
        description: "Your new profile image has been hashed and secured on the blockchain.",
      });
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between">
            <Link to="/dashboard" className="inline-flex items-center text-sm text-slate-500 hover:text-primary transition-colors">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Back to Dashboard
            </Link>
            <Button
              variant="outline"
              className="text-destructive border-destructive hover:bg-destructive/5"
              onClick={() => toast({ title: "Profile Deletion Requested", description: "A request to remove your decentralized ID has been submitted. This takes 24h to propagate.", variant: "destructive" })}
            >
              Delete Secure Profile
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Profile Sidebar */}
            <div className="md:col-span-1 space-y-6">
              <Card className="text-center overflow-hidden border-border shadow-sm">
                <div className="h-24 bg-gradient-to-r from-primary/20 to-accent/20" />
                <CardContent className="relative px-6 pb-6">
                  <div
                    className={cn(
                      "w-24 h-24 rounded-full bg-white p-1 shadow-lg mx-auto -mt-12 mb-4 border transition-all duration-300 relative group",
                      isDragging ? "border-primary scale-110" : "border-slate-100"
                    )}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <div className={cn(
                      "w-full h-full rounded-full flex items-center justify-center transition-colors overflow-hidden",
                      isDragging ? "bg-primary/20" : "bg-primary/10"
                    )}>
                      {isUpdating ? (
                        <Loader2 className="w-8 h-8 text-primary animate-spin" />
                      ) : (
                        <User className="w-12 h-12 text-primary" />
                      )}

                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity rounded-full cursor-pointer">
                        <Camera className="w-6 h-6 text-white" />
                      </div>
                    </div>
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">{user.name || "Not set"}</h2>
                  <p className="text-sm text-slate-500 mb-4">{user.email || "Not set"}</p>
                  <Badge className="bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
                    Verified Holder
                  </Badge>
                  <div className="mt-8 pt-8 border-t border-slate-100 grid grid-cols-2 gap-4 text-center">
                    <div>
                      <p className="text-xl font-bold text-slate-900">0</p>
                      <p className="text-xs text-slate-500 uppercase font-bold tracking-tight">Docs</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold text-slate-900">0</p>
                      <p className="text-xs text-slate-500 uppercase font-bold tracking-tight">Verifications</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-md">Blockchain Proof</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Root Identity Hash</p>
                    <div className="p-3 bg-slate-900 rounded-lg">
                      <p className="text-[10px] font-mono text-primary break-all leading-relaxed">
                        {user.verifiedHash || "No hash available"}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" className="w-full h-9 text-xs flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4" />
                    View on Explorer
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Profile Details */}
            <div className="md:col-span-2 space-y-6">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>
                    These details are derived from your blockchain-verified documents.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <User className="w-4 h-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Full Legal Name</p>
                      </div>
                      <p className="text-lg font-medium text-slate-900">{user.name || "Not set"}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <Calendar className="w-4 h-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Date of Birth</p>
                      </div>
                      <p className="text-lg font-medium text-slate-900">{user.dob || "Not set"}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <CreditCard className="w-4 h-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Primary Document</p>
                      </div>
                      <p className="text-lg font-medium text-slate-900">{user.documentType || "Not set"}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <Mail className="w-4 h-4" />
                        <p className="text-xs font-bold uppercase tracking-wider">Email Contact</p>
                      </div>
                      <p className="text-lg font-medium text-slate-900">{user.email || "Not set"}</p>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="bg-slate-50 border-t border-slate-100 flex justify-between items-center px-6 py-4">
                  <p className="text-xs text-slate-500">Member since {user.joinedDate || "Not available"}</p>
                  <Button size="sm" onClick={() => toast({ title: "Edit Mode", description: "You can now edit your profile fields." })}>Edit Details</Button>
                </CardFooter>
              </Card>

              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle>Security Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-slate-100 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                        <ShieldCheck className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900">Two-Factor Authentication</p>
                        <p className="text-xs text-slate-500">Enabled - Protecting your private key</p>
                      </div>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100 border-none">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between p-4 border border-slate-100 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center text-amber-600">
                        <Lock className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900">Private Key Recovery</p>
                        <p className="text-xs text-slate-500">Setup recovery phrase and delegates</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" className="text-primary hover:text-primary hover:bg-primary/5">Configure</Button>
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
