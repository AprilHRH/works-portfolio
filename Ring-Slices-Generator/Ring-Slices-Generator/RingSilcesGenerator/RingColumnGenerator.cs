using UnityEngine;
using System.Collections.Generic;

#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteInEditMode]
public class RingColumnGenerator : MonoBehaviour
{
    [Header("圆环柱体参数")]
    public float innerRadius = 0.5f; // 内径/2
    public float outerRadius = 1f;    // 外径/2
    public float height = 0.2f;       // 高度

    [Header("分段")]
    public List<ArcSegment> segments = new List<ArcSegment>() { new ArcSegment() { angle = 360f } };

    private void OnValidate()
    {
        FixAngles();
    }

    /// <summary>
    /// 保证分段自动均分，并最后一段自动补足
    /// </summary>
    public void FixAngles()
    {
        if (segments.Count == 0) return;

        float total = 0f;
        for (int i = 0; i < segments.Count - 1; i++)
        {
            segments[i].angle = 360f / segments.Count; // 自动均分
            total += segments[i].angle;
        }
        segments[segments.Count - 1].angle = Mathf.Max(0f, 360f - total);
    }

#if UNITY_EDITOR
    [ContextMenu("生成圆环柱体")]
    public void GenerateRingColumn()
    {
        FixAngles();

        // 删除旧的
        for (int i = transform.childCount - 1; i >= 0; i--)
        {
            DestroyImmediate(transform.GetChild(i).gameObject);
        }

        float startAngle = 0f;
        for (int i = 0; i < segments.Count; i++)
        {
            ArcSegment seg = segments[i];

            GameObject slice = new GameObject($"Slice_{(i + 1).ToString("00")}");
            slice.transform.SetParent(transform, false);

            RingColumnSlice sliceComp = slice.AddComponent<RingColumnSlice>();
            sliceComp.innerRadius = innerRadius;
            sliceComp.outerRadius = outerRadius;
            sliceComp.height = height;
            sliceComp.angle = seg.angle;

            sliceComp.GenerateMesh();

            slice.transform.localRotation = Quaternion.Euler(0, startAngle, 0);
            startAngle += seg.angle;
        }
    }
#endif
}
