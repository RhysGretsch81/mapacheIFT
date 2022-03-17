import pyrtl

def and_gate(a, b, a_t, b_t):
    
    # regular AND
    o = a & b

    # glift AND
    an_t = ~a_t
    bn_t = ~b_t
    o_t = a_t & b_t | a & an_t & b_t | b & a_t & bn_t

    return o, o_t

def or_gate(a, b, a_t, b_t):

    # regular OR
    o = a | b

    # glift OR
    an_t = ~a_t
    bn_t = ~b_t
    an = ~a
    bn = ~b
    o_t = a_t & b_t | an & an_t & b_t | bn & a_t & bn_t

    return o, o_t

def xor_gate(a, b, a_t, b_t):

    # regular XOR
    o = a ^ b

    # glift XOR
    an_t = ~a_t
    bn_t = ~b_t
    o_t = a_t & b_t | an_t & b_t | a_t & bn_t
    return o, o_t


def xnor_gate(a, b, a_t, b_t):

    # regular XNOR
    o = ~(a ^ b)

    # glift XNOR
    an_t = ~a_t
    bn_t = ~b_t
    o_t = ~(a_t & b_t | an_t & b_t | a_t & bn_t)
    return o, o_t