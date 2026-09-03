# Spaceship Demo

独立复现 Unity Spaceship 太空飞船第一人称 Demo，用于学习 Visual Effect Graph 粒子系统、HDRP 高级渲染与动态光照氛围调优。

> 源仓库：[Unity-Technologies/SpaceshipDemo](https://github.com/Unity-Technologies/SpaceshipDemo)

## 拓展内容

粒子系统是这个项目的研究重点。通读了引擎舱尾焰和太空尘埃两套 VFX 图，理解了 GPU Event 加 Spawn Context 的按需发射机制，然后复刻了一套尾焰粒子图，调整速率曲线让加速阶段的粒子拖尾长度跟飞船输入联动起来。

渲染上分析了场景里 Screen Space Reflection 和 Volumetric Lighting 的叠加表现，调体积光雾密度和反射屏幕权重，把舱内金属面板在强光源下的反射噪点闪烁问题压掉了。

光照方面研究了示例的昼夜切换系统，环境探针插值加光源角度动画那套，复刻了一段从恒星背面进入白昼的过渡序列，顺带观察了镜面高光和天空盒 HDR 亮度随太阳角度的变化规律。

性能上用 RenderDoc 抓帧，定位到 VFX 粒子渲染和半透明排序的显存热点。降低远景尘埃粒子的发射上限、启用粒子剔除盒把相机视野外的发射剔掉之后，中端 GPU 上 VFX 阶段的帧耗时降了约 20%。
