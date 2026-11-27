---
created: 2026-11-26
updated: 2026-11-27
---

<!--
这个文件是一篇文章的高亮和批注，页面在 docs/read.html?id=<文件名>。格式说明见 README 的"批注页"一节。
英文是原文的摘录，逐字保留；中文是译文。备注是读的人自己的话，解读是 Claude 写的。
-->

## 原文结构

- 0 | Introduction | 引言
- 5.3 | Summary of findings | 主要发现
- 10.3 | Simple settings | 简单设定
- 19.7 | Low-level locomotion | 低层运动
- 27.2 | Low-level manipulation | 低层操作
- 33.4 | High-level locomotion | 高层运动
- 42.4 | High-level manipulation | 高层操作
- 51.7 | Visual perception | 视觉感知
- 58.7 | Vision tools on the Go2 | 真机视觉工具
- 61.9 | Reasoning | 推理
- 66.2 | Learning from experience | 从经验学习
- 75.2 | Real-world vignettes | 真机小故事
- 80.1 | Conclusion | 结论
- 82.0 | Appendix | 附录

## 第一遍总结

### 文章的结论 | What the article concludes

**中文**

- 模型在机器人任务上的能力，很大程度上取决于它和机器人的连接方式。亲自驱动关节大多失败；监督预训练控制器，或使用简单的定向工具，就能完成真实的导航和操作任务。（A001）
- 代际提升很大一部分来自"看到结果后调整策略"：各代模型的首次尝试相差不大，差距出现在后续尝试。（A004）
- 在经典控制任务上，几乎所有模型自己训练 RL 策略，都不如自己手写控制器。（A005）
- 人形最难。没有一个模型让 G1 从倒地站起；没有预训练策略，前沿模型控制不了人形。
- 配上预训练步态，模型能完成简单导航；需要持续空间记录或开环规划的任务稳定失败，瓶颈主要是掌握自己在哪。（A007）
- 有效的辅助是定向信息。光标和指南针对测试过的每个模型和配置都有帮助，深度图和分割叠加大致中性。（A008、A011）
- 直接控制的成绩是上限。测试时在两次模型调用之间暂停了仿真器；实时控制约需 83 Hz，当前模型约 0.2 到 0.4 Hz。（A003）

**EN**

- A model's robotics capability depends heavily on how it is connected to the robot. Driving the joints directly mostly fails; supervising a pretrained controller, or using simple orientation tools, lets it complete real navigation and manipulation tasks. (A001)
- Much of the generational improvement comes from revising strategy after seeing outcomes: first attempts are similar across generations, and the gap appears in later attempts. (A004)
- On classic-control tasks, nearly every model does worse training its own RL policy than writing a controller by hand. (A005)
- The humanoid is the hardest. No model stood the G1 up from a collapsed pose, and frontier models cannot control a humanoid without a pretrained policy.
- With a pretrained gait, models complete simple navigation; tasks that need sustained spatial bookkeeping or open-loop planning fail reliably, and the main bottleneck is keeping track of where the robot is. (A007)
- The aids that work are orientation aids. The cursor and the compass help every model and configuration tested, while depth maps and segmentation overlays are roughly neutral. (A008, A011)
- Direct-control scores are an upper bound. The simulator was paused between model calls; real-time control needs about 83 Hz, and current models run at about 0.2 to 0.4 Hz. (A003)

### 我们的看法 | Our views

**中文**

- **我的判断** 本体、模型、接口三者之中，接口的设计与实现更重要。原文说的是三者同等重要，"更重要"是我们的判断。（A001）
- **我的判断** 自训策略的成绩，很可能受限于训练管线。附录显示它是基础的 PPO 设置，默认最多 32 个并行环境，策略网络上限 20 万参数；这是不是主因，原文没有验证。（A006）
- **我的判断** 深度图没有帮助，可能是叠加造成的。原文只测了"叠加在 RGB 上的热力图"这一种给法，只能说明这种给法没用。（A011）
- **Claude 的推断** 三条看法指向同一点：模型拿到什么工具、信息以什么形式给，决定了测出来的能力。原文结论里也有同样的话：工具或控制上的小改动，会带来能力上的大变化。

