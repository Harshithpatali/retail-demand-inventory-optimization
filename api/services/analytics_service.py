from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row


class AnalyticsService:
    """Read-only access to the private Supabase retail analytics schema."""

    def _connect(self):
        dsn = os.getenv("SUPABASE_DB_URL", "").strip()
        if not dsn:
            raise RuntimeError("SUPABASE_DB_URL is not configured on the API service.")
        return psycopg.connect(
            dsn, connect_timeout=5, row_factory=dict_row,
            options="-c default_transaction_read_only=on",
        )

    def _query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [dict(row) for row in cur.fetchall()]

    def overview(self) -> dict:
        rows = self._query("""
            select r.run_id::text as run_id,r.dataset_version,r.row_count,r.series_count,
                   r.start_date::text as start_date,r.end_date::text as end_date,r.loaded_at,
                   count(distinct f.item_id) as product_count,
                   count(distinct f.store_id) as store_count,
                   coalesce(sum(f.demand),0)::bigint as total_units,
                   avg(f.demand)::float8 as mean_daily_units,
                   avg((f.demand=0)::int)::float8 as zero_demand_rate
            from retail.dataset_runs r
            left join retail.fact_daily_demand f on f.run_id=r.run_id
            where r.run_id=(select run_id from retail.dataset_runs order by loaded_at desc limit 1)
            group by r.run_id
        """)
        if not rows:
            return {"available": False, "message": "No M5 panel has been published to the retail warehouse."}
        return {"available": True, **rows[0]}

    def product_performance(self, limit: int = 50, sort_by: str = "total_units") -> list[dict]:
        allowed = {
            "total_units": "total_units desc",
            "demand_cv": "demand_cv desc nulls last",
            "zero_demand_rate": "zero_demand_rate desc",
            "avg_sell_price": "avg_sell_price desc nulls last",
        }
        order = allowed.get(sort_by, allowed["total_units"])
        return self._query(f"""
            select item_id,dept_id,cat_id,store_id,state_id,observed_days,total_units,
                   avg_daily_demand,demand_std,demand_cv,avg_sell_price,zero_demand_rate
            from retail.v_product_store_performance order by {order} limit %s
        """, (max(1, min(int(limit), 200)),))

    def seasonality(self, store_id: str | None = None, item_id: str | None = None) -> dict:
        filters = []
        params: list[Any] = []
        if store_id:
            filters.append("store_id=%s"); params.append(store_id)
        if item_id:
            filters.append("item_id=%s"); params.append(item_id)
        where = (" where " + " and ".join(filters)) if filters else ""
        weekday = self._query(f"""
            select weekday,wday,avg(avg_demand)::float8 as mean_demand,
                   sum(total_demand)::bigint as total_demand,sum(observations)::bigint as observations
            from retail.v_demand_seasonality{where}
            group by weekday,wday order by wday
        """, tuple(params))
        month = self._query(f"""
            select month,avg(avg_demand)::float8 as mean_demand,
                   sum(total_demand)::bigint as total_demand,sum(observations)::bigint as observations
            from retail.v_demand_seasonality{where}
            group by month order by month
        """, tuple(params))
        return {"weekday": weekday, "month": month}

    def interval_evaluation(self, limit: int = 20) -> list[dict]:
        return self._query("""
            select evaluation_run,nominal_coverage,empirical_coverage,mean_interval_width,
                   observations,calibration_method,evaluated_at
            from retail.forecast_interval_evaluation
            order by evaluated_at desc, nominal_coverage limit %s
        """, (max(1, min(int(limit), 100)),))

    def inventory_sensitivity(self, limit: int = 100) -> list[dict]:
        return self._query("""
            select evaluation_run,lead_time_days,review_period_days,service_level_target,
                   cost_scenario,series_count,baseline_total_cost,candidate_total_cost,
                   baseline_stockout_units,candidate_stockout_units,baseline_fill_rate,
                   candidate_fill_rate,baseline_average_inventory,candidate_average_inventory,
                   cost_change_pct,stockout_change_pct,evaluated_at
            from retail.inventory_sensitivity
            order by evaluated_at desc, lead_time_days, service_level_target limit %s
        """, (max(1, min(int(limit), 500)),))

    def model_evaluation(self, limit: int = 100) -> list[dict]:
        return self._query("""
            select evaluation_run,model_name,demand_segment,fold,sample_count,
                   mae,rmse,wape,bias,evaluated_at,metadata
            from retail.model_evaluation order by evaluated_at desc limit %s
        """, (max(1, min(int(limit), 500)),))
