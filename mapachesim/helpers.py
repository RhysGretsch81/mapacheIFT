''' Helper functions and classes used throughout. '''

class ISADefinitionError(Exception):
    pass

class AssemblyError(Exception):
    pass

class MapacheInternalError(Exception):
    pass

class MapacheError(Exception):
    pass

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
