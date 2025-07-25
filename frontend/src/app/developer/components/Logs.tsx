"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import styles from "./Logs.module.scss";

interface LogEntry {
  id: number;
  timestamp: string;
  error_type?: string;
  error_message?: string;
  method?: string;
  path?: string;
  status_code?: number;
  response_time_ms?: number;
  additional_data?: string;
}

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [logType, setLogType] = useState<"api" | "ui">("api");

  useEffect(() => {
    fetchLogs();
  }, [logType]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const endpoint =
        logType === "api" ? "/api/log/api-logs" : "/api/log/ui-logs";
      const response = await api.get(endpoint);
      setLogs(response.data);
    } catch (error) {
      console.error("Error fetching logs:", error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatAdditionalData = (data: string) => {
    try {
      return JSON.stringify(JSON.parse(data), null, 2);
    } catch {
      return data;
    }
  };

  return (
    <div className={styles.logs}>
      <div className={styles.header}>
        <h2>System Logs</h2>
        <div className={styles.toggle}>
          <button
            className={`${styles.toggleButton} ${
              logType === "api" ? styles.active : ""
            }`}
            onClick={() => setLogType("api")}
          >
            API Logs
          </button>
          <button
            className={`${styles.toggleButton} ${
              logType === "ui" ? styles.active : ""
            }`}
            onClick={() => setLogType("ui")}
          >
            UI Logs
          </button>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Loading logs...</div>
      ) : logs.length === 0 ? (
        <div className={styles.noLogs}>
          No {logType.toUpperCase()} logs found
        </div>
      ) : (
        <div className={styles.logsList}>
          {logs.map((log) => (
            <div key={log.id} className={styles.logEntry}>
              <div className={styles.logHeader}>
                <span className={styles.timestamp}>
                  {formatTimestamp(log.timestamp)}
                </span>

                <span className={styles.errorType}>{log.error_type}</span>
              </div>

              <div className={styles.logContent}>
                <div>
                  <div className={styles.errorMessage}>{log.error_message}</div>
                  {log.additional_data && (
                    <details className={styles.additionalData}>
                      <summary>Additional Data</summary>
                      <pre>{formatAdditionalData(log.additional_data)}</pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
