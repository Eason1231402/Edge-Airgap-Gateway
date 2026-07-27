  # Edge-Assisted Smart Home Gateway with Hardware-Level Air-Gap

  > 基于物理熔断机制的边缘计算隔离架构 —— 从专利构想到实物原型与学术验证

  ## 项目背景

  简述"云端语音助手隐私泄露"这一问题的第一性原理分析（1-2段，可参考论文Introduction）。

  ## 核心成果

  - **发明专利**：《一种基于物理熔断机制的智能中控系统及方法》
  - **申请号**：202610261302.7｜ 状态：实质审查阶段 ｜ 申请人/第一发明人
  - **学术论文**：*Edge-Assisted Smart Home Gateway with Hardware-Level
    Air-Gap for Deterministic Privacy*, IEEE GAIIS 2026（第一作者）
  - **实物原型**：树莓派5 + 双路通信拓扑 + 电磁继电器物理熔断模块

  ## 技术演进路线（路线一，主线）

  1. **阶段一**：Qwen2.5 1.5B部署，跑通语音指令解析逻辑
  2. **问题**：复杂指令响应存在延迟
  3. **解决**：引入if-else快速响应路径，兼顾灵活性与实时性
  4. 详见 `software/nlp_pipeline/README.md`

  ## 延伸方向（专利二，非本仓库重点）

  在完善专利一的过程中，识别到"软件级隔离仍无法应对物理级攻击"的更深层问题，
  提出了基于热力学熵与纳秒级物理短接的下一代防御思路（专利申请中，尚未实物验证）。
  详见 `patent/patent2_future_direction.md`。

  ## 商业化探索（路线二三，简述）

  参与北京大学上海临港国际科技创新中心"燕缘·协创者号 AI+ 国际创业大赛 | SynNovator"，尝试将上述架构转型为AI安全插件，
  线下决赛评审中未获奖项，但在临港管委会数据处的推荐下，获得临港集团'零界魔方'孵化器初步入驻资格并签署意向书。
  后续在推进商业化落地时，发现现阶段团队资源与市场化能力尚不足以支撑独立运营，主动终止入驻流程，转而聚焦回核心技术研发。
  该阶段的具体经验与局限见 `docs/route2_exploration.md`。

  ## 演示视频

  - `prototype/demo_video_route1.mp4`：物理熔断触发全过程

  ## 引用

  如引用本项目相关论文，请使用：
  ```
  Y. Chen and M. Zha, "Edge-Assisted Smart Home Gateway with
  Hardware-Level Air-Gap for Deterministic Privacy," 2026 IEEE GAIIS.
  ```
