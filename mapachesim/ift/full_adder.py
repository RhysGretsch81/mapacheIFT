import pyrtl

from ift.gates import *
BITMAX = 32

def half_adder(a, b, a_t, b_t):
    sum, sum_t = xor_gate(a, b, a_t, b_t)
    carry, carry_t = and_gate(a, b, a_t, b_t)
    return sum, carry, sum_t, carry_t

def full_adder(a, b, c, a_t, b_t, c_t):
    sum1, carry1, sum1_t, carry1_t = half_adder(a, b, a_t, b_t)
    sum2, carry2, sum2_t, carry2_t = half_adder(c, sum1, c_t, sum1_t)
    sum, sum_t = sum2, sum2_t
    carry, carry_t = or_gate(carry1, carry2, carry1_t, carry2_t)
    return sum, carry, sum_t, carry_t


def full_adder_32bit(a_32, b_32, c_32, a_t_32, b_t_32, c_t_32, n=1):
    a_32, b_32, c_32, a_t_32, b_t_32, c_t_32 = pyrtl.match_bitwidth(a_32, b_32, c_32, a_t_32, b_t_32, c_t_32)

    if len(a_32) <= n:
        sum, carry, sum_t, carry_t = full_adder(a_32, b_32, c_32, a_t_32, b_t_32, c_t_32)
        return sum, carry, sum_t, carry_t 
    else:
        sum, carry, sum_t, carry_t = full_adder(a_32[0:n], b_32[0:n], c_32[0:n], a_t_32[0:n], b_t_32[0:n], c_t_32[0:n])
        sum_32, carry_32, sum_t_32, carry_t_32 = full_adder_32bit(a_32[n:], b_32[n:], carry, a_t_32[n:], b_t_32[n:], carry_t)
        return pyrtl.concat(sum_32, sum), carry_32, pyrtl.concat(sum_t_32, sum_t), carry_t_32