**EN**

- **My judgment** Among the body, the model and the interface, the design and implementation of the interface matters more. The article says the three matter equally; "more" is our judgment. (A001)
- **My judgment** The self-trained policy results are likely limited by the training pipeline. The appendix shows a basic PPO setup, with up to 32 parallel environments by default and a policy network capped at 200,000 parameters; the article does not test whether this is the main cause. (A006)
- **My judgment** The depth map may have failed because it was overlaid. The article tested only a heatmap overlaid on the RGB image, so it shows only that this form did not help. (A011)
- **Claude's inference** The three views point to the same thing: which tools a model gets, and the form its information comes in, decide the capability that gets measured. The article's conclusion says the same: small changes in tools or control can produce large changes in capability.

### 经验 | Lessons

**中文**

以下由 Claude 根据批注和讨论归纳。

- 先定接口层级，再比模型。同一个模型换一种接口，结论就不同；比较方案要在同一层接口上比。
- 人形要从监督预训练策略起步。原文里没有预训练策略就控制不了人形，让 G1 从倒地站起的尝试全部失败。
- 给模型的信息要少而准。按需查询一个点、用文字给出朝向，比整张叠加图有效。
- 监督预训练策略时，少干预也是能力。在 VLA 熟悉的任务上，所有模型加上监督后都不如 VLA 单独运行；Mythos Preview 否决得太多，成绩不如 Opus 4.5 和 4.6。
- 读成绩先看测量条件。直接控制是暂停仿真器测出的上限；每次平衡尝试之间会重置环境；光标的 6% 到 32% 只基于 50 次试验。
- 正文之外要读附录。A006 的判断在读到附录之后，从"无法证实"改成了"脚手架是基础设置"。

**EN**

Drafted by Claude from the annotations and the discussion.

- Fix the interface level before comparing models. The same model gives a different conclusion under a different interface, so compare options at the same interface level.
- For a humanoid, start from supervising a pretrained policy. In the article, models cannot control a humanoid without one, and every attempt to stand the G1 up from a collapsed pose failed.
- Give the model little information, but precise. Querying one point on demand, or stating the heading as text, works better than a whole-image overlay.
- When supervising a pretrained policy, intervening less is part of the skill. On tasks the VLA knows, every model supervising the VLA does worse than the VLA alone; Mythos Preview overrides too often and scores below Opus 4.5 and 4.6.
- Check the measurement conditions before reading a score. Direct control is an upper bound measured with the simulator paused; the environment is reset between balancing attempts; the cursor's 6% to 32% rests on 50 trials.
- Read the appendix, not only the main text. The assessment in A006 changed from "cannot be confirmed" to "the scaffold is a basic setup" after reading it.

### 还没解决的问题 | Open questions

**中文**

- **我的问题** 换成成熟的训练管线（SuperMimic、XMimic）之后，自训策略的结果会不会改观？要注意这样测的是"模型会不会用管线"，不再是"模型会不会设计 RL 训练"。（A006）
- **我的问题** 深度信息到底有没有用？需要对照四种给法：RGB、RGB 加单独深度图、叠加、文字数值。（A011）
- **Claude 提出** 光标工具在真机上还有多大效果？原文只有仿真结果，也没有说明物体名和距离的数据从哪里来。
- **Claude 提出** "接口更重要"怎么验证？需要两组对照，一组固定模型换接口，一组固定接口换模型，都在目标本体上做。
- **Claude 提出** 在宇树人形上，让模型监督哪个预训练策略、用什么指令接口？原文只说明需要预训练策略，没有回答选哪一个。
- **Claude 提出** 代码发布后要回头核对。附录说代码会放在 github.com/safety-research/embody，脚手架和工具的实现到时可以确认。
- **Claude 提出** 第二遍要读的部分：主要发现、低层操作、高层操作（VLA 监督）、推理、从经验学习、真机小故事、结论。这些部分第一遍没有高亮。

