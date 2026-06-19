import "./global.css";

import { Toaster } from "@/components/ui/toaster";
import { createRoot } from "react-dom/client";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";

// Public Pages
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

// User Pages
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Dashboard from "./pages/Dashboard";
import ProfilePage from "./pages/Profile";
import MyTokens from "./pages/user/MyTokens";
import TokenGenerator from "./pages/user/TokenGenerator";
import MyDocuments from "./pages/user/MyDocuments";
import DocumentScanner from "./pages/user/DocumentScanner";

// Company Pages
import CompanyRegister from "./pages/company/CompanyRegister";
import CompanyLogin from "./pages/company/CompanyLogin";
import CompanyDashboard from "./pages/company/CompanyDashboard";
import ValidationHistory from "./pages/company/ValidationHistory";

// Admin Pages
import AdminLogin from "./pages/admin/AdminLogin";
import SystemMonitor from "./pages/admin/SystemMonitor";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Index />} />
            
            {/* User Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/user/tokens" element={<MyTokens />} />
            <Route path="/user/tokens/generate" element={<TokenGenerator />} />
            <Route path="/user/documents" element={<MyDocuments />} />
            <Route path="/user/documents/scan" element={<DocumentScanner />} />

            {/* Company Routes */}
            <Route path="/company/register" element={<CompanyRegister />} />
            <Route path="/company/login" element={<CompanyLogin />} />
            <Route path="/company/dashboard" element={<CompanyDashboard />} />
            <Route path="/company/validations" element={<ValidationHistory />} />

            {/* Admin Routes */}
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin/monitor" element={<SystemMonitor />} />

            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

createRoot(document.getElementById("root")!).render(<App />);
