import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error(
      "404 Error: User attempted to access non-existent route:",
      location.pathname,
    );
  }, [location.pathname]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="text-center space-y-6 max-w-md animate-in fade-in zoom-in duration-300">
        <div className="mx-auto w-20 h-20 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 mb-4">
          <ShieldAlert className="w-10 h-10" />
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">404 - Area Restricted</h1>
        <p className="text-lg text-slate-600">
          The requested identity record or secure area could not be located on our servers.
        </p>
        <Link to="/" className="block">
          <Button size="lg" className="w-full h-12 shadow-lg shadow-primary/20">
            Return to Secure Portal
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
