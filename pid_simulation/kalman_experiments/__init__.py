import numpy as np
from filterpy.kalman import KalmanFilter

if __name__ == '__main__':
    f = KalmanFilter(dim_x=3, dim_z=2)
    f.x = np.array([1., 1., 0.])
    # f.F = np.array([[]])
    f.H = np.array([[0., 1., 0.],
                    [0., 0., 1.]])
    f.P *= 100
    f.R = np.array([[0., 0.],
                    [0., 0.]])
    s_dev = 1
    l_dev = 1
    f.Q = np.array([[l_dev ** 2, 0., 0.],
                    [0., 0., 0.],
                    [0., 0., s_dev ** 2]])

    t = 0
    s = 2
    dt = 1
    for _ in range(10):
        f.F = np.array([[1., 0., 0.],
                        [0., 1., 0.],
                        [-dt, s * dt, 1.]])

        v, d = map(float, input().split())
        z = np.array([v, d])
        f.predict()
        f.update(z)

        print(f'{f.x=}')

        t += dt

