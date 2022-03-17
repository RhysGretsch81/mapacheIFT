import pyrtl 
from pyrtl.rtllib import libutils

from ift.gates import *
from ift.full_adder import *

def multiplier(a, b, a_t, b_t):

    p, p_t = [0]*8, [0]*8

    w0, x0 = and_gate(a[3], b[0], a_t[3], b_t[0])
    w1, x1 = and_gate(a[2], b[0], a_t[2], b_t[0])
    w2, x2 = and_gate(a[1], b[0], a_t[1], b_t[0])

    p[0], p_t[0] = and_gate(a[0], b[0], a_t[0], b_t[0])

    w3, x3 = and_gate(a[3], b[1], a_t[3], b_t[1])
    w4, x4 = and_gate(a[2], b[1], a_t[2], b_t[1])
    w5, x5 = and_gate(a[1], b[1], a_t[1], b_t[1])
    w6, x6 = and_gate(a[0], b[1], a_t[0], b_t[1])
    w7, x7 = and_gate(a[3], b[2], a_t[3], b_t[2])
    w8, x8 = and_gate(a[2], b[2], a_t[2], b_t[2])
    w9, x9 = and_gate(a[1], b[2], a_t[1], b_t[2])
    w10, x10 = and_gate(a[0], b[2], a_t[0], b_t[2])
    w11, x11 = and_gate(a[3], b[3], a_t[3], b_t[3])
    w12, x12 = and_gate(a[2], b[3], a_t[2], b_t[3])
    w13, x13 = and_gate(a[1], b[3], a_t[1], b_t[3])
    w14, x14 = and_gate(a[0], b[3], a_t[0], b_t[3])

    p[1], w15, p_t[1], x15 = full_adder(w6, w2, pyrtl.Const(0,1), x6, x2, pyrtl.Const(0,1))
    w16, w17, x16, x17 = full_adder(w5, w1, pyrtl.Const(0,1), x5, x1, pyrtl.Const(0,1))
    w18, w19, x18, x19 = full_adder(w4, w0, pyrtl.Const(0,1), x4, x0, pyrtl.Const(0,1))
    p[2], w20, p_t[2], x20 = full_adder(w15, w10, w16, x15, x10, x16)
    w21, w22, x21, x22 = full_adder(w9, w17, w18, x9, x17, x18)
    w23, w24, x23, x24 = full_adder(w8, w3, w19, x8, x3, x19)
    p[3], w25, p_t[3], x25 = full_adder(w14, w20, w21, x14, x20, x21)
    w26, w27, x26, x27 = full_adder(w13, w22, w23, x13, x22, x23)
    w28, w29, x28, x29 = full_adder(w12, w7, w24, x12, x7, x24)
    p[4], w30, p_t[4], x30 = full_adder(w25, w26, pyrtl.Const(0,1), x25, x26, pyrtl.Const(0,1))
    p[5], w31, p_t[5], x31 = full_adder(w27, w30, w28, x27, x30, x28)
    p[6], p[7], p_t[6], p_t[7] = full_adder(w11, w31, w29, x11, x31, x29)

    return pyrtl.concat_list(p), pyrtl.concat_list(p_t)

    

