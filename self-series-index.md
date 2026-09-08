# self · AI Self-Series（自我系列产品线）

> 20 条全英文命名的 self-* 系列。每条都是**独立、同级、能主动干活的 AI Agent**，
> 品质对齐已验证的 `self-improvement-agent`（v1.1.0，4.7 级）五维标准。
> 用户下载任意一条都能单独完成一个真实任务，不依赖其他条。

## 排序逻辑
1. **AI 自改组（7）**：锚点 + 评/修/验/优/教/护 —— 与既有 self-improvement-agent 同宗，先立。
2. **人·认知习惯组（5）**：自省/自律/习惯/聚焦/决策 —— 用 AI 的人最普适的自我管理。
3. **人·身知财组（5）**：自学/精通/睡眠/健身/预算 —— 身体与硬技能基础。
4. **人·关系创作情绪组（3）**：沟通/创作/安抚 —— 软技能收尾。

## 总表（20 条，按序）

| 序 | 英文名 | 一句话描述 | 存放位置 | 状态 | 实测评分 |
|----|--------|-----------|----------|------|----------|
| 1 | self-improvement-agent | AI 从错误/反馈长记性：错→永久记忆→升指令→抽 skill（棘轮） | `E:/Skills/self/self-improvement-agent/` | 基准（已有 v1.1.0） | **4.7** 优秀 |
| 2 | self-evaluate-agent | 元认知评估与反思引擎：Reflexion 多轮闭环(打分→反思→重写→重评→收敛)+元认知校准(Brier/OCI)，含客观探针预检 | `E:/Skills/self/self-evaluate-agent/` | ✅ 已写 v2.0.0（深度版） | **4.7** 优秀 |
| 3 | self-debug-agent | 自主调试引擎：复现→归类(六类探针)→SBFL定位(Ochiai)→治愈循环→自动落永久回归测试（理论：Self-Debugging ICLR2024 / Delta Debugging / SBFL） | `E:/Skills/self/self-debug-agent/` | ✅ 已写 v2.0.0（深度版） | **4.8** 优秀 |
| 4 | self-verify-agent | 正确性验证与交付门禁引擎：执行门禁(测试/断言)+自洽性(Self-Consistency 多路径收敛)+步骤级核对(PRM 风格)+证伪探针，不达标物理拦下（理论：Self-Consistency Wang2022 / PRM-vs-ORM Lightman2023 / DeepSeek-R1 反例） | `E:/Skills/self/self-verify-agent/` | ✅ 已写 v2.0.0（深度版） | **4.8** 优秀 |
| 5 | self-optimize-agent | 受控自我实验优化引擎：define→run→compare→promote/rollback，Welch 显著判定+贝叶斯式 EI 建议下一个候选（理论：贝叶斯优化 Snoek2012 / SMBO / RISE 2024） | `E:/Skills/self/self-optimize-agent/` | ✅ 已写 v2.0.0（深度版） | **4.6** 优秀 |
| 6 | self-teach-agent | 自我教学/知识内化引擎：摄入→排课(由易到难)→自测→间隔复现→晋升，四要素门禁不达标不晋升 | `E:/Skills/self/self-teach-agent/` | ✅ 已写 v2.0.0（12 文件） | **4.7** 优秀 |
| 7 | self-protect-agent | 自我边界守护引擎：scan 红线扫描+check 预执行校验(路径保护/批量/HITL)+record 近失累积+audit 趋势报告，安全不贰过（理论：海恩法则/Bird三角/瑞士奶酪模型/最小权限/影响×可逆矩阵/纵深防御） | `E:/Skills/self/self-protect-agent/` | ✅ 已写 v2.0.1（11 文件，小升级：+--json/+4红线） | **4.8** 优秀 |
| 8 | self-reflect-agent | 日三省：洞察日志+模式识别+言行盲点，看见思维惯性与盲点，四问复盘推向双环学习 | `E:/Skills/self/self-reflect-agent/` | ✅ 已写 v2.0.0（9 文件） | **4.7** 优秀 |
| 9 | self-discipline-agent | 承诺装置+问责日志：登记承诺(后果/监督人/类别)+到期打卡履约+自动违约检测+问责报告暴露最易破类型，把靠意志变成机制 | `E:/Skills/self/self-discipline-agent/` | ✅ 已写 v2.0.0（9 文件） | **4.7** 优秀 |
| 10 | self-habit-agent | 习惯叠加+streak 引擎：把新行为接旧锚点，养成就不丢 | `E:/Skills/self/self-habit-agent/` | ✅ 已写 v2.0.0（9 文件） | **4.7** 优秀 |
| 11 | self-focus-agent | 深度工作+防干扰引擎：规划专注块+记录实际专注与打断来源+量化切换税，看清什么最常打断我（理论：Newport深度工作/Leroy注意力残留/Csikszentmihalyi心流/Rubinstein切换成本/Gloria Mark/Cirillo番茄钟/Zeigarnik） | `E:/Skills/self/self-focus-agent/` | ✅ 已写 v2.0.0（9 文件，理论做到位） | **4.7** 优秀 |
| 12 | self-decide-agent | 决策日志+回放评分引擎：事前preter/premortem+单向门/二阶，事中记录可逆性，事后回放打分+可逆性误判检测+反复偏差识别+问责报告。理论13条带出处（Bezos单向门/后悔最小化/Klein pre-mortem/Marks二阶/KT损失厌恶/锚定/Staw沉没成本/Kahneman外部视角/Welch 10-10-10/Snowden Cynefin/Boyd OODA/Dixit实物期权/Baumeister）；文件20个（10篇references+3 resources+examples） | `E:/Skills/self/self-decide-agent/` | ✅ 已写 v2.0.0（20 文件，理论13条加量） | **4.8** 优秀 |
| 13 | self-learn-agent | 知识消化+抗遗忘间隔重复：把书/课吃透成你的私有库 | `E:/Skills/self/self-learn-agent/` | ✅ 已写 v2.0.0（21 文件，理论12+条带出处；真引擎 learn.py：ingest/review/quiz/elaborate/interleave/report；SM-2+Leitner间隔；jsonl+md实物证据；退出码0/1/4；冒烟36/0） | **4.7** 优秀 |
| 14 | self-master-agent | 技能登顶阶梯+实战检验：帮你从入门到精通一门技能（L1入门→L5登顶，实数实战驱动晋升） | `E:/Skills/self/self-master-agent/` | ✅ 已写 v2.0.0（22 文件，理论12+条带出处；真引擎 master.py：add/ladder/drill/measure/report/plan；Dreyfus五阶段/Ericsson刻意练习/ACT-R程序性知识/心流/迁移/元认知校准等；五级阶梯逐级晋升+弱项预警；jsonl+md实物证据；退出码0/1/4；冒烟33/0） | **4.7** 优秀 |
| 15 | self-sleep-agent | 睡眠质量趋势+生理节律学习：记录每晚睡眠、学出你的时型与社会时差、量化睡眠债与规律性、预警弱项并给出本周计划 | `E:/Skills/self/self-sleep-agent/` | ✅ 已写 v2.0.0（22 文件，理论12+条带出处；真引擎 sleep.py：log/trend/rhythm/nudge/report/plan；Borbély双过程 1982/Phillips SRI 2017/Roenneberg MCTQ 2003/Wittmann社会时差 2006/Hirshkowitz时长 2015/Irish睡眠卫生 2015/Rechtschaffen分期 1968/Czeisler光照 1986/Stickgold记忆巩固 2005/Spielman SRT 1987/Morin CBT-I 2006/Ohayon年龄化 2004/Jones时型GWAS 2019/Dinges睡眠惯性 1985；睡眠效率/潜伏期/WASO/中点/睡眠债/规律性/SRI近似/时型/社会时差/弱项判定；jsonl+md实物证据；退出码0/1/4；冒烟53/0） | **4.8** 优秀 |
| 16 | self-fitness-agent | 训练负荷与恢复管理：记录训练、量化 ACWR/单调性、预警伤痛风险、给渐进计划 | `E:/Skills/self/self-fitness-agent/` | ✅ 已写 v2.0.0 | **4.8** 优秀 |
| 17 | self-budget-agent | 个人记账与存钱：记录每笔收支、算清储蓄率与钱去哪了、量化应急金够撑几个月、点名漏钱分类、给本周唯一行动 | `E:/Skills/self/self-budget-agent/` | ✅ 已写 v2.0.0（23 文件，理论13条带出处；真引擎 budget.py：set/log/trend/budget/risk/plan/report；Warren&Tyagi 50-30-20 2005/美联储应急金2019/Bengen 4%1994+Trinity1998/Thaler心理账户1985/Laibson双曲贴现1997+Thaler&Benartzi SMT2004/Prelec&Loewenstein支付痛感1998+Feinberg1986/Arkes&Blumer沉没成本1985/Tversky&Kahneman锚定1974/Brickman享乐适应1971·1978/Malkiel复利1973/Ramsey雪球2003+Kellogg2020/Harkin自我监控元分析2016/Domínguez&Robin FIRE1992；储蓄率/折算月支出/固定支出占比/必需-想要/变异系数/应急金覆盖/分类预算执行；jsonl+profile+md实物证据；退出码0/1/2/4；冒烟75/0） | **4.8** 优秀 |
| 18 | self-communicate-agent | 对话复盘+模式识别+下次话术：帮你把话说对 | `E:/Skills/self/self-communicate-agent/` | ✅ 已写 v2.0.0（24 文件，理论14篇带出处；真引擎 comm.py：set/log/trend/review/script/risk/plan/report；Stone&Patton&Heen 困难对话三层次1999/Rosenberg NVC 2003/Patterson 关键对话2002/Fisher&Ury 立场换利益1981/Rock SCARF 2008/Kluger&DeNisi 反馈元分析1996/Scott 激进坦诚2017/Luft&Ingham Johari窗口1955/Lieberman 情绪标注2007/Rogers 积极倾听1957/Thomas&Kilmann TKI冲突1974/Asch 印象形成1946/Edmondson 心理安全1999/Altman&Taylor 社会渗透1973/Ericsson 刻意练习1993；结果率/防御率/对抗率/语气/被听懂率/关系账/身份层占比/情绪成本/话术率/最弱场景+三层次卡点识别(事实/情绪/身份,优先级身份>情绪>事实)；jsonl+profile+md实物证据；退出码0/1/2/4；冒烟71/0） | **4.8** 优秀 |
| 19 | self-create-agent | 作品集+灵感库+登顶曲线：帮你持续产出、越创越强 | `E:/Skills/self/self-create-agent/` | ✅ 已写 v2.0.0（24 文件，理论14篇带出处；真引擎 create.py：set/idea/work/trend/review/script/risk/plan/report；Csikszentmihalyi 心流1990/Ericsson 刻意练习1993/Wallas 创作四阶段1926+Guilford 发散聚合1956/Koestler 组合创造1964/Cameron 灵感捕捉1992/Pressfield 阻力2002+Ries 精益创业2011/Amabile 内在动机1982·1996+共识评估/Deci&Ryan 自我决定1985/Oyserman 身份动机2011/Clear 习惯叠加2018/Markowitz 组合1952+Koriat 元认知校准1993；频率/质量趋势/完成率/打磨率/发布率/灵感兑现率/最长断档/主题跨度；原创量化点=创作闭环卡点推断(灵感变作品/启动到完成/完成到打磨/打磨到发布/质量提升/持续产出/聚焦与跨度/登顶健康)；jsonl+profile+md实物证据；退出码0/1/2/4；冒烟59/0） | **4.8** 优秀 |
| 20 | self-soothe-agent | 情绪曲线+CBT 工具包：帮你稳下来、别被情绪卷走 | `E:/Skills/self/self-soothe-agent/` | ✅ 已写 v2.0.0（24 文件，理论13篇带出处；真引擎 soothe.py：set/log/trend/review/script/risk/plan/report；Beck 1976/Burns 1980/Ellis 1962/Gross 1998/Kabat-Zinn 1990/Linehan 1993/Hayes 1999/Lazarus/Sapolsky 1998/Fredrickson 2001/Nolen-Hoeksema 1991/Wegner 1987/Tice 2001/Pennebaker 1997；频率/平均强度/强度趋势/最常见情绪/主导认知扭曲/应对有效性/高频诱因/影响面(睡眠·关系)；原创量化点=主导认知扭曲推断(优先级 情绪过载>高强波动>应对低效>主导扭曲清晰>均衡>健康)；events.jsonl+profile+md实物证据；退出码0/1/2/4；冒烟46/0） | **4.8** 优秀 |

