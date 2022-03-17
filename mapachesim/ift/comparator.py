import pyrtl

from ift.gates import *

BITMAX = 32

def comparator(a, b, a_t, b_t):

    # equal to
    n13, n14 = xnor_gate(a[3], b[3], a_t[3], b_t[3])
    n15, n16 = xnor_gate(a[2], b[2], a_t[2], b_t[2])
    n17, n18 = xnor_gate(a[1], b[1], a_t[1], b_t[1])
    n19, n20 = xnor_gate(a[0], b[0], a_t[0], b_t[0])

    n21, n22 = and_gate(n13, n15, n14, n16)
    n23, n24 = and_gate(n17, n21, n18, n22)


    equal, equal_t = and_gate(n19, n23, n20, n24)

    # greater than
    n1, n2 = and_gate(a[3], ~b[3], a_t[3], ~b_t[3])

    n3, n4 = and_gate(a[2], ~b[2], a_t[2], ~b_t[2])
    p1, p2 = and_gate(n13, n3, n14, n4)

    n5, n6 = and_gate(a[1], ~b[1], a_t[1], ~b_t[1])
    p3, p4 = and_gate(n13, n15, n14, n16)
    p5, p6 = and_gate(p3, n5, p4, n6)

    n7, n8 = and_gate(a[0], ~b[0], a_t[0], ~b_t[0])
    p7, p8 = and_gate(p3, n17, p4, n18)
    p9, p10 = and_gate(p7, n7, p8, n8)

    n9, n10 = or_gate(n1, p1, n2, p2)
    n11, n12 = or_gate(p5, n9, p6, n10)
    greater, greater_t = or_gate(p9, n11, p10, n12)


    # less than
    n25, n26 = and_gate(~a[3], b[3], ~a_t[3], b_t[3])
    
    n27, n28 = and_gate(~a[2], b[2], ~a_t[2], b_t[2])
    q1, q2 = and_gate(n13, n27, n14, n28)

    n29, n30 = and_gate(~a[1], b[1], ~a_t[1], b_t[1])
    q3, q4 = and_gate(n13, n15, n14, n16)
    q5, q6 = and_gate(q3, n29, q4, n30)

    n31, n32 = and_gate(~a[0], b[0], ~a_t[0], b_t[0])
    q7, q8 = and_gate(q3, n17, q4, n18)
    q9, q10 = and_gate(q7, n31, q8, n32)

    n33, n34 = or_gate(n25, q1, n26, q2)
    n35, n36 = or_gate(q5, n33, q6, n34)
    less, less_t = or_gate(q9, n35, q10, n36)

    return less, equal, greater, less_t, equal_t, greater_t


def comparator_32bit(a_32, b_32, a_t_32, b_t_32, n=4):
    a_32, b_32, a_t_32, b_t_32 = pyrtl.match_bitwidth(a_32, b_32, a_t_32, b_t_32)
    w = len(a_32)

    if len(a_32) <= n:
        l, e, g, l_t, e_t, g_t = comparator(a_32, b_32, a_t_32, b_t_32)
        return l, e, g, l_t, e_t, g_t 
    else:
        l, e, g, l_t, e_t, g_t = comparator(a_32[w-n:w], b_32[w-n:w], a_t_32[w-n:w], b_t_32[w-n:w])
        l_32, e_32, g_32, l_t_32, e_t_32, g_t_32 = comparator_32bit(a_32[:w-n], b_32[:w-n], a_t_32[:w-n], b_t_32[:w-n])
        return l_32, e_32, g_32, l_t_32, e_t_32, g_t_32
        