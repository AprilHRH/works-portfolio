# Boat Attack

独立复现 Unity BoatAttack 开源示例，用于学习 URP 实时水体渲染、平面反射与移动端性能优化。

> 源仓库：[Unity-Technologies/BoatAttack](https://github.com/Unity-Technologies/BoatAttack)

## 拓展内容

在原版水体渲染通路基础上，我新增了一套水面交互涟漪系统。做法是基于 RenderTexture 高度场模拟，检测船体和浮标接触水面的位置，实时注入涟漪源并让波纹自然传播扩散，替代了原版固定波形的静态表现，水面被触碰后会有真实的动态反馈。

第二个模块是水下后处理管线。写了一个自定义 ScriptableRenderPass，相机进入水面以下时自动切换雾效颜色，用 GrabPass 加 UV 偏移做屏幕空间折射扭曲，再叠一层体积光透射，水上水下视角切换的体验是完整的。

天气方面，把原版写死的 Gerstner 波参数改成了受全局风场控制，振幅和频率都是动态的。配合雨滴粒子系统在水面产生高频噪声扰动，晴天和暴雨两种天气下水体形态可以实时切换。

性能这块在骁龙 8 Gen 2 设备上实测，帧率从 28 提到 45。具体手段：水面法线计算从逐像素改为顶点插值加逐像素混合，反射 Camera 分辨率降到屏幕的 1/4 再用 Bilinear 上采样，三个独立 Pass 合并成单个 Compute Shader 调度。