**EN**

- **My question** Would a mature training pipeline (SuperMimic, XMimic) change the self-trained policy results? Note that this would test whether the model can operate a pipeline, not whether it can design RL training. (A006)
- **My question** Is depth information useful at all? This needs four conditions: RGB, RGB plus a separate depth image, overlay, and numeric text. (A011)
- **Raised by Claude** How much does the cursor tool help on a real robot? The article reports only simulation results and does not say where the object name and distance come from.
- **Raised by Claude** How can "the interface matters more" be tested? It needs two comparisons, one with a fixed model and varied interfaces and one with a fixed interface and varied models, both on the target body.
- **Raised by Claude** On a Unitree humanoid, which pretrained policy should the model supervise, and through what command interface? The article shows that a pretrained policy is needed, not which one to choose.
- **Raised by Claude** Check again when the code is released. The appendix says it will be at github.com/safety-research/embody; the scaffold and tool implementations can be confirmed then.
- **Raised by Claude** Sections for a second pass: summary of findings, low-level manipulation, high-level manipulation (VLA supervision), reasoning, learning from experience, real-world vignettes, conclusion. None has a highlight yet.

## A001

- section: Introduction（引言，第 3 段）
- link: https://www.anthropic.com/research/claude-plays-robotics
- added: 2026-11-26
- pos: 2.4

**EN**

> Models are getting better at robotics quickly, but we found that how capable they are depends heavily on how they are connected to the robot—which of the control methods they used. When they must drive the joints themselves they mostly fail. But when they supervise a pretrained controller or use simple orientation tools, they can complete real navigation and manipulation tasks. Some forms of embodiment remain unwieldy and difficult to control, but newer models, especially, are substantially stronger at adjusting their strategies and converting image and sensory understanding into appropriate actions across domains.

**中文**

> 模型在机器人任务上进步很快，但我们发现，它们能力的高低在很大程度上取决于它们与机器人的连接方式——即使用的是哪一种控制方法。当必须亲自驱动关节时，它们大多会失败。但当它们监督一个预训练控制器，或使用简单的定向工具时，就能完成真实的导航和操作任务。某些具身形态仍然笨拙、难以控制，但较新的模型尤其在调整策略、以及跨领域地将对图像和传感信息的理解转化为恰当动作方面，明显更强。

**备注**

读到这里，最大的启发正是这段话所说的：用 Agent 控制机器人，效果由三件事共同决定——要控制的本体、选用的模型，以及把两者连起来的控制方式，也就是接口的设计与实现。三者之中，接口的设计与实现更重要。

**Note**

The biggest takeaway so far is exactly what this passage says: when an agent controls a robot, the outcome is determined by three things together — the body you want to control, the model you choose, and the control method that connects them, i.e. the design and implementation of the interface. Of the three, interface design and implementation matters more.

## A002

- section: Simple settings（简单设定，第 2 段）
- link: https://www.anthropic.com/research/claude-plays-robotics#simple-settings
- added: 2026-11-26
- pos: 11.1

**EN**

> In these low-dimensional environments, sensory data provides nearly all the necessary information, allowing them to be solved with little to no visual input. This kind of low-dimensional control also arises in some real-world settings, such as camera stabilization.

**中文**

> 在这些低维环境中，传感数据几乎提供了全部所需的信息，因此只需很少、甚至完全不需要视觉输入就能求解。这类低维控制在一些真实场景中也会出现，例如相机增稳。

## A003

- section: Simple settings（简单设定，第 4 段）
- link: https://www.anthropic.com/research/claude-plays-robotics#simple-settings
- added: 2026-11-26
- pos: 12.9

**EN**

> To approximate an upper bound on direct-control performance, we pause the simulator between LLM calls so real-time latency does not dominate the results. Without this, many direct tests would fail for a trivial reason: the models would simply react too slowly to control the environment. We expect inference speed to continue increasing, and this setup gives a clear view of best-case capability as it does.

