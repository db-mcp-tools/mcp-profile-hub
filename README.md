# mcp-profile-hub

**档案中枢** · MCP Server

> 所有 MCP 的唯一数据落点 —— 也是「每次交付都在积累」这件事的物理载体。

## 安装（按需，不必装其他 MCP）

```bash
pip install ./mcp-profile-hub              # 在工具链根目录下执行
pip install "./mcp-profile-hub[mysql]"     # 需要连库时补驱动，或 [postgres]
```

会自动带上它需要的共享库：`dbt-core`（指纹/协议）、`dbt-store`（真正干活的存储库）、`dbt-know`（指标字典）。**不会**带其他 MCP。

## 挂到 MCP 客户端

```json
{
  "mcpServers": {
    "profile-hub": {
      "command": "python",
      "args": ["-m", "profile_hub"],
      "env": { "DBT_STORE": "~/.dbtoolchain" }
    }
  }
}
```

按你的客户端（Claude Desktop / Cursor / Cline 等）说明，把这段合并到对应的 `mcpServers` 配置里。

命令行调试（不挂客户端也能用）：

```bash
dbt-profile-hub tools
dbt-profile-hub call <tool> --args '{"sql": "SELECT 1"}'
```

## 工具（24）

| 工具 | 作用 |
|---|---|
| `compute_baselines` | 从已有观测计算**标量基线**（每项指标一个常态值）。单点不算基线，样本不足跳过。 |
| `compute_metric_baselines` | 从 raw 指标样本计算**分位数基线**（p50/p95/p99）。样本不足的指标跳过，绝不编造。 |
| `export_profile` | ★ 导出脱敏知识包。 |
| `finding_stats` | 技术债总览（月报素材）：开放/已修复/误报率 + 明细清单。 |
| `get_baseline` | 读取已存在的基线；metric 不传则返回该实例全部基线。 |
| `get_instance_profile` | 实例全貌 —— 给 LLM 和客户看的完整画像（元数据 + 档位 + 最近观测 + 基线 + 技术债）。 |
| `get_related_instances` | 查与该实例关联的其他实例（同一业务的异构库、主从、上下游）。 |
| `import_profile` | ★ 导入知识包 —— 冷启动的第二条解法。 |
| `link_cross_instance` | 异构实例关联（同一业务跨多个引擎）—— 这是通用工具做不到的事。 |
| `list_incidents` | 事故单清单（含诊断结论与时间线）。 |
| `list_instances` | 列出档案库里登记过的实例（id / 方言 / 版本 / 标签 / 档位）。 |
| `list_metrics` | 列出某引擎支持的逻辑指标，方便确认能采到什么。 |
| `metric_series` | 读取一维指标时间序列（趋势/容量/异常检测的统一输入）。 |
| `query_audit` | 按时间倒序查审计留痕；instance_id 不传则跨实例返回。 |
| `query_observations` | 按时间倒序查观测记录；kind 不传则返回全部类型。 |
| `record_audit` | 写一条审计留痕：谁在什么时候对哪个实例做了什么。 |
| `record_finding` | 登记/累加一条体检发现（技术债账本）。重复出现自动 occurrences+1。 |
| `record_observation` | 写入一次观测。**这是 Tier0 → Tier2 升级的唯一写入点** |
| `set_baseline` | 手工设定一个基线值（人工校准用）。 |
| `store_stats` | 档案库自身的情况：文件大小、各表行数。 |
| `tier_of` | 查询实例当前的能力档位。**要求 Tier2 的能力会用它来明确报错，而不是悄悄降级** |
| `top_sql` | 出现次数最多的 SQL（一条 SQL 的一生）。 |
| `transition_finding` | 推进发现的生命周期：open→confirmed→fixing→fixed→verified / dismissed（状态机校验）。 |
| `upsert_instance` | 注册/更新实例元数据。url 会参与脱敏处理，密码绝不落盘。 |

## 闭环

`upsert_instance` 建档 → `record_observation` → `compute_metric_baselines` 分位数基线 → `record_finding` / `transition_finding` 技术债账本 → `finding_stats` 月报口径 → `export_profile` 知识包

## Tier（冷启动保证）

`tier_of` 直接给出实例当前档位（tier1 = 一次观测 / tier2 = ≥2 次且跨 ≥7 天）。

## 边界：这个仓不做什么

本 MCP **不含任何判断逻辑**，只负责把其他 MCP 产生的档案读写、聚合、导出。
其他 MCP 不通过 MCP 协议调它，而是直接依赖 `dbt-store` 这个库写同一个 SQLite —— 少一跳，且装不装 hub 都不影响记录。

## 开发

```bash
python tests/test_profile_hub.py      # 不需要 pytest，也不需要数据库
```
