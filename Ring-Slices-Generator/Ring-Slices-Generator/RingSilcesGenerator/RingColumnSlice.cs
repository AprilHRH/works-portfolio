using UnityEngine;
using System.Collections.Generic;

[ExecuteInEditMode]
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer), typeof(MeshCollider))]
public class RingColumnSlice : MonoBehaviour
{
    public float innerRadius = 0.5f;
    public float outerRadius = 1f;
    public float height = 0.2f;
    [Range(0, 360)]
    public float angle = 90f;

    [Range(3, 128)]
    public int sides = 32;

    private MeshFilter mf;
    private MeshRenderer mr;
    private MeshCollider mc;

    void OnValidate()
    {
        GenerateMesh();
    }

    public void GenerateMesh()
    {
        mf = GetComponent<MeshFilter>();
        mr = GetComponent<MeshRenderer>();
        mc = GetComponent<MeshCollider>();

        Mesh mesh = new Mesh();
        mesh.name = "RingColumnSlice";

        List<Vector3> vertices = new List<Vector3>();
        List<int> triangles = new List<int>();
        List<Vector3> normals = new List<Vector3>();

        float halfH = height / 2f;

        int baseTop = 0;
        int baseBottom = (sides + 1) * 2;

        // === 顶面 ===
        for (int i = 0; i <= sides; i++)
        {
            float t = i / (float)sides;
            float theta = t * angle * Mathf.Deg2Rad;

            float cos = Mathf.Cos(theta);
            float sin = Mathf.Sin(theta);

            vertices.Add(new Vector3(cos * outerRadius, halfH, sin * outerRadius)); // 外圈
            normals.Add(Vector3.up);

            vertices.Add(new Vector3(cos * innerRadius, halfH, sin * innerRadius)); // 内圈
            normals.Add(Vector3.up);
        }

        // === 底面 ===
        for (int i = 0; i <= sides; i++)
        {
            float t = i / (float)sides;
            float theta = t * angle * Mathf.Deg2Rad;

            float cos = Mathf.Cos(theta);
            float sin = Mathf.Sin(theta);

            vertices.Add(new Vector3(cos * outerRadius, -halfH, sin * outerRadius)); // 外圈
            normals.Add(Vector3.down);

            vertices.Add(new Vector3(cos * innerRadius, -halfH, sin * innerRadius)); // 内圈
            normals.Add(Vector3.down);
        }

        // === 顶面三角形 ===
        for (int i = 0; i < sides; i++)
        {
            int o0 = baseTop + i * 2;
            int i0 = baseTop + i * 2 + 1;
            int o1 = baseTop + (i + 1) * 2;
            int i1 = baseTop + (i + 1) * 2 + 1;

            triangles.Add(o0);
            triangles.Add(i0);
            triangles.Add(o1);
            triangles.Add(i0);
            triangles.Add(i1);
            triangles.Add(o1);
        }

        // === 底面三角形 ===
        for (int i = 0; i < sides; i++)
        {
            int o0 = baseBottom + i * 2;
            int i0 = baseBottom + i * 2 + 1;
            int o1 = baseBottom + (i + 1) * 2;
            int i1 = baseBottom + (i + 1) * 2 + 1;

            triangles.Add(o0);
            triangles.Add(o1);
            triangles.Add(i0);
            triangles.Add(i0);
            triangles.Add(o1);
            triangles.Add(i1);
        }

        // === 外壁 ===
        for (int i = 0; i < sides; i++)
        {
            float t0 = i / (float)sides;
            float t1 = (i + 1) / (float)sides;

            float theta0 = t0 * angle * Mathf.Deg2Rad;
            float theta1 = t1 * angle * Mathf.Deg2Rad;

            Vector3 p0 = new Vector3(Mathf.Cos(theta0) * outerRadius, -halfH, Mathf.Sin(theta0) * outerRadius);
            Vector3 p1 = new Vector3(Mathf.Cos(theta1) * outerRadius, -halfH, Mathf.Sin(theta1) * outerRadius);
            Vector3 p2 = new Vector3(Mathf.Cos(theta0) * outerRadius, halfH, Mathf.Sin(theta0) * outerRadius);
            Vector3 p3 = new Vector3(Mathf.Cos(theta1) * outerRadius, halfH, Mathf.Sin(theta1) * outerRadius);

            Vector3 normal = Vector3.Cross(p2 - p0, p1 - p0).normalized;

            int baseIdx = vertices.Count;
            vertices.AddRange(new[] { p0, p1, p2, p3 });
            normals.AddRange(new[] { normal, normal, normal, normal });

            triangles.Add(baseIdx + 0);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 3);
        }