**中文**

> 为了近似直接控制性能的上限，我们在两次 LLM 调用之间暂停仿真器，使实时延迟不至于主导结果。如果不这样做，许多直接控制测试会因为一个无关紧要的原因而失败：模型反应太慢，根本来不及控制环境。我们预计推理速度会持续提升，而这一设置能让我们清楚地看到，随着速度提升，模型在最佳情况下的能力。

## A004

- section: Simple settings（简单设定，第 7 段首句，经典控制结果图之后）
- link: https://www.anthropic.com/research/claude-plays-robotics#simple-settings
- added: 2026-11-26
- pos: 16.5

**EN**

> Our results suggest that much of the improvement comes from a better ability to adapt after seeing prior outcomes and to revise strategy accordingly.

**中文**

> 我们的结果表明，大部分提升来自一种更强的能力：在看到先前的结果之后进行适应，并据此修正策略。

## A005

- section: Simple settings（简单设定，第 8 段，RL 策略结果图之后）
- link: https://www.anthropic.com/research/claude-plays-robotics#simple-settings
- added: 2026-11-26
- pos: 17.7

**EN**

> Nearly all models performed worse when training an RL policy than they did when creating a Pythonic controller. The standout is TwinFlipper, where GPT-5.4 was the only model that consistently learned a competent policy. This is striking in light of its relatively poor performance under the other control interfaces. On Pendulum and Hopper the picture is different: Mythos Preview leads, GPT-5.4 is close behind, and the spread across models is much narrower. Across all three tasks, newer Claude models show a meaningful improvement over older ones.

**中文**

> 几乎所有模型在训练 RL 策略时的表现，都不如它们编写 Python 控制器时。最突出的是 TwinFlipper：GPT-5.4 是唯一能稳定学出合格策略的模型。考虑到它在其他控制接口下表现相对较差，这一点尤其引人注目。在 Pendulum 和 Hopper 上情况则不同：Mythos Preview 领先，GPT-5.4 紧随其后，各模型之间的差距要小得多。在全部三个任务上，较新的 Claude 模型都比旧模型有明显提升。

**解读**

问题：为什么训了 RL 策略，反而不如不训？

回答：这里比的不是"训与不训"，而是两种做法——模型手写控制器，和模型自己搭 RL 流程再训出策略。它反映的是模型搭建 RL 训练的水平，不是 RL 方法本身的上限。

原文的解释（见下一段）：

- 自训策略要先定义环境和奖励，迭代周期更长，多个设计选择互相牵连。
- 在目标难以指定的任务上（Hopper、TwinFlipper），RL 在进步，但仍落后于手写控制器。

Claude 的推断（非原文）：

- 低维任务用简单规则就能写出可用的控制器，手写的起点高。
- 手写控制器改一版很快，RL 要训完才有反馈；A004 说提升很大程度上来自"看结果后改策略"，RL 下能改的次数更少。
- 这一结论只针对三个低维经典控制任务；高自由度本体的情况要另看后文 Go2/G1 的对比。

**Interpretation**

Question: Why does training an RL policy do worse than not training one?

Answer: The comparison is not "trained vs. untrained". It is between two approaches: the model writing a controller by hand, and the model building its own RL pipeline and then training a policy. It reflects how well the model can set up RL training, not the ceiling of RL as a method.

The article's explanation (see the next paragraph):

- Training its own policy requires defining the environment and reward, managing longer iteration cycles, and making several interdependent design choices.
- On tasks with harder-to-specify objectives (Hopper, TwinFlipper), RL is improving but still lags behind code control.

Claude's inferences (not from the article):

- On low-dimensional tasks, simple rules are enough for a usable controller, so hand-written code starts from a high baseline.
- A hand-written controller can be revised quickly, while RL gives feedback only after training. A004 says much of the improvement comes from revising strategy after seeing outcomes, and RL allows fewer revisions.
- This finding covers only the three low-dimensional classic-control tasks; for high-DoF bodies, see the Go2/G1 comparison later in the article.

