# Current Handoff - 2026-05-30

## Read This First

- Project: `C:\Users\admin\location-tool`
- Launch target: `uniapp` WeChat Mini Program
- Web `frontend/`: **已删除** — uni-app 唯一客户端
- GitHub: `https://github.com/dacui5201314/location-tool` (干净仓库)
- Admin Dashboard: `http://localhost:8000/admin` (独立 HTML，替代旧 React 后台)
- Latest commit: `8b9213f` — debug wechat pay error logging

## 项目结构

```
location-tool/
├── backend/
│   ├── admin/index.html      ← 管理后台（单文件，浏览器直接访问）
│   ├── main.py               ← FastAPI 入口
│   ├── routers/              ← 9 个路由模块
│   ├── services/             ← amap/billing/runtime_config/storage/poi_name_guard
│   ├── prompts/              ← location_analysis + industry_config（14 Master 模板）
│   ├── tests/                ← 2168 PASS / 147 PASS
│   └── storage/              ← 运行时文件
├── uniapp/                   ← 主力客户端（Vue3 + Vite → 微信小程序）
└── miniprogram/              ← 原生小程序 scaffold（登录参考，不开发）
```

## 当前工作状态

- 后端测试基线：compileall PASS / industry 2168 PASS / fact guard 147 PASS
- 管理后台 `/admin` — 8 个导航模块，功能对齐旧版 React 后台
- 微信支付后端（JSAPI v3）代码就绪，配置已填写，待部署到公网 HTTPS 后真机测试
- 小程序充值页面已接入真实支付流程（不再显示"暂未开放"）
- 业态规则页改为从 industry_config.py 读取，按 Master 模板分组展示
- 4 个页面已适配 iPhone safe-area

## 2026-05-30 完成清单

### P0 修复
- 计费扣点延后到 AMap 成功后 commit，失败 rollback
- location.py suggest/regeocode 接入 key 池
- BrandInput 受控组件 bug（随前端删除）

### 项目清理
- 删除 Web 前端 React（~17,000 行）
- 死代码清理 ~1,000 行（ai_providers 6文件 + business_profiles.py + config.py）
- B27 billing rowcount 修复
- B26 错误格式统一

### 管理后台（新建）
- 独立 HTML 文件，FastAPI `/admin` 路由 serve
- 8 模块：仪表盘、用户管理、系统设置、系统日志、兑换码、全局参数、操作记录、业态规则
- 系统设置含 7 个子标签：核心配置、UI 配置、分享配置、客服二维码、SKU 套餐、Key 池、存储配置
- 仪表盘含 15 天趋势柱状图 + 热门业态/品牌
- 业态规则从 industry_config.py 读取（14 Master + 57 映射）

### 微信支付
- 管理后台核心配置页：大模型、高德 Key、System Prompt、微信支付密钥一站式管理
- 后端 prepay 接口增强调试日志
- 小程序充值页接入真实支付：选套餐 → createPrepay → requestPayment
- 配置已填写完毕，待公网 HTTPS 环境联调

### 文档
- README 重写（uni-app 为主，宝塔部署指南）
- uniapp/miniprogram README 更新
- 交接文档更新

## C-4 真实报告验证

- 业态：小餐饮 | 地址：陕二丫擀面皮(兰宝小区店) | 宝鸡
- 结果：AMap 成功、计费链路正确（扣点→退款）、报告未保存
- 失败原因：LLM 两次编造假 POI 名称（好又多、学校、住宅小区），P0 guard 拦截但 retry 后仍未通过

## 测试基线

```
python -m compileall backend              → PASS
python tests/check_industry_rigor_rules.py → 2168 PASS, 0 FAIL
python tests/check_report_fact_guard.py    → 147 PASS, 0 FAIL
```

## 下一步（等 Codex 额度恢复后）

1. **全面排查** — 管理后台功能完整性验证
2. **管理后台完善** — 细节打磨、边界情况处理
3. **样本库完善** — 13 个业态补 substitute 列
4. **正式上线**
