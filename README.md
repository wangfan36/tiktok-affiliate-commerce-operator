# TikTok Affiliate Commerce Operator

面向美国 TikTok Shop 达人挂车业务的 Codex Skill。它把 FastMoss 商品与达人数据、
利润优先的选品方法、受控创意实验、PixVerse 素材生产以及发布后漏斗复盘整合为一套
可审计工作流。

## 能力

- 按美国本地仓、在售、价格、佣金、评分、库存证据和 AI 素材适配性筛选商品。
- 使用两个完整 28 天窗口，按绝对销量增量而非增长率排名。
- 计算毛佣金、退款及成本后的净佣金，以及有同口径漏斗时的净佣金 GPM。
- 分析商品对应达人、受众重合度及竞品视频的抽象商业模式。
- 生成单变量 A/B/C 脚本、UGC 导演方案、PixVerse 任务和发布前审核。
- 从留存、点击、订单、佣金到净收益定位发布后的首个失败环节。

商品决策统一使用 `ELIGIBLE / HOLD / REJECT`，经营动作统一使用
`TEST / SCALE / PAUSE / MONITOR / INVESTIGATE / RETIRE`。

## 安装

将仓库克隆到 Codex Skills 目录：

```powershell
git clone https://github.com/wangfan36/tiktok-affiliate-commerce-operator.git `
  "$env:USERPROFILE\.codex\skills\tiktok-affiliate-commerce-operator"
```

仓库为私有时，克隆前需要完成 GitHub 身份验证。

## 使用

```text
$tiktok-affiliate-commerce-operator 查找近期美国适合AI素材的达人挂车商品，
并按绝对销量增长和预期净佣金排名。
```

支持六种模式：选品扫描、商品深挖、达人匹配、创意生产、发布前审核和发布后优化。
详细路由与权限边界见 [`SKILL.md`](SKILL.md)。

## 数据与工具

- FastMoss 是默认商品、销量、达人和竞品视频数据源；需要用户自己的有效授权。
- PixVerse 是默认视频生成通道，但付费生成与本地文件上传必须单独确认。
- Clipcat 默认关闭，只有用户在当前任务明确要求时才能启用。
- 商品页面、TikTok 官方政策和第一方账户数据优先于第三方估算。

仓库不包含 API Key、Cookie、浏览器会话、客户数据或私人联系方式。任何凭据都应通过
工具自身的安全认证流程配置，不得写入 Skill、命令参数或运营台账。

## 排名程序

```powershell
python scripts\rank_candidates.py candidate-input.json --output ranked.json
```

输入格式和收益公式见
[`references/selection-and-economics.md`](references/selection-and-economics.md)。程序仅使用
Python 标准库，最多处理 30 个候选商品，并把历史不足、日期缺失或库存证据不足的商品
置为 `HOLD`。

## 验证

```powershell
$env:PYTHONUTF8 = "1"
python -m unittest discover -s tests -v
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" .
```

当前版本包含 18 项离线单元与行为测试。

## 权限边界

Skill 不会自主发布视频、联系达人、寄样、修改商品、投流、上传本地素材或产生付费任务。
这些操作都要求用户针对当前动作明确授权。私有运营状态也只会在用户明确要求保存后创建。
