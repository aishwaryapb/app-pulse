"use client";
import { useEffect } from "react";
import errorLogger from "@/services/errorLogger";

export default function ErrorLogger() {
  useEffect(() => {
    // Error logger is automatically initialized when imported
    console.log("Error logger initialized");
  }, []);

  return null; // This component renders nothing
}
