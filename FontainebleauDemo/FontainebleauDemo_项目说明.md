# Fontainebleau Demo

独立复现 Unity Fontainebleau 摄影测量森林场景，用于学习 HDRP 实景扫描材质渲染、植被着色与光照氛围调优。

> 源仓库：[Unity-Technologies/FontainebleauDemo](https://github.com/Unity-Technologies/FontainebleauDemo)

## 拓展内容

植被着色是花时间最多的部分。通读了 VegetationDeformation 这个 ShaderGraph 子图，理解了顶点级弯曲的两级位移模型——主枝低频摆动叠叶片高频抖动。之后调风场强度和相位偏移参数，把大风档位下叶片穿插地面的穿模问题消掉了。

LOD 切换原本有明显的 popping。分析了 Vegetation Shader 里 Dither 交叉渐变的实现后，把树木 LOD0 到 LOD1 的过渡改成 2 米距离内的平滑渐变，配合 dither_crossfade 子图的屏幕空间噪声分布，切换时肉眼基本察觉不到。

光照氛围方面，用项目自带的 LightmapSwitcher 工具在晴、阴、雾三套光照贴图之间实时切换，同时调整 Fog Volume 的衰减曲线和 Skybox 反射强度，做出了黄昏低角度光照下整个场景偏暖的色彩倾向。

摄影测量材质也是学习重点。实景扫描资产走的是 Albedo、Normal、Mask 三张贴图的流程，Mask 贴图在叶子半透（次表面散射模拟）和树干湿度控制里起关键作用，把这套材质球的参数配置完整复刻了一遍。

最后用 RenderDoc 抓帧分析了 Draw Call 和显存分布，定位到草地和树冠的 Overdraw 热点，通过调整 LOD 距离阈值把 GPU 帧时间降了大约 18%。
