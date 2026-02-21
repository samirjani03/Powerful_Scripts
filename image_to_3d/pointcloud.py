import numpy as np
import open3d as o3d

def depth_to_pointcloud(depth, output_path):
    h, w = depth.shape
    fx = fy = 500
    cx = w / 2
    cy = h / 2

    points = []

    for y in range(h):
        for x in range(w):
            z = depth[y, x]
            if z <= 0:
                continue
            X = (x - cx) * z / fx
            Y = (y - cy) * z / fy
            points.append([X, Y, z])

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.array(points))

    o3d.io.write_point_cloud(output_path, pcd)