## 统一交付标准（每条必过）
- 五维自评（T/R/A/C/E）改到完美，写进各自 `SELF_EVAL.md`。
- 深度剖析：references 下至少 2 篇方法论长文，不两三个文件糊弄。
- 主动 Agent：SKILL.md 含"主动触发"段落，能自己干活而非被动问答。
- 项目名（slug/文件夹/title 字段）全英文（用户自定品牌标识）；**包内所有文件内容全中文**，对国人友好，仅命令行参数名（如 `--eval`）保留英文技术惯例。第三人称站位（禁用"你是 X"命令式）。
- 4.7 公式件：SKILL.md + scripts 引擎(preflight+中文报错+退出码) + references×2 + FAQ.md + README.md(导航) + resources。

## 已交付 v2.0.0 汇总（深度版）

| 名称 | 存放位置 | 描述 | 五维自评 TRACE | 文件数 |
|---|---|---|---|---|
| self-evaluate-agent | `E:/Skills/self/self-evaluate-agent/` | 元认知评估与反思引擎。Reflexion 多轮闭环（打分→反思→重写→重评→收敛）+ 元认知校准（Brier/OCI），含客观探针预检、七套 rubric、三篇方法论长文 | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 10 |
| self-protect-agent | `E:/Skills/self/self-protect-agent/` | 自我边界守护引擎。scan 红线扫描 + check 预执行校验（路径保护/批量/HITL）+ record 近失累积 + audit 趋势报告；v2.0.1 小升级：scan/check 加 --json（CI/钩子门禁）+ 新增 RL-FORK-BOMB/RL-DROP-DB/RL-GIT-CLEAN/RL-CHMOD-000，curl 管道扩展到 wget | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 11 |
| self-reflect-agent | `E:/Skills/self/self-reflect-agent/` | 日三省引擎。log 反省记录 + pattern 跨时间惯性识别 + claim/blindspot 言行盲点（双环警报退出4）+ aar 四问复盘 + report 周期报告；理论：Schön反思实践/Argyris单双环/Gibbs/Brookfield四透镜/AAR/Dweck成长型/Flavell元认知 | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 9 |
| self-discipline-agent | `E:/Skills/self/self-discipline-agent/` | 自律承诺装置引擎。commit 登记(后果/监督人/类别)+checkin 履约打卡+streak 连续履约+audit 违约检测(按类别暴露最易破类型)+report 问责报告；理论：承诺装置(Thaler&Sunstein)/预承诺(Schelling)/实施意图(Gollwitzer)/自我损耗(Baumeister,争议标注)/习惯回路(Duhigg)/透明助推(Sunstein) | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 9 |
| self-habit-agent | `E:/Skills/self/self-habit-agent/` | 习惯叠加/streak 引擎。define 锚点+新行为+线索(生成叠加公式)+checkin 每日打卡(去重)+streak 连击统计+lapse 断签分级(中断1/长期未养成4)+report 养成进度(最稳/最易断+微习惯重启)；理论：习惯叠加(Clear)/习惯回路(Duhigg)/养成天数(Lally 66·18-254)/微习惯(Guise)/执行意图(Gollwitzer) | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 9 |
| self-focus-agent | `E:/Skills/self/self-focus-agent/` | 深度工作/防干扰引擎。plan 规划专注块+log 记录实际专注(时长/打断/来源)+interrupt 单次干扰(来源归一)+measure 度量(打断过多/时长不足→1)+report 趋势+干扰来源Top+长期评估(日均不足→4)；理论扎实：Newport深度工作/Csikszentmihalyi心流/Leroy注意力残留/Rubinstein切换成本/Gloria Mark中断恢复/Cirillo番茄钟/Zeigarnik/Weinberg，并诚实标注争议与无出处网络说法 | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 9 |
| self-decide-agent | `E:/Skills/self/self-decide-agent/` | 决策日志/回放评分引擎。7子命令：frameworks(框架库12)/log(记录+偏差预检+框架标注)/replay(打分+可逆性误判检测)/premortem(假设失败+二阶+可逆校验)/bias(反复偏差→1)/report(误判率+后悔最小化，严重≥2→4)/list；资源3个(13偏差库/12框架库/三阶段自问)；references 10篇长文逐条带出处 | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 20 |
| 打包(zip) | `E:/Skills/self/self-evaluate-agent-2.0.0.zip` | 去 BOM、CRLF→LF、扁平结构（SKILL.md 在根）、排除运行时日志与冗余文件 | — | 1 |
| self-soothe-agent | `E:/Skills/self/self-soothe-agent/` | 情绪调节与 CBT 工具包。记录每次情绪事件的诱因/强度/自动思维/认知扭曲/应对/缓解；量化频率·平均强度·强度趋势·最常见情绪·主导认知扭曲·应对有效性·高频诱因·影响面；原创量化点=主导认知扭曲推断（优先级 情绪过载>高强波动>应对低效>主导扭曲清晰>均衡>健康）；13 篇方法论长文（Beck/Burns/Ellis/Gross/Kabat-Zinn/Linehan/Hayes/Lazarus/Sapolsky/Fredrickson/Nolen-Hoeksema/Wegner/Tice/Pennebaker） | T5 / R5 / A5 / C5 / E5 = **5.0/5** | 24 |

### v2.0.0 相对 v1.0.0 的关键升级
1. **定位**：打分记录器 → 元认知评估与反思引擎（Reflexion + 元认知理论根基）。
2. **真引擎**：`evaluate.py` 新增客观探针、低分强制证据、收敛分析；`calibrate.py` 实现 Brier/OCI 元认知校准（v1.0.0 完全没有）。
3. **评分标准库化**：单套 → 七套（TRACE/WRITING/CODE/PRODUCT/SELF_AGENT/REASONING/SAFETY），含锚点与探针钩子。
4. **深度长文×3**：reflexion-method / metacognition / rubric-design，各 ≥3K 字。
