using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(RingColumnGenerator))]
public class RingColumnGeneratorEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();

        RingColumnGenerator gen = (RingColumnGenerator)target;

        if (GUILayout.Button("生成圆环柱体"))
        {
            gen.GenerateRingColumn();
        }
    }
}
