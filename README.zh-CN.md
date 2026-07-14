# no-german-required 🇩🇪🚫🗣️

[English](README.md) | **简体中文**

**为德语不流利的在德留学生打造的找工作 agent。**

每天自动扫描英语友好的岗位源,识别关键词过滤器抓不住的隐藏德语要求,用 LLM 按*你的*
个人档案给每个岗位打分,再把精简日报发到你邮箱。Fork 仓库、填两个 secret 就能用——
跑在 GitHub Actions 上,完全免费。

## 为什么做这个项目

每个在德国的留学生都踩过这个坑:JD 全英文写得漂漂亮亮,你花一小时投完简历,然后——
*"fließend Deutsch in Wort und Schrift erforderlich."*(要求德语听说读写流利)

**英文 JD ≠ 英语工作环境。** 普通招聘网站分不出这个区别,这个 agent 替你读小字:

- 🔍 **两级语言过滤** —— 正则先筛掉明显的(`verhandlungssicher`、`C1`、
  `fluent German required`),再由 LLM 附原文证据判断隐晦的
- 🎓 **懂学生** —— 专注 Werkstudent(工作学生)/ Praktikum(实习)岗位,
  且理解你的德语水平(B1 ≠ 零基础:"German is a plus" 的岗位会保留)
- 📊 **打分推荐,不是灌列表** —— 每个匹配岗位附 0-100 匹配分、工作语言判断和
  红旗提示(无薪、注册学籍要求、每周 5 天到岗……)
- 📬 **每天一份日报** —— 邮件或 Telegram;Top 5 匹配 + 3 个"差一点"的岗位,
  方便你校准过滤器
- 📋 **申请追踪** —— 标记为已申请/面试/offer 后,该岗位不再出现在日报里
- 🆓 **零基础设施** —— GitHub Actions + 你自己的 LLM key
  (Anthropic / OpenAI / DeepSeek / 任何 OpenAI 兼容接口)

## 这个项目不做什么