## A006

- section: Direct control is bad, but improving › Low-level locomotion（低层运动控制，Go2/G1 手写与自训策略对比图之后）
- link: https://www.anthropic.com/research/claude-plays-robotics#direct-control-is-bad-but-improving
- added: 2026-11-26
- pos: 25.3

**EN**

> We also evaluated how well models can train locomotive policies. To do this, we gave them a training scaffold with access to a GPU and visualization environment, and let it control the reward function, training environment, and model architecture. Over four hours, GPT-5.4 and Claude Mythos Preview consistently train the most competent RL policies, confirming our previous results on classic RL tasks. We also observe a progression within the Claude family, with performance improving from Opus 4 to Opus 4.6 and improving further with Mythos Preview.

**中文**

> 我们还评估了模型训练运动策略的能力。为此，我们给它们提供了一个训练脚手架，可以使用 GPU 和可视化环境，并让模型自行掌控奖励函数、训练环境和模型架构。在四小时内，GPT-5.4 和 Claude Mythos Preview 稳定地训练出了最出色的 RL 策略，这印证了我们此前在经典 RL 任务上的结果。我们还观察到 Claude 系列内部的递进：从 Opus 4 到 Opus 4.6 性能逐步提升，到 Mythos Preview 又进一步提升。

**备注**

这里的自训策略结果，很可能受限于缺少合适的 RL 训练管线。如果换用 SuperMimic 或 XMimic，结果或许会不一样。

**Note**

The self-trained policy results here are likely limited by the lack of a suitable RL training pipeline. With SuperMimic or XMimic, the outcome might be different.

**解读**

判断：方向合理。附录显示脚手架是基础的 PPO 设置，不是成熟的人形训练管线；它是否就是成绩差的主因，原文没有验证。

原文依据：

- 原文提供了训练脚手架（GPU 和可视化环境），奖励函数、训练环境、模型架构由模型自己决定，限时四小时。
- 正文没有说明脚手架的具体内容，所以"缺少合适管线"无法从正文确认。

附录的补充：

- 训练用的是标准 PPO，跑在 GPU 批量 MuJoCo 环境上；模型自己写奖励函数、策略网络和训练计划。
- 默认最多 32 个并行环境，策略网络上限 20 万参数，单次训练调用不能超过会话时长的三分之一。
- 自训策略在人形和四足上只测了 G1 站立和 Go2 从趴姿站起，各限时 4 小时。

背景（已核对 arXiv 摘要）：

- SuperMimic（arXiv 2610.28480）：用一个可微世界模型做人形全身动作跟踪；单 GPU 训练 3 小时，回报超过 128 GPU 训练 7 天的基线；已迁移到真机 G1。提交于 2026-10，晚于本文。
- XMimic（HumanX 的学习框架，arXiv 2602.02473）：从人类视频学习交互技能（球类、搬运、对抗），零样本迁移到真机 G1。

Claude 的推断（非原文）：

- 默认最多 32 个并行环境，而常见的人形 RL 训练通常用数千个；这支持管线受限的判断。
- 成熟管线替模型完成了奖励和环境设计，结果可能更好；但测的就变成"模型会不会用管线"，不再是"模型会不会设计 RL 训练"。这相当于提高了接口的抽象层级（呼应 A001）。
- 两者都是动作模仿管线，需要参考动作；原文任务是从倒地站起和保持平衡，能否套用取决于有没有对应的参考动作。
- XMimic 面向交互技能，与站起、平衡的匹配度不如 SuperMimic。

**Interpretation**

Assessment: The direction is reasonable. The appendix shows the scaffold is a basic PPO setup, not a mature humanoid training pipeline; whether that is the main cause of the weak results is not tested in the article.

From the article:

- The models were given a training scaffold (a GPU and a visualization environment), chose the reward function, training environment, and model architecture themselves, and had four hours.
- The main text does not describe the scaffold in detail, so "lack of a suitable pipeline" cannot be confirmed from it.

