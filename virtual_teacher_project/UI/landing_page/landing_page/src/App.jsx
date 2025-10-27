import React, { useMemo, useRef, useState } from "react";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import {
  DocumentTextIcon,
  PencilSquareIcon,
  SparklesIcon,
} from "@heroicons/react/24/solid";
import classNames from "classnames";
import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";

// Import logo for watermark

// API Configuration - Use API Gateway instead of direct service calls
const API_BASE_URL = "http://localhost:8000";

// API functions
const apiCall = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      credentials: "include", // Include cookies for session management
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    let data;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = { message: await response.text() };
    }

    if (!response.ok) {
      // Handle various error response formats from Django/DRF
      let errorMessage = "An error occurred";

      if (data.error) {
        errorMessage = data.error;
      } else if (data.detail) {
        errorMessage = data.detail;
      } else if (data.password) {
        // Handle password validation errors specifically
        errorMessage = Array.isArray(data.password)
          ? data.password.join(" ")
          : data.password;
      } else if (data.email) {
        // Handle email validation errors
        errorMessage = Array.isArray(data.email)
          ? data.email.join(" ")
          : data.email;
      } else if (data.username) {
        // Handle username validation errors
        errorMessage = Array.isArray(data.username)
          ? data.username.join(" ")
          : data.username;
      } else if (data.non_field_errors) {
        errorMessage = Array.isArray(data.non_field_errors)
          ? data.non_field_errors[0]
          : data.non_field_errors;
      } else if (typeof data === "object" && Object.keys(data).length > 0) {
        // Extract all field errors and combine them
        const errors = Object.entries(data)
          .map(([field, msgs]) => {
            const messages = Array.isArray(msgs) ? msgs.join(" ") : msgs;
            return `${field}: ${messages}`;
          })
          .join("; ");
        errorMessage = errors || "Validation error occurred";
      } else if (typeof data === "string") {
        errorMessage = data;
      }

      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error("API call failed:", error);
    throw error;
  }
};

const authAPI = {
  login: (email, password) =>
    apiCall("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  signup: (full_name, email, password, password_confirm, username) =>
    apiCall("/api/auth/signup/", {
      method: "POST",
      body: JSON.stringify({
        full_name,
        email,
        password,
        password_confirm,
        username: username || email.split("@")[0], // Generate username from email if not provided
        terms_accepted: true, // Auto-accept for now, can add checkbox later
      }),
    }),

  forgotPassword: (email) =>
    apiCall("/api/auth/forgot-password/", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  logout: () =>
    apiCall("/api/auth/logout/", {
      method: "POST",
    }),
};

// Google OAuth handler
const handleGoogleSuccess = async (credentialResponse) => {
  try {
    console.log("🔐 Google Login - Credential received");
    console.log("📤 Sending to backend:", {
      token: credentialResponse.credential ? "✓ Present" : "✗ Missing",
    });

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/google/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: credentialResponse.credential, // Backend expects 'token', not 'access_token'
      }),
    });

    console.log("📥 Backend response status:", response.status);
    const data = await response.json();
    console.log("📥 Backend response data:", data);

    if (response.ok) {
      // Save tokens
      const accessToken = data.tokens.access;
      const refreshToken = data.tokens.refresh;

      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      localStorage.setItem("gnyansetu_auth_token", accessToken);
      localStorage.setItem("user", JSON.stringify(data.user));

      // Save user data for dashboard
      const userId = data.user?.id || data.user?._id;
      const userEmail = data.user?.email;
      const userName = data.user?.full_name || data.user?.name;

      if (userId) {
        sessionStorage.setItem("userId", userId);
        localStorage.setItem("userId", userId);
      }

      if (userEmail) {
        sessionStorage.setItem("userEmail", userEmail);
        localStorage.setItem("userEmail", userEmail);
      }

      if (userName) {
        sessionStorage.setItem("userName", userName);
        localStorage.setItem("userName", userName);
      }

      console.log("✅ Google login - User data stored:", {
        userId,
        userEmail,
        userName,
      });

      // Redirect to dashboard with data in URL hash
      const dashboardUrl =
        `http://localhost:3001/#login?` +
        `userId=${encodeURIComponent(userId)}&` +
        `userEmail=${encodeURIComponent(userEmail)}&` +
        `userName=${encodeURIComponent(userName)}&` +
        `accessToken=${encodeURIComponent(accessToken)}&` +
        `refreshToken=${encodeURIComponent(refreshToken)}&` +
        `user=${encodeURIComponent(JSON.stringify(data.user))}`;

      window.location.href = dashboardUrl;
    } else {
      console.error("Google login failed:", data);
      alert(data.error || "Google login failed. Please try again.");
    }
  } catch (error) {
    console.error("Error during Google login:", error);
    alert("An error occurred during Google login. Please try again.");
  }
};

