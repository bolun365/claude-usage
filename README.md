# Claude Usage Report

A lightweight Python CLI tool that parses local Claude usage logs,
auto-syncs live model pricing, and generates clear daily/monthly token
and cost breakdown reports.

------------------------------------------------------------------------

## ✨ Features

-   📊 Daily token & cost breakdown
-   📆 Monthly aggregation
-   📈 Last 30 days summary
-   🤖 Per-model usage percentage
-   💰 Automatic pricing sync from LiteLLM
-   🧯 Fallback hardcoded pricing if network unavailable
-   ⚡ Zero dependencies (pure Python standard library)

------------------------------------------------------------------------

## 📦 What It Does

The script reads Claude CLI usage logs from:

    ~/.claude/projects/*/*.jsonl

It extracts:

-   Input tokens
-   Output tokens
-   Cache read tokens
-   Cache creation tokens
-   Model name
-   Timestamp

Then it:

-   Fetches latest Claude pricing from LiteLLM\
-   Calculates exact cost per day/month\
-   Outputs a formatted terminal report

------------------------------------------------------------------------

## 🖥 Example Output

pricing: live (litellm)
```
=== Monthly ===

Month             Input        $     Output        $    CacheRd        $    CacheCr        $      Total   $Total  Model
------------------------------------------------------------------------------------------------------------------------------------------
2026-02            125K   $0.568       800K    $16.2       349M     $147      18.1M    $96.3       368M     $260  <synthetic> 0%
                                                                                                                  claude-haiku 0%
                                                                                                                  claude-opus 16%
                                                                                                                  claude-opus 45%
                                                                                                                  claude-sonnet 9%
                                                                                                                  claude-sonnet 30%
------------------------------------------------------------------------------------------------------------------------------------------
Sum                125K   $0.568       800K    $16.2       349M     $147      18.1M    $96.3       368M     $260  <synthetic> 0%
                                                                                                                  claude-haiku 0%
                                                                                                                  claude-opus 16%
                                                                                                                  claude-opus 45%
                                                                                                                  claude-sonnet 9%
                                                                                                                  claude-sonnet 30%

=== Last 30 days (2026-01-28 ~ 2026-02-27) ===

Date              Input        $     Output        $    CacheRd        $    CacheCr        $      Total   $Total  Model
------------------------------------------------------------------------------------------------------------------------------------------
2026-02-03         4.7K   $0.023        147  $0.0037       1.8M   $0.921       155K   $0.969       2.0M    $1.92  claude-opus 100%
2026-02-04          598  $0.0019       141K    $2.12      29.4M    $8.83       2.8M    $11.0      32.3M    $21.9  <synthetic> 0%
                                                                                                                  claude-opus 1%
                                                                                                                  claude-sonnet 99%
2026-02-05        31.1K   $0.155      20.8K   $0.521      56.5M    $28.2       1.4M    $8.77      57.9M    $37.7  <synthetic> 0%
                                                                                                                  claude-opus 100%
2026-02-06         9.6K   $0.048      86.5K    $2.16      44.9M    $22.4       3.6M    $22.7      48.6M    $47.3  <synthetic> 0%
                                                                                                                  claude-opus 100%
2026-02-07         3.5K   $0.017      82.5K    $2.06      32.8M    $16.4       1.8M    $11.1      34.7M    $29.6  claude-opus 100%
2026-02-08          519  $0.0026      79.4K    $1.99      18.4M    $9.20       1.4M    $8.54      19.9M    $19.7  claude-opus 100%
2026-02-10        30.2K   $0.151      23.0K   $0.576       9.5M    $4.75       582K    $3.64      10.1M    $9.12  claude-opus 100%
2026-02-11           18  $0.0001         56  $0.0014       153K   $0.077      13.9K   $0.087       167K   $0.165  claude-opus 100%
2026-02-12        13.5K   $0.067      63.3K    $1.58      25.2M    $12.6       1.1M    $6.59      26.4M    $20.9  claude-opus 100%
2026-02-13         3.4K   $0.017      45.0K    $1.13      20.3M    $10.2       958K    $5.99      21.3M    $17.3  claude-opus 100%
2026-02-24           74  $0.0002       3.1K   $0.047       1.4M   $0.411      90.9K   $0.341       1.5M   $0.799  claude-sonnet 100%
2026-02-25        26.6K   $0.080      84.7K    $1.29      55.4M    $16.7       2.3M    $9.21      57.8M    $27.2  <synthetic> 0%
                                                                                                                  claude-opus 1%
                                                                                                                  claude-sonnet 99%
2026-02-26          424  $0.0013      88.9K    $1.40      25.9M    $8.12       823K    $3.40      26.8M    $12.9  claude-haiku 0%
                                                                                                                  claude-opus 7%
                                                                                                                  claude-sonnet 93%
2026-02-27          607  $0.0019      81.8K    $1.29      27.3M    $8.32       1.0M    $4.08      28.4M    $13.7  <synthetic> 0%
                                                                                                                  claude-opus 3%
                                                                                                                  claude-sonnet 97%
------------------------------------------------------------------------------------------------------------------------------------------
Sum                125K   $0.568       800K    $16.2       349M     $147      18.1M    $96.3       368M     $260  <synthetic> 0%
                                                                                                                  claude-haiku 0%
                                                                                                                  claude-opus 16%
                                                                                                                  claude-opus 45%
                                                                                                                  claude-sonnet 9%
                                                                                                                  claude-sonnet 30%

```

## 🚀 Installation

``` bash
git clone https://github.com/yourname/claude-usage-report.git
cd claude-usage-report
```

Python 3.8+ recommended.

------------------------------------------------------------------------

## ▶ Usage

``` bash
python report.py
```

------------------------------------------------------------------------

## 💰 Pricing Logic

1.  Attempts to fetch latest pricing from LiteLLM.
2.  Cached locally at:
    ~/.claude/claude_pricing_cache.json

3.  Falls back to hardcoded pricing if:
    -   Network unavailable
    -   Fetch fails
    -   Cache expired and refresh fails

Cache TTL: 24 hours

------------------------------------------------------------------------

## 📁 Data Source

Reads local Claude CLI logs:

    ~/.claude/projects/*/*.jsonl

-   No API calls to Claude
-   No external data transmission
-   Fully local analysis

------------------------------------------------------------------------

## 🔐 Privacy

-   100% local processing
-   No telemetry
-   No tracking
-   No external uploads

------------------------------------------------------------------------

## 📜 License

MIT License
