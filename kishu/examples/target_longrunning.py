"""Example of a long-running script.""" 

def a():
    cnt_a = 0
    for adx in range(1000):
        cnt_a += adx
    return cnt_a


def a2():
    cnt_a = 0
    for adx in range(1000):
        cnt_a += adx
    return cnt_a


def b(bi=3):
    if bi > 0:
        return b(bi - 1)
    cnt_b = 0
    for bdx in range(1000):
        cnt_b += a()
    for bdx in range(1000):
        cnt_b += a2()
    return cnt_b


def c():
    cnt_c = 0
    for cdx in range(1000):
        cnt_c += b()
    return cnt_c


def d():
    cnt_d = 0
    for ddx in range(1000):
        cnt_d += c()
        print(ddx)
    return cnt_d

# print(locals())
print(d())
