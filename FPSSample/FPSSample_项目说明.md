# FPS Sample

独立复现 Unity FPS Sample 多人射击示例，用于学习 HDRP 高级渲染特性、多人网络同步架构与 ECS 性能优化。

> 源仓库：[Unity-Technologies/FPSSample](https://github.com/Unity-Technologies/FPSSample)

## 拓展内容

网络同步是这个项目最有含金量的部分。通读了 Netcode 的客户端预测（Client-Side Prediction）与服务器权威回滚（Server Reconciliation）实现，理清了输入快照和状态快照的序列化协议，然后在模拟 200ms 高延迟的环境下对比开启和关闭预测的操作响应差异，延迟感完全不是一个量级。

渲染上重点研究了两个模块。一个是 HDRP 的皮肤次表面散射（SSS）profiles 配置，复刻了角色近距离受光时的边缘透光效果；另一个是 Volumetric Fog 的密度衰减参数，调整高度衰减曲线后解决了室内外过渡处的亮度跳变。

性能架构方面，梳理了项目里 damage、movement、projectile 几个系统如何用 IJobChunk 并行处理大量实体，在 64 个同步移动单位的场景下对比了主线程逐实体更新和 Jobs 分片调度的耗时差距。

角色动画研究了 locomotion 状态机与程序化 IK（脚部贴地、持枪手部对位）的混合权重分配，跑动、急停、瞄准三态过渡中上半身分层动画的 Layer Mask 遮罩配置复刻了一遍。

最后用 Unity Profiler 和 Frame Debugger 定位了 Screen Space Shadows 与 volumetric pass 在低端 GPU 上的耗时占比，把体积雾采样步数降下来、后处理 Pass 合并之后，1080p 下 GPU 帧时间降了约 15%。
