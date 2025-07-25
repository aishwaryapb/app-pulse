import api from "./api";

interface UIError {
  error_type: string;
  error_message: string;
  user_id?: string;
  additional_data?: any;
}

class ErrorLogger {
  private isEnabled: boolean = true;
  private userId: string = `user_${Date.now()}`;
  private originalConsoleError!: typeof console.error;
  private isClient: boolean = typeof window !== "undefined";

  constructor() {
    if (!this.isClient) return; // Skip initialization on server

    this.originalConsoleError = console.error;
    this.interceptConsoleError();
    this.interceptUnhandledErrors();
  }

  private async logError(error: UIError) {
    if (!this.isEnabled || !this.isClient) return;

    try {
      await api.post("/api/log/errors", {
        ...error,
        user_id: this.userId,
      });
    } catch (err) {
      this.originalConsoleError?.("Failed to log error to backend:", err);
    }
  }

  private interceptConsoleError() {
    if (!this.isClient) return;

    console.error = (...args: any[]) => {
      this.originalConsoleError.apply(console, args);

      const errorMessage = args
        .map((arg) =>
          typeof arg === "object" ? JSON.stringify(arg) : String(arg)
        )
        .join(" ");

      this.logError({
        error_type: "Console Error",
        error_message: errorMessage,
        additional_data: {
          source: "console.error",
          timestamp: new Date().toISOString(),
          url: window.location.href,
          userAgent: navigator.userAgent,
        },
      });
    };
  }

  private interceptUnhandledErrors() {
    if (!this.isClient) return;

    window.addEventListener("error", (event) => {
      this.logError({
        error_type: "Unhandled Error",
        error_message: event.message,
        additional_data: {
          source: "window.error",
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          stack: event.error?.stack,
          url: window.location.href,
        },
      });
    });

    window.addEventListener("unhandledrejection", (event) => {
      this.logError({
        error_type: "Unhandled Promise Rejection",
        error_message: event.reason?.message || String(event.reason),
        additional_data: {
          source: "unhandledrejection",
          stack: event.reason?.stack,
          url: window.location.href,
        },
      });
    });
  }

  public log(errorType: string, message: string, additionalData?: any) {
    if (!this.isClient) return;

    this.logError({
      error_type: errorType,
      error_message: message,
      additional_data: {
        source: "manual",
        ...additionalData,
        url: window.location.href,
      },
    });
  }

  public enable() {
    this.isEnabled = true;
  }
  public disable() {
    this.isEnabled = false;
  }
  public setUserId(userId: string) {
    this.userId = userId;
  }
}

const errorLogger = new ErrorLogger();
export default errorLogger;
