import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { ShieldCheck, Lock, Fingerprint, Database, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function Index() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      
      <main className="flex-1 pt-16">
        {/* Hero Section */}
        <section className="relative py-20 md:py-32 overflow-hidden bg-slate-50">
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-sm font-medium text-primary mb-4">
                <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse" />
                Next Generation ID Authentication
              </div>
              <h1 className="text-4xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
                Blockchain-Based <br />
                <span className="text-primary">Identity Authentication</span>
              </h1>
              <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
                Secure, tamper-proof identity verification platform using blockchain technology.
                No personal data stored centrally—only cryptographic hashes.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Link to="/signup" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto h-12 px-8 text-base shadow-lg shadow-primary/20">
                    Get Started Now
                  </Button>
                </Link>
                <Link to="/login" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto h-12 px-8 text-base border-primary/20 hover:bg-primary/5">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </div>
          {/* Background Decorative Element */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-3xl pointer-events-none -z-10" />
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 bg-white">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
              <div className="space-y-4 p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary mb-6">
                  <Lock className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Cryptographic Hashing</h3>
                <p className="text-slate-600 leading-relaxed">
                  We store a cryptographic hash of your identity data instead of the data itself, ensuring privacy and security.
                </p>
              </div>
              <div className="space-y-4 p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary mb-6">
                  <Database className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Immutable Blockchain</h3>
                <p className="text-slate-600 leading-relaxed">
                  Decentralized storage means records cannot be altered or forged once they are committed to the blockchain.
                </p>
              </div>
              <div className="space-y-4 p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary mb-6">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Instant Verification</h3>
                <p className="text-slate-600 leading-relaxed">
                  Verify authenticity by checking stored hash values, making duplication or manipulation virtually impossible.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Why it Matters Section */}
        <section id="about" className="py-24 bg-slate-900 text-white overflow-hidden relative">
          <div className="container mx-auto px-4 relative z-10">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div className="space-y-8">
                <h2 className="text-3xl md:text-5xl font-bold leading-tight">
                  Addressing the Growing Threat of <span className="text-primary">Identity Theft</span>
                </h2>
                <div className="space-y-6">
                  {[
                    "Zero central database vulnerability",
                    "Complete user control over personal data",
                    "Tamper-proof identity records",
                    "Trust through mathematical certainty"
                  ].map((item, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0 mt-1">
                        <CheckCircle2 className="w-4 h-4 text-primary" />
                      </div>
                      <p className="text-lg text-slate-300">{item}</p>
                    </div>
                  ))}
                </div>
                <Link to="/signup">
                  <Button className="mt-8 h-12 px-8 text-base">Secure Your ID Now</Button>
                </Link>
              </div>
              <div className="relative">
                <div className="w-full aspect-square max-w-md mx-auto bg-primary/20 rounded-full blur-[100px] absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
                <div className="relative bg-slate-800 p-8 rounded-3xl border border-slate-700 shadow-2xl overflow-hidden group">
                   <ShieldCheck className="w-64 h-64 text-primary/20 absolute -right-16 -bottom-16 rotate-12 group-hover:rotate-0 transition-transform duration-700" />
                   <div className="relative space-y-4">
                     <div className="flex items-center gap-3 p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                       <Fingerprint className="w-8 h-8 text-primary" />
                       <div>
                         <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Identity Status</p>
                         <p className="text-lg font-mono">ENCRYPTED & HASHED</p>
                       </div>
                     </div>
                     <div className="space-y-2">
                       <p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Blockchain Transaction Hash</p>
                       <p className="text-xs font-mono break-all text-primary">0x4a9b2c3d8e7f1a6b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7</p>
                     </div>
                     <div className="pt-4 border-t border-slate-700">
                       <p className="text-sm text-slate-400 italic">"Verified identity is stored as an immutable proof of authenticity."</p>
                     </div>
                   </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-24 bg-primary text-white text-center">
          <div className="container mx-auto px-4 max-w-3xl space-y-8">
            <h2 className="text-3xl md:text-5xl font-bold">Ready to build a safer future?</h2>
            <p className="text-xl text-primary-foreground/80">
              Join thousands of users who trust our blockchain identity verification system for a more reliable digital identity.
            </p>
            <div className="pt-4">
              <Link to="/signup">
                <Button size="lg" variant="secondary" className="h-14 px-10 text-lg shadow-xl">
                  Get Started for Free
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
