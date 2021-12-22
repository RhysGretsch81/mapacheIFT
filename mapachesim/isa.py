''' MIPS definition classes. '''

import collections
import types
import re

class ISAError(Exception):
    pass

#-----------------------------------------------------------------------
def mask(n):
    '''Return an n-bit bit mask (e.g mask(3) returns 0x7).'''
    return (1<<n)-1

assert mask(3) == 0x7

#-----------------------------------------------------------------------
def bit_select(value, upper_bit, lower_bit, shift=False):
    '''Mask out all but a field of bits (from upper->lower inclusive).'''
    if upper_bit < lower_bit:
        raise ISAError(f'upper_bit "{upper_bit}" is lower than lower_bit "{lower_bit}".')
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
def sign_extend(i, bits):
    '''Sign extend a set of bits.'''
    upper_mask = ~mask(bits)
    if i & upper_mask != 0:
        raise ISAError(f'upper bits of i "{i}" not 0.')

    if i & (1<<(bits-1)) == 0:
        return i
    else:
        return i | upper_mask

assert sign_extend(0b1111,4) == -1
assert sign_extend(0b1000,4) == -8
assert sign_extend(0b0000,4) == 0
assert sign_extend(0b0111,4) == 7


#-----------------------------------------------------------------------

# Error checking to add:
# 1) check if function name and op in docstring mismatch

