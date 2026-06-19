import { ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-8 h-8 text-primary" />
              <span className="font-bold text-xl">WalletID</span>
            </div>
            <p className="text-slate-400 max-w-sm">
              Securing identities through decentralized blockchain technology. 
              Reducing identity theft and increasing trust in digital verification.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-lg mb-4">Quick Links</h4>
            <ul className="space-y-2 text-slate-400">
              <li><a href="/" className="hover:text-primary transition-colors">Home</a></li>
              <li><a href="/login" className="hover:text-primary transition-colors">Login</a></li>
              <li><a href="/signup" className="hover:text-primary transition-colors">Sign Up</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-lg mb-4">Technology</h4>
            <ul className="space-y-2 text-slate-400">
              <li>Blockchain Hashing</li>
              <li>Decentralized Ledgers</li>
              <li>Immutable Authentication</li>
              <li>Cryptographic Verification</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-800 pt-8 flex flex-col md:row items-center justify-between gap-4 text-slate-500 text-sm">
          <p>© 2024 WalletID Blockchain Authentication System. All rights reserved.</p>
          <div className="flex gap-8">
            <a href="#" className="hover:text-white">Privacy Policy</a>
            <a href="#" className="hover:text-white">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
