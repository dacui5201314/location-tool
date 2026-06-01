# Claude Code 修复指令 - 2026-06-01

项目：`C:\Users\admin\location-tool`

执行角色：Claude Code 负责代码修改与自测；Codex 负责后续复核。  
本轮目标：修复上线闭环、资损、安全、后台基础可用性和文档错配。  
本轮禁止：不要改报告评分、POI 分类、行业规则、prompt 语义、`report_fact_guard`、财务测算口径；不要调用 AMap/LLM 生成真实报告；不要 push。

## 执行前必读

1. 先执行 `git status --short`，确认当前工作树状态。
2. 当前允许改动范围优先限制在：
   - `.gitignore`
   - `uniapp/src/pages/profile/recharge.vue`
   - `uniapp/src/utils/api.js`
   - `backend/admin/index.html`
   - `backend/services/billing_service.py`
   - `backend/routers/location.py`
   - `backend/services/amap_service.py`
   - `README.md`
   - `PROJECT_RULES.md`
   - `PROJECT_PROGRESS.yml`
   - `CURRENT_HANDOFF.md`
   - `uniapp/README.md`
3. 如必须改其他文件，先在执行结果中说明原因。

## P0 - 必须立即修

### P0-1 支付闭环防假成功

文件：
- `uniapp/src/pages/profile/recharge.vue`
- `uniapp/src/utils/api.js`
- `backend/routers/pay.py` 如确有必要

问题：当前前端 `requestPayment` 成功后直接显示“支付成功”并刷新 profile，但没有调用 `queryOrder(out_trade_no)` 确认后端 notify 已到账。notify 延迟或失败时会造成“用户看到成功，但余额/会员未到账”的假成功。

修复要求：
- 保持流程为：`createPrepay -> requestPayment -> queryOrder(out_trade_no) -> fetchProfile`。
- 只有 `queryOrder` 返回订单 `status === "PAID"` 时，才能显示“支付成功”。
- `requestPayment` 取消时显示“支付已取消”，不得刷新为成功。
- `requestPayment` 成功但 `queryOrder` 未确认 PAID 时，显示“支付确认中，请稍后刷新”或等价文案，不得显示成功。
- 可以做短轮询，例如 5-8 次、每次间隔 1-2 秒；不要无限轮询。
- 保留并复用现有 `api.queryOrder(outTradeNo)`，不要新增重复 API。

验收：
- 未收到 notify 时，前端不显示支付成功。
- notify 到账后，查询订单为 PAID，余额/会员刷新。
- 取消支付不创建成功态。

### P0-2 .gitignore 防止本地数据入库

文件：
- `.gitignore`

添加忽略：

```gitignore
backend/location_tool.db
backend/location_tool.db-wal
backend/location_tool.db-shm
backend/storage/
__pycache__/
*.pyc
```

验收：
- `git ls-files backend/.env .env backend/location_tool.db backend/storage` 输出为空。
- `git status --short` 不出现数据库、报告存储、pyc、`__pycache__`。

### P0-3 管理后台用户搜索参数修复

文件：
- `backend/admin/index.html`
- `backend/routers/admin.py` 仅在需要兼容时修改

问题：后台用户列表前端发送 `search=`，后端 `GET /api/admin/users` 接收 `phone=`，导致搜索无效。

修复要求：
- 优先将前端请求改为 `phone=`。
- 如希望兼容旧链接，可以后端同时接受 `search` 并映射到 `phone`，但不要做大改。

验收：
- 在后台用户管理输入手机号或用户 ID，返回过滤结果。
- 空搜索仍显示分页用户列表。

### P0-4 后台 innerHTML 字段转义

文件：
- `backend/admin/index.html`

问题：后台多个列表直接将接口返回字段拼入 `innerHTML`，SKU label/badge/desc、Key 名称、日志、CDK、行业名等存在配置型 XSS 风险。

修复要求：
- 增加统一 `esc(value)` helper。
- 所有由接口返回并进入 HTML 字符串的文本字段必须转义。
- URL 字段至少转义双引号和尖括号；如用于 `src`，避免直接拼接未清洗的 `javascript:`。
- 不要求本轮重构为 DOM API，但不能留下明显未转义的后台配置字段。

验收：
- SKU 名称填入 `<img src=x onerror=alert(1)>` 时，页面显示文本，不执行脚本。
- Key 名称、分享标题、CDK 使用者、操作日志、行业名同理。

## P1 - 高优先级

### P1-1 匿名设备 ID 去硬编码

文件：
- `uniapp/src/utils/api.js`

问题：`ensureAnonToken()` 使用固定 `device_id=uni-default`，所有匿名用户共享同一设备 ID，影响反滥用。

修复要求：
- 首次启动生成随机设备 ID，写入 `uni.setStorageSync`。
- 后续复用该 ID。
- 不要使用手机号、openid、真实设备敏感标识拼接。
- 建议格式：`uni_<timestamp>_<random>`。

验收：
- 清空 storage 后首次调用会生成新 ID。
- 后续调用复用同一 ID。

### P1-2 退款幂等保护

