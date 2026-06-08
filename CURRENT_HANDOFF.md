# 址得选 · 当前交接文档

**最后更新**：2026-06-08
**版本**：v3.9.0
**阶段**：退款全链路闭环，正式提交微信审核

---

## 项目信息

| 项 | 值 |
|----|-----|
| 本地路径 | `C:\Users\admin\location-tool` |
| 服务器路径 | `/www/wwwroot/location-tool/` |
| 生产域名 | `https://www.oliver188.top` |
| 小程序 AppID | `wxc8f7f6a2e29e7bb4` |
| 上传目录 | `uniapp/dist/build/mp-weixin` |
| GitHub | `https://github.com/dacui5201314/location-tool-v2` |

---

## 启动命令

**本地后端**：
```bash
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**本地前端构建**：
```bash
cd uniapp && npm run build:mp-weixin
```

**生产重启**：
```bash
fuser -k 8000/tcp ; sleep 1 && cd /www/wwwroot/location-tool/backend && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
```

---

## 不可随意修改的模块

牵一发动全身，**除非明确需求，否则不要改**：

| 文件 | 原因 |
|------|------|
| `backend/prompts/industry_config.py` | 32 个业态阈值/权重/严谨度规则 |
| `backend/tests/check_report_fact_guard.py` | 175 条事实校验测试 |
| `backend/tests/check_industry_rigor_rules.py` | 2168 条严谨度测试 |
| `backend/services/report_fact_guard.py` | 报告事实校验核心 |
| 评分逻辑 / POI 分类 / Prompt | 评分关联前端，POI 关联高德 API |

---

## 分享图策略

- 后台 HTTPS 配置优先，不再使用包内静态分享封面图
- 流程：`fetchShareConfig` → `resolveShareImage` → `uni.downloadFile` → tempFilePath
- fallback：tempFilePath → HTTPS URL → _remoteImage 缓存 → 无（微信截图兜底）
- 图片：500×400 JPEG，~42KB

---

## 微信支付

- v3 JSAPI prepay + notify + order query 已打通
- 生产需确认：`wx_app_id` = `wx_mini_appid` = `wxc8f7f6a2e29e7bb4`
- 商户号 `1113129021` 须与 AppID 同一主体
- notify_url 须 `https://`

---

## 测试基线

```text
python -m compileall backend                     PASS
python backend/tests/check_industry_rigor_rules.py  2168 PASS, 0 FAIL
python backend/tests/check_report_fact_guard.py      175 PASS, 0 FAIL
npm run build:mp-weixin                             DONE
```

---

## 提交注意

- 不要提交 `backend/c4_test.json`、`backend.zip`、`backend/storage/`
- 不要提交 `logo-1/`
- 未经明确同意不要 push

---

## 下次开发

从第二阶段需求开始，详见 `阶段总结_上线前稳定版_2026-06-04.md`。
