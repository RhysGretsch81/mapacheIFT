''' ISA definition classes. '''

import collections
import itertools
import types

import assembler
from helpers import ISADefinitionError, AssemblyError, ExecutionError


class  IsaDefinition:
    ''' A base class for defining ISAs. '''

    def __init__(self):
        self._instrfuncs = [getattr(self,f) for f in dir(self) if f.startswith('instruction_')]
        self._pseudofuncs = [getattr(self,f) for f in dir(self) if f.startswith('pseudo_')]
        self._reg_list = []
        self._mem = {}  # a dictionary of 4k bytearrays
        # the parameters below are set by default but can be overridden in derived classes
        self.endian = 'big'  # can be either 'big' or 'little'
        self.isize = 4  # width of an instruction in bytes
        self.text_start_address = 0x10000
        self.data_start_address = 0x40000
        self.assembler = assembler.Assembler(self)
        # try and catch some common errors early
        self.sanity_check()

    def sanity_check(self):
        '''Run a series of checks for common errors in ISA specification.'''
        # check for misspelled "psuedo" for "pseudo"
        if [f for f in dir(self) if f.startswith('psuedo_')]:
            raise ISADefinitionError('misspelled pseudo!')
        # check a mismatch between the instruction name and specification
        for f in dir(self):
            if f.startswith('instruction_'):
                func_op = f[12:]
                def_op = self._extract_asm(getattr(self,f)).split()[0]
                if func_op != def_op:
                    raise ISADefinitionError(f'{f} name "{func_op}" and def "{def_op}" differ.')
        # check that all bitpatterns are pairwise unique
        for f1, f2 in itertools.combinations(self._instrfuncs, 2):
            p1 = self._extract_pattern(f1)
            p2 = self._extract_pattern(f2)
            differ = lambda x,y: (x=='0' and y=='1') or (x=='1' and y=='0')
            differ_by_at_least_one_bit = any(differ(x,y) for x,y in zip(p1,p2))
            if not differ_by_at_least_one_bit:
                raise ISADefinitionError(f'Patterns "{p1}" and "{p2}" overlap.')

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

    def reset_registers(self):
        '''Reset all of the registers to zero.'''
        for rtype, name, bits, size, rnames in self._reg_list:
            if rtype=='reg':
                setattr(self, name, 0)
            else:
                assert rtype=='file'
                for i in range(size):
                    getattr(self, name)[i] = 0

    def register_number_from_name(self, name_in_code):
        for rtype,name,bits,size,rname in self._reg_list:
            if rtype=='file':
                for rnum,register_name in rname.items():
                    if register_name==name_in_code:
                        return rnum
        # can't find name, maybe it is a number directly
        if name_in_code.startswith('$'):
            try:
                return int(name_in_code[1:])
            except ValueError:
                pass
        return None

    def _extract_pattern(self, func):
        '''Extract an patterns from the instruction function docstring.'''
        # string should look like 'add immediate : 001000 sssss ttttt iiiiiiiiiii: something'
        # TODO: this should probably be done once at initialization
        docstring = func.__doc__
        clean_format = docstring.replace(' ','').split(':')[1]
        if len(clean_format) != self.isize*8:
            raise ISADefinitionError(f'format for "{clean_format}" is {len(clean_format)} bits not {self.isize*8}.')
        return clean_format

    def _pattern_match(self, ifunc, instr):
        '''Check if a function docstring matches the raw bytes of instr provided, return fields or None.'''
        if len(instr) != self.isize:
            raise ISADefinitionError(f'instruction "{instr}" is {len(instr)} bytes not {self.isize}.')
        pattern = self._extract_pattern(ifunc)
        instr_as_integer = int.from_bytes(instr, self.endian)
        instr_as_list_of_bits = [(instr_as_integer>>(s-1)) & 0x1 for s in range(self.isize*8,0,-1)]
        fields = collections.defaultdict(int)

        for bpattern, bit in zip(pattern, instr_as_list_of_bits):
            if bpattern=='0' and bit==1:
                return None
            elif bpattern=='1' and bit==0:
                return None
            elif bpattern!='-':
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
            elif part.startswith('&'):
                addr = operand_field(part, '&')
                instruction.append(f'{hex(addr)}')
            elif part.startswith('^'):
                addr = operand_field(part, '^')
                instruction.append(f'+{hex(addr<<2)}')
            elif part.startswith('!'):
                immed = operand_field(part, '!')
                instruction.append(f'{immed}')
            else:
                raise ISADefinitionError(f'Unknown operand specifier: "{part}" in "{asm_pattern}"')
        return str.join(' ', instruction)

    def invalid_when(self, condition, message):
        '''If condition is true, raise ExecutionError with specified message.'''
        if condition:
            raise ExecutionError(message)

    def fetch(self):
        '''Fetch the next instruction at PC and return as an array of bytes.'''
        return self.mem_read(self.PC, self.isize)

    def decode(self, instr):
        '''Given an instruction (as array of bytes) return its decoded form.'''
        for ifunc in self._instrfuncs:
            ifield = self._pattern_match(ifunc, instr)
            if ifield is not None:
                return ifunc, ifield
        raise ExecutionError(f'Unable to decode bytes as instruction: "{instr}".')

    def execute(self, decoded_instr):
        '''Execute a decoded instruction.'''
        ifunction, ifield = decoded_instr
        return ifunction(ifield)

    def istring(self, decoded_instr):
        '''Return a string representation of a decoded instruction.'''
        ifunction, ifield = decoded_instr
        asm_pattern = self._extract_asm(ifunction)
        instr_string = self._format_asm(asm_pattern, ifield)
        return instr_string

    def step(self):
        '''Step the simulator forward and return tuple(pc, a string of instruction executed).'''
        ipc = self.PC
        instr_mem = self.fetch()
        decoded_instr = self.decode(instr_mem)
        ireturn = self.execute(decoded_instr)
        if hasattr(self,'finalize_execution'):
            self.finalize_execution(decoded_instr)
        return ipc, self.istring(decoded_instr), ireturn

    def mem_map(self, start_address, size):
        '''Map a region of physical memory into the simulator.'''
        # TODO: page size be configurable by the isa
        self.invalid_when(start_address & 0xfff, 'Memory start address is not 4k page aligned' )
        self.invalid_when(size & 0xfff, 'Memory size is not 4k page aligned' )
        self.invalid_when(size <= 0, 'Non-positive memory allocation size' )
        self.invalid_when(start_address < 0, 'Negative start address' )
        for page in range(start_address, start_address+size, 4096):
            self.invalid_when(page in self._mem, 'Attempted to map page which is already mapped' )
            self._mem[page] = bytearray(4096)

    def mem_read(self, start_addr, size):
        '''Read a region of memory and return an array of bytes.'''
        if size <= 0:
            raise ISADefinitionError(f'Memory read of size "{size}" not supported')
        page, offset = start_addr & ~0xfff, start_addr & 0xfff
        end_page = (start_addr + size - 1) & ~0xfff
        self.invalid_when(page != end_page, f'Memory read across page boundries not supported' )
        self.invalid_when(page not in self._mem, f'Segmentation Fault (access to unmapped page "{hex(page)}")' )
        return self._mem[page][offset:offset+size]

    def mem_write(self, start_addr, data):
        '''Write an array of bytes into memory.'''
        page, offset = start_addr & ~0xfff, start_addr & 0xfff
        size = len(data)
        end_page = (start_addr + size - 1) & ~0xfff
        self.invalid_when(page != end_page, f'Memory write across page boundries not supported' )
        self.invalid_when(page not in self._mem, f'Segmentation Fault (access to unmapped page "{hex(page)}")' )
        self._mem[page][offset:offset+size] = data

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
        return int.from_bytes(self.mem_read(start_addr, 8), self.endian, signed=True)
    def mem_read_32bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 4), self.endian, signed=True)
    def mem_read_16bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 2), self.endian, signed=True)
    def mem_read_8bit(self, start_addr):
        return int.from_bytes(self.mem_read(start_addr, 1), self.endian, signed=True)