文件：
- `backend/services/billing_service.py`
- `backend/main.py` 仅在传入幂等 key 时修改

问题：`refund_credits` 无条件加余额。虽然 `main.py` 当前有 `_refund_processed`，但函数本身缺少幂等保护，同一失败链路重复触发可能重复补点。

修复要求：
- 给 `refund_credits` 增加可选 `idempotency_key` 参数。
- 若传入 key，退款前先检查同一用户是否已有对应 REFUND 记录；已有则直接返回，不再加余额。
- 不强制数据库 migration；可将 key 写入 `BillingRecord.reason` 的稳定前缀，例如 `AUTO_REFUND:<key>:<reason>`。
- 保持现有调用兼容，不破坏未传 key 的旧路径。
- `main.py` 中 LLM/JSON/DB 保存失败退款应传入稳定 key，例如当前分析请求可用 `current_user_id + req.address + timestamp/record context`。如果没有稳定 request id，就至少避免在同一 event_stream 内重复退款。

验收：
- 同一 key 调用两次，只增加一次余额，只写一条有效 REFUND。
- 未传 key 的旧调用仍可工作。

### P1-3 地址联想/反查使用完整 Key 池重试

文件：
- `backend/routers/location.py`
- `backend/services/amap_service.py`

问题：`location.py` 当前只从 Key 池取第一个 key，不等于完整 failover。分析链路的 `AmapService._request` 才有多 key retry。

修复要求：
- 复用 `AmapService._request` 或抽出公共 key retry helper。
- `/api/location/suggest` 和 `/api/location/regeocode` 在 QPS/日限额类错误时尝试下一个 key。
- 不要把完整 key、URL query、security secret 打进日志。
- 保留现有返回格式 `{ok, data/error, source}`。

验收：
- 第一个 key 日限额/QPS 时自动尝试下一个 key。
- key 全部失败时返回清晰错误。

### P1-4 文档统一，避免后续误修

文件：
- `README.md`
- `PROJECT_RULES.md`
- `PROJECT_PROGRESS.yml`
- `CURRENT_HANDOFF.md`
- `uniapp/README.md`

修复要求：
- 统一描述：`frontend/` 已删除，`uniapp` 是唯一客户端。
- 管理后台是 `/admin` 独立 HTML，不是只通过 Swagger 操作。
- `uniapp/README.md` 中微信支付状态改为：前端已接入真实支付，但需 `queryOrder` 闭环和公网 HTTPS 真机验收。
- README Nginx 示例补 `/admin` 代理。
- 更新 `CURRENT_HANDOFF.md` 的 latest commit 描述，不要继续写旧 commit 为最新。
- 删除或标注过期的 React/Vite 前端构建说明。

验收：
- `rg "frontend|React|Swagger UI|uni-app 端待接" README.md PROJECT_RULES.md PROJECT_PROGRESS.yml CURRENT_HANDOFF.md uniapp/README.md` 后，剩余命中必须是明确的历史说明或“已删除/已过期”语境。

## P2 - 上线前补强

### P2-1 管理后台信息架构轻整理

不要大改视觉。只做轻量归类和文案修正：
- 核心密钥
- 微信支付
- 展示与客服
- 套餐与兑换
- 高德 Key 池
- 存储配置

目标：减少“系统设置太混”的问题，方便上线配置。

### P2-2 关键路径测试或手工验收记录

至少在执行结果中列出：
- 支付未配置态
- 支付取消态
- 支付 requestPayment 成功但 queryOrder 未 PAID
- 支付 PAID 后余额/会员刷新
- 用户搜索
- SKU XSS 文本转义
- 匿名 device_id 生成

## C-4 报告幻觉 - 暂不在本轮修

当前 C-4 小餐饮样本存在 LLM 编造假 POI 的问题。此问题重要，但本轮不要混修。

后续单独任务流程：
1. 读取 `backend/c4_test.json` 和失败日志，确认编造项来源。
2. 只读审计 `main.py` 中 fact_errors 注入 retry prompt 的位置。
3. 如需改，只允许窄改 retry 修正指令和对应 guard 测试。
4. 未经用户明确授权，不调用 AMap/LLM 重新生成真实报告。

## 最终验证命令

按顺序执行并把结果贴回：

```powershell
git status --short
python -m compileall backend
python backend/tests/check_industry_rigor_rules.py
python backend/tests/check_report_fact_guard.py
cd uniapp
npm run build:mp-weixin
cd ..
rg "unlock-pdf|/download" uniapp/src
rg "frontend|React|Swagger UI|uni-app 端待接" README.md PROJECT_RULES.md PROJECT_PROGRESS.yml CURRENT_HANDOFF.md uniapp/README.md
git status --short
```

如果本机 `python` 不可用，使用项目既有可用解释器路径或 `uv run python`，但要在结果中说明实际命令。

## 交付格式

Claude Code 执行完后，请输出：

1. 修改文件列表。
2. 每个 P0/P1/P2 项的处理结果。
3. 未完成项和原因。
4. 验证命令完整输出摘要。
5. `git diff --stat`。
6. 是否存在新未跟踪文件。

