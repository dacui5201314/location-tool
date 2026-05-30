# Next Session Prompt — 2026-05-30

Project: `C:\Users\admin\location-tool`
GitHub: `https://github.com/dacui5201314/location-tool` (干净仓库)

## 开门三件事

1. 读 `PROJECT_RULES.md`（产品原则、禁止事项）
2. 读 `CURRENT_HANDOFF.md`（最新状态）
3. 不读 `PROJECT_STATE.md` / `WORKING_SET.md` 旧章节（已过期）

## 当前基线

- compileall: PASS
- industry_rigor_rules: 2168 PASS, 0 FAIL
- report_fact_guard: 147 PASS, 0 FAIL

## 首要任务：LLM POI 名称幻觉

**C-4 验证结果**：小餐饮/宝鸡，LLM 两次生成均编造不存在的 POI（好又多、学校、住宅小区）。
P0 guard 正确拦截并退款，但 retry 后仍然编造，报告无法保存。

**需要 Codex 审核后给出指令**：
- System prompt 层如何约束 LLM 只引用 real_data 中的真实 POI
- 是否需要更强的 retry 策略
- Python 层是否可以做更严格的后处理

## 次要任务：微信支付联调

用户下午会填入真实微信支付商户密钥。需要：
- 测试 `/api/pay/wx-prepay` 生成预支付订单
- 测试 `/api/pay/wx-notify` 支付回调验签
- uniapp 端 `requestPayment` 拉起收银台

## Web 前端已删除

`frontend/` 目录已不存在。uni-app 是唯一客户端。管理后台通过 Swagger `/docs` 操作。

## 今天已完成的修复

- 计费时序：AMap 成功后 commit，失败 rollback
- location.py 接入 key 池
- 死代码清理 ~1000 行
- B26/B27 修复
- safe-area 适配
- 全部文档更新
- GitHub 仓库重建

不要重复执行以上修复。