From the appendix:

- Training uses standard PPO on a GPU-backed batched MuJoCo environment; the model writes the reward function, policy network, and training schedule.
- By default there are up to 32 parallel environments; the policy network is capped at 200,000 parameters; a single training call cannot use more than one third of the session.
- On the humanoid and quadruped, self-trained policies were tested only on G1 standing and Go2 standing from prone, each with a 4-hour limit.

Background (checked against the arXiv abstracts):

- SuperMimic (arXiv 2610.28480): humanoid whole-body motion tracking with one differentiable world model; in 3 hours on a single GPU it surpasses the return of a baseline trained for 7 days on 128 GPUs; transfers to a physical Unitree G1. Submitted in October 2026, after this article.
- XMimic (the learning framework of HumanX, arXiv 2602.02473): learns interaction skills (ball sports, cargo pickup, reactive fighting) from human videos and transfers them zero-shot to a physical Unitree G1.

Claude's inferences (not from the article):

- The default is up to 32 parallel environments, while humanoid RL training commonly uses thousands; this supports the view that the pipeline was limiting.
- A mature pipeline does the reward and environment design for the model, so results may improve; but the test then measures whether the model can operate a pipeline, not whether it can design RL training. This amounts to raising the abstraction level of the interface (cf. A001).
- Both are motion-imitation pipelines that need reference motions; the article's tasks are standing up from a collapsed pose and balancing, so whether they apply depends on having matching reference motions.
- XMimic targets interaction skills, so it fits standing up and balancing less well than SuperMimic.

## A007

- section: Tools bridge some of the gap › High-level locomotion（高层运动控制，小节末尾的 Takeaway）
- link: https://www.anthropic.com/research/claude-plays-robotics#tools-bridge-some-of-the-gap
- added: 2026-11-26
- pos: 41.8

**EN**

> Takeaway: Paired with a pretrained gait, current models can complete simple navigation tasks but reliably fail tasks that require sustained spatial bookkeeping or open-loop planning. The bottleneck is primarily keeping track of where the robot is, and small bits of information can remediate some perceptual failures.

**中文**

> 要点：与预训练步态搭配时，当前模型能完成简单的导航任务，但在需要持续记录空间信息或进行开环规划的任务上，会稳定地失败。瓶颈主要在于持续掌握机器人自身的位置，而少量信息就能弥补一部分感知上的失误。

## A008

- section: What's the bottleneck? › Is visual perception the bottleneck?（视觉感知是瓶颈吗，第 4 段）
- link: https://www.anthropic.com/research/claude-plays-robotics#whats-the-bottleneck
- added: 2026-11-27
- pos: 55.0

**EN**

> The cursor tool, by contrast, gives every model a large uplift on manipulation—for Mythos Preview, success on the 10-task subset goes from 6% to 32%. The compass does the same for locomotion, lifting every configuration we tested. In both cases the results suggest that models mainly need better orientation, not a different view of the scene: it is still more helpful to tell the model which way it is facing than to show it a picture of itself.

**中文**

> 相比之下，光标工具让每个模型在操作任务上都有大幅提升——对 Mythos Preview 而言，10 个任务子集上的成功率从 6% 升到 32%。指南针对运动任务起到了同样的作用，我们测试的每一种配置都得到了提升。这两种情况下的结果都表明，模型主要需要的是更好的定向，而不是换一个视角看场景：告诉模型它面朝哪个方向，仍然比给它看一张拍到它自己的画面更有帮助。

## A009

- section: What's the bottleneck? › Is visual perception the bottleneck?（视觉感知是瓶颈吗，第 6 段前两句，"图像换成文字描述"对比图之后）
- link: https://www.anthropic.com/research/claude-plays-robotics#whats-the-bottleneck
- added: 2026-11-27
- pos: 56.9

**EN**