        // === 内壁 ===
        for (int i = 0; i < sides; i++)
        {
            float t0 = i / (float)sides;
            float t1 = (i + 1) / (float)sides;

            float theta0 = t0 * angle * Mathf.Deg2Rad;
            float theta1 = t1 * angle * Mathf.Deg2Rad;

            Vector3 p0 = new Vector3(Mathf.Cos(theta0) * innerRadius, -halfH, Mathf.Sin(theta0) * innerRadius);
            Vector3 p1 = new Vector3(Mathf.Cos(theta1) * innerRadius, -halfH, Mathf.Sin(theta1) * innerRadius);
            Vector3 p2 = new Vector3(Mathf.Cos(theta0) * innerRadius, halfH, Mathf.Sin(theta0) * innerRadius);
            Vector3 p3 = new Vector3(Mathf.Cos(theta1) * innerRadius, halfH, Mathf.Sin(theta1) * innerRadius);

            Vector3 normal = -Vector3.Cross(p2 - p0, p1 - p0).normalized;

            int baseIdx = vertices.Count;
            vertices.AddRange(new[] { p0, p1, p2, p3 });
            normals.AddRange(new[] { normal, normal, normal, normal });

            triangles.Add(baseIdx + 0);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 3);
            triangles.Add(baseIdx + 2);
        }

        // === 开口左侧面（首面） ===
        {
            float theta = 0f;
            Vector3 p0 = new Vector3(Mathf.Cos(theta) * innerRadius, -halfH, Mathf.Sin(theta) * innerRadius);
            Vector3 p1 = new Vector3(Mathf.Cos(theta) * outerRadius, -halfH, Mathf.Sin(theta) * outerRadius);
            Vector3 p2 = new Vector3(Mathf.Cos(theta) * innerRadius, halfH, Mathf.Sin(theta) * innerRadius);
            Vector3 p3 = new Vector3(Mathf.Cos(theta) * outerRadius, halfH, Mathf.Sin(theta) * outerRadius);

            Vector3 normal = Vector3.Cross(p1 - p0, p2 - p0).normalized * -1f;

            int baseIdx = vertices.Count;
            vertices.AddRange(new[] { p0, p1, p2, p3 });
            normals.AddRange(new[] { normal, normal, normal, normal });

            triangles.Add(baseIdx + 0);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 3);
        }

        // === 开口右侧面（尾面） ===
        {
            float theta = angle * Mathf.Deg2Rad;
            Vector3 p0 = new Vector3(Mathf.Cos(theta) * innerRadius, -halfH, Mathf.Sin(theta) * innerRadius);
            Vector3 p1 = new Vector3(Mathf.Cos(theta) * outerRadius, -halfH, Mathf.Sin(theta) * outerRadius);
            Vector3 p2 = new Vector3(Mathf.Cos(theta) * innerRadius, halfH, Mathf.Sin(theta) * innerRadius);
            Vector3 p3 = new Vector3(Mathf.Cos(theta) * outerRadius, halfH, Mathf.Sin(theta) * outerRadius);

            Vector3 normal = Vector3.Cross(p1 - p0, p2 - p0).normalized;

            int baseIdx = vertices.Count;
            vertices.AddRange(new[] { p0, p1, p2, p3 });
            normals.AddRange(new[] { normal, normal, normal, normal });

            triangles.Add(baseIdx + 0);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 2);
            triangles.Add(baseIdx + 1);
            triangles.Add(baseIdx + 3);
            triangles.Add(baseIdx + 2);
        }

        mesh.vertices = vertices.ToArray();
        mesh.triangles = triangles.ToArray();
        mesh.normals = normals.ToArray();
        mesh.RecalculateBounds();

        mf.sharedMesh = mesh;
        mc.sharedMesh = mesh;

        if (mr.sharedMaterial == null)
        {
            mr.sharedMaterial = new Material(Shader.Find("Standard"));
        }
    }
}
