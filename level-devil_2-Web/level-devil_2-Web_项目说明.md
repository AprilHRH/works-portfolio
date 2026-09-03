# FableDevil（Level Devil 2 Web）

独立复现浏览器端陷阱闯关小游戏，用于学习 2D Canvas 游戏架构、碰撞检测优化与移动端适配方案。

> 源仓库：[Leonxlnx/level-devil](https://github.com/Leonxlnx/level-devil)

## 拓展内容

内容层面，在原版 30 关的基础上独立设计并开发了 5 个新关卡，分别是反向控制加电锯加压碎器、摆锤传送带、按钮机关门、双炮台交叉火力、传送门加激光，复用 Trap 基类状态机组合出了新的难度曲线。陷阱机制本身也做了扩展，新增传送门、按钮加机关门、摆锤、炮台四类陷阱，统一抽象成 Trap 基类的状态机（待机 / 触发 / 复位），新陷阱只需要实现三个回调就能挂载到关卡编辑数据里。

性能上做了一次碰撞检测重构。原来是逐帧全量 AABB 遍历，改成按关卡分区（Spatial Partition）的粗筛加精筛两级检测之后，30 关同时存在 200 多个碰撞体的极端场景下，碰撞阶段耗时降了约 60%。

移动端适配做了完整的一套：全屏浮动半透明控件，左侧方向、右侧跳跃加重开；touchstart/touchend 和 pointer events 双通道兼容不同浏览器；safe-area-inset 适配刘海屏；触控响应延迟控制在 1 帧以内。

主题系统是 Canvas 渲染与 DOM UI 分离的双主题实现，运行时切换调色板对象和 CSS 的 data-theme 变量，偏好写入 localStorage，初次进入跟随系统的 prefers-color-scheme。

音效没有用任何外部音频文件，全部基于 Web Audio API 的 OscillatorNode 加 GainNode 程序化合成，点击、跳跃、死亡都是实时生成的，包体零增加，顺带处理了浏览器的自动播放限制。

部署方面，写了一个 Node.js 静态服务器并完成部署上线，公网可以直接访问游玩。
