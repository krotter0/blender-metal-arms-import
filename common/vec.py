
import math

def add(*args):
    return (sum(v[0] for v in args), sum(v[1] for v in args), sum(v[2] for v in args))

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def mul(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)

def len(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])

def norm(v):
    length = len(v)
    if length <= 1e-8:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)