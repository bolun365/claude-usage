import glob, json, os, time, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta


def new_bucket():
    return {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}


# --- 定价自动更新 (来源: litellm model_prices_and_context_window.json) ---
_PRICING_CACHE_PATH = os.path.expanduser("~/.claude/claude_pricing_cache.json")
_LITELLM_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
_CACHE_TTL = 86400  # 24小时

# 兜底硬编码价格 (来源: costgoat.com/pricing/claude-api)
_FALLBACK_PRICING = [
    ("claude-opus-4-6",    5.00,  25.00),
    ("claude-opus-4-5",    5.00,  25.00),
    ("claude-opus-4-1",   15.00,  75.00),
    ("claude-opus-4",     15.00,  75.00),
    ("claude-sonnet-4-6",  3.00,  15.00),
    ("claude-sonnet-4-5",  3.00,  15.00),
    ("claude-sonnet-4",    3.00,  15.00),
    ("claude-sonnet-3-7",  3.00,  15.00),
    ("claude-sonnet-3-5",  3.00,  15.00),
    ("claude-sonnet-3",    3.00,  15.00),
    ("claude-haiku-4-5",   1.00,   5.00),
    ("claude-haiku-4",     1.00,   5.00),
    ("claude-haiku-3-5",   0.80,   4.00),
    ("claude-haiku-3",     0.25,   1.25),
]


def _fetch_pricing():
    """从 litellm 拉取最新 Claude 定价。
    返回 {model_id: (inp_per_M, out_per_M, cr_per_M, cc_per_M)} 或 None。
    cache 字段直接来自 litellm，无数据则为 0。
    """
    try:
        with urllib.request.urlopen(_LITELLM_URL, timeout=8) as r:
            raw = json.loads(r.read())
        pricing = {}
        for model_id, info in raw.items():
            if "claude" not in model_id.lower():
                continue
            inp = info.get("input_cost_per_token", 0)
            out = info.get("output_cost_per_token", 0)
            if inp <= 0 and out <= 0:
                continue
            cr = info.get("cache_read_input_token_cost", 0) or 0
            cc = info.get("cache_creation_input_token_cost", 0) or 0
            pricing[model_id.lower()] = (inp * 1e6, out * 1e6, cr * 1e6, cc * 1e6)
        return pricing if pricing else None
    except Exception:
        return None


def _load_pricing_cache():
    """读取本地缓存，若过期则尝试刷新；返回定价 dict 或 None。"""
    needs_refresh = True
    cached = None

    if os.path.exists(_PRICING_CACHE_PATH):
        try:
            with open(_PRICING_CACHE_PATH) as f:
                obj = json.load(f)
            if time.time() - obj.get("updated", 0) < _CACHE_TTL:
                needs_refresh = False
            cached = {k: tuple(v) for k, v in obj.get("pricing", {}).items()}
        except Exception:
            pass

    if needs_refresh:
        fresh = _fetch_pricing()
        if fresh:
            try:
                with open(_PRICING_CACHE_PATH, "w") as f:
                    json.dump({"updated": time.time(), "pricing": {k: list(v) for k, v in fresh.items()}}, f)
            except Exception:
                pass
            return fresh
        # 刷新失败，用旧缓存
        return cached

    return cached


_live_pricing = _load_pricing_cache()  # {model_id: (inp_per_M, out_per_M)}


def get_pricing(model):
    """返回 (inp_per_M, out_per_M, cr_per_M, cc_per_M)。
    cr/cc 来自 litellm 实测值；fallback 时 cr/cc 为 0（官网无此数据）。
    """
    m = model.lower()
    if _live_pricing:
        if m in _live_pricing:
            p = _live_pricing[m]
            return p if len(p) == 4 else (*p, 0, 0)
        best = max(
            (k for k in _live_pricing if m.startswith(k) or k.startswith(m)),
            key=len, default=None
        )
        if best:
            p = _live_pricing[best]
            return p if len(p) == 4 else (*p, 0, 0)
    # 兜底（costgoat.com 仅有 input/output，cache 无官方来源，置 0）
    for prefix, inp, out in _FALLBACK_PRICING:
        if m.startswith(prefix):
            return inp, out, 0, 0
    return 3.00, 15.00, 0, 0


def token_cost(tokens, model):
    inp_p, out_p, cr_p, cc_p = get_pricing(model)
    return {
        "input":        tokens["input"]        * inp_p / 1e6,
        "output":       tokens["output"]       * out_p / 1e6,
        "cache_read":   tokens["cache_read"]   * cr_p  / 1e6,
        "cache_create": tokens["cache_create"] * cc_p  / 1e6,
    }


# --- 读取使用数据 ---
daily       = defaultdict(new_bucket)
daily_model = defaultdict(lambda: defaultdict(new_bucket))
daily_cost  = defaultdict(new_bucket)

