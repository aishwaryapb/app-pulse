"use client";
import { useState } from "react";
import Link from "next/link";
import Dashboard from "./components/Dashboard";
import Logs from "./components/Logs";
import Chat from "./components/Chat";
import styles from "./page.module.scss";

export default function DeveloperPage() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "logs" | "chat">(
    "dashboard"
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Link href="/" className={styles.homeButton}>
          ← Home
        </Link>
        <h1>Developer Dashboard</h1>
      </div>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${
            activeTab === "dashboard" ? styles.active : ""
          }`}
          onClick={() => setActiveTab("dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`${styles.tab} ${
            activeTab === "logs" ? styles.active : ""
          }`}
          onClick={() => setActiveTab("logs")}
        >
          Logs
        </button>
        <button
          className={`${styles.tab} ${
            activeTab === "chat" ? styles.active : ""
          }`}
          onClick={() => setActiveTab("chat")}
        >
          AI Assistant
        </button>
      </div>

      <div className={styles.content}>
        {activeTab === "dashboard" && <Dashboard />}
        {activeTab === "logs" && <Logs />}
        {activeTab === "chat" && <Chat />}
      </div>
    </div>
  );
}
