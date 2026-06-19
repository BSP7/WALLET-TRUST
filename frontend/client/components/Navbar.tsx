import { Link, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, User, LogOut, LayoutDashboard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/context/AuthContext";

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isLoggedIn = !!user;

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged Out",
      description: "You have been securely logged out of your identity profile.",
    });
    navigate("/");
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-border shadow-sm">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to={isLoggedIn ? "/dashboard" : "/"} className="flex items-center gap-2">
          <ShieldCheck className="w-8 h-8 text-primary" />
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            WalletID
          </span>
        </Link>
        <div className="flex items-center gap-4">
          {!isLoggedIn && (
            <>
              <Link to="/#about">
                <Button variant="ghost" className="hidden md:flex">About</Button>
              </Link>
              <Link to="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link to="/signup">
                <Button>Get Started</Button>
              </Link>
            </>
          )}

          {isLoggedIn && (
            <>
              <Link to="/dashboard" className="hidden md:flex">
                <Button variant="ghost" className="flex items-center gap-2">
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Button>
              </Link>
              <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100">
                <User className="w-4 h-4 text-slate-600" />
                <span className="text-sm font-medium text-slate-700">{user?.fullName}</span>
              </div>
              <Link to="/profile">
                <Button variant="outline" size="icon" className="rounded-full">
                  <User className="w-5 h-5" />
                </Button>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-500 hover:text-destructive transition-colors"
                onClick={handleLogout}
              >
                <LogOut className="w-5 h-5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
