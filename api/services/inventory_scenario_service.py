from __future__ import annotations

import json
import os
from typing import Any

import psycopg

from api.services.inventory_service import InventoryService


class InventoryScenarioService:
    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        dsn = os.getenv("SUPABASE_DB_URL", "").strip()
        if not dsn:
            raise RuntimeError("SUPABASE_DB_URL is not configured on the API service.")
        result = InventoryService().calculate(
            store_id=payload["store_id"],
            item_id=payload["item_id"],
            service_level=payload["service_level"],
            lead_time_days=payload["lead_time_days"],
            review_period_days=payload["review_period_days"],
            current_inventory=payload["current_inventory"],
            include_model_metadata=False,
        )
        assumptions = {
            "unit_holding_cost": payload["unit_holding_cost"],
            "ordering_cost": payload["ordering_cost"],
            "stockout_cost": payload["stockout_cost"],
            "inventory_position_assumption": result["inventory_position_assumption"],
            "source": "user-entered scenario assumptions; not observed M5 inventory or retailer costs",
        }
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("select run_id from retail.dataset_runs order by loaded_at desc limit 1")
                row = cur.fetchone()
                run_id = row[0] if row else None
                cur.execute("""
                    insert into retail.inventory_scenarios
                    (run_id,store_id,item_id,current_inventory,lead_time_days,review_period_days,
                     service_level,unit_holding_cost,ordering_cost,stockout_cost,
                     mean_daily_demand,demand_std,safety_stock,reorder_point,
                     recommended_order_quantity,assumptions)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                    returning scenario_id::text
                """, (
                    run_id, payload["store_id"], payload["item_id"],
                    payload["current_inventory"], payload["lead_time_days"],
                    payload["review_period_days"], payload["service_level"],
                    payload["unit_holding_cost"], payload["ordering_cost"],
                    payload["stockout_cost"], result["mean_daily_demand"],
                    result["demand_std"], result["safety_stock"],
                    result["reorder_point"], result["order_quantity"],
                    json.dumps(assumptions),
                ))
                scenario_id = cur.fetchone()[0]
            conn.commit()
        return {"scenario_id": scenario_id, "policy": result, "assumptions": assumptions}