const handleGoogleError = () => {
  console.log("Google Login Failed");
  alert("Google login was cancelled or failed. Please try again.");
};

function useLockBodyScroll(locked) {
  React.useEffect(() => {
    if (!locked) return;

    const originalStyle = window.getComputedStyle(document.body).overflow;
    const originalPaddingRight = document.body.style.paddingRight;

    // Calculate scrollbar width
    const scrollBarWidth =
      window.innerWidth - document.documentElement.clientWidth;

    // Apply styles to prevent layout shift
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${scrollBarWidth}px`;

    // Also apply to fixed positioned elements (like navbar)
    const fixedElements = document.querySelectorAll('header[class*="fixed"]');
    const originalFixedStyles = [];

    fixedElements.forEach((element, index) => {
      originalFixedStyles[index] = element.style.paddingRight;
      element.style.paddingRight = `${scrollBarWidth}px`;
    });

    return () => {
      document.body.style.overflow = originalStyle;
      document.body.style.paddingRight = originalPaddingRight;

      // Restore fixed elements
      fixedElements.forEach((element, index) => {
        element.style.paddingRight = originalFixedStyles[index];
      });
    };
  }, [locked]);
}

const NavBar = ({ onLogin, onSignup }) => {
  const [open, setOpen] = useState(false);
  return (
    <header className="fixed top-0 inset-x-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-slate-900/40">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <a
            href="#hero"
            className="flex items-center gap-3 text-xl font-semibold tracking-tight"
          >
            <img
              src="/GnyanSetu-2.png"
              alt="GnyanSetu Logo"
              className="h-10 w-10 rounded-lg"
            />
            <div className="flex items-center">
              <span className="text-slate-200">Gyan</span>
              <span className="text-accentBlue">सेतु</span>
            </div>
          </a>
          <nav className="hidden md:flex items-center gap-8">
            <a
              href="#about"
              className="text-slate-300 hover:text-white transition-colors"
            >
              About
            </a>
            <a
              href="#features"
              className="text-slate-300 hover:text-white transition-colors"
            >
              Features
            </a>
            <a
              href="#contact"
              className="text-slate-300 hover:text-white transition-colors"
            >
              Contact
            </a>
          </nav>
          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={onLogin}
              className="px-4 py-2 rounded-lg border border-slate-700 text-slate-200 hover:bg-slate-800 hover:border-slate-600 hover:text-white transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
            >
              Login
            </button>
            <button
              onClick={onSignup}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
            >
              Signup
            </button>
          </div>
          <button
            className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-slate-300 hover:text-white hover:bg-slate-800/60 transition"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            <Bars3Icon className="w-6 h-6" />
          </button>
        </div>
      </div>
      {open && (
        <div className="md:hidden fixed inset-0 z-50 bg-slate-900/70 backdrop-blur">
          <div className="absolute top-3 right-4">
            <button
              className="p-2 rounded hover:bg-slate-800"
              onClick={() => setOpen(false)}
              aria-label="Close menu"
            >
              <XMarkIcon className="w-7 h-7" />
            </button>
          </div>
          <div className="mt-20 flex flex-col items-center gap-6 text-lg">
            <a
              onClick={() => setOpen(false)}
              href="#about"
              className="text-slate-200"
            >
              About
            </a>
            <a
              onClick={() => setOpen(false)}
              href="#features"
              className="text-slate-200"
            >
              Features
            </a>
            <a
              onClick={() => setOpen(false)}
              href="#contact"
              className="text-slate-200"
            >
              Contact
            </a>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => {
                  setOpen(false);
                  onLogin();
                }}
                className="px-4 py-2 rounded-lg border border-slate-700 hover:bg-slate-800 hover:border-slate-600 hover:text-white transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
              >
                Login
              </button>
              <button
                onClick={() => {
                  setOpen(false);
                  onSignup();
                }}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
              >
                Signup
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

const BackgroundBlobs = () => {
  return (
    <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-24 -left-24 w-[40rem] h-[40rem] rounded-full bg-accentBlue/20 blur-3xl animate-blob"></div>
      <div
        className="absolute top-1/3 -right-28 w-[35rem] h-[35rem] rounded-full bg-accentPurple/20 blur-3xl animate-blob"
        style={{ animationDelay: "2s" }}
      ></div>
      <div
        className="absolute -bottom-24 left-1/3 w-[45rem] h-[45rem] rounded-full bg-accentBlue/10 blur-3xl animate-blob"
        style={{ animationDelay: "4s" }}
      ></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(59,130,246,0.08),transparent_60%),_radial-gradient(ellipse_at_bottom,_rgba(139,92,246,0.08),transparent_60%)]"></div>
    </div>
  );
};

const Section = ({ id, className, children }) => (
  <section
    id={id}
    className={classNames("relative min-h-screen flex items-center", className)}
  >
    {children}
  </section>
);

const Hero = ({ onPrimary }) => (
  <Section id="hero" className="pt-16">
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full">
      <div className="grid lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7">
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white">
            Bridge knowledge with{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accentBlue to-accentPurple">
              Gyanसेतु
            </span>
          </h1>
          <p className="mt-7 text-2xl text-slate-200 max-w-2xl">
            Your AI-powered companion for learning: convert PDFs to voice,
            collaborate on a live whiteboard, and generate quizzes instantly.
            Experience the future of education with cutting-edge technology.
          </p>
          <div className="mt-8 text-slate-300 text-lg max-w-2xl">
            ✨ AI-Powered Learning • 🎯 Personalized Experience • 🌐
            Collaborative Tools
          </div>
          <div className="mt-10 flex flex-wrap gap-6">
            <button
              onClick={onPrimary}
              className="px-8 py-4 rounded-2xl bg-gradient-to-r from-accentBlue to-accentPurple text-white text-lg shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
            >
              Get Started
            </button>
            <a
              href="#features"
              className="px-8 py-4 rounded-2xl border border-slate-700 text-slate-200 text-lg hover:bg-slate-800 hover:border-slate-600 hover:text-white transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
            >
              Explore Features
            </a>
          </div>
        </div>
        <div className="lg:col-span-5">
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-accentBlue/40 to-accentPurple/40 rounded-3xl blur-xl"></div>
            <div className="relative rounded-3xl border border-slate-800 bg-slate-900/50 p-8 backdrop-blur-xl">
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2 h-24 rounded-xl bg-slate-800/60"></div>
                <div className="h-24 rounded-xl bg-slate-800/60"></div>
                <div className="h-24 rounded-xl bg-slate-800/60"></div>
                <div className="col-span-2 h-24 rounded-xl bg-slate-800/60"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Section>
);

const About = () => (
  <Section id="about">
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
      <h2 className="text-4xl sm:text-5xl font-bold text-white">
        About GyanSetu
      </h2>
      <p className="mt-7 text-slate-200 text-2xl leading-relaxed">
        GyanSetu is a modern, AI-augmented learning platform that makes studying
        effortless. Turn dense PDFs into natural voice narration, collaborate in
        real-time using an intuitive whiteboard, and generate tailored quizzes
        to test your understanding— all in one place.
      </p>
      <div className="mt-10 grid md:grid-cols-3 gap-8 text-center">
        <div className="p-6">
          <div className="text-4xl mb-3">🚀</div>
          <h3 className="text-xl font-bold text-white mb-3">
            Innovation First
          </h3>
          <p className="text-slate-300 text-lg">
            Cutting-edge AI technology that adapts to your learning style
          </p>
        </div>
        <div className="p-6">
          <div className="text-4xl mb-3">🎓</div>
          <h3 className="text-xl font-bold text-white mb-3">
            Academic Excellence
          </h3>
          <p className="text-slate-300 text-lg">
            Designed by educators for students, ensuring quality learning
            outcomes
          </p>
        </div>
        <div className="p-6">
          <div className="text-4xl mb-3">🌍</div>
          <h3 className="text-xl font-bold text-white mb-3">Global Access</h3>
          <p className="text-slate-300 text-lg">
            Break down language barriers and make education accessible to all
          </p>
        </div>
      </div>
    </div>
  </Section>
);

const FeatureCard = ({ Icon, title, description }) => (
  <div className="group relative rounded-2xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:-translate-y-1 hover:shadow-2xl hover:shadow-accentBlue/10">
    <div className="absolute -inset-px rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-r from-accentBlue/20 to-accentPurple/20 blur"></div>
    <div className="relative flex items-start gap-4">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-accentBlue/20 to-accentPurple/20 text-accentBlue">
        <Icon className="w-6 h-6 text-accentBlue" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="mt-2 text-slate-300 text-sm">{description}</p>
      </div>
    </div>
  </div>
);

const Features = () => (
  <Section id="features">
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 w-full">
      <div className="text-center">
        <h2 className="text-5xl sm:text-6xl font-bold text-white">
          Powerful features
        </h2>
        <p className="mt-7 text-slate-200 text-2xl">
          Everything you need to learn effectively
        </p>
      </div>
      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          Icon={DocumentTextIcon}
          title="PDF to Voice"
          description="Listen to your study material with natural voice narration and adjustable speed."
        />
        <FeatureCard
          Icon={PencilSquareIcon}
          title="Interactive Whiteboard"
          description="Draw, annotate, and collaborate with classmates in real-time sessions."
        />
        <FeatureCard
          Icon={SparklesIcon}
          title="AI-Generated Quizzes"
          description="Create smart quizzes tailored to your uploaded content for quick revision."
        />
      </div>
    </div>
  </Section>
);

const CTA = ({ onClick }) => (
  <Section id="cta">
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
      <h2 className="text-5xl sm:text-6xl font-bold text-white">
        Ready to build your bridge to knowledge?
      </h2>
      <p className="mt-7 text-slate-200 text-2xl">
        Join GyanSetu today and transform how you learn.
      </p>
      <button
        onClick={onClick}
        className="mt-8 px-8 py-3 rounded-xl bg-gradient-to-r from-accentBlue to-accentPurple text-white shadow-lg hover:shadow-xl hover:shadow-accentPurple/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
      >
        Get Started
      </button>
    </div>
  </Section>
);

const Footer = () => (
  <footer className="border-t border-slate-800 py-10" id="contact">
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="text-lg font-semibold">
          <span className="text-slate-200">Gyan</span>
          <span className="text-accentBlue">सेतु</span>
        </div>
        <nav className="flex flex-wrap items-center gap-6 text-slate-300">
          <a href="#about" className="hover:text-white">
            About
          </a>
          <a href="#features" className="hover:text-white">
            Features
          </a>
          <a href="#contact" className="hover:text-white">
            Contact
          </a>
          <a href="#privacy" className="hover:text-white">
            Privacy Policy
          </a>
        </nav>
        <div className="flex items-center gap-4 text-slate-300">
          <a
            href="https://twitter.com"
            target="_blank"
            rel="noreferrer"
            aria-label="Twitter"
            className="hover:text-white transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-6 h-6"
            >
              <path d="M8.29 20c7.55 0 11.68-6.26 11.68-11.68 0-.18 0-.35-.01-.53A8.36 8.36 0 0 0 22 5.92a8.2 8.2 0 0 1-2.36.65 4.12 4.12 0 0 0 1.8-2.27 8.24 8.24 0 0 1-2.61 1 4.1 4.1 0 0 0-6.98 3.74 11.64 11.64 0 0 1-8.45-4.29 4.1 4.1 0 0 0 1.27 5.47 4.08 4.08 0 0 1-1.86-.51v.05a4.1 4.1 0 0 0 3.29 4.02 4.1 4.1 0 0 1-1.85.07 4.11 4.11 0 0 0 3.83 2.85A8.23 8.23 0 0 1 2 18.58 11.62 11.62 0 0 0 8.29 20" />
            </svg>
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub"
            className="hover:text-white transition-colors"
          >
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-6 h-6"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.48 2 2 6.7 2 12.37c0 4.56 2.87 8.42 6.84 9.78.5.1.68-.23.68-.5 0-.25-.01-1.08-.02-1.95-2.78.62-3.37-1.23-3.37-1.23-.46-1.2-1.12-1.52-1.12-1.52-.92-.65.07-.64.07-.64 1.02.07 1.56 1.08 1.56 1.08.9 1.6 2.36 1.14 2.94.87.09-.67.35-1.14.63-1.4-2.22-.26-4.55-1.15-4.55-5.14 0-1.14.39-2.07 1.03-2.8-.1-.26-.45-1.3.1-2.7 0 0 .85-.28 2.79 1.07a9.37 9.37 0 0 1 5.08 0c1.94-1.35 2.79-1.07 2.79-1.07.55 1.4.2 2.44.1 2.7.64.73 1.03 1.66 1.03 2.8 0 4-2.34 4.88-4.57 5.14.36.32.68.93.68 1.89 0 1.36-.01 2.45-.01 2.78 0 .27.18.6.69.5C19.12 20.79 22 16.93 22 12.37 22 6.7 17.52 2 12 2z"
              />
            </svg>
          </a>
          <a
            href="https://linkedin.com"
            target="_blank"
            rel="noreferrer"
            aria-label="LinkedIn"
            className="hover:text-white transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-6 h-6"
            >
              <path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM0 8.98h4.99V24H0zM8.98 8.98H14v2.05h.08c.7-1.33 2.42-2.73 4.98-2.73 5.32 0 6.31 3.5 6.31 8.04V24h-5v-6.56c0-1.56-.03-3.57-2.18-3.57-2.18 0-2.51 1.7-2.51 3.45V24h-4.98z" />
            </svg>
          </a>
        </div>
      </div>
      <p className="mt-6 text-center text-sm text-slate-500">
        © {new Date().getFullYear()} GyanSetu. All rights reserved.
      </p>
    </div>
  </footer>
);

const Modal = ({ isOpen, title, children, onClose }) => {
  const [mounted, setMounted] = React.useState(isOpen);
  const [visible, setVisible] = React.useState(false);
  const dialogRef = useRef(null);

  React.useEffect(() => {
    if (isOpen) {
      setMounted(true);
      const id = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(id);
    } else if (mounted) {
      setVisible(false);
      const t = setTimeout(() => setMounted(false), 200);
      return () => clearTimeout(t);
    }
  }, [isOpen, mounted]);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className={classNames(
          "absolute inset-0 bg-slate-900/30 backdrop-blur-md transition-opacity duration-200",
          visible ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
      />
      <div
        className="absolute inset-0 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <div
          ref={dialogRef}
          onClick={(e) => e.stopPropagation()}
          className={classNames(
            "w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 shadow-2xl backdrop-blur-xl transition duration-200",
            visible
              ? "opacity-100 scale-100 translate-y-0"
              : "opacity-0 scale-95 translate-y-2"
          )}
        >
          <div className="flex items-center justify-center border-b border-slate-800 px-5 py-3">
            <h3 className="text-lg font-semibold text-white">{title}</h3>
          </div>
          <div className="px-5 py-5">{children}</div>
        </div>
      </div>
    </div>
  );
};

const Input = (props) => {
  const [show, setShow] = useState(false);
  const isPassword = props.type === "password";
  const inputType = isPassword && show ? "text" : props.type;

  return (
    <div className="relative">
      <input
        {...props}
        type={inputType}
        className={classNames(
          "w-full rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-2 text-slate-200 placeholder-slate-400 outline-none focus:border-accentBlue/60 focus:ring-2 focus:ring-accentBlue/30 transition",
          props.className
        )}
      />
      {isPassword && (
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setShow((v) => !v)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 focus:outline-none flex items-center justify-center"
          aria-label={show ? "Hide password" : "Show password"}
          style={{ height: "20px" }}
        >
          {show ? (
            // Eye open icon (full eye)
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24">
              <path
                d="M1 12C1 12 5 5 12 5C19 5 23 12 23 12C23 12 19 19 12 19C5 19 1 12 1 12Z"
                stroke="currentColor"
                strokeWidth="2"
              />
              <circle
                cx="12"
                cy="12"
                r="3"
                stroke="currentColor"
                strokeWidth="2"
              />
            </svg>
          ) : (
            // Eye open icon with a diagonal slash overlay, perfectly centered
            <span
              style={{
                position: "relative",
                display: "inline-flex",
                width: "20px",
                height: "20px",
                verticalAlign: "middle",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <svg
                width="20"
                height="20"
                fill="none"
                viewBox="0 0 24 24"
                style={{ position: "absolute", top: 0, left: 0 }}
              >
                <path
                  d="M1 12C1 12 5 5 12 5C19 5 23 12 23 12C23 12 19 19 12 19C5 19 1 12 1 12Z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <circle
                  cx="12"
                  cy="12"
                  r="3"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              </svg>
              <svg
                width="20"
                height="20"
                fill="none"
                viewBox="0 0 24 24"
                style={{ position: "absolute", top: 0, left: 0 }}
              >
                <line
                  x1="4"
                  y1="20"
                  x2="20"
                  y2="4"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </span>
          )}
        </button>
      )}
    </div>
  );
};

const Checkbox = ({ label, ...props }) => (
  <label className="flex items-center gap-2 text-sm text-slate-300 select-none">
    <input
      type="checkbox"
      {...props}
      className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-accentBlue focus:ring-accentBlue"
    />
    {label}
  </label>
);

const GoogleButton = ({ text }) => (
  <div className="mt-3 w-full">
    <GoogleLogin
      onSuccess={handleGoogleSuccess}
      onError={handleGoogleError}
      text="continue_with"
      shape="rectangular"
      theme="filled_blue"
      size="large"
      width="100%"
      logo_alignment="left"
    />
  </div>
);

const LoginForm = ({ onForgot, onSignup, onSuccess, onError }) => {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authAPI.login(formData.email, formData.password);
      onSuccess(result);
    } catch (error) {
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="mb-1 block text-sm text-slate-300">Email</label>
        <Input
          type="email"
          name="email"
          placeholder="you@example.com"
          value={formData.email}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm text-slate-300">Password</label>
        <Input
          type="password"
          name="password"
          placeholder="••••••••"
          value={formData.password}
          onChange={handleChange}
          required
        />
      </div>
      <div className="flex items-center justify-between">
        <Checkbox label="Remember me" />
        <button
          type="button"
          onClick={onForgot}
          className="text-sm text-accentBlue hover:underline"
        >
          Forgot password?
        </button>
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Logging in..." : "Login"}
      </button>
      <GoogleButton text="Login using Google" />
      <div className="text-center text-sm text-slate-400">
        New to GyanSetu?{" "}
        <button
          type="button"
          onClick={onSignup}
          className="text-accentBlue hover:underline font-medium"
        >
          Sign Up
        </button>
      </div>
    </form>
  );
};

const SignupForm = ({ onLogin, onSuccess, onError }) => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Check if password contains any part of name or email username (case-insensitive)
    const password = formData.password.toLowerCase();
    const nameParts = formData.name
      .split(/\s+/)
      .filter(Boolean)
      .map((part) => part.toLowerCase());
    const emailUser = formData.email
      .split("@")[0]
      .replace(/\s+/g, "")
      .toLowerCase();
    const errors = [];
    for (const part of nameParts) {
      if (part && password.includes(part)) {
        errors.push(
          "Password should not contain part of your name or email username."
        );
        break;
      }
    }
    if (emailUser && password.includes(emailUser)) {
      errors.push(
        "Password should not contain part of your name or email username."
      );
    }
    if (errors.length > 0) {
      onError(errors);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const result = await authAPI.signup(
        formData.name,
        formData.email,
        formData.password,
        formData.confirm_password
      );
      onSuccess(result);
    } catch (error) {
      console.error("Signup error:", error);
      console.error("Error message:", error.message);
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      <div>
        <label className="mb-1 block text-sm text-slate-300">Name</label>
        <Input
          type="text"
          name="name"
          placeholder="Your name"
          value={formData.name}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm text-slate-300">Email</label>
        <Input
          type="email"
          name="email"
          placeholder="you@example.com"
          value={formData.email}
          onChange={handleChange}
          required
        />
      </div>
      <div>
        <label className="mb-1 block text-sm text-slate-300">Password</label>
        <Input
          type="password"
          name="password"
          placeholder="Create a password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <p className="mt-1 text-xs text-slate-400">
          Must be 8+ characters with uppercase, number, and special character
          (!@#$%^&* etc.)
        </p>
      </div>
      <div>
        <label className="mb-1 block text-sm text-slate-300">
          Confirm Password
        </label>
        <Input
          type="password"
          name="confirm_password"
          placeholder="Repeat your password"
          value={formData.confirm_password}
          onChange={handleChange}
          required
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Creating account..." : "Create account"}
      </button>
      <GoogleButton text="Continue with Google" />
      <div className="text-center text-sm text-slate-400">
        Already a user?{" "}
        <button
          type="button"
          onClick={onLogin}
          className="text-accentBlue hover:underline font-medium"
        >
          Login
        </button>
      </div>
    </form>
  );
};

const ForgotPasswordForm = ({ onLogin, onSuccess, onError, onStepChange }) => {
  const [step, setStep] = useState(1); // 1: email, 2: OTP, 3: new password
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(600); // 10 minutes in seconds
  const [canResend, setCanResend] = useState(false);

  // Notify parent component of step changes
  React.useEffect(() => {
    if (onStepChange) {
      onStepChange(step);
    }
  }, [step, onStepChange]);

  // Countdown timer effect
  React.useEffect(() => {
    if (step === 2 && countdown > 0) {
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            setCanResend(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [step, countdown]);

  // Format countdown as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authAPI.forgotPassword(email);
      setStep(2);
      setCountdown(600);
      setCanResend(false);
      onSuccess(
        result.message ||
          "If an account exists with this email, an OTP has been sent."
      );
    } catch (error) {
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setLoading(true);
    try {
      const result = await authAPI.forgotPassword(email);
      setCountdown(600);
      setCanResend(false);
      onSuccess(
        result.message ||
          "If an account exists with this email, an OTP has been sent."
      );
    } catch (error) {
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/verify-otp/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      const data = await response.json();

      if (response.ok) {
        setStep(3);
        onSuccess("OTP verified! Enter your new password.");
      } else {
        onError(data.error || "Invalid OTP");
      }
    } catch (error) {
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      onError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/auth/password-reset-confirm/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            otp,
            new_password: newPassword,
            confirm_password: confirmPassword,
          }),
        }
      );
      const data = await response.json();

      if (response.ok) {
        onSuccess("Password reset successful! You can now log in.");
        setTimeout(() => onLogin(), 2000);
      } else {
        onError(data.error || "Failed to reset password");
      }
    } catch (error) {
      onError(error.message);
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Enter Email
  if (step === 1) {
    return (
      <form className="space-y-4" onSubmit={handleSendOTP}>
        <div>
          <label className="mb-1 block text-sm text-slate-300">Email</label>
          <Input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <p className="text-sm text-slate-400 text-center">
          Enter your email address and we'll send you an OTP to reset your
          password.
        </p>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Sending OTP..." : "Send OTP"}
        </button>
        <div className="text-center text-sm text-slate-400">
          Remember your password?{" "}
          <button
            type="button"
            onClick={onLogin}
            className="text-accentBlue hover:underline font-medium"
          >
            Back to Login
          </button>
        </div>
      </form>
    );
  }

  // Step 2: Enter OTP
  if (step === 2) {
    return (
      <form className="space-y-4" onSubmit={handleVerifyOTP}>
        <div>
          <label className="mb-1 block text-sm text-slate-300">Enter OTP</label>
          <Input
            type="text"
            placeholder="123456"
            value={otp}
            onChange={(e) =>
              setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))
            }
            maxLength="6"
            required
            className="text-center text-2xl tracking-widest"
          />
          <p className="mt-2 text-xs text-slate-400 text-center">
            We sent a 6-digit code to{" "}
            <span className="text-accentBlue font-medium">{email}</span>
          </p>
        </div>

        {/* Countdown Timer */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800/50 rounded-lg">
            <svg
              className="w-4 h-4 text-accentBlue"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
            <span
              className={`text-sm font-mono ${
                countdown < 60 ? "text-red-400" : "text-slate-300"
              }`}
            >
              {formatTime(countdown)}
            </span>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Verifying..." : "Verify OTP"}
        </button>

        {/* Resend OTP Button */}
        <div className="text-center text-sm">
          {canResend || countdown === 0 ? (
            <button
              type="button"
              onClick={handleResendOTP}
              disabled={loading}
              className="text-accentBlue hover:underline font-medium disabled:opacity-50"
            >
              Resend OTP
            </button>
          ) : (
            <span className="text-slate-500">
              Didn't receive? Resend in {formatTime(countdown)}
            </span>
          )}
        </div>

        <div className="text-center text-sm text-slate-400">
          <button
            type="button"
            onClick={() => setStep(1)}
            className="text-accentBlue hover:underline font-medium"
          >
            ← Change Email
          </button>
        </div>
      </form>
    );
  }

  // Step 3: Reset Password
  if (step === 3) {
    return (
      <form className="space-y-4" onSubmit={handleResetPassword}>
        <div>
          <label className="mb-1 block text-sm text-slate-300">
            New Password
          </label>
          <Input
            type="password"
            placeholder="Enter new password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <p className="mt-1 text-xs text-slate-500">
            Must be 8+ characters with uppercase, number, and special character
            (!@#$%^&* etc.)
          </p>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-300">
            Confirm Password
          </label>
          <Input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    );
  }
};

export default function App() {
  const [modal, setModal] = useState(null); // 'login' | 'signup' | 'forgot' | null
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [forgotPasswordStep, setForgotPasswordStep] = useState(1);

  // Apply scroll lock when any modal is open
  useLockBodyScroll(modal !== null);

  const openLogin = () => {
    setModal("login");
    setError("");
    setSuccess("");
  };

  const openSignup = () => {
    setModal("signup");
    setError("");
    setSuccess("");
  };

  const openForgot = () => {
    setModal("forgot");
    setError("");
    setSuccess("");
    setForgotPasswordStep(1); // Reset to step 1
  };

  const closeModal = () => {
    setModal(null);
    setError("");
    setSuccess("");
    setForgotPasswordStep(1); // Reset step when closing
  };

  const handleAuthSuccess = (result) => {
    console.log("====================================");
    console.log("🔍 RAW Login API Response:");
    console.log("====================================");
    console.log("Full result object:", JSON.stringify(result, null, 2));
    console.log("result.access:", result.access);
    console.log("result.token:", result.token);
    console.log("result.refresh:", result.refresh);
    console.log("result.user:", result.user);
    console.log("====================================");

    // Clear any old data first
    localStorage.removeItem("user");
    localStorage.removeItem("gnyansetu_user");
    sessionStorage.clear();

    if (result.access || result.user || result.token) {
      // Authentication successful, store tokens and user data
      console.log("✅ Authentication successful:", result);

      // Store JWT tokens (Django returns 'access' and 'refresh')
      const accessToken = result.access || result.token;
      const refreshToken = result.refresh;

      if (accessToken) {
        localStorage.setItem("access_token", accessToken);
        localStorage.setItem("gnyansetu_auth_token", accessToken);
        console.log(
          "✅ Access token stored:",
          accessToken.substring(0, 20) + "..."
        );
      } else {
        console.error("❌ No access token in response!");
      }

      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
        console.log("✅ Refresh token stored");
      }

      // Store user data
      if (result.user) {
        localStorage.setItem("user", JSON.stringify(result.user));
        localStorage.setItem("gnyansetu_user", JSON.stringify(result.user));
        console.log("✅ User object stored:", result.user);

        // Extract and store user details
        const userId = result.user.id || result.user._id;
        const userEmail = result.user.email;
        const userName = result.user.full_name || result.user.name;

        if (userId) {
          sessionStorage.setItem("userId", userId);
          localStorage.setItem("userId", userId);
          console.log("✅ User ID stored:", userId);
        } else {
          console.error("❌ No userId found in user object!");
        }

        if (userEmail) {
          sessionStorage.setItem("userEmail", userEmail);
          localStorage.setItem("userEmail", userEmail);
          console.log("✅ User email stored:", userEmail);
        }

        if (userName) {
          sessionStorage.setItem("userName", userName);
          localStorage.setItem("userName", userName);
          console.log("✅ User name stored:", userName);
        }

        console.log("\n📦 Storage Summary:");
        console.log(
          "- access_token:",
          localStorage.getItem("access_token") ? "✅ Stored" : "❌ Missing"
        );
        console.log(
          "- userId:",
          localStorage.getItem("userId") || "❌ Missing"
        );
        console.log(
          "- userEmail:",
          localStorage.getItem("userEmail") || "❌ Missing"
        );
        console.log(
          "- userName:",
          localStorage.getItem("userName") || "❌ Missing"
        );
      } else {
        console.error("❌ No user object in response!");
      }

      console.log("\n🚀 Redirecting to dashboard with user data...");

      // Small delay to ensure storage is written
      setTimeout(() => {
        // Since localhost:3000 and localhost:3001 have separate localStorage,
        // we need to pass the data via URL or store it on the dashboard side
        const userId = result.user.id || result.user._id;
        const userEmail = result.user.email;
        const userName = result.user.full_name || result.user.name;
        const accessToken = result.access || result.token;
        const refreshToken = result.refresh;

        // Create a URL with all the data as hash (not query params to avoid server logs)
        const dashboardUrl =
          `http://localhost:3001/#login?` +
          `userId=${encodeURIComponent(userId)}&` +
          `userEmail=${encodeURIComponent(userEmail)}&` +
          `userName=${encodeURIComponent(userName)}&` +
          `accessToken=${encodeURIComponent(accessToken)}&` +
          `refreshToken=${encodeURIComponent(refreshToken)}&` +
          `user=${encodeURIComponent(JSON.stringify(result.user))}`;

        console.log("📡 Redirecting with user data in URL hash");
        window.location.href = dashboardUrl;
      }, 100);
    } else {
      console.error("❌ Invalid response format:", result);
      setError("Login failed: Invalid response from server");
    }
  };

  const handleAuthError = (errorMessage) => {
    setError(errorMessage);
    setSuccess("");
  };

  const handleForgotPasswordSuccess = (message) => {
    setSuccess(message);
    setError("");
  };

  const redirectToDashboard = () => {
    // Open dashboard in new tab instead of redirecting
    window.open("http://localhost:3001", "_blank");
  };

  return (
    <GoogleOAuthProvider clientId="334410826401-5dc8sdfntd1unbfnjamd6k4dvd7c3g1r.apps.googleusercontent.com">
      <div className="relative min-h-screen overflow-hidden">
        <BackgroundBlobs />
        {/* Watermark Logo */}
        <img
          src="/GnyanSetu.png"
          alt="GnyanSetu Watermark"
          style={{
            position: "fixed",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "600px",
            opacity: 0.08,
            zIndex: 0,
            pointerEvents: "none",
            userSelect: "none",
          }}
        />
        <NavBar onLogin={openLogin} onSignup={openSignup} />
        <main>
          <Hero onPrimary={openSignup} />
          <About />
          <Features />
          <CTA onClick={openSignup} />
        </main>
        <Footer />

        {/* Error/Success Messages */}
        {error && (
          <div className="fixed top-4 right-4 z-[200] bg-red-500 text-white p-4 rounded-lg shadow-lg max-w-md">
            <div className="flex items-start justify-between">
              <span className="text-sm">{error}</span>
              <button
                onClick={() => setError("")}
                className="ml-2 text-white hover:text-gray-200 text-lg leading-none"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {success && (
          <div className="fixed top-4 right-4 z-[200] bg-green-500 text-white p-4 rounded-lg shadow-lg max-w-md">
            <div className="flex items-start justify-between">
              <span className="text-sm">{success}</span>
              <button
                onClick={() => setSuccess("")}
                className="ml-2 text-white hover:text-gray-200 text-lg leading-none"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        <Modal
          isOpen={modal === "login"}
          title="Login to GyanSetu"
          onClose={closeModal}
        >
          <LoginForm
            onForgot={() => setModal("forgot")}
            onSignup={() => setModal("signup")}
            onSuccess={handleAuthSuccess}
            onError={handleAuthError}
          />
        </Modal>

        <Modal
          isOpen={modal === "signup"}
          title="Create your account"
          onClose={closeModal}
        >
          <SignupForm
            onLogin={() => setModal("login")}
            onSuccess={handleAuthSuccess}
            onError={handleAuthError}
          />
        </Modal>

        <Modal
          isOpen={modal === "forgot"}
          title={
            forgotPasswordStep === 1
              ? "Reset Password"
              : forgotPasswordStep === 2
              ? "Verify OTP"
              : "Create New Password"
          }
          onClose={closeModal}
        >
          <ForgotPasswordForm
            onLogin={() => setModal("login")}
            onSuccess={handleForgotPasswordSuccess}
            onError={handleAuthError}
            onStepChange={setForgotPasswordStep}
          />
        </Modal>
      </div>
    </GoogleOAuthProvider>
  );
}
