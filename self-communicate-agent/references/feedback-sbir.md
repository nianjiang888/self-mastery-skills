# 反馈怎么给：SBI-R 与激进坦诚

## 出处

- SBI-R（情境-行为-影响-请求）模型：源自行为科学与管理反馈实践，Center for Creative Leadership 等机构广泛采用。
- Scott, K. (2017). *Radical Candor: Be a Kick-Ass Boss Without Losing Your Humanity*. St. Martin's Press. 提出「关心 personally + 直接挑战 directly」二维框架。
- 经典对照：Kluger & DeNisi (1996). "The Effects of Feedback Interventions on Performance: A Historical Review, a Meta-Analysis, and a Preliminary Feedback Intervention Theory." *Psychological Bulletin*, 119(2), 254–284.

## 核心结论

Kluger 与 DeNisi 的元分析有个不太舒服的发现：**超过三分之一的反馈干预，实际上让表现变差了。** 反馈不是天然有益的，给错了就是负资产。

两个模型分别解决「怎么说」和「敢不敢说」。

### SBI-R：怎么说

1. **S 情境**——时间地点。「周二上午的客户会」。跳过情境，对方根本不知道你在说哪件事。
2. **B 行为**——只描述可观察的动作，不评价人格。「客户提问时你打断了三次」，不是「你太不尊重人了」。
3. **I 影响**——这个行为造成了什么实际后果。「客户后来基本不说话了」。**这一步最常被跳过，也最要命。**
4. **R 请求**——具体的下一步。「下次能不能先让客户说完？」

为什么「影响」不能省：人不介意被指出问题，介意的是不知道为什么要改。没有影响，反馈听起来就像挑刺。

### 激进坦诚：敢不敢说

Scott 的二维框架：

|  | 直接挑战 | 不直接挑战 |
|---|---|---|
| **关心对方** | 激进坦诚（Radical Candor） | 毁灭性同理（Ruinous Empathy） |
| **不关心对方** | 令人讨厌的攻击（Obnoxious Aggression） | 操纵性虚伪（Manipulative Insincerity） |

多数人的问题出在**毁灭性同理**——怕伤感情，该说的不说，事后在别处抱怨。这被 Scott 认为是四种里危害最大的，因为它同时毁掉了反馈和信任。

## 怎么用

- 话术库里 SBI-R 模板对应 `script --scene 反馈 --goal 达成`。四步都有具体的说法和示例。
- 本引擎的 `reaction` 字段可以验证你反馈的效果：如果你的反馈后对方频繁进入「防御」，多半是 B（行为）和 I（影响）混在一起了——你描述行为时夹带了评价。
- **`goal` 设为「达成」但 aftermath 为负**，通常说明你的直接挑战过了头，对方没感受到关心。此时把目标改成「关系」再谈一次。

## 边界与误用

- **SBI-R 适合具体行为的反馈，不适合根本性的价值分歧或绩效定性。** 后者是另一类对话。
- **「激进」不等于「粗暴」。** Scott 反复强调，缺少关心的直接挑战只是攻击。
- **时机很重要。** 当众反馈几乎必然触发地位威胁（见 SCARF 模型）。除非对方明确要求公开，否则私下一对一。
- 本引擎不评估你的反馈是否正确，只记录发生了什么和你的自评结果。
