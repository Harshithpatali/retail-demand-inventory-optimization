from __future__ import annotations

from typing import Iterable


def normal_interval(
    forecast: Iterable[float],
    residual_std: float,
    z: float = 1.96,
):
    margin = (
        z
        * float(residual_std)
    )

    lower = []
    upper = []

    for value in forecast:

        prediction = float(
            value
        )

        lower.append(
            max(
                0.0,
                prediction - margin,
            )
        )

        upper.append(
            prediction + margin
        )

    return lower, upper