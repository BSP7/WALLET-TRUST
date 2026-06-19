import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Key,
  Copy,
  ChevronLeft,
  Shield,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";

export default function TokenGenerator() {
  const { user } = useAuth();

  const [txHash, setTxHash] = useState("");
  const [etherscanUrl, setEtherscanUrl] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [hasExistingToken, setHasExistingToken] = useState(false);

  /* ---------------- Check Existing Token ---------------- */

  useEffect(() => {
    if (user) {
      checkExistingToken();
    }
  }, [user]);

  const checkExistingToken = async () => {
    try {
      const accessToken = localStorage.getItem("access_token");
      if (!accessToken) return;

      const response = await fetch("/api/users/tokens", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) return;

      const data = await response.json();

      if (data?.tokens?.length > 0) {
        const existingToken = data.tokens[0];

        setHasExistingToken(true);
        setTxHash(existingToken.tx_hash || "");

        if (existingToken.tx_hash) {
          setEtherscanUrl(
            `https://sepolia.etherscan.io/tx/${existingToken.tx_hash}`
          );
        }
      }
    } catch (error) {
      console.error("Error checking existing token:", error);
    }
  };

  /* ---------------- Generate Token ---------------- */

  const handleGenerateToken = async () => {
    if (hasExistingToken) {
      toast({
        title: "Token Already Exists",
        description: "Only one active token per account is allowed.",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);

    try {
      const accessToken = localStorage.getItem("access_token");

      if (!accessToken || !user?.userId) {
        toast({
          title: "Authentication Required",
          description: "Please log in again.",
          variant: "destructive",
        });
        return;
      }

      const governmentIdNumber = localStorage.getItem("government_id_number");

      const response = await fetch("/api/blockchain/token/generate", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: user.userId,
          government_id_number: governmentIdNumber || undefined,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Token generation failed";

        try {
          const errorData = await response.json();
          errorMessage = errorData.revert_reason || errorData.details || errorData.error || errorMessage;
        } catch {
          const text = await response.text();
          if (text) errorMessage = text;
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      setTxHash(data.tx_hash);
      setEtherscanUrl(
        data.etherscan_url ||
          `https://sepolia.etherscan.io/tx/${data.tx_hash}`
      );
      setHasExistingToken(true);

      toast({
        title: "Token Generated Successfully",
        description: "Your blockchain verification token is now live.",
      });
    } catch (error) {
      console.error("Token generation error:", error);

      toast({
        title: "Generation Failed",
        description:
          error instanceof Error
            ? error.message
            : "Something went wrong.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  /* ---------------- Copy Hash ---------------- */

  const copyToken = async () => {
    try {
      await navigator.clipboard.writeText(txHash);

      toast({
        title: "Copied",
        description: "Transaction hash copied to clipboard.",
      });
    } catch {
      toast({
        title: "Copy Failed",
        description: "Unable to copy hash.",
        variant: "destructive",
      });
    }
  };

  /* ---------------- UI ---------------- */

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="flex-1 container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-2xl mx-auto space-y-6">

          <Link
            to="/user/tokens"
            className="inline-flex items-center text-sm text-slate-500 hover:text-primary"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Back to My Tokens
          </Link>

          <Card>
            <CardHeader>
              <CardTitle>Generate Verification Token</CardTitle>
              <CardDescription>
                Create a blockchain-based identity verification token.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">

              <div className="space-y-2">
                <Label>Blockchain Transaction Hash</Label>

                <div className="p-6 bg-slate-900 rounded-xl text-center">
                  <p className="text-sm text-slate-400 break-all font-mono">
                    {txHash || "--------"}
                  </p>

                  {etherscanUrl && (
                    <a
                      href={etherscanUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 mt-3 text-blue-400 hover:text-blue-300 text-sm"
                    >
                      <ExternalLink className="w-4 h-4" />
                      View on Etherscan
                    </a>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={handleGenerateToken}
                  disabled={isGenerating || hasExistingToken}
                  className="flex-1 h-12"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="animate-spin w-4 h-4 mr-2" />
                      Generating...
                    </>
                  ) : hasExistingToken ? (
                    "Token Already Generated"
                  ) : (
                    <>
                      <Key className="w-4 h-4 mr-2" />
                      Generate Blockchain Token
                    </>
                  )}
                </Button>

                {txHash && (
                  <Button
                    onClick={copyToken}
                    className="h-12 px-6 bg-slate-200 text-slate-900 hover:bg-slate-300"
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    Copy
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary/5 border-primary/20 shadow-none">
            <CardContent className="pt-6">
              <div className="flex gap-4">
                <Shield className="w-6 h-6 text-primary shrink-0 mt-1" />
                <div>
                  <h3 className="font-bold">How It Works</h3>
                  <ul className="text-sm space-y-1 mt-2">
                    <li>• Token is recorded on the blockchain</li>
                    <li>• Linked to your verified identity documents</li>
                    <li>• Can be shared for third-party verification</li>
                    <li>• Immutable and tamper-proof</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
}