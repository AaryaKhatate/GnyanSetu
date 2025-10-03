import React, { useMemo, useRef, useState } from "react";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import {
  DocumentTextIcon,
  PencilSquareIcon,
  SparklesIcon,
} from "@heroicons/react/24/solid";
import classNames from "classnames";

// API Configuration - Use API Gateway instead of direct service calls
const API_BASE_URL = "http://localhost:8002";

// API functions
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include", // Include cookies for session management
  };

  const response = await fetch(url, { ...defaultOptions, ...options });
  const data = await response.json();

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
const handleGoogleSignup = () => {
  // Redirect to Google OAuth endpoint
  window.location.href = `${API_BASE_URL}/accounts/google/login/?next=/dashboard/`;
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
            className="flex items-center text-xl font-semibold tracking-tight"
          >
            <div className="w-12 h-12 mr-3">
              <img
                src="/GnyanSetu.png"
                alt="GyanSetu Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <span className="text-slate-200">Gyan</span>
            <span className="text-accentBlue">सेतु</span>
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
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white">
            Bridge knowledge with{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accentBlue to-accentPurple">
              GyanSetu
            </span>
          </h1>
          <p className="mt-5 text-lg text-slate-300 max-w-2xl">
            Your AI-powered companion for learning: convert PDFs to voice,
            collaborate on a live whiteboard, and generate quizzes instantly.
            Experience the future of education with cutting-edge technology.
          </p>
          <div className="mt-6 text-slate-400 text-sm max-w-2xl">
            ✨ AI-Powered Learning • 🎯 Personalized Experience • 🌐
            Collaborative Tools
          </div>
          <div className="mt-8 flex flex-wrap gap-4">
            <button
              onClick={onPrimary}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-accentBlue to-accentPurple text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
            >
              Get Started
            </button>
            <a
              href="#features"
              className="px-6 py-3 rounded-xl border border-slate-700 text-slate-200 hover:bg-slate-800 hover:border-slate-600 hover:text-white transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
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
      <h2 className="text-3xl sm:text-4xl font-semibold text-white">
        About GyanSetu
      </h2>
      <p className="mt-5 text-slate-300 text-lg leading-relaxed">
        GyanSetu is a modern, AI-augmented learning platform that makes studying
        effortless. Turn dense PDFs into natural voice narration, collaborate in
        real-time using an intuitive whiteboard, and generate tailored quizzes
        to test your understanding— all in one place.
      </p>
      <div className="mt-8 grid md:grid-cols-3 gap-6 text-center">
        <div className="p-4">
          <div className="text-3xl mb-2">🚀</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            Innovation First
          </h3>
          <p className="text-slate-400 text-sm">
            Cutting-edge AI technology that adapts to your learning style
          </p>
        </div>
        <div className="p-4">
          <div className="text-3xl mb-2">🎓</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            Academic Excellence
          </h3>
          <p className="text-slate-400 text-sm">
            Designed by educators for students, ensuring quality learning
            outcomes
          </p>
        </div>
        <div className="p-4">
          <div className="text-3xl mb-2">🌍</div>
          <h3 className="text-lg font-semibold text-white mb-2">
            Global Access
          </h3>
          <p className="text-slate-400 text-sm">
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
        <h2 className="text-3xl sm:text-4xl font-semibold text-white">
          Powerful features
        </h2>
        <p className="mt-3 text-slate-300">
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
      <h2 className="text-3xl sm:text-4xl font-semibold text-white">
        Ready to build your bridge to knowledge?
      </h2>
      <p className="mt-4 text-slate-300">
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

const Input = (props) => (
  <input
    {...props}
    className={classNames(
      "w-full rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-2 text-slate-200 placeholder-slate-400 outline-none focus:border-accentBlue/60 focus:ring-2 focus:ring-accentBlue/30 transition",
      props.className
    )}
  />
);

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

const GoogleButton = ({ text, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className="mt-3 w-full inline-flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900/40 px-4 py-2 text-slate-200 hover:bg-slate-800 hover:border-slate-600 hover:text-white transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 533.5 544.3"
      className="h-5 w-5"
    >
      <path
        fill="#4285F4"
        d="M533.5 278.4c0-18.6-1.7-37-5.2-54.8H272.1v103.9h147.2c-6.2 33.6-25 62-53.5 81v67.2h86.6c50.8-46.8 81.1-115.7 81.1-197.3z"
      />
      <path
        fill="#34A853"
        d="M272.1 544.3c72.7 0 133.8-24.1 178.4-65.7l-86.6-67.2c-24.1 16.2-55 25.6-91.8 25.6-70.7 0-130.6-47.7-152-111.8H30.1v70.1c44.2 87.7 134.9 149 242 149z"
      />
      <path
        fill="#FBBC05"
        d="M120.1 325.2c-10.4-30.9-10.4-64.2 0-95.1V160H30.1c-43.3 86.6-43.3 189.8 0 276.5l90-70.9z"
      />
      <path
        fill="#EA4335"
        d="M272.1 106.6c39.5-.6 77.6 14.5 106.4 42.2l79.1-79.1C409.4 25.1 343 0 272.1 0 165 0 74.2 61.3 30.1 149.9l90 70.1c21.3-64 81.2-111.8 152-111.8z"
      />
    </svg>
    <span>{text}</span>
  </button>
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
      <GoogleButton text="Login using Google" onClick={handleGoogleSignup} />
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
      <GoogleButton text="Continue with Google" onClick={handleGoogleSignup} />
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

const ForgotPasswordForm = ({ onLogin, onSuccess, onError }) => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await authAPI.forgotPassword(email);
      onSuccess(result.message);
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
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <p className="text-sm text-slate-400 text-center">
        Enter your email address and we'll send you a link to reset your
        password.
      </p>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-gradient-to-r from-accentBlue to-accentPurple px-4 py-2 text-white shadow-lg hover:shadow-xl hover:shadow-accentBlue/25 transform hover:-translate-y-0.5 transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Sending..." : "Send Reset Link"}
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
};

export default function App() {
  const [modal, setModal] = useState(null); // 'login' | 'signup' | 'forgot' | null
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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
  };

  const closeModal = () => {
    setModal(null);
    setError("");
    setSuccess("");
  };

  const handleAuthSuccess = (result) => {
    if (result.user) {
      // Authentication successful, open dashboard in new tab
      console.log("Authentication successful:", result);
      // Store user data for dashboard
      localStorage.setItem("gnyansetu_user", JSON.stringify(result.user));
      // Open dashboard in new tab instead of redirecting
      window.open("http://localhost:3001", "_blank");
      // Close modal
      closeModal();
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
    <div className="relative min-h-screen">
      <BackgroundBlobs />
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
        title="Reset Password"
        onClose={closeModal}
      >
        <ForgotPasswordForm
          onLogin={() => setModal("login")}
          onSuccess={handleForgotPasswordSuccess}
          onError={handleAuthError}
        />
      </Modal>
    </div>
  );
}
