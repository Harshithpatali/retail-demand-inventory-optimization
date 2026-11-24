"""Repeated stratified LightGBM experiments; production model is never overwritten."""
from __future__ import annotations
import argparse, gc, json
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scripts import train_full_population_forecaster as base

RUNS, SAMPLE_ROWS, SEED_BASE = 20, 200_000, 20261124
OUT = base.OUT / "repeated_lightgbm_experiments"
CANDIDATE = base.MODEL / "candidates" / "repeated_200k_lightgbm_candidate.txt"
STRATA = ["store_segment", "category_segment", "horizon", "demand_pattern"]

def _allocate(sizes, n):
    total = int(sizes.sum())
    if n > total: raise ValueError(f"Need {n:,} rows; only {total:,} available.")
    raw = sizes.astype(float) * n / total
    alloc = np.minimum(np.floor(raw).astype(int), sizes)
    left = n - int(alloc.sum())
    while left:
        eligible = np.flatnonzero(sizes > alloc)
        order = eligible[np.argsort(-(raw[eligible] - alloc[eligible]))]
        take = min(left, len(order))
        alloc[order[:take]] += 1
        left -= take
    return alloc

def stratified_sample(frame, sample_size=SAMPLE_ROWS, seed=SEED_BASE):
    if len(frame) < sample_size:
        raise ValueError(f"Need {sample_size:,} eligible rows; found {len(frame):,}.")
    work = frame.copy()
    z = work["zero_frac_90"].fillna(1.0)
    work["demand_pattern"] = np.select([z >= .90, z >= .50],
                                       ["intermittent", "lumpy"], default="regular")
    grouped = work.groupby(STRATA, observed=True, sort=True).indices
    positions = [np.asarray(grouped[k], dtype=np.int64) for k in grouped]
    alloc = _allocate(np.asarray([len(p) for p in positions]), sample_size)
    rng = np.random.default_rng(seed)
    picked = [rng.choice(p, size=int(n), replace=False)
              for p, n in zip(positions, alloc) if n]
    indices = np.concatenate(picked)
    rng.shuffle(indices)
    result = work.iloc[indices].drop(columns=["demand_pattern"]).reset_index(drop=True)
    if len(result) != sample_size: raise RuntimeError("Stratified sampler did not return exact size.")
    return result

def _load_evaluation(path, val_origin, test_origin):
    cols = base.FEATURES + ["target","seasonal_naive","origin_index","store_segment",
        "state_segment","category_segment","department_segment"]
    parts = []
    for batch in pq.ParquetFile(path).iter_batches(batch_size=65536, columns=cols):
        part = batch.to_pandas()
        part = part[part.origin_index.isin([val_origin, test_origin])]
        if not part.empty: parts.append(part)
    if not parts: raise RuntimeError("Fixed validation/test rows are missing.")
    return pd.concat(parts, ignore_index=True)

def _matrix(frame, levels):
    x = frame[base.FEATURES].copy()
    sizes = {"item_code":len(levels["item_id"]), "store_code":len(levels["store_id"]),
        "dept_code":len(levels["dept_id"]), "cat_code":len(levels["cat_id"]),
        "state_code":len(levels["state_id"])}
    for col in base.CATS: x[col] = pd.Categorical(x[col], categories=range(sizes[col]))
    return x

def _metrics(model, frame, levels, split):
    pred = np.clip(model.predict(_matrix(frame, levels)), 0, None)
    actual = frame.target.to_numpy(dtype=float)
    error = pred - actual
    return {"split":split, "rows":int(len(frame)),
        "MAE":float(np.abs(error).mean()), "RMSE":float(np.sqrt(np.mean(error**2))),
        "WAPE":float(np.abs(error).sum()/max(float(np.abs(actual).sum()),1e-9)),
        "bias":float(error.sum()/max(float(actual.sum()),1e-9)),
        "actual_units":float(actual.sum()), "forecast_units":float(pred.sum())}

