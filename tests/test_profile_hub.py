#!/usr/bin/env python3
"""profile-hub 回归测试：档案 / 基线 / 审计 / 知识包

不依赖 pytest / 真实数据库。直接运行：

    python tests/test_profile_hub.py
"""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "src"))
# 开发期：兄弟仓库用源码目录；正式使用请 pip install（见 README）
for _sib in ("dbt-core", "dbt-store", "dbt-know"):
    _p = _HERE.parent.parent / _sib / "src"
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

os.environ.setdefault("DBT_LOG_LEVEL", "ERROR")
_TMPDIR = tempfile.mkdtemp(prefix="dbt-profile_hub-")
os.environ.setdefault("DBT_STORE", os.path.join(_TMPDIR, "store.db"))

from dbcore.protocol import Result, ToolError  # noqa: E402

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASSED.append(name)
    else:
        FAILED.append(f"{name}  << {detail[:300] if detail else ''}")


def section(title: str) -> None:
    print(f"\n── {title}")


section("9. profile-hub 与跨 MCP 契约")
# ==================================================================
from profile_hub import server as PH  # noqa: E402

PH.upsert_instance_tool(instance_id="hub-test-1", dialect="mysql", version="8.0.32")
obs = PH.record_observation_tool("hub-test-1", "snapshot",
                                 {"metrics": {"connections_used": 42}}).to_dict()
check("观测写入", obs["ok"])
t = PH.tier_of_tool("hub-test-1").to_dict()
check("tier 查询", t["data"]["tier"] == "tier1", str(t["data"]["tier"]))
prof = PH.get_instance_profile("hub-test-1").to_dict()
check("实例画像", prof["data"]["known"])
PH.set_baseline_tool("hub-test-1", "connections_used", 40)
gb = PH.get_baseline_tool("hub-test-1", "connections_used").to_dict()
check("基线读写", gb["data"]["baselines"]["connections_used"]["value"] == 40)
st2 = PH.store_stats_tool().to_dict()
check("档案库统计", st2["data"]["counts"]["observations"] >= 1)

# 知识包导出/导入 —— 冷启动第二条解法
exp = PH.export_profile_tool().to_dict()
check("知识包导出", exp["ok"] and "instances" in exp["data"])
imp = PH.import_profile_tool(exp["data"], remap_to="hub-test-2").to_dict()
check("知识包导入", imp["ok"])
check("导入后可提升档位",
      PH.tier_of_tool("hub-test-2").to_dict()["data"]["tier"] in ("tier1", "tier2"),
      PH.tier_of_tool("hub-test-2").to_dict()["data"]["tier"])
try:
    PH.import_profile_tool({"schema": "wrong"})
    check("非法知识包被拒绝", False)
except ToolError:
    check("非法知识包被拒绝", True)
PH.record_audit_tool("test.tool", "审计测试")
check("审计写入", PH.query_audit().to_dict()["data"]["count"] >= 1)
PH.link_cross_instance_tool("hub-test-1", "hub-test-2", "same_business")
check("实例关联", PH.get_related_instances("hub-test-1").to_dict()["data"]["count"] >= 1)

# ------------------------------------------------------------------
# 工具粒度回归：query_observations 吸收 get_history 之后的能力
# ------------------------------------------------------------------
PH.record_observation_tool("hub-test-1", "review", {"verdict": "pass"})
_all_obs = PH.query_observations("hub-test-1").to_dict()
_only_snap = PH.query_observations("hub-test-1", kind="snapshot").to_dict()
check("观测查询：kind 不传返回全部", _all_obs["data"]["count"] >= 2,
      str(_all_obs["data"]["count"]))
check("观测查询：kind 可过滤（原 get_history 的能力）",
      0 < _only_snap["data"]["count"] < _all_obs["data"]["count"],
      f"{_only_snap['data']['count']} / {_all_obs['data']['count']}")
check("get_history 已并入 query_observations，不再是独立工具",
      "get_history" not in PH.TOOLS)

# ------------------------------------------------------------------
# 可用性门禁：每个工具必须有 docstring
# 缺了不会报错，但 tools 列表和 README 工具表会留下空白描述 ——
# 模型只能靠名字猜用途，等于工具白做。
# ------------------------------------------------------------------
import inspect  # noqa: E402

_undocumented = [n for n, f in PH.TOOLS.items() if not (inspect.getdoc(f) or "").strip()]
check("每个工具都有 docstring", not _undocumented, ", ".join(_undocumented))

# ==================================================================


# ==================================================================
print("\n" + "=" * 60)
print("通过 %d 项，失败 %d 项" % (len(PASSED), len(FAILED)))
if FAILED:
    print("\n失败明细：")
    for _f in FAILED:
        print("  ✗", _f)
    raise SystemExit(1)
print("全部通过")
