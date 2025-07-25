from fastmcp import FastMCP
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Initialize FastMCP server
mcp = FastMCP("AppPulse Metrics Server")

# Database setup
project_root = Path(__file__).resolve().parent.parent.parent
db_path = project_root / "data" / "pulse.db"
engine = create_engine(f"sqlite:///{db_path}")

@mcp.tool()
def get_api_metrics_summary(hours: int = 24) -> dict[str, Any]:
    """Get comprehensive API metrics including request counts, response times, and success rates"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with engine.connect() as conn:
        query = text("""
            SELECT 
                COUNT(*) as total_requests,
                AVG(response_time_ms) as avg_response_time,
                COUNT(*) FILTER (WHERE success = 1) as successful_requests,
                COUNT(*) FILTER (WHERE success = 0) as failed_requests,
                MIN(response_time_ms) as min_response_time,
                MAX(response_time_ms) as max_response_time,
                COUNT(DISTINCT path) as unique_endpoints
            FROM api_metrics 
            WHERE timestamp >= :cutoff_time
        """)
        
        result = conn.execute(query, {"cutoff_time": cutoff_time}).fetchone()
        
        total = result[0] if result[0] else 0
        success_rate = (result[2] / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "avg_response_time_ms": round(result[1], 2) if result[1] else 0,
            "success_rate_percent": round(success_rate, 2),
            "successful_requests": result[2] or 0,
            "failed_requests": result[3] or 0,
            "min_response_time_ms": result[4] or 0,
            "max_response_time_ms": result[5] or 0,
            "unique_endpoints": result[6] or 0,
            "time_period_hours": hours
        }

@mcp.tool()
def get_system_metrics_summary(hours: int = 24) -> dict[str, Any]:
    """Get system health metrics including CPU, memory, and disk usage"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with engine.connect() as conn:
        query = text("""
            SELECT 
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(disk_usage) as avg_disk,
                COUNT(*) as data_points
            FROM system_metrics 
            WHERE timestamp >= :cutoff_time
        """)
        
        result = conn.execute(query, {"cutoff_time": cutoff_time}).fetchone()
        
        return {
            "avg_cpu_percent": round(result[0], 2) if result[0] else 0,
            "max_cpu_percent": round(result[1], 2) if result[1] else 0,
            "avg_memory_percent": round(result[2], 2) if result[2] else 0,
            "max_memory_percent": round(result[3], 2) if result[3] else 0,
            "avg_disk_usage_percent": round(result[4], 2) if result[4] else 0,
            "data_points": result[5] or 0,
            "time_period_hours": hours
        }

@mcp.tool()
def get_error_analysis(hours: int = 24) -> dict[str, Any]:
    """Analyze API and UI errors, get error counts and types"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with engine.connect() as conn:
        # API Errors
        api_query = text("""
            SELECT error_type, COUNT(*) as count
            FROM api_errors 
            WHERE timestamp >= :cutoff_time
            GROUP BY error_type
            ORDER BY count DESC
        """)
        
        api_results = conn.execute(api_query, {"cutoff_time": cutoff_time}).fetchall()
        
        # UI Errors  
        ui_query = text("""
            SELECT error_type, COUNT(*) as count
            FROM ui_errors 
            WHERE timestamp >= :cutoff_time
            GROUP BY error_type
            ORDER BY count DESC
        """)
        
        ui_results = conn.execute(ui_query, {"cutoff_time": cutoff_time}).fetchall()
        
        return {
            "total_api_errors": sum(row[1] for row in api_results),
            "api_error_types": [{"type": row[0], "count": row[1]} for row in api_results],
            "total_ui_errors": sum(row[1] for row in ui_results),
            "ui_error_types": [{"type": row[0], "count": row[1]} for row in ui_results],
            "time_period_hours": hours
        }

@mcp.tool()
def get_performance_trends(hours: int = 24) -> dict[str, Any]:
    """Get performance trends and identify bottlenecks"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    with engine.connect() as conn:
        query = text("""
            SELECT 
                path,
                COUNT(*) as request_count,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                COUNT(*) FILTER (WHERE success = 0) as error_count
            FROM api_metrics 
            WHERE timestamp >= :cutoff_time
            GROUP BY path
            ORDER BY avg_response_time DESC
            LIMIT 10
        """)
        
        results = conn.execute(query, {"cutoff_time": cutoff_time}).fetchall()
        
        return {
            "slowest_endpoints": [
                {
                    "path": row[0],
                    "request_count": row[1],
                    "avg_response_time_ms": round(row[2], 2),
                    "max_response_time_ms": round(row[3], 2),
                    "error_count": row[4]
                } for row in results
            ],
            "time_period_hours": hours
        }

if __name__ == "__main__":
    mcp.run()