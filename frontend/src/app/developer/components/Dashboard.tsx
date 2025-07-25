"use client";
import { useState, useEffect } from "react";
import api from "@/services/api";
import styles from "./Dashboard.module.scss";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface DashboardData {
  aggregated: {
    api_stats: {
      total_requests: number;
      success_rate: number;
      avg_response_time: number;
      error_count: number;
      requests_per_minute: number;
    };
    system_stats: {
      avg_cpu: number;
      avg_memory: number;
      latest_metrics: any;
    };
  };
  recent_api_metrics: Array<{
    timestamp: string;
    data: {
      method: string;
      path: string;
      status_code: number;
      response_time_ms: number;
      success: boolean;
    };
  }>;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get("/api/log/dashboard-data");
      setData(response.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateUIError = async () => {
    try {
      await api.post("/api/log/errors", {
        error_type: "Test UI Error",
        error_message: "This is a test error generated from the dashboard",
        user_id: "test-user",
        additional_data: { source: "dashboard_test_button" },
      });
      alert("Test UI error generated successfully!");
    } catch (error) {
      console.error("Error generating test error:", error);
    }
  };

  const processTimeSeriesData = (
    metrics: DashboardData["recent_api_metrics"]
  ) => {
    if (!metrics || metrics.length === 0) return [];

    const timeGroups = new Map<
      string,
      { count: number; totalLatency: number; avgLatency: number }
    >();

    metrics.forEach((metric) => {
      const timestamp = new Date(metric.timestamp);
      const timeKey = timestamp.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });

      if (!timeGroups.has(timeKey)) {
        timeGroups.set(timeKey, { count: 0, totalLatency: 0, avgLatency: 0 });
      }

      const group = timeGroups.get(timeKey)!;
      group.count += 1;
      group.totalLatency += metric.data.response_time_ms;
      group.avgLatency = group.totalLatency / group.count;
    });

    return Array.from(timeGroups.entries())
      .map(([time, data]) => ({
        time,
        requests: data.count,
        latency: Math.round(data.avgLatency * 100) / 100,
      }))
      .sort((a, b) => a.time.localeCompare(b.time))
      .slice(-20); // Last 20 time points
  };

  if (loading)
    return <div className={styles.loading}>Loading dashboard...</div>;
  if (!data)
    return <div className={styles.error}>Failed to load dashboard data</div>;

  const { api_stats, system_stats } = data.aggregated;
  const timeSeriesData = processTimeSeriesData(data.recent_api_metrics);

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h2>Real-time Monitoring</h2>
        <button className={styles.testButton} onClick={generateUIError}>
          Generate Test UI Error
        </button>
      </div>

      <div className={styles.widgets}>
        {/* API Metrics Widgets */}
        <div className={styles.widget}>
          <h3>Request Rate</h3>
          <div className={styles.metric}>
            <span className={styles.value}>
              {api_stats.requests_per_minute.toFixed(1)}
            </span>
            <span className={styles.unit}>req/min</span>
          </div>
        </div>

        <div className={styles.widget}>
          <h3>Response Time</h3>
          <div className={styles.metric}>
            <span className={styles.value}>
              {api_stats.avg_response_time.toFixed(1)}
            </span>
            <span className={styles.unit}>ms</span>
          </div>
        </div>

        <div className={styles.widget}>
          <h3>Success Rate</h3>
          <div className={styles.metric}>
            <span className={styles.value}>
              {api_stats.success_rate.toFixed(1)}
            </span>
            <span className={styles.unit}>%</span>
          </div>
          <div className={styles.progressBar}>
            <div
              className={styles.progress}
              style={{ width: `${api_stats.success_rate}%` }}
            ></div>
          </div>
        </div>

        {/* System Health Widget */}
        <div className={styles.widget}>
          <h3>System Health</h3>
          <div className={styles.systemHealth}>
            <div className={styles.healthItem}>
              <span>CPU</span>
              <span className={styles.healthValue}>
                {system_stats.avg_cpu.toFixed(1)}%
              </span>
            </div>
            <div className={styles.healthItem}>
              <span>Memory</span>
              <span className={styles.healthValue}>
                {system_stats.avg_memory.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Error Tracking Widgets */}
        <div className={styles.widget}>
          <h3>API Errors</h3>
          <div className={styles.metric}>
            <span className={styles.value}>{api_stats.error_count}</span>
            <span className={styles.unit}>errors</span>
          </div>
        </div>

        <div className={styles.widget}>
          <h3>Total Requests</h3>
          <div className={styles.metric}>
            <span className={styles.value}>{api_stats.total_requests}</span>
            <span className={styles.unit}>total</span>
          </div>
        </div>

        {/* Timeseries Widgets */}
        <div className={`${styles.widget} ${styles.chartWidget}`}>
          <h3>Requests per Minute (Last 20 intervals)</h3>
          <div className={styles.chartContainer}>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className={`${styles.widget} ${styles.chartWidget}`}>
          <h3>Average Latency (ms)</h3>
          <div className={styles.chartContainer}>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
