<template>
  <view class="legal-page">
    <text class="legal-heading">隐私政策</text>
    <text class="legal-meta">更新日期：2026年5月</text>

    <text class="legal-h2">一、引言</text>
    <text class="legal-p">本小程序运营方（以下简称"我们"）深知个人信息对您的重要性，并会尽力保护您的个人信息安全。本隐私政策将说明我们如何收集、使用、存储和保护您的个人信息。使用本小程序前，请您仔细阅读本政策。</text>

    <text class="legal-h2">二、我们收集的信息</text>
    <text class="legal-p">2.1 手机号：当您注册或登录时，我们会收集您的手机号用于账号创建、身份识别与安全验证。手机号是您的唯一账号标识。</text>
    <text class="legal-p">2.2 微信头像与昵称：当您授权后，我们会收集您的微信头像和昵称用于个人资料展示。您可以在"完善资料"页面修改或删除这些信息。</text>
    <text class="legal-p">2.3 位置信息：为提供选址分析服务，我们会收集您选择的门店地址与地理位置信息。此信息仅用于生成选址分析报告，不会用于其他目的。</text>
    <text class="legal-p">2.4 订单与支付信息：当您购买套餐或开通会员时，微信小程序虚拟支付会处理您的支付信息。我们仅记录订单状态与交易流水号，不直接收集您的银行卡或支付密码。</text>
    <text class="legal-p">2.5 设备信息：我们会收集您使用的设备类型、操作系统版本等基本信息，用于优化服务体验和排查问题。</text>

    <text class="legal-h2">三、信息使用目的</text>
    <text class="legal-p">3.1 为您提供选址分析服务：使用您选择的位置信息生成选址分析参考报告。</text>
    <text class="legal-p">3.2 账号管理：使用手机号进行注册、登录和身份验证。</text>
    <text class="legal-p">3.3 个性化展示：使用昵称和头像在个人页面及管理后台展示用户信息。</text>
    <text class="legal-p">3.4 支付与订单：处理会员开通、点数购买和订单查询。</text>
    <text class="legal-p">3.5 服务优化：基于使用数据改进产品功能和用户体验。</text>

    <text class="legal-h2">四、信息的存储与保护</text>
    <text class="legal-p">4.1 我们将您的个人信息存储在中华人民共和国境内的服务器上。</text>
    <text class="legal-p">4.2 我们采用业界通行的安全技术和管理措施保护您的个人信息，防止未经授权的访问、使用或泄露。</text>
    <text class="legal-p">4.3 您的手机号和密码采用加密存储。我们不会以明文方式存储或传输您的密码。</text>

    <text class="legal-h2">五、信息的共享与披露</text>
    <text class="legal-p">5.1 我们不会将您的个人信息出售给任何第三方。</text>
    <text class="legal-p">5.2 在以下情形下，我们可能会共享必要的信息：经您明确授权同意、法律法规要求的披露、为保护我们或公众的合法权益、与第三方服务商合作提供必要服务（如微信小程序虚拟支付、地图服务），此类合作会要求第三方遵守数据保护义务。</text>

    <text class="legal-h2">六、您对信息的权利</text>
    <text class="legal-p">6.1 您可以在"完善资料"页面修改或删除您的头像和昵称。</text>
    <text class="legal-p">6.2 您可以通过注销账号来删除您的个人信息。账号注销后，您的分析记录、收藏信息将被清除。</text>
    <text class="legal-p">6.3 如您对个人信息处理有任何疑问或请求，可通过客服渠道联系我们。</text>

    <text class="legal-h2">七、微信相关权限说明</text>
    <text class="legal-p">7.1 微信手机号授权：用于一键登录和账号绑定。您可以选择拒绝授权，使用密码登录方式注册账号。</text>
    <text class="legal-p">7.2 微信头像昵称授权：用于个人资料展示。此项为可选授权，不会影响核心服务使用。</text>
    <text class="legal-p">7.3 位置信息授权：用于选址分析服务。此项为可选授权，您可手动输入地址完成分析。</text>

    <text class="legal-h2">八、未成年人信息保护</text>
    <text class="legal-p">本小程序主要面向成年人。如您是未满18周岁的未成年人，请在监护人指导下使用，并由监护人阅读并同意本政策。</text>

    <text class="legal-h2">九、政策更新</text>
    <text class="legal-p">我们可能会适时更新本隐私政策。更新后的政策将在本页面发布并立即生效。建议您定期查阅。</text>

    <text class="legal-h2">十、联系方式</text>
    <text class="legal-p">如您对本隐私政策有任何疑问，请通过本小程序内的"联系客服"入口与我们联系。</text>
  </view>
</template>

<script>
export default { name: 'PrivacyPolicy' }
</script>

<style scoped>
.legal-page { min-height:100vh; background:#fff; padding:32rpx 28rpx 80rpx; }
.legal-heading { display:block; font-size:36rpx; font-weight:900; color:#0f172a; margin-bottom:8rpx; }
.legal-meta { display:block; font-size:22rpx; color:#94a3b8; margin-bottom:32rpx; }
.legal-h2 { display:block; font-size:28rpx; font-weight:800; color:#1e293b; margin:28rpx 0 12rpx; }
.legal-p { display:block; font-size:26rpx; color:#475569; line-height:1.75; margin-bottom:12rpx; }
</style>