for fpath in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    with open(fpath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue

            msg = entry.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            ts    = entry.get("timestamp")
            model = msg.get("model", "unknown")
            if not usage or not ts:
                continue

            if isinstance(ts, (int, float)):
                if ts > 1e12:
                    ts = ts / 1000
                date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            else:
                date = str(ts)[:10]

            tokens = {
                "input":        usage.get("input_tokens", 0),
                "output":       usage.get("output_tokens", 0),
                "cache_read":   usage.get("cache_read_input_tokens", 0),
                "cache_create": usage.get("cache_creation_input_tokens", 0),
            }
            for k, v in tokens.items():
                daily[date][k]              += v
                daily_model[date][model][k] += v

            c = token_cost(tokens, model)
            for k in c:
                daily_cost[date][k] += c[k]


# --- 格式化 ---
def fmt(n):
    units = [(1e12, "T"), (1e9, "G"), (1e6, "M"), (1e3, "K")]
    for threshold, suffix in units:
        if n >= threshold:
            val = n / threshold
            return f"{val:.1f}{suffix}" if val < 100 else f"{val:.0f}{suffix}"
    return str(n)


def fmt_cost(c):
    if c == 0:      return "$0"
    if c >= 100:    return f"${c:.0f}"
    if c >= 10:     return f"${c:.1f}"
    if c >= 1:      return f"${c:.2f}"
    if c >= 0.01:   return f"${c:.3f}"
    return f"${c:.4f}"


def short_model(name):
    parts = name.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else name


def model_lines(model_data, total):
    if total == 0:
        return []
    # 按 short_model 合并后再算占比，避免同一系列多行
    by_short = defaultdict(new_bucket)
    for model, data in model_data.items():
        short = short_model(model)
        for k in data:
            by_short[short][k] += data[k]
    lines = []
    for short in sorted(by_short.keys()):
        if "synthetic" in short.lower():
            continue
        v = by_short[short]
        t = v["input"] + v["output"] + v["cache_read"] + v["cache_create"]
        pct = t / total * 100
        lines.append(f"{short} {pct:.0f}%")
    return lines


def print_header(label="Date"):
    print(
        f"{label:<12}"
        f" {'Input':>10} {'$':>8}"
        f" {'Output':>10} {'$':>8}"
        f" {'CacheRd':>10} {'$':>8}"
        f" {'CacheCr':>10} {'$':>8}"
        f" {'Total':>10} {'$Total':>8}"
        f"  Model"
    )
    print("-" * 138)


def print_row(label, v, cost, models=None):
    total      = v["input"] + v["output"] + v["cache_read"] + v["cache_create"]
    total_cost = cost["input"] + cost["output"] + cost["cache_read"] + cost["cache_create"]
    mlines     = model_lines(models, total) if models else []
    first_model = mlines[0] if mlines else ""
    row = (
        f"{label:<12}"
        f" {fmt(v['input']):>10} {fmt_cost(cost['input']):>8}"
        f" {fmt(v['output']):>10} {fmt_cost(cost['output']):>8}"
        f" {fmt(v['cache_read']):>10} {fmt_cost(cost['cache_read']):>8}"
        f" {fmt(v['cache_create']):>10} {fmt_cost(cost['cache_create']):>8}"
        f" {fmt(total):>10} {fmt_cost(total_cost):>8}"
    )
    print(f"{row}  {first_model}")
    pad = " " * len(row)
    for ml in mlines[1:]:
        print(f"{pad}  {ml}")


def sum_bucket(rows):
    s = new_bucket()
    for v in rows:
        for k in s:
            s[k] += v[k]
    return s


def merge_models(model_dicts):
    merged = defaultdict(new_bucket)
    for md in model_dicts:
        for model, v in md.items():
            for k in v:
                merged[model][k] += v[k]
    return dict(merged)


# --- Monthly ---
monthly       = defaultdict(new_bucket)
monthly_model = defaultdict(lambda: defaultdict(new_bucket))
monthly_cost  = defaultdict(new_bucket)

for d, v in daily.items():
    month = d[:7]
    for k in v:
        monthly[month][k] += v[k]
    for model, mv in daily_model[d].items():
        for k in mv:
            monthly_model[month][model][k] += mv[k]
    for k in daily_cost[d]:
        monthly_cost[month][k] += daily_cost[d][k]

pricing_src = "live (litellm)" if _live_pricing else "fallback (hardcoded)"
print(f"pricing: {pricing_src}\n")

print("=== Monthly ===\n")
print_header("Month")
for m in sorted(monthly.keys()):
    print_row(m, monthly[m], monthly_cost[m], monthly_model[m])
print("-" * 138)
print_row("Sum", sum_bucket(monthly.values()), sum_bucket(monthly_cost.values()), merge_models(monthly_model.values()))

# --- Last 30 days ---
today  = datetime.now().date()
cutoff = today - timedelta(days=30)

print(f"\n=== Last 30 days ({cutoff} ~ {today}) ===\n")
print_header()
recent        = {}
recent_models = {}
recent_costs  = {}
for d in sorted(daily.keys()):
    if datetime.strptime(d, "%Y-%m-%d").date() >= cutoff:
        recent[d]        = daily[d]
        recent_models[d] = daily_model[d]
        recent_costs[d]  = daily_cost[d]
        print_row(d, daily[d], daily_cost[d], daily_model[d])
print("-" * 138)
print_row("Sum", sum_bucket(recent.values()), sum_bucket(recent_costs.values()), merge_models(recent_models.values()))
