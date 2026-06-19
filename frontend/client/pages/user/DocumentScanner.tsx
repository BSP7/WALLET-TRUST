import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  Camera,
  ChevronLeft,
  Loader2,
  CheckCircle2,
  Scan,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import Navbar from "@/components/Navbar";

export default function DocumentScanner() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("");
  const [fullName, setFullName] = useState(user?.fullName || "");
  const [useAI, setUseAI] = useState(false);

  /* ------------------ File Handling ------------------ */

  const validateFile = (file: File) => {
    if (!file.type.startsWith("image/") && file.type !== "application/pdf") {
      toast({
        title: "Invalid File Type",
        description: "Please upload JPG, PNG or PDF file.",
        variant: "destructive",
      });
      return false;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "File Too Large",
        description: "File size must be less than 5MB.",
        variant: "destructive",
      });
      return false;
    }

    return true;
  };

  const handleFileSelect = (file: File | undefined | null) => {
    if (!file) return;
    if (!validateFile(file)) return;
    setSelectedFile(file);

    toast({
      title: "File Selected",
      description: `"${file.name}" is ready for upload.`,
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  /* ------------------ Upload Handler ------------------ */

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      toast({
        title: "No File Selected",
        description: "Please select a document.",
        variant: "destructive",
      });
      return;
    }

    if (!documentType) {
      toast({
        title: "Missing Document Type",
        description: "Please select a document type.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append("title", fullName || "Document");
      formData.append("doc_type", documentType);
      formData.append("file", selectedFile);
      formData.append("useAI", String(useAI));

      const authToken = localStorage.getItem("access_token");

      const response = await fetch("/api/documents/upload", {
        method: "POST",
        headers: {
          ...(authToken && { Authorization: `Bearer ${authToken}` }),
        },
        body: formData,
      });

      setUploadProgress(100);

      if (!response.ok) {
        let errorMessage = "Upload failed";

        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch {
          const text = await response.text();
          if (text) errorMessage = text;
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      const txHash = data.blockchain?.transaction_hash;

      toast({
        title: "Upload Successful",
        description: (
          <div className="space-y-2">
            <p>Document securely hashed and added to blockchain.</p>
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

      // Reset state
      setSelectedFile(null);
      setDocumentType("");
      setUploadProgress(0);

      navigate("/user/documents");
    } catch (error) {
      console.error("Upload error:", error);

      toast({
        title: "Upload Failed",
        description:
          error instanceof Error
            ? error.message
            : "Something went wrong. Try again.",
        variant: "destructive",
      });

      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  /* ------------------ UI ------------------ */

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-3xl mx-auto space-y-6">

          <Link
            to="/user/documents"
            className="inline-flex items-center text-sm text-slate-500 hover:text-primary"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back to My Documents
          </Link>

          <Card>
            <CardHeader>
              <CardTitle>Upload Identity Document</CardTitle>
              <CardDescription>
                Securely hash and store your document on blockchain.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">

                <div>
                  <Label>Full Name</Label>
                  <Input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>

                <div>
                  <Label>Document Type</Label>
                  <Select value={documentType} onValueChange={setDocumentType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select document type" />
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
                    "p-8 border-2 border-dashed rounded-xl text-center",
                    isDragging
                      ? "border-primary bg-primary/5"
                      : selectedFile
                        ? "border-green-400 bg-green-50"
                        : "border-slate-200"
                  )}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                >
                  {selectedFile ? (
                    <>
                      <CheckCircle2 className="mx-auto text-green-600 w-8 h-8" />
                      <p className="font-semibold mt-2">{selectedFile.name}</p>
                    </>
                  ) : (
                    <>
                      <FileText className="mx-auto w-8 h-8 text-slate-400" />
                      <p className="mt-2">Drag & Drop file here</p>
                    </>
                  )}

                  <div className="mt-4 flex justify-center gap-2">
                    <Button variant="outline" size="sm" type="button" className="relative overflow-hidden">
                      <Upload className="w-4 h-4 mr-2" />
                      Browse
                      <input
                        type="file"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept="image/*,application/pdf"
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            handleFileSelect(e.target.files[0]);
                          }
                        }}
                      />
                    </Button>

                    <Button variant="outline" size="sm" type="button" className="relative overflow-hidden">
                      <Camera className="w-4 h-4 mr-2" />
                      Take Photo
                      <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            handleFileSelect(e.target.files[0]);
                          }
                        }}
                      />
                    </Button>
                  </div>
                </div>

                <div className="flex items-center justify-between bg-blue-50 p-4 rounded-xl">
                  <span className="text-sm font-medium">
                    AI Document Extraction
                  </span>
                  <input
                    type="checkbox"
                    checked={useAI}
                    onChange={(e) => setUseAI(e.target.checked)}
                  />
                </div>

                {isUploading && (
                  <div className="text-sm text-primary">
                    Processing... {uploadProgress}%
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="w-full"
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="animate-spin mr-2" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2" />
                      Upload & Secure
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
}