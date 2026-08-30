from dataclasses import dataclass

@dataclass(frozen=True)
class CostModel:
    holding_cost_per_unit_day: float
    ordering_cost_per_order: float
    stockout_cost_per_unit: float

    def total(self, holding: float, ordering: float, stockout: float) -> float:
        return holding + ordering + stockout
