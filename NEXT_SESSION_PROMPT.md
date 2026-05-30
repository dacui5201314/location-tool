# Next Session Prompt — 2026-05-30

Project: `C:\Users\admin\location-tool`
GitHub: `https://github.com/dacui5201314/location-tool`

## 开门三件事

1. 读 `CURRENT_HANDOFF.md`（最新状态，今天全部更新过）
2. 读 `PROJECT_RULES.md`（产品原则、禁止事项）
3. 不读 `PROJECT_STATE.md` / `WORKING_SET.md` 旧章节（已过期）

## 当前基线

```
compileall → PASS
industry_rigor_rules → 2168 PASS, 0 FAIL
report_fact_guard → 147 PASS, 0 FAIL
```

## 本 session 重点变更

### 项目结构简化
- Web 前端 `frontend/` 已删除（17,000 行）
- 项目只剩 backend + uniapp + miniprogram
- 管理后台重建为 `backend/admin/index.html`（独立 HTML，访问 `/admin`）

### 管理后台 `/admin`
- 完整复刻旧 React 后台功能
- 系统设置含子标签：核心配置、UI、分享、二维码、SKU、Key 池、存储
- 业态规则从 industry_config.py 直接读取
- 微信支付配置嵌入核心配置页

### 微信支付
- 后端 JSAPI v3 完整链路代码已就绪
- 小程序充值页已接真实支付（不再显示"暂未开放"）
- 本地无法完整测试（需要公网 HTTPS notify_url）
- 代码路径：`routers/pay.py` → prepay + notify

### P0 修复
- 计费时序：AMap 成功 → commit 扣点，失败 → rollback
- location.py 接入 key 池
- B26 错误格式 / B27 billing refresh

### LLM 幻觉问题（C-4 验证）
- 小餐饮/宝鸡：LLM 编造假 POI（好又多、学校）
- P0 guard 拦截正确，但 retry 后仍编造
- 这是当前最大阻塞 — 等 Codex 审核给 prompt 层修复指令

## 下一步任务

1. **全面排查** — 管理后台各模块功能完整性走查
2. **管理后台完善** — 边界情况、错误处理、交互细节
3. **样本库完善** — 13 个业态补 substitute 列
4. **正式上线** — 部署到公网服务器，微信支付真机联调
