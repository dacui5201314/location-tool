# 址得选项目长期规则

## 角色分工

- 用户是产品负责人、需求提出者和最终验收人；用户负责决定产品方向，并用真实报告验收效果。
- Codex 是项目总负责、代码审查者、Claude Code 指挥官。Codex 当前重点是维护边界、复核改动、保护报告逻辑不回退，并协调前端/管理后台优化。
- Claude Code 是主要代码执行者，负责按 Codex 下发的明确提示词修改代码并做代码级自测。
- Codex 默认不直接改后端 POI/AMap/评分/数据库逻辑；这些改动优先交给 Claude Code 执行，再由 Codex 复核。文档交接类修改可由 Codex 直接完成。
- 当前最高优先级是前端体验、管理后台信息架构、用户反馈闭环和上线验收。报告精准度与知识蒸馏框架已收口，涉及评分、POI 分类、YAML、prompt、guard 的改动只允许在明确需求和测试保护下进行。

## 核心产品原则

- 产品名：址得选。
- 产品定位：全国商铺选址初筛参考工具。
- 服务范围：面向全国城市、全国商圈、后台配置业态的选址初筛；当前样本只用于验证规则，不代表产品只服务某城市或某业态。
- 规则通用性：POI 分类、竞品识别、替代消费、客流锚点、评分口径必须抽象为全国通用规则。
- 禁止为单个城市、街道、商场、门店、品牌写硬编码特判。宝鸡、经二路、名汇购物商城、陕二丫擀面皮等只能作为测试样本出现在自测/验收说明中。
- 所有报告必须强调“初筛参考”，不得包装成投资建议或最终决策结论。
- 用户可见文案应统一使用：选址初筛参考工具、商业选址初筛报告、初筛状态、数据解读状态、需线下验证。
- 禁止用户可见文案继续使用：决策平台、商业数据决策平台、助力决策、推荐/不推荐、建议推进/高风险推进等替用户做决策的表达。

## 报告可信度铁律

- 报告必须区分：
  - `direct_competitors`：直接竞品
  - `substitute_competitors`：替代消费压力
  - `traffic_anchors`：客流锚点
  - `irrelevant_excluded`：无关 POI 剔除
- `rigor_enabled` 是唯一严谨框架开关。
- 禁止用 `direct_competitors_1000m is not None` 或 JS `direct_competitors_1000m !== undefined` 判断严谨框架。
- `rigor_enabled === false` 时，不得显示“暂无直接竞品”这类严谨框架结论；如必须展示旧竞品口径，只能称为“旧口径竞品参考（非严谨直接竞品）”。
- 后台所有业态都需要独立可信的 direct/substitute/anchor/irrelevant 边界；修某个业态时不得污染其他业态。

## 规则体系重构原则

- 当前策略是体系化重构规则，不再靠零散关键词修补。
- 规则变更必须同时考虑两条链路：
  - 规则层：`classify_poi_rigor(name, cat, type_code, rigor, business_type)`
  - 真实链路：`classify_poi_type -> category 脱水 -> classify_poi_rigor`
- 新增或调整规则必须补入 canonical 本地自测：`backend/tests/check_industry_rigor_rules.py`。
- 高风险 AMap 大类或宽类 code 不允许裸直通 direct；如确需使用，必须配置化约束，例如 `require_name_keyword_for_code=True`。
- 明确替代品类应支持优先进入 substitute，不应被 direct code 直通吞掉；使用 `substitute_before_direct=True` 或等价配置。
- 多子业态 master 必须用 subtype 隔离，不允许一个粗口径覆盖多个子业态。
- subtype 规则必须继承 master 级保护字段：
  - `require_name_keyword_for_code`
  - `substitute_before_direct`
  - `strict_exclude_names`
  - `exclude_names`
- subtype 的 `name_keywords` / `amap_codes` 应按业务优先使用 subtype 自身配置，不能无脑合并导致口径变宽。
- 新增 category 只能加入 `real_data` JSON 兼容层，不改数据库 schema。

## 当前严禁破坏的兼容层

- 旧报告必须还能打开。
- 旧 `report_json` 缺新字段不能崩溃。
- `report_file` / `report_url` 只能作为 fallback；若 `record.report_json` 存在，下载历史报告应优先动态重建 HTML。
- 小程序/HTML 展示口径必须一致，只能消费同一份 `report_json`，不得在展示层各自生成业务判断。
- 不改 AMap API 调用方式，只改分类、脱水、规则和测试。
- 不强制数据库 migration，除非用户明确要求。

## 财务估算规则

- 禁止输出看似精确的单点数字，例如日均 183 单、月营收 23.6 万、月净利 4.7 万、盈亏平衡 124 单/天、月亏损 -10,800 元。
- 必须输出区间、假设条件、置信度和线下验证说明。
- 租金、人工、毛利率、转化率、客单价如无用户输入或可靠来源，必须标注“模型假设”。
- `industry_config.py` 中涉及月营收、月净利、回本周期的配置必须区间化，不得单点精确。

## 后端技术规范

- 后端主框架：FastAPI。
- 后端重点文件：
  - `backend/main.py`
  - `backend/services/amap_service.py`
  - `backend/prompts/industry_config.py`
  - `backend/prompts/location_analysis.py`
  - `backend/services/storage_service.py`
- 后端验证优先：
  - `python -m compileall backend`
  - `python backend/tests/check_industry_rigor_rules.py`
- 本机 `python`/`py` 有时不可用。常用可用路径：
  - `C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe`
  - `C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

## 前端技术规范

- 前端框架：uni-app (Vue 3 + Vite) → 微信小程序 / 抖音 / App 多端
- 前端验证：`cd uniapp && npm run build:mp-weixin`
- 当前前端/管理后台优化阶段允许修改 `uniapp/` 体验和管理后台 UI/IA，但不得借 UI 优化修改报告生成语义。
- `frontend/` 目录已删除（原 React Web 前端，~17,000 行）；uni-app 是唯一客户端。
- 小程序登录审核文案不得混淆腾讯官方元素，手机号授权统一使用“手机号快捷登录”等中性表达。
- 用户反馈闭环是产品体验功能：前端可提交和查看反馈，后台可回复；默认不设置反馈积分奖励。
- 报告分享保持公开 token 查看，不强制被分享人登录，避免影响分享裂变；如未来改变，必须由用户明确确认。
- 管理后台报告库预览必须向小程序报告详情对齐，且同样只消费 `report_json`。

## 禁止事项

- 禁止为当前测试样本硬编码城市名、街道名、商场名、品牌名、门店名。
- 禁止让客户端传入的 `real_data` 参与正式评分和报告，除非显式开启调试环境变量。
- 禁止把 AMap 失败 fallback 到用户伪造 `real_data` 的正式链路。
- 禁止模型输出坏 JSON、空报告、缺结构报告后仍扣点生成正式报告。
- 禁止把医院院内科室、住院部、创伤中心、急诊中心等重复算成多家医院。
- 禁止把体检中心、整形美容中心、眼科、视光、助听器、皮肤修护、疤痕管理、医美算作医院或药店。
- 禁止把产业园、大厦、办公楼算作住宅小区。
- 禁止把美甲、手机维修、彩票、黄金回收、OPPO 体验店算作便利店。
- `frontend/` 已删除；不要再修改或引用该目录。
