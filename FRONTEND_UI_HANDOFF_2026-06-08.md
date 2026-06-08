# 前端 UI 收口交接 - 2026-06-08

## 当前目标

小程序支付和退款主链路已基本打通。本轮只做第一个剩余板块：前端 UI 收口。

新窗口请只处理 `uniapp` 前端体验，不要修改后端。

## 严格边界

- 不改 `backend/`。
- 不改支付、退款、虚拟支付接口逻辑。
- 不改报告生成、评分、POI 分类、prompt、`report_fact_guard`、`industry_config.py`。
- 不做大范围重构。
- 先执行 `git status --short`，确认已有改动，不要回滚他人改动。

## 已知现状

当前工作区已经有较多未提交改动，包含后端退款、报告库、前端订单等内容。

尤其注意：`uniapp/src/pages/profile/order-detail.vue` 当前可能仍有乱码和旧样式，需要重点检查并重写成正式订单详情页。

## 本轮要处理的问题

### 1. 顶部/下拉视觉割裂

现象：小程序首页下拉时顶部出现一块灰色区域，和其他成熟小程序相比不够一体。

处理方向：
- 优先检查 `uniapp/src/pages.json` 的 `backgroundColorTop`、`backgroundTextStyle`、页面 `enablePullDownRefresh`。
- 保持蓝色品牌视觉统一。
- 不引入复杂新结构，不大改首页业务逻辑。

### 2. 未登录拦截

未登录时，以下入口必须先提示登录：

- 充值记录
- 意见反馈
- 联系客服

期望：
- 弹窗标题：`请先登录`
- 确认后跳转登录页
- 取消则留在当前页
- 不允许未登录用户直接进入这些页面

主要文件：
- `uniapp/src/components/tab/ProfilePanel.vue`

### 3. 退出登录确认

点击退出登录时必须二次确认。

期望：
- `uni.showModal`
- 确认后清除 token 和用户状态
- 取消不退出

主要文件：
- `uniapp/src/components/tab/ProfilePanel.vue`

### 4. 按钮样式统一

完善资料页保存按钮需要和意见反馈提交按钮视觉统一。

期望：
- 蓝紫渐变主按钮
- 白色文字
- 正式、干净、有禁用态

主要文件：
- `uniapp/src/pages/profile/edit.vue`
- 可参考 `uniapp/src/pages/profile/feedback.vue`

### 5. 充值记录页正规化

当前充值记录页太像简陋列表，需要做成正式订单列表。

每条订单至少展示：
- 套餐
- 金额
- 权益
- 支付方式
- 状态
- 时间

用户侧支付方式统一显示：`微信支付`，不要显示 `虚拟支付`。

状态和按钮：
- `CREATED`：显示 `待支付`，有 `继续支付` 按钮
- `PAID`：显示 `已完成`，有 `申请退款` 按钮
- `REFUND_REQUESTED`：显示 `退款申请中`
- `REFUNDING`：显示 `退款处理中`
- `REFUNDED`：显示 `已退款 / 权益已关闭`
- `TIMEOUT` / `FAILED`：显示 `已关闭`
- `CANCELLED`：显示 `已取消`

必须保留：
- 原有继续支付逻辑
- 原有申请退款逻辑
- 下拉刷新逻辑

主要文件：
- `uniapp/src/pages/profile/orders.vue`

### 6. 订单详情页正规化

当前订单详情页不正规，可能还有乱码，需要重写。

建议结构：
- 顶部品牌标题区
- 订单状态摘要卡片
- 订单信息卡片
- 操作区

展示字段：
- 状态
- 套餐
- 金额
- 权益
- 支付方式
- 订单号
- 创建时间
- 支付时间

按钮：
- `CREATED`：`继续支付`
- `PAID`：`申请退款`
- 退款中/已退款/已关闭：展示对应提示

必须保留的 API / 逻辑：
- `queryVirtualOrder`
- `payExistingOrder`
- `refundRequestVirtual`
- `refreshWxLogin`
- `wx.requestVirtualPayment`

主要文件：
- `uniapp/src/pages/profile/order-detail.vue`

## 验收命令

```powershell
cd C:\Users\admin\location-tool\uniapp
npm.cmd run build:mp-weixin
```

构建必须通过。

## 最终输出

完成后输出：

- 修改文件清单
- 构建结果
- 是否涉及后端：应为否

