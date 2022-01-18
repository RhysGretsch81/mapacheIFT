''' Helper functions and classes used throughout. '''

class ISADefinitionError(Exception):
    pass

class AssemblyError(Exception):
    pass

class ExecutionError(Exception):
    pass

class MapacheInternalError(Exception):
    pass

class MapacheError(Exception):
    pass

# should be replaced with a proper sentinel value ala:
# https://www.python.org/dev/peps/pep-0661/#reference-github-repo
ExecutionComplete = object();


#-----------------------------------------------------------------------
def mask(n):
    '''Return an n-bit bit mask (e.g mask(3) returns 0x7).'''
    return (1<<n)-1

assert mask(3) == 0x7

#-----------------------------------------------------------------------
def align(addr, alignment):
    '''Given an address, return the smallest aligned address larger than addr.'''
    if addr % alignment:
        offset = alignment-(addr%alignment)
        return addr + offset
    else:
        return addr

assert align(0,4) == 0
assert align(4,4) == 4
assert align(5,4) == 8
assert align(7,4) == 8
assert align(8,4) == 8
assert align(9,4) == 12
assert align(9,2) == 10
assert align(9,1) == 9

#-----------------------------------------------------------------------
def hexstr_to_int(hexstr):
    '''Given a number is hex, return its value as an int (or None if unsucessful).'''
    try:
        return int(hexstr, 16)
    except ValueError:
        return None

assert hexstr_to_int('0x10') == 16
assert hexstr_to_int('10') == 16
assert hexstr_to_int('foobar') == None
assert hexstr_to_int('') == None

#-----------------------------------------------------------------------
def decimalstr_to_int(decstr):
    '''Given a number is decimal, return its value as an int (or None if unsucessful).'''
    try:
        return int(decstr, 10)
    except ValueError:
        return None

assert decimalstr_to_int('10') == 10
assert decimalstr_to_int('0') == 0
assert decimalstr_to_int('0x5') == None

#-----------------------------------------------------------------------
def int_to_bitstring(val, field_len, signed=False):
    if val >= 0:
        bitwidth = len(bin(val)) - 2  # the -2 for the "0b" at the start of the string
        if signed and val != 0:
            bitwidth += 1  # extra bit needed for the zero
        if bitwidth > field_len:
            return None # insufficient bits
        return bin(val)[2:].zfill(field_len)
    else:  # val is negative
        if not signed:
            return None
        if (val >> field_len - 1) != -1:
            return None  # insufficient bits
        return bin(val & mask(field_len))[2:]

assert int_to_bitstring(1, 1, signed=True) == None
assert int_to_bitstring(0, 1, signed=True) == '0'
assert int_to_bitstring(-1, 1, signed=True) == '1'
assert int_to_bitstring(-2, 1, signed=True) == None

assert int_to_bitstring(1, 1, signed=False) == '1'
assert int_to_bitstring(0, 1, signed=False) == '0'
assert int_to_bitstring(-1, 1, signed=False) == None
assert int_to_bitstring(-2, 1, signed=False) == None

assert int_to_bitstring(1, 2, signed=True) == '01'
assert int_to_bitstring(0, 2, signed=True) == '00'
assert int_to_bitstring(-1, 2, signed=True) == '11'
assert int_to_bitstring(-2, 2, signed=True) == '10'

assert int_to_bitstring(1, 2, signed=False) == '01'
assert int_to_bitstring(0, 2, signed=False) == '00'
assert int_to_bitstring(-1, 2, signed=False) == None
assert int_to_bitstring(-2, 2, signed=False) == None

assert int_to_bitstring(4, 3, signed=True) == None
assert int_to_bitstring(3, 3, signed=True) == '011'
assert int_to_bitstring(-1, 3, signed=True) == '111'
assert int_to_bitstring(-4, 3, signed=True) == '100'
assert int_to_bitstring(-5, 3, signed=True) == None

assert int_to_bitstring(8, 3, signed=False) == None
assert int_to_bitstring(7, 3, signed=False) == '111'
assert int_to_bitstring(4, 3, signed=False) == '100'
assert int_to_bitstring(0, 3, signed=False) == '000'
assert int_to_bitstring(-5, 3, signed=False) == None


#-----------------------------------------------------------------------
def bit_select(value, upper_bit, lower_bit, shift=False):
    '''Mask out all but a field of bits (from upper->lower inclusive).'''
    if upper_bit < lower_bit:
        raise MapacheError(f'upper_bit "{upper_bit}" is lower than lower_bit "{lower_bit}".')
    if lower_bit < 0:
        raise MapacheError(f'lower_bit "{lower_bit}" is less than zero.')
    smask = mask(upper_bit+1) & ~mask(lower_bit)
    shamt = lower_bit if shift else 0
    return (value & smask) >> shamt

#     bit position: 543210
assert bit_select(0b111111,3,1) == 0b01110
assert bit_select(0b111000,3,1) == 0b01000
assert bit_select(0b111111,2,2) == 0b00100
assert bit_select(0b111000,3,1,shift=True) == 0b0100
assert bit_select(0b111111,2,2,shift=True) == 0b001


#-----------------------------------------------------------------------
def log2(val):
    '''Return log base 2 of val, if val is a power of 2, otherwise raised ValueError.'''
    if (val & (val-1) != 0) or (val == 0):
        raise ValueError(f'non-positive power of two "{val}" provided to log2.')
    return val.bit_length()-1

assert log2(1) == 0
assert log2(2) == 1
assert log2(4) == 2

#-----------------------------------------------------------------------
def sign_extend(i, bits):
    '''Sign extend a set of bits.'''
    upper_mask = ~mask(bits)
    if i & upper_mask != 0:
        raise MapacheError(f'upper bits of i "{i}" not 0.')

    if i & (1<<(bits-1)) == 0:
        return i
    else:
        return i | upper_mask

assert sign_extend(0b1111,4) == -1
assert sign_extend(0b1000,4) == -8
assert sign_extend(0b0000,4) == 0
assert sign_extend(0b0111,4) == 7
