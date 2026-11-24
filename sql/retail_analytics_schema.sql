-- Retail Decision Intelligence analytical mart.
-- Raw M5 ZIP remains in private Supabase Storage; this schema stores only
-- the selected, cleaned item-store-day panel and decision outputs.
create schema if not exists retail;
revoke all on schema retail from public, anon, authenticated;
grant usage on schema retail to service_role;

create table if not exists retail.dataset_runs (
  run_id uuid primary key default gen_random_uuid(),
  source_bucket text not null,
  source_object text not null,
  dataset_version text not null,
  row_count bigint not null check (row_count >= 0),
  series_count integer not null check (series_count >= 0),
  start_date date,
  end_date date,
  loaded_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);
create table if not exists retail.dim_product (
  item_id text primary key, dept_id text not null, cat_id text not null
);
create table if not exists retail.dim_store (
  store_id text primary key, state_id text not null
);
create table if not exists retail.dim_date (
  calendar_date date primary key, d text not null, weekday text, wday smallint,
  month smallint, year smallint, wm_yr_wk integer,
  event_name_1 text, event_type_1 text, event_name_2 text, event_type_2 text,
  snap_ca boolean, snap_tx boolean, snap_wi boolean
);
create table if not exists retail.fact_daily_demand (
  run_id uuid not null references retail.dataset_runs(run_id) on delete cascade,
  store_id text not null references retail.dim_store(store_id),
  item_id text not null references retail.dim_product(item_id),
  calendar_date date not null references retail.dim_date(calendar_date),
  demand integer not null check (demand >= 0),
  sell_price numeric(12,4),
  primary key (run_id, store_id, item_id, calendar_date)
);
create index if not exists ix_fact_daily_demand_item_date on retail.fact_daily_demand(item_id, calendar_date);
create index if not exists ix_fact_daily_demand_store_date on retail.fact_daily_demand(store_id, calendar_date);
create index if not exists ix_fact_daily_demand_series_date on retail.fact_daily_demand(store_id, item_id, calendar_date);
create index if not exists ix_fact_daily_demand_run on retail.fact_daily_demand(run_id);

create table if not exists retail.model_evaluation (
  evaluation_id bigserial primary key, evaluation_run text not null,
  model_name text not null, demand_segment text not null default 'all',
  fold integer, sample_count bigint not null check (sample_count >= 0),
  mae double precision, rmse double precision, wape double precision,
  bias double precision, evaluated_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb,
  unique (evaluation_run, model_name, demand_segment, fold)
);
create index if not exists ix_model_evaluation_latest on retail.model_evaluation(evaluated_at desc);

create table if not exists retail.forecast_runs (
  forecast_run_id uuid primary key default gen_random_uuid(),
  model_name text not null, horizon_days integer not null check (horizon_days > 0),
  nominal_coverage numeric(5,4), interval_method text,
  created_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb
);
create table if not exists retail.forecast_predictions (
  forecast_run_id uuid not null references retail.forecast_runs(forecast_run_id) on delete cascade,
  store_id text not null, item_id text not null, forecast_date date not null,
  prediction numeric(14,4) not null check (prediction >= 0),
  lower_bound numeric(14,4), upper_bound numeric(14,4),
  primary key (forecast_run_id, store_id, item_id, forecast_date),
  check (lower_bound is null or lower_bound >= 0),
  check (upper_bound is null or upper_bound >= prediction)
);
create index if not exists ix_forecast_predictions_series_date on retail.forecast_predictions(store_id, item_id, forecast_date);

create table if not exists retail.inventory_scenarios (
  scenario_id uuid primary key default gen_random_uuid(),
  run_id uuid references retail.dataset_runs(run_id),
  store_id text not null, item_id text not null,
  current_inventory numeric(14,3) not null check (current_inventory >= 0),
  lead_time_days integer not null check (lead_time_days >= 0),
  review_period_days integer not null check (review_period_days > 0),
  service_level numeric(5,4) not null check (service_level > 0.5 and service_level < 0.999),
  unit_holding_cost numeric(14,4) not null default 0 check (unit_holding_cost >= 0),
  ordering_cost numeric(14,4) not null default 0 check (ordering_cost >= 0),
  stockout_cost numeric(14,4) not null default 0 check (stockout_cost >= 0),
  mean_daily_demand numeric(14,4), demand_std numeric(14,4),
  safety_stock numeric(14,4), reorder_point numeric(14,4),
  recommended_order_quantity numeric(14,4),
  assumptions jsonb not null default '{}'::jsonb, created_at timestamptz not null default now()
);
create index if not exists ix_inventory_scenarios_created on retail.inventory_scenarios(created_at desc);

create or replace view retail.v_product_store_performance as
with latest as (select run_id from retail.dataset_runs order by loaded_at desc limit 1)
select f.run_id, f.item_id, p.dept_id, p.cat_id, f.store_id, s.state_id,
       count(*) as observed_days, sum(f.demand)::bigint as total_units,
       avg(f.demand)::numeric(14,4) as avg_daily_demand,
       stddev_samp(f.demand)::numeric(14,4) as demand_std,
       case when avg(f.demand)>0 then stddev_samp(f.demand)/avg(f.demand) end as demand_cv,
       avg(f.sell_price)::numeric(14,4) as avg_sell_price,
       sum(case when f.demand=0 then 1 else 0 end)::numeric/nullif(count(*),0) as zero_demand_rate
from retail.fact_daily_demand f join latest l on l.run_id=f.run_id
join retail.dim_product p on p.item_id=f.item_id
join retail.dim_store s on s.store_id=f.store_id
group by f.run_id,f.item_id,p.dept_id,p.cat_id,f.store_id,s.state_id;

create or replace view retail.v_demand_seasonality as
with latest as (select run_id from retail.dataset_runs order by loaded_at desc limit 1)
select f.store_id,f.item_id,d.weekday,d.wday,d.month,d.year,
       avg(f.demand)::numeric(14,4) as avg_demand,
       sum(f.demand)::bigint as total_demand,count(*) as observations
from retail.fact_daily_demand f join latest l on l.run_id=f.run_id
join retail.dim_date d on d.calendar_date=f.calendar_date
group by f.store_id,f.item_id,d.weekday,d.wday,d.month,d.year;

create or replace view retail.v_inventory_demand_profile as
with latest as (select run_id from retail.dataset_runs order by loaded_at desc limit 1)
select f.store_id,f.item_id,avg(f.demand)::numeric(14,4) as mean_daily_demand,
       stddev_samp(f.demand)::numeric(14,4) as demand_std,
       case when avg(f.demand)>0 then stddev_samp(f.demand)/avg(f.demand) end as coefficient_of_variation,
       avg(case when f.demand=0 then 1.0 else 0.0 end)::numeric(8,5) as zero_demand_rate,
       count(*) as observed_days,sum(f.demand)::bigint as total_demand
from retail.fact_daily_demand f join latest l on l.run_id=f.run_id
group by f.store_id,f.item_id;

alter table retail.dataset_runs enable row level security;
alter table retail.dim_product enable row level security;
alter table retail.dim_store enable row level security;
alter table retail.dim_date enable row level security;
alter table retail.fact_daily_demand enable row level security;
alter table retail.model_evaluation enable row level security;
alter table retail.forecast_runs enable row level security;
alter table retail.forecast_predictions enable row level security;
alter table retail.inventory_scenarios enable row level security;
revoke all on all tables in schema retail from public,anon,authenticated;
grant select,insert,update,delete on all tables in schema retail to service_role;
grant usage,select on all sequences in schema retail to service_role;