def run(examples, levels_path, train_origins, val_origin, test_origin):
    OUT.mkdir(parents=True, exist_ok=True)
    levels = json.loads(levels_path.read_text())
    evaluation = _load_evaluation(examples, val_origin, test_origin)
    validation = evaluation[evaluation.origin_index.eq(val_origin)].reset_index(drop=True)
    test = evaluation[evaluation.origin_index.eq(test_origin)].reset_index(drop=True)
    cols = base.FEATURES + ["target","seasonal_naive","origin_index","store_segment",
        "state_segment","category_segment","department_segment"]
    train_parts = []
    for batch in pq.ParquetFile(examples).iter_batches(batch_size=65536, columns=cols):
        part = batch.to_pandas()
        part = part[part.origin_index.isin(train_origins)]
        if not part.empty: train_parts.append(part)
    training = pd.concat(train_parts, ignore_index=True)
    del train_parts
    if len(training) < SAMPLE_ROWS:
        raise ValueError(f"Only {len(training):,} training rows; 200,000 required per run.")
    rows, best, best_score = [], None, float("inf")
    for run_no in range(1, RUNS+1):
        seed = SEED_BASE + run_no
        sample = stratified_sample(training, SAMPLE_ROWS, seed)
        model = base.make_model()
        model.set_params(random_state=seed)
        model.fit(_matrix(sample, levels), sample.target.astype(np.float32),
                  categorical_feature=base.CATS)
        m = _metrics(model, validation, levels, "validation")
        score = m["WAPE"] + .15 * abs(m["bias"])
        rows.append({"run":run_no,"seed":seed,"sample_rows":len(sample),
                     **{f"validation_{k}":v for k,v in m.items() if k!="split"},
                     "selection_score":score})
        print(f"run={run_no:02d}/20 seed={seed} WAPE={m['WAPE']:.5f} bias={m['bias']:.5f}", flush=True)
        if score < best_score:
            if best is not None: del best[0]
            best_score, best = score, (model, run_no, seed, m)
        else: del model
        del sample
        gc.collect()
    result = pd.DataFrame(rows)
    result.to_csv(OUT/"experiment_metrics.csv", index=False)
    metric_cols = ["validation_WAPE","validation_MAE","validation_RMSE","validation_bias","selection_score"]
    summary = result[metric_cols].agg(["mean","std","median","min","max"]).to_dict()
    (OUT/"experiment_summary.json").write_text(json.dumps({
        "runs":RUNS,"sample_rows_per_run":SAMPLE_ROWS,"seed_base":SEED_BASE,
        "training_origins":train_origins,"validation_origin":val_origin,
        "test_origin":test_origin,"selection_rule":"validation WAPE + 0.15 * abs(validation bias)",
        "metrics_summary":summary}, indent=2))
    selected, selected_run, selected_seed, val_metrics = best
    test_metrics = _metrics(selected, test, levels, "test")
    test_metrics.update({"selected_run":selected_run,"selected_seed":selected_seed})
    pd.DataFrame([test_metrics]).to_csv(OUT/"selected_model_test_metrics.csv", index=False)
    CANDIDATE.parent.mkdir(parents=True, exist_ok=True)
    selected.booster_.save_model(str(CANDIDATE))
    metadata = {"status":"candidate_not_promoted","active_model_untouched":str(base.MODEL/"m5_global_lightgbm_28d.txt"),
        "candidate_model":str(CANDIDATE),"selected_run":selected_run,"selected_seed":selected_seed,
        "sample_rows":SAMPLE_ROWS,"runs":RUNS,"training_origins":train_origins,
        "validation_origin":val_origin,"test_origin":test_origin,"features":base.FEATURES,
        "categorical_features":base.CATS,"category_code_maps":str(levels_path),
        "validation_metrics":val_metrics,"untouched_test_metrics":test_metrics,
        "promotion_policy":"Manual review only; active model and serving API are not modified."}
    (OUT/"candidate_model_metadata.json").write_text(json.dumps(metadata, indent=2))
    del selected, training, evaluation
    gc.collect()
    return metadata

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=RUNS)
    parser.add_argument("--sample-rows", type=int, default=SAMPLE_ROWS)
    args = parser.parse_args()
    if args.runs != RUNS or args.sample_rows != SAMPLE_ROWS:
        raise ValueError("This approved workflow requires exactly 20 runs and 200,000 rows/run.")
    source = base.source_file()
    dates = [c for c in pd.read_csv(source, nrows=0).columns if c.startswith("d_")]
    n = len(dates)
    cal = base.read_calendar(dates)
    train_origins = [n-365-1,n-273-1,n-181-1,n-89-1]
    val_origin, test_origin = n-56-1, n-28-1
    examples = OUT/"training_examples.parquet"
    examples.parent.mkdir(parents=True, exist_ok=True)
    base.build_examples(source, dates, cal, train_origins+[val_origin,test_origin], examples)
    try:
        run(examples, base.OUT/"category_code_maps.json", train_origins, val_origin, test_origin)
    finally:
        examples.unlink(missing_ok=True)

if __name__ == "__main__": main()
