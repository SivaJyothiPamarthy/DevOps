#!/usr/bin/env python3
"""Summarise an nginx access log (combined format + $request_time at the end).

Usage: analyze.py access.log      or      cat access.log | analyze.py -

Talking points for the interview:
- Streams the file line by line => O(1) memory for counters, works on GB-sized logs
  (only latencies are kept; for huge files use a t-digest / histogram instead).
- Regex is compiled once; malformed lines are counted, not fatal.
- Query strings are stripped so /orders?page=2 groups with /orders.
"""

import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

LINE_RE = re.compile(
    r"^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "
    r'"(?P<method>[A-Z]+) (?P<path>\S+) [^"]*" '
    r"(?P<status>\d{3}) \S+ "
    r'"[^"]*" "[^"]*" '
    r"(?P<rt>\d+(?:\.\d+)?)$"
)


@dataclass
class Report:
    total: int = 0
    malformed: int = 0
    ips: Counter = field(default_factory=Counter)
    status: Counter = field(default_factory=Counter)
    latencies: list[float] = field(default_factory=list)
    endpoint_latency: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    @property
    def error_rate_5xx(self) -> float:
        errors = sum(c for s, c in self.status.items() if s >= 500)
        return errors / self.total if self.total else 0.0

    def percentile(self, p: float) -> float:
        """Nearest-rank percentile."""
        if not self.latencies:
            return 0.0
        data = sorted(self.latencies)
        rank = max(1, math.ceil(p / 100 * len(data)))
        return data[rank - 1]

    def slowest_endpoint(self) -> tuple[str, float] | None:
        if not self.endpoint_latency:
            return None
        avg = {ep: sum(v) / len(v) for ep, v in self.endpoint_latency.items()}
        ep = max(avg, key=avg.get)
        return ep, avg[ep]


def analyze(lines) -> Report:
    r = Report()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = LINE_RE.match(line)
        if not m:
            r.malformed += 1
            continue
        r.total += 1
        rt = float(m["rt"])
        path = m["path"].split("?", 1)[0]
        r.ips[m["ip"]] += 1
        r.status[int(m["status"])] += 1
        r.latencies.append(rt)
        r.endpoint_latency[f'{m["method"]} {path}'].append(rt)
    return r


def render(r: Report) -> str:
    out = [
        f"Total requests : {r.total}",
        f"Malformed lines: {r.malformed}",
        f"5xx error rate : {r.error_rate_5xx:.2%}",
        f"p95 latency    : {r.percentile(95) * 1000:.0f} ms",
        "Top 5 IPs      :",
    ]
    out += [f"  {ip:<15} {n}" for ip, n in r.ips.most_common(5)]
    slow = r.slowest_endpoint()
    if slow:
        out.append(f"Slowest (avg)  : {slow[0]} ({slow[1] * 1000:.0f} ms)")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "-":
        report = analyze(sys.stdin)
    else:
        with open(argv[1], encoding="utf-8", errors="replace") as fh:
            report = analyze(fh)
    print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
