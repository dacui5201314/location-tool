<template>
  <view class="legal-page">
    <text class="legal-heading">用户协议</text>
    <text class="legal-meta">更新日期：2026年5月</text>

    <text class="legal-h2">一、总则</text>
    <text class="legal-p">欢迎使用址得选（以下简称"本小程序"）。本协议由您与本小程序运营方（以下简称"运营方"或"我们"）共同缔结，具有合同效力。请您在使用本小程序前仔细阅读本协议。一旦您开始使用本小程序，即视为您已阅读、理解并同意接受本协议的全部内容。</text>
    <text class="legal-p">本小程序提供商业选址分析参考服务，所有分析结果仅供参考，不构成投资建议、经营决策依据或任何形式的商业承诺。</text>

    <text class="legal-h2">二、账号与登录</text>
    <text class="legal-p">2.1 您可以通过微信手机号快捷登录或手机号密码登录方式注册并使用本小程序。您应保证所提供的手机号真实、有效，因手机号不实导致的任何问题由您自行承担。</text>
    <text class="legal-p">2.2 您应妥善保管账号及密码。通过您的账号进行的所有操作均视为您的行为，由您承担相应责任。</text>
    <text class="legal-p">2.3 每个手机号仅限注册一个账号。禁止转让、出借或出售账号。</text>

    <text class="legal-h2">三、服务说明</text>
    <text class="legal-p">3.1 本小程序提供基于地理信息与周边商业数据的选址分析参考服务。分析报告包含周边业态分布、客流评估、竞争环境分析等内容，所有结论均为选址分析参考。</text>
    <text class="legal-p">3.2 生成分析报告需要消耗分析点数。点数可通过购买套餐、兑换码激活或会员权益获得。</text>
    <text class="legal-p">3.3 会员服务分为月度、季度、年度不同档位，会员有效期内可不限次生成分析报告，并享有会员专属权益。</text>
    <text class="legal-p">3.4 分析报告仅供您个人参考使用。未经运营方书面许可，不得将报告用于商业转售、公开发布或作为第三方决策依据。</text>

    <text class="legal-h2">四、会员、点数与支付</text>
    <text class="legal-p">4.1 您可通过微信支付购买点数套餐或开通会员服务。支付金额以页面展示为准。</text>
    <text class="legal-p">4.2 兑换码（CDK）是运营方发放的激活码，可用于兑换分析点数。兑换码一经激活不可退还。</text>
    <text class="legal-p">4.3 已消耗的分析点数不予退还。已支付的会员费用在会员期间内有效，不支持部分退款。</text>
    <text class="legal-p">4.4 如有支付问题或退款需求，请联系客服处理。</text>

    <text class="legal-h2">五、用户行为规范</text>
    <text class="legal-p">5.1 您在使用本小程序过程中应遵守中华人民共和国法律法规。</text>
    <text class="legal-p">5.2 禁止利用本小程序从事以下行为：发布违法信息、干扰服务正常运行、利用技术手段获取不当利益、反向工程或破解本小程序、其他损害运营方或第三方合法权益的行为。</text>
    <text class="legal-p">5.3 如发现您违反上述规定，运营方有权暂停或终止向您提供服务，并保留追究法律责任的权利。</text>

    <text class="legal-h2">六、免责声明</text>
    <text class="legal-p">6.1 本小程序提供的选址分析结果基于公开数据分析与算法模型，运营方不保证分析结果的准确性、完整性或时效性。任何选址或经营决策应以实地考察和专业人士意见为准。</text>
    <text class="legal-p">6.2 因不可抗力、系统维护、网络故障等原因导致的服务中断，运营方不承担责任。</text>
    <text class="legal-p">6.3 第三方数据源（如地图服务、POI数据）的准确性由相应数据提供方负责。</text>

    <text class="legal-h2">七、未成年人保护</text>
    <text class="legal-p">本小程序主要面向具有完全民事行为能力的成年人。未满18周岁的未成年人应在监护人指导下使用本服务。</text>

    <text class="legal-h2">八、协议更新</text>
    <text class="legal-p">运营方有权根据需要修改本协议。修改后的协议将在本页面公示，并于公示之日生效。继续使用本服务即视为您接受修改后的协议。</text>

    <text class="legal-h2">九、联系方式</text>
    <text class="legal-p">如您对本协议有任何疑问，可通过本小程序内的"联系客服"入口与运营方取得联系。</text>
  </view>
</template>

<script>
export default { name: 'UserAgreement' }
</script>

<style scoped>
.legal-page { min-height:100vh; background:#fff; padding:32rpx 28rpx 80rpx; }
.legal-heading { display:block; font-size:36rpx; font-weight:900; color:#0f172a; margin-bottom:8rpx; }
.legal-meta { display:block; font-size:22rpx; color:#94a3b8; margin-bottom:32rpx; }
.legal-h2 { display:block; font-size:28rpx; font-weight:800; color:#1e293b; margin:28rpx 0 12rpx; }
.legal-p { display:block; font-size:26rpx; color:#475569; line-height:1.75; margin-bottom:12rpx; }
</style>
