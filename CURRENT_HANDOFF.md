# Current Handoff - 2026-05-30

## Read This First

- Project: `C:\Users\admin\location-tool`
- Launch target: `uniapp` WeChat Mini Program
- Web `frontend/`: **已删除** — uni-app 是唯一客户端
- GitHub: `https://github.com/dacui5201314/location-tool` (干净仓库，重新上传)
- Latest commit: `3073dab` — docs: update uniapp/miniprogram READMEs

## 当前工作状态

- 后端 FastAPI 运行正常，测试基线：compileall PASS / industry 2168 PASS / fact guard 147 PASS
- uni-app 小程序：地址联想、SSE 分析、登录/充值/CDK 均已集成
- 管理后台功能完整，通过 Swagger `/docs` 操作（key 池、SKU、业态配置、用户管理）
- 微信支付后端（JSAPI v3）已就绪，**待填入真实商户密钥后联调**
- 报告分享（share_token）正常
- 四个页面已适配 iPhone safe-area

## 2026-05-30 今日完成

1. **P0 修复** — 计费扣点延后到 AMap 成功后 commit，失败 rollback（不再丢点）
2. **P0 修复** — location.py suggest/regeocode 接入 key 池，配额自动切换
3. **P0 修复** — BrandInput 受控组件 bug（已随前端删除）
4. **删除 Web 前端** — React frontend/ 全部移除，项目仅保留 backend + uniapp + miniprogram
5. **死代码清理** — ai_providers 6 个废弃 provider + business_profiles.py 777 行 + config.py 重复配置（共 ~1000 行）
6. **B27** — billing rowcount==0 时 refresh user ORM 状态
7. **B26** — records/favorites 错误响应统一为 HTTPException(404)
8. **safe-area** — 4 页面添加 env(safe-area-inset-bottom)
9. **文档重写** — README、uniapp/miniprogram README 全部更新
10. **GitHub 仓库重建** — 清理旧仓库，推送干净代码

## C-4 真实报告验证

- 业态：小餐饮 | 地址：陕二丫擀面皮(兰宝小区店) | 宝鸡
- 结果：AMap 采集成功、计费链路正确（扣点→退款）、报告未保存
- 失败原因：LLM 两次生成均编造了不存在的 POI 名称（好又多、学校、住宅小区）
- P0 guard 正确拦截并触发退款，但 retry 后仍未通过

## 当前唯一阻塞问题

**LLM 在报告中编造假 POI 名称。** P0 guard 能拦截，但 retry 后仍然编造，导致报告无法保存。
这是 prompt 层的对抗问题，需要 Codex 审核后给出指令。

## 下一步

1. **微信支付联调** — 填写真实商户密钥后测试支付全链路
2. **Prompt 对抗优化** — 等 Codex 额度恢复后审核，给出 prompt 层修复指令
3. **样本库补充** — 13 个业态缺 substitute 列（非阻塞）

## 测试基线

- `python -m compileall backend`: PASS
- `python backend/tests/check_industry_rigor_rules.py`: 2168 PASS, 0 FAIL
- `python backend/tests/check_report_fact_guard.py`: 147 PASS, 0 FAIL
- 后端运行中：http://localhost:8000
- Swagger：http://localhost:8000/docs