**永不自动投递。** 自动投递机器人会导致账号封禁、浪费招聘方时间,海投产生的低质量
申请只会害了你。这个 agent 只负责发现和筛选,申请由*你*来。它也只使用**公开免鉴权
API**([Arbeitnow](https://www.arbeitnow.com/api)、Greenhouse/Lever/Ashby 公开看板)——
不爬登录墙后的数据,不违反任何平台服务条款。

## 快速开始(5 分钟)

1. **Fork** 本仓库(保持 public 可用免费 Actions 额度,private 则消耗你的配额)
2. **编辑 [`profile.yaml`](profile.yaml)** —— 你的目标岗位、城市、德语水平和
   3 行简历摘要
3. **添加仓库 secrets**(Settings → Secrets and variables → Actions → Secrets):

   | Secret | 值 |
   |---|---|
   | `LLM_API_KEY` | 你的 Anthropic / OpenAI / DeepSeek key |
   | `SMTP_USER` | 你的 Gmail 地址 |
   | `SMTP_PASS` | [Gmail 应用密码](https://myaccount.google.com/apppasswords)(不是登录密码) |

4. **可选变量**(同页面 → Variables):`LLM_PROVIDER`(默认 `anthropic` /
   `openai` / `deepseek`)、`LLM_MODEL`、`MAIL_TO`、`MAX_LLM_CALLS`(默认每天
   25 次以控制成本)、`NOTIFY`(默认 `email` / `telegram` / `both` —— Telegram
   需要额外配置 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` secrets,
   见 [`src/notify/telegram.py`](src/notify/telegram.py))
5. **测试**:Actions 页 → *Daily job scan* → *Run workflow*

之后每天早上 ~7 点(德国时间)日报准时送达。

### 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env        # 填入你的 key
python -m src.main --dry-run   # 不调 LLM、不发邮件——看看哪些岗位通过了规则筛选
python -m src.main             # 完整运行
```

### 子代理

除每日打分外的两个可选 LLM 角色:

- **公司情报官**(自动):日报中每个高分岗位附带公司简报——业务、规模、
  工作语言文化、2-3 个申请切入点。每家公司只调用一次并永久缓存。信息来自
  模型知识,面试前请自行核实。
- **求职信写手**(手动、本地运行):

  ```bash
  python -m src.agents.draft --list        # 查看可起草的岗位
  python -m src.agents.draft <岗位链接>     # 生成 drafts/<公司>-<岗位>.md
  python -m src.agents.draft <岗位链接> --de  # 德语版
  ```

  草稿设计上保持诚实(绝不编造你没有的经历),存放在 `drafts/`(不入 git)。
  发送前务必自己修改——它是草稿,不是你。任何内容都不会被自动提交。

### 追踪申请状态

```bash
python -m src.track add https://n26.com/en/careers/positions/12345   # 标记为已申请
python -m src.track add <url> interview "周五电话面试"
python -m src.track list
python -m src.track stats
```

已追踪的岗位不会再出现在日报里。提交 `data/applications.json` 可与
GitHub Actions 的运行状态同步。

## 工作原理

```
Arbeitnow API ─┐
               ├─→ 去重 ─→ 规则筛选 ─→ LLM 精判 ─→ 日报推送
ATS 公开接口 ──┘  (seen.json)  (免费)    (≤25 次调用)  (Top 5 + 差一点的)
(Greenhouse/Ashby,
 16 家已验证的德国科技公司)
```

LLM 对每个岗位输出结构化判断:

```json
{
  "working_language": "English",
  "german_required": "nice-to-have",
  "evidence": "Our company language is English; German is a plus.",
  "match_score": 85,
  "red_flags": ["要求剩余注册学期 ≥2 个"],
  "summary": "高匹配:柏林 Werkstudent 数据岗,英语优先团队。"
}
```

如果岗位要求的德语超过你的 `german_level`,匹配分会被限制在 30 以内——
它会进入"差一点"区域而不是日报头条。

## 覆盖哪些岗位来源

两类来源,全部公开免鉴权:

- **[Arbeitnow](https://www.arbeitnow.com/english-speaking-jobs)** —— 德国英语友好
  岗位聚合板,约 300 个在招岗位,以创业公司和中型科技公司为主。公司每天都在变,
  无需配置。
- **[`data/companies.yaml`](data/companies.yaml) 中固定监控的 35 家公司**,直接从
  各家 ATS 接口拉取:金融科技(N26、Trade Republic、Solaris、德意志银行……)、
  消费科技(HelloFresh、GetYourGuide、Flix、FreeNow、Scout24……)、企业软件
  (Celonis、Contentful、commercetools、KONUX……)、工业制造(Airbus、蒂森克虏伯、
  蔡司、BorgWarner、Zeppelin、Isar Aerospace)、医药(辉瑞、Moderna、GSK、IQVIA)等。

**不覆盖**:使用 SuccessFactors 或完全自建招聘系统的公司(宝马、奔驰、奥迪、大众、
西门子、博世、SAP、DHL……)。它们的学生岗偶尔会出现在 Arbeitnow 里,但别指望。
公司列表一行一家,想盯谁就加谁,欢迎提 PR。

## 按你的情况定制(任何专业、任何德语水平)

所有个人化配置都在 [`profile.yaml`](profile.yaml),不用改代码。默认档案面向
商科/数据方向,其他情况这样改:

- **你的专业** → `field_keywords`。机械工程:`[mechanical, cad, simulation,
  automotive, manufacturing]`;市场营销:`[marketing, social media, content, seo,
  brand]`;金融:`[finance, accounting, controlling, audit, m&a]`。岗位描述中
  至少命中一个关键词才会保留。
- **岗位类型** → `role_keywords`。默认覆盖 Werkstudent / intern / Praktikum /
  thesis;找全职初级岗就换成 `[graduate, junior, entry level, trainee]`。
- **德语水平** → `german_level: A1..C1`。这是核心功能:LLM 会把每个岗位的*真实*
  语言要求(常藏在小字里)和你的水平对比。`apply_anyway: true` 时超出你水平的
  岗位仍会出现,但会扣分并挂红旗,由你自己决定投不投;设为 `false` 则直接过滤。
- **地点** → 指定城市用 `cities: [berlin, munich]`;全德国用 `cities: []` +
  `germany_only: true`。
- **数量与精度** → `min_score`(进日报的分数线),以及仓库 Variables:
  `MAX_LLM_CALLS`(每日 LLM 预算)、`TOP_N` / `NEAR_MISS_N`(日报条数)。
- **自我介绍** → `cv_summary`:3-5 行你的背景。LLM 按这段文字给每个岗位打分,
  写得越具体,排序越准。

改完档案后,如果想让已处理过的存量岗位按新规则重评,把 `data/seen.json` 重置为
`{"seen": []}` 即可。

## 签证与工作规则须知 📋

不构成法律建议,但这些是 agent 会标注的规则:

- **Werkstudent**:上课期间每周最多 **20 小时**(假期可全职)
- **非欧盟学生**:每年 **140 个全天**(或 280 个半天)工作额度;
  Werkstudent 和必修实习(*Pflichtpraktikum*)的计算方式不同
- 许多 Werkstudent 岗位要求在读注册证明(*Immatrikulationsbescheinigung*)

## 参与贡献

最有价值的 PR:向 [`data/companies.yaml`](data/companies.yaml) **添加英语友好的
公司**——每家一行,slug 从公司招聘页 URL 获取(提交前请先验证 API 有响应)。
同样欢迎:新数据源适配器(`src/sources/`)、更好的德语要求识别模式
(`src/filters/rules.py`)、新通知渠道(`src/notify/`)。

## 许可证

MIT