class  IsaDefinition:
    ''' A base class for defining ISAs. '''

    def __init__(self):
        self._ifuncs = [getattr(self,f) for f in dir(self) if f.startswith('instruction_')]
        self._reg_list = []
        self._mem = None
        # the parameters below are set by default but can be overridden in derived classes
        self.endian = 'big'  # can be either 'big' or 'little'
        self.isize = 4  # width of an instruction in bytes
        self.text_start_address = 0x10000
        self.data_start_address = 0x40000

    def make_register(self, name, bits=32):
        '''Add a special purpose register to the machine specification.'''
        setattr(self, name, 0)
        self._reg_list.append(('reg',name,bits,None,None))
        #self.mask[name] = (1<<bits)-1

    def make_register_file(self, name, size, bits=32, rnames=None):
        '''Add a register file to the machine specification.'''
        setattr(self, name, {x:0 for x in range(size)})
        if rnames is None:
            rnames = {x:f'${name}{x}' for x in range(size)}
        self._reg_list.append(('file',name,bits,size,rnames))

    def registers(self):
        '''Generates a triple of information for each register (name, bitwidth, value).'''
        for rtype, name, bits, size, rnames in self._reg_list:
            if rtype=='reg':
                yield name, bits, getattr(self, name)
            else:
                assert rtype=='file'
                for i in range(size):
                    yield rnames[i], bits, getattr(self, name)[i]

    def _extract_pattern(self, func):
        '''Extract an patterns from the instruction function docstring.'''
        # string should look like 'add immediate : 001000 sssss ttttt iiiiiiiiiii: something'
        docstring = func.__doc__
        clean_format = docstring.replace(' ','').split(':')[1]
        if len(clean_format) != self.isize*8:
            raise ISAError(f'format for "{clean_format}" is {len(clean_format)} bits not {self.isize*8}.')
        return clean_format

    def _pattern_match(self, ifunc, instr):
        '''Check if a function docstring matches the raw bytes of instr provided, return fields or None.'''
        if len(instr) != self.isize:
            raise ISAError(f'instruction "{instr}" is {len(instr)} bytes not {self.isize}.')
        pattern = self._extract_pattern(ifunc)
        instr_as_integer = int.from_bytes(instr, self.endian)
        instr_as_list_of_bits = [(instr_as_integer>>(s-1)) & 0x1 for s in range(self.isize*8,0,-1)]
        fields = collections.defaultdict(int)

        for bpattern, bit in zip(pattern, instr_as_list_of_bits):
            if bpattern=='0' and bit==1:
                return None
            elif bpattern=='1' and bit==0:
                return None
            else:
                fields[bpattern] = (fields[bpattern] << 1) | bit
        ifield = types.SimpleNamespace(**fields)
        return ifield

    def _extract_asm(self, ifunction):
        '''Given an instruction_func, return a clean asm definition from docstring.'''
        asm_pattern = ifunction.__doc__.split(':')[2]
        clean_pattern = asm_pattern.replace(',',' ').strip()
        monospaced_pattern = str.join(' ', clean_pattern.split())
        return monospaced_pattern

    def _format_asm(self, asm_pattern, ifield):
        def operand_field(part, indicator):
            # TODO much better error handling
            fchar = part[1:]
            assert len(fchar)==1
            return getattr(ifield, fchar)

        instruction = []
        for i,part in enumerate(asm_pattern.split()):
            if i==0:
                instruction.append(part)  # instruction name
            elif part.startswith('$'):
                rnum = operand_field(part, '$')
                instruction.append(f'${rnum}')
            elif part.startswith('@'):
                addr = operand_field(part, '@')
                instruction.append(f'{hex(addr<<2)}')
            elif part.startswith('!'):
                immed = operand_field(part, '!')
                instruction.append(f'{hex(immed)}')
            else:
                raise ISAError(f'Unknown operand specifier: "{part}" in "{asm_pattern}"')
        return str.join(' ', instruction)

    def fetch(self):
        '''Fetch the next instruction at PC and return as an array of bytes.'''
        return self.mem_read(self.PC, self.isize)

    def decode(self, instr):
        '''Given an instruction (as array of bytes) return its decoded form.'''
        for ifunc in self._ifuncs:
            ifield = self._pattern_match(ifunc, instr)
            if ifield is not None:
                return ifunc, ifield
        raise ISAError(f'Unable to decode bytes as instruction:"{instr}".')

    def execute(self, decoded_instr):
        '''Execute a decoded instruction.'''
        ifunction, ifield = decoded_instr
        ifunction(ifield)

    def istring(self, decoded_instr):
        '''Return a string representation of a decoded instruction.'''
        ifunction, ifield = decoded_instr
        asm_pattern = self._extract_asm(ifunction)
        instr_string = self._format_asm(asm_pattern, ifield)
        return instr_string

    def step(self):
        '''Step the simulator forward and return a string of instruction executed.'''
        instr_mem = self.fetch()
        decoded_instr = self.decode(instr_mem)
        self.execute(decoded_instr)
        if hasattr(self,'finalize_execution'):
            self.finalize_execution(decoded_instr)
        return self.istring(decoded_instr)

    def mem_map(self, start_address, size):
        '''Map a region of physical memory into the simulator.'''
        print('Warning: memory map not fully implemented -- assuming start_address is zero')
        self._mem = bytearray(size)

    def mem_read(self, start_addr, size):
        '''Read a region of memory and return an array of bytes.'''
        return self._mem[start_addr:start_addr+size]

    def mem_write(self, start_addr, data):
        '''Write an array of bytes into memory.'''
        self._mem[start_addr:start_addr+len(data)] = data

    # Some simple wrappers for mem_read and mem_write for readability
    def mem_write_64bit(self, start_addr, value):
        self.mem_write(start_addr, int.to_bytes(value, 8, self.endian, signed=True))
    def mem_write_32bit(self, start_addr, value):
        self.mem_write(start_addr, int.to_bytes(value, 4, self.endian, signed=True))
    def mem_write_16bit(self, start_addr, value):
        self.mem_write(start_addr, int.to_bytes(value, 2, self.endian, signed=True))
    def mem_write_8bit(self, start_addr, value):
        self.mem_write(start_addr, int.to_bytes(value, 1, self.endian, signed=True))
    def mem_read_64bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 8), signed=True)
    def mem_read_32bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 4), signed=True)
    def mem_read_16bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 2), signed=True)
    def mem_read_8bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 1), signed=True)

    def assemble(self, program):
        ''' Return a list of byte-encoded assembly from source. '''
        rawtext, data = [], []
        labels = {}
        for tokens in self.assemble_segment_tokens(program,'.data'):
            data.append(self.assemble_data(tokens, labels))
        for tokens in self.assemble_segment_tokens(program,'.text'):
            label = self.assemble_label(tokens)
            if label:
                labels[label] = len(rawtext)
                rawtext.append(tokens[1:])
            else:
                rawtext.append(tokens)

        text = []
        for tokens in rawtext[1:]:  # first row is ".text"
            if tokens == []:
                continue
            coded_instr = self.machine_code(tokens, labels)
            text.append(coded_instr)
        return text, data

    def assemble_segment_tokens(self, program, segment_name):
        current_segment = None
        for line in program.splitlines():
            # this is a hack and will mess up string constants for certain
            line = line.split('#')[0] # remove everything after "#"
            line = re.sub(',',' ',line) # remove all commas
            tokens = line.split()
            if len(tokens)>0 and re.match('^\.[a-zA-Z][a-zA-Z]*$', tokens[0]):
                current_segment = tokens[0]
            if current_segment == segment_name:
                yield tokens

    def assemble_data(self, tokens, labels):
        return b'' # STUB

    def assemble_label(self, tokens):
        '''Parse assembly string and return label as string or None.'''
        # "mylabel: foo $2 $3" -> "mylabel' or None
        if len(tokens)>0 and re.match('^[a-zA-Z][a-zA-Z]*:$', tokens[0]):
            return tokens[0][:-1]
        else:
            return None

    def machine_code(self, tokens, labels):
        # find matching instruction and then pack the bits as specified :)
        '''Takes a list of assembly tokens and dictionary of labels, returns bytearray of encoded instruction'''
        # example: machine_code(['addi','$t0','$t0','4'], {}) -> b'\x21\x08\x00\x04'
        return b''