def multiplier_8bit(a_32, b_32, a_t_32, b_t_32, bitlen = 16):
    a_32, b_32, a_t_32, b_t_32 = pyrtl.match_bitwidth(a_32, b_32, a_t_32, b_t_32)

    n = bitlen//2

    try:    p1, pt1 = multiplier(a_32[0:(n//2)], b_32[0:(n//2)], a_t_32[0:(n//2)], b_t_32[0:(n//2)])
    except: p1, pt1 = [0]*n, [0]*n

    try:    p2, pt2 = multiplier(a_32[0:(n//2)], b_32[(n//2):n], a_t_32[0:(n//2)], b_t_32[(n//2):n])
    except: p2, pt2 = [0]*n, [0]*n

    try:    p3, pt3 = multiplier(a_32[(n//2):n], b_32[0:(n//2)], a_t_32[(n//2):n], b_t_32[0:(n//2)])
    except: p3, pt3 = [0]*n, [0]*n

    try:    p4, pt4 = multiplier(a_32[(n//2):n], b_32[(n//2):n], a_t_32[(n//2):n], b_t_32[(n//2):n])
    except: p4, pt4 = [0]*n, [0]*n

    s1, c1, st1, ct1 = full_adder_32bit(pyrtl.concat_list(p2), pyrtl.concat_list(p3), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(pt2), pyrtl.concat_list(pt3), pyrtl.Const(0b0))
    
    s2, c2, st2, ct2 = full_adder_32bit(pyrtl.concat_list(s1), pyrtl.concat_list(p1[(n//2):n]), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(st1), pyrtl.concat_list(pt1[(n//2):n]), pyrtl.Const(0b0))

    s3, c3, st3, ct3 = full_adder_32bit(pyrtl.concat_list([s2[(n//2):n], c1]), pyrtl.concat_list(p4), pyrtl.Const(0b0), 
                                        pyrtl.concat_list([st2[(n//2):n], ct1]), pyrtl.concat_list(pt4), pyrtl.Const(0b0))


    p = [p1[:(n//2)], s2[:(n//2)], s3]
    p_t = [pt1[:(n//2)], st2[:(n//2)], st3]

    return pyrtl.concat_list(p), pyrtl.concat_list(p_t)
    


def multiplier_16bit(a_32, b_32, a_t_32, b_t_32, bitlen = 32):
    a_32, b_32, a_t_32, b_t_32 = pyrtl.match_bitwidth(a_32, b_32, a_t_32, b_t_32)

    n = bitlen//2

    try:    p1, pt1 = multiplier_8bit(a_32[0:(n//2)], b_32[0:(n//2)], a_t_32[0:(n//2)], b_t_32[0:(n//2)])
    except: p1, pt1 = [0]*n, [0]*n

    try:    p2, pt2 = multiplier_8bit(a_32[0:(n//2)], b_32[(n//2):n], a_t_32[0:(n//2)], b_t_32[(n//2):n])
    except: p2, pt2 = [0]*n, [0]*n

    try:    p3, pt3 = multiplier_8bit(a_32[(n//2):n], b_32[0:(n//2)], a_t_32[(n//2):n], b_t_32[0:(n//2)])
    except: p3, pt3 = [0]*n, [0]*n

    try:    p4, pt4 = multiplier_8bit(a_32[(n//2):n], b_32[(n//2):n], a_t_32[(n//2):n], b_t_32[(n//2):n])
    except: p4, pt4 = [0]*n, [0]*n

    s1, c1, st1, ct1 = full_adder_32bit(pyrtl.concat_list(p2), pyrtl.concat_list(p3), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(pt2), pyrtl.concat_list(pt3), pyrtl.Const(0b0))
    
    s2, c2, st2, ct2 = full_adder_32bit(pyrtl.concat_list(s1), pyrtl.concat_list(p1[(n//2):n]), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(st1), pyrtl.concat_list(pt1[(n//2):n]), pyrtl.Const(0b0))

    s3, c3, st3, ct3 = full_adder_32bit(pyrtl.concat_list([s2[(n//2):n], c1]), pyrtl.concat_list(p4), pyrtl.Const(0b0), 
                                        pyrtl.concat_list([st2[(n//2):n], ct1]), pyrtl.concat_list(pt4), pyrtl.Const(0b0))

    p = [p1[:(n//2)], s2[:(n//2)], s3]
    p_t = [pt1[:(n//2)], st2[:(n//2)], st3]

    return pyrtl.concat_list(p), pyrtl.concat_list(p_t)
    


def multiplier_32bit(a_32, b_32, a_t_32, b_t_32, bitlen = 64):
    a_32, b_32, a_t_32, b_t_32 = pyrtl.match_bitwidth(a_32, b_32, a_t_32, b_t_32)

    n = bitlen//2

    try:    p1, pt1 = multiplier_16bit(a_32[0:(n//2)], b_32[0:(n//2)], a_t_32[0:(n//2)], b_t_32[0:(n//2)])
    except: p1, pt1 = [0]*n, [0]*n

    try:    p2, pt2 = multiplier_16bit(a_32[0:(n//2)], b_32[(n//2):n], a_t_32[0:(n//2)], b_t_32[(n//2):n])
    except: p2, pt2 = [0]*n, [0]*n

    try:    p3, pt3 = multiplier_16bit(a_32[(n//2):n], b_32[0:(n//2)], a_t_32[(n//2):n], b_t_32[0:(n//2)])
    except: p3, pt3 = [0]*n, [0]*n

    try:    p4, pt4 = multiplier_16bit(a_32[(n//2):n], b_32[(n//2):n], a_t_32[(n//2):n], b_t_32[(n//2):n])
    except: p4, pt4 = [0]*n, [0]*n

    s1, c1, st1, ct1 = full_adder_32bit(pyrtl.concat_list(p2), pyrtl.concat_list(p3), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(pt2), pyrtl.concat_list(pt3), pyrtl.Const(0b0))
    
    s2, c2, st2, ct2 = full_adder_32bit(pyrtl.concat_list(s1), pyrtl.concat_list(p1[(n//2):n]), pyrtl.Const(0b0), 
                                        pyrtl.concat_list(st1), pyrtl.concat_list(pt1[(n//2):n]), pyrtl.Const(0b0))

    s3, c3, st3, ct3 = full_adder_32bit(pyrtl.concat_list([s2[(n//2):n], c1]), pyrtl.concat_list(p4), pyrtl.Const(0b0), 
                                        pyrtl.concat_list([st2[(n//2):n], ct1]), pyrtl.concat_list(pt4), pyrtl.Const(0b0))

    p = [p1[:(n//2)], s2[:(n//2)], s3]
    p_t = [pt1[:(n//2)], st2[:(n//2)], st3]

    return pyrtl.concat_list(p), pyrtl.concat_list(p_t)