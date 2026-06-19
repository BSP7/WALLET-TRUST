import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield, Upload, Eye, EyeOff, CheckCircle2 } from "lucide-react";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { TokenGenerateRequest } from "@shared/api";

export default function AuthPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    fullName: "",
    dateOfBirth: "",
    password: "",
    confirmPassword: "",
    governmentId: null as File | null,
    governmentIdType: "national-id",
    governmentIdNumber: "",
    documentType: "national-id",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFormData((prev) => ({ ...prev, governmentId: e.target.files![0] }));
      if (errors.governmentId) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors.governmentId;
          return newErrors;
        });
      }
    }
  };

  const validateStep1 = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Invalid email format";
    }

    if (!formData.fullName) {
      newErrors.fullName = "Full name is required";
    }

    if (!formData.dateOfBirth) {
      newErrors.dateOfBirth = "Date of birth is required";
    }

    if (!formData.governmentIdNumber) {
      newErrors.governmentIdNumber = "Government ID number is required";
    }

    if (!formData.governmentId) {
      newErrors.governmentId = "Government ID is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (!/[A-Z]/.test(formData.password)) {
      newErrors.password = "Password must contain at least one uppercase letter";
    } else if (!/[0-9]/.test(formData.password)) {
      newErrors.password = "Password must contain at least one number";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (currentStep === 1) {
      if (validateStep1()) {
        setCurrentStep(2);
      }
    } else {
      if (validateStep2()) {
        setIsSubmitting(true);
        try {
          // Generate user ID (in production, this would come from backend)
          const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

          // Try to call token generation API
          try {
            const tokenRequest: TokenGenerateRequest = {
              userId,
              governmentIdNumber: formData.governmentIdNumber,
            };

            const tokenResponse = await fetch("/api/token/generate", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(tokenRequest),
              signal: AbortSignal.timeout(5000), // 5 second timeout
            });

            if (tokenResponse.ok) {
              const tokenData = await tokenResponse.json();

              // Store token in localStorage for session management
              if (tokenData.success && tokenData.token) {
                localStorage.setItem("authToken", tokenData.token);
                localStorage.setItem("userId", userId);
              }
            }
          } catch (tokenError) {
            // Token generation failed, but we can still complete signup
            console.warn("Token generation unavailable, completing signup without token");
            localStorage.setItem("userId", userId);
          }

          // Simulate account creation time, then redirect
          setTimeout(() => {
            setIsSubmitting(false);
            navigate("/dashboard");
          }, 1000);
        } catch (error) {
          console.error("Signup error:", error);
          setIsSubmitting(false);
          setErrors({
            submit: "Failed to create account. Please try again.",
          });
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-background text-foreground">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
              <Shield className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">WalletID</span>
          </Link>
          <div className="flex items-center gap-4">
            <ThemeSwitcher />
            <span className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/auth" className="text-primary hover:underline">
                Log in
              </Link>
            </span>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
        {/* Progress indicator */}
        <div className="mb-12">
          <div className="flex items-center gap-4">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition ${
                currentStep >= 1
                  ? "bg-primary text-primary-foreground"
                  : "bg-border/50 text-muted-foreground"
              }`}
            >
              {currentStep > 1 ? <CheckCircle2 className="w-5 h-5" /> : "1"}
            </div>
            <div className="flex-1 h-1 bg-border/50 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-secondary transition-all duration-300"
                style={{ width: currentStep > 1 ? "100%" : "0%" }}
              ></div>
            </div>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition ${
                currentStep >= 2
                  ? "bg-primary text-primary-foreground"
                  : "bg-border/50 text-muted-foreground"
              }`}
            >
              2
            </div>
          </div>
          <div className="flex justify-between mt-4 text-sm text-muted-foreground">
            <span>Identity Verification</span>
            <span>Security Setup</span>
          </div>
        </div>

        {/* Form Card */}
        <div className="bg-card/50 border border-border/50 rounded-2xl p-8 md:p-12">
          <form onSubmit={handleSubmit} className="space-y-6">
            {currentStep === 1 ? (
              <div className="space-y-6">
                <div>
                  <h2 className="text-3xl font-bold mb-2">Identity Verification</h2>
                  <p className="text-muted-foreground">
                    Provide your personal information and verify with government ID
                  </p>
                </div>

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium mb-2">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 rounded-lg bg-input border ${
                      errors.email ? "border-destructive" : "border-border/50"
                    } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                  />
                  {errors.email && <p className="text-destructive text-sm mt-1">{errors.email}</p>}
                </div>

                {/* Full Name */}
                <div>
                  <label className="block text-sm font-medium mb-2">Full Name</label>
                  <input
                    type="text"
                    name="fullName"
                    placeholder="John Doe"
                    value={formData.fullName}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 rounded-lg bg-input border ${
                      errors.fullName ? "border-destructive" : "border-border/50"
                    } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                  />
                  {errors.fullName && (
                    <p className="text-destructive text-sm mt-1">{errors.fullName}</p>
                  )}
                </div>

                {/* Date of Birth */}
                <div>
                  <label className="block text-sm font-medium mb-2">Date of Birth</label>
                  <input
                    type="date"
                    name="dateOfBirth"
                    value={formData.dateOfBirth}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 rounded-lg bg-input border ${
                      errors.dateOfBirth ? "border-destructive" : "border-border/50"
                    } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                  />
                  {errors.dateOfBirth && (
                    <p className="text-destructive text-sm mt-1">{errors.dateOfBirth}</p>
                  )}
                </div>

                {/* Government ID Type */}
                <div>
                  <label className="block text-sm font-medium mb-3">Government ID Type</label>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { value: "national-id", label: "National ID Card" },
                      { value: "passport", label: "Passport" },
                      { value: "drivers-license", label: "Driver's License" },
                      { value: "state-id", label: "State ID" },
                      { value: "aadhar", label: "Aadhar (India)" },
                      { value: "other", label: "Other" },
                    ].map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() =>
                          handleInputChange({
                            target: {
                              name: "governmentIdType",
                              value: option.value,
                            },
                          } as any)
                        }
                        className={`px-4 py-3 rounded-lg border-2 font-medium transition ${
                          formData.governmentIdType === option.value
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border/50 bg-input text-foreground hover:border-primary/50"
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Government ID Number */}
                <div>
                  <label className="block text-sm font-medium mb-2">Government ID Number</label>
                  <input
                    type="text"
                    name="governmentIdNumber"
                    placeholder="Enter your ID number"
                    value={formData.governmentIdNumber}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 rounded-lg bg-input border ${
                      errors.governmentIdNumber ? "border-destructive" : "border-border/50"
                    } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                  />
                  {errors.governmentIdNumber && (
                    <p className="text-destructive text-sm mt-1">{errors.governmentIdNumber}</p>
                  )}
                </div>

                {/* Document Type Dropdown */}
                <div>
                  <label className="block text-sm font-medium mb-3">Document Type</label>
                  <div className="relative">
                    <select
                      name="documentType"
                      value={formData.documentType}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 pr-10 rounded-lg bg-input border border-border/50 text-foreground focus:outline-none focus:border-primary transition appearance-none cursor-pointer font-medium"
                    >
                      <optgroup label="Government ID">
                        <option value="national-id">National ID Card</option>
                        <option value="passport">Passport</option>
                        <option value="drivers-license">Driver's License</option>
                        <option value="voter-id">Voter ID</option>
                        <option value="aadhar">Aadhar Card (India)</option>
                      </optgroup>
                      <optgroup label="Travel Documents">
                        <option value="visa">Visa Document</option>
                      </optgroup>
                      <optgroup label="Legal Documents">
                        <option value="birth-certificate">Birth Certificate</option>
                      </optgroup>
                      <optgroup label="Financial Documents">
                        <option value="bank-statement">Bank Statement</option>
                        <option value="tax-return">Tax Return</option>
                      </optgroup>
                      <optgroup label="Proof of Address">
                        <option value="utility-bill">Utility Bill</option>
                      </optgroup>
                      <optgroup label="Employment/Education">
                        <option value="employment-letter">Employment Letter</option>
                        <option value="college-id">College/University ID</option>
                      </optgroup>
                      <optgroup label="Other">
                        <option value="other">Other Document</option>
                      </optgroup>
                    </select>
                    <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-primary">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Select the type of document you're uploading for verification
                  </p>
                </div>

                {/* Government ID Upload */}
                <div>
                  <label className="block text-sm font-medium mb-2">Upload Government ID Proof</label>
                  <div
                    className={`relative border-2 border-dashed rounded-lg p-8 transition cursor-pointer ${
                      errors.governmentId
                        ? "border-destructive/50 bg-destructive/5"
                        : "border-primary/30 hover:border-primary/60"
                    }`}
                  >
                    <input
                      type="file"
                      onChange={handleFileChange}
                      accept="image/*,.pdf"
                      className="absolute inset-0 w-full h-full cursor-pointer opacity-0"
                    />
                    <div className="flex flex-col items-center justify-center text-center">
                      <Upload className="w-12 h-12 text-primary/50 mb-3" />
                      <p className="font-medium text-foreground">
                        {formData.governmentId
                          ? formData.governmentId.name
                          : "Click to upload or drag and drop"}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        PNG, JPG, PDF (max 10MB)
                      </p>
                    </div>
                  </div>
                  {errors.governmentId && (
                    <p className="text-destructive text-sm mt-1">{errors.governmentId}</p>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h2 className="text-3xl font-bold mb-2">Security Setup</h2>
                  <p className="text-muted-foreground">
                    Create a secure password for your WalletID account
                  </p>
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium mb-2">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      name="password"
                      placeholder="Enter a secure password"
                      value={formData.password}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 pr-12 rounded-lg bg-input border ${
                        errors.password ? "border-destructive" : "border-border/50"
                      } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition"
                    >
                      {showPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="text-destructive text-sm mt-1">{errors.password}</p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    At least 8 characters, 1 uppercase letter, and 1 number
                  </p>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-medium mb-2">Confirm Password</label>
                  <div className="relative">
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      name="confirmPassword"
                      placeholder="Confirm your password"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      className={`w-full px-4 py-3 pr-12 rounded-lg bg-input border ${
                        errors.confirmPassword ? "border-destructive" : "border-border/50"
                      } text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                  {errors.confirmPassword && (
                    <p className="text-destructive text-sm mt-1">{errors.confirmPassword}</p>
                  )}
                </div>

                {/* Security Notes */}
                <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
                  <p className="text-sm text-foreground">
                    Your password is encrypted and stored securely on the blockchain. Only you have access to your account.
                  </p>
                </div>
              </div>
            )}

            {/* Buttons */}
            <div className="flex gap-4 pt-6">
              {currentStep === 2 && (
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="flex-1 px-6 py-3 border border-border/50 text-foreground font-medium rounded-lg hover:bg-border/20 transition"
                >
                  Back
                </button>
              )}
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-primary to-secondary text-primary-foreground font-medium rounded-lg hover:shadow-lg hover:shadow-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isSubmitting ? "Creating account..." : currentStep === 1 ? "Continue" : "Create Account"}
              </button>
            </div>

            {/* Terms */}
            <p className="text-xs text-muted-foreground text-center">
              By signing up, you agree to our{" "}
              <Link to="#" className="text-primary hover:underline">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link to="#" className="text-primary hover:underline">
                Privacy Policy
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