> Visual perception is a more severe limitation for older models than for stronger ones. In other words, newer models are substantially better at extracting spatial information directly from images.

**中文**

> 视觉感知对较老模型的限制，比对较强模型更严重。换句话说，较新的模型直接从图像中提取空间信息的能力明显更强。

## A010

- section: What's the bottleneck? › Vignettes: Vision tools on the physical Go2（真机 Go2 上的视觉工具，第 1 段后半）
- link: https://www.anthropic.com/research/claude-plays-robotics#whats-the-bottleneck
- added: 2026-11-27
- pos: 59.9

**EN**

> In one run there was a small trash can ahead of the robot; the model recognized it and confidently stated that because the can was to the left of the crosshair, it was out of the way and safe to proceed. The trash can was in fact directly in front of the dog. It walked into it, got a leg caught, and dragged the can for a couple of meters before we stopped it.

**中文**

> 有一次，机器人前方有一个小垃圾桶；模型认出了它，并自信地表示，由于垃圾桶在准星左侧，它不挡路，可以安全前进。实际上垃圾桶就在机器狗的正前方。它撞了上去，一条腿被卡住，拖着垃圾桶走了几米，直到我们把它停下。

## A011

- section: What's the bottleneck? › Is visual perception the bottleneck?（视觉感知是瓶颈吗，第 2 段）
- link: https://www.anthropic.com/research/claude-plays-robotics#whats-the-bottleneck
- added: 2026-11-27
- pos: 53.2

**EN**

> On manipulation, the depth maps and segmentation overlays are roughly neutral. They convey the right kind of information, but the signal seems too diffuse to help reliably. On locomotion, the depth heatmap and the crosshair overlay are similarly close to neutral, with the depth heatmap mildly hurting the stronger models.

**中文**

> 在操作任务上，深度图和分割叠加层的效果大致中性。它们传达的信息种类是对的，但信号似乎过于分散，无法稳定地起到帮助。在运动任务上，深度热力图和十字准星叠加层同样接近中性，其中深度热力图对较强的模型略有损害。

**备注**

深度图没有帮助，是否可能是因为它是叠加在画面上使用的？

**Note**

Could the depth map's lack of benefit be because it was used as an overlay on the image?

**解读**

判断：有可能，原文排除不了。原文只证明了叠加的深度热力图没用，没有证明深度信息没用。

原文和附录的事实：

- 机械臂和 Go2 上的深度都是叠加在 RGB 画面上的热力图；没有测单独的深度图，也没有测数值形式。
- 附录：所有公开结果每回合只发一帧图。
- 原文的解释：信息种类是对的，但信号太分散。

Claude 的推断（非原文）：

- 叠加会干扰 RGB 画面；较强的模型更依赖原始图像，而受损的正是它们。
- 光标以文字给出单点距离，效果很大，说明距离信息本身可能有用；但光标同时给了物体名，不能全归因于距离。
- 分割叠加同样中性，所以也可能是整图形式的问题，单独发深度图未必有效。
- 要分清，需要对照四种给法：RGB、RGB 加单独深度图、叠加、文字数值。

**Interpretation**

Assessment: Possible, and the article cannot rule it out. It shows only that an overlaid depth heatmap did not help, not that depth information does not help.

From the article and its appendix:

- On both the arm and the Go2, depth was given as a heatmap overlaid on the RGB image; a separate depth image and numeric depth were not tested.
- Appendix: all published results used one image frame per turn.
- The article's explanation: the information is the right kind, but the signal is too diffuse.

Claude's inferences (not from the article):

- An overlay interferes with the RGB image; stronger models rely more on the raw image, and they are the ones it hurt.
- The cursor gives the distance at a single point as text and helps a lot, which suggests distance information itself may be useful; but the cursor also gives the object name, so the gain cannot be attributed to distance alone.
- The segmentation overlay is also neutral, so the problem may be the whole-image format, and a separate depth image might not help either.
- Telling these apart needs four conditions: RGB, RGB plus a separate depth image, overlay, and numeric text.
