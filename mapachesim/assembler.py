''' Generic Assembler. '''

import re
import types
import shlex
import codecs
import collections

from helpers import bit_select, log2, align
from helpers import ISADefinitionError, AssemblyError

asm_id = '[a-zA-Z_][a-zA-Z0-9_]*'

class Assembler:
    def __init__(self, isa):
        self.isa = isa
        self.END_OF_LINE = object()
        self.labels = {}
        self.current_line = None
        
    def assemble(self, program, text_start_address, data_start_address):
        ''' Return a list of byte-encoded assembly from source. '''
        self.labels = {}  # reset all the labels  TODO: clear the breakpoints?
        tokenized_program = list(self.tokenize(program))
        data = self.assemble_data(tokenized_program, data_start_address)
        self.set_text_labels(tokenized_program, text_start_address)
        text = self.assemble_text(tokenized_program)
        return text, data, self.labels

    def assemble_data(self, tokenized_program, data_start_address):
        ''' Return the data segment bytes and update the label table. '''
        data_bytes = []
        address = data_start_address
        for label, type, coded_data in self.program_data(tokenized_program):
            # add padding as appropriate
            padding = self.pad_to_align(address, type)
            address += len(padding)
            data_bytes.append(padding)
            # set the label to point to the padded location and append bytes
            self.labels[label] = address
            address += len(coded_data)
            data_bytes.append(coded_data)
        final_data = b''.join(data_bytes)
        return final_data

    def pad_to_align(self, address, type):
        ''' Return the bytes necessary to pad the address for the correct type.'''
        # TODO: should these data types and alignments be ISA specific?
        if type in ['word']:
            alignment = 4
        elif type in ['half']:
            alignment = 2
        else:
            alignment = 1
        pad_amount = align(address, alignment) - address
        padding = b'\x00' * pad_amount
        return padding

    def program_data(self, tokenized_program):
        ''' Given the tokenized program, return data specifiers for assembly. '''
        dline = []
        for token in self.segment(tokenized_program, '.data'):
            if token == self.END_OF_LINE:
                if dline == []:
                    continue
                label = self.parse_label(dline[0])
                type, value = self.code_data(dline[1], dline[2])
                yield label, type, value 
                dline = []
            else:
                dline.append(token)
        if dline != []:
            raise AssemblyError(f'Incomplete data "{dline}" at line {self.current_line}.')

    def parse_label(self, label):
        ''' Return the name of the label, raising an error if a problem exists. '''
        if re.match(f'^{asm_id}:$', label):
            return label[:-1]
        else:
            raise AssemblyError(f'Bad data label at line {self.current_line}.')

    def code_data(self, type, value):
        ''' Encode the provided assembly data as bytestring. '''
        # TODO should the word size be an ISA specific thing?
        # TODO More error checking here 
        if type == '.asciiz':
            if value[0]!='"' or value[-1]!='"':
                raise AssemblyError(f'Bad string constant at line {self.current_line}.')
            naked_string = value[1:-1]
            #return 'asciiz', naked_string.encode('ascii') + b'\x00'
            return 'asciiz', codecs.escape_decode(naked_string)[0] + b'\x00'
        elif type == '.word':
            return 'word', int(value).to_bytes(4, self.isa.endian)
        elif type == '.half':
            return 'half', int(value).to_bytes(2, self.isa.endian)
        else:
            raise AssemblyError(f'Unknown data type "{type}" at line {self.current_line}.')

    def set_text_labels(self, tokenized_program, text_start_address):
        ''' Walk the instructions and set the text label addresses. '''
        instr_number = 0
        for instr in self.instructions(tokenized_program):
            if re.match(f'^{asm_id}:$', instr[0]):
                label_name = instr[0][:-1]
                self.labels[label_name] = instr_number * self.isa.isize + text_start_address
            else:
                instr_number += 1

    def assemble_text(self, tokenized_program):
        ''' Given the labels and tokenized program, return a list of bytes for the text segment. '''
        instr_bytes = []
        for instr in self.instructions(tokenized_program):
            if re.match(f'^{asm_id}:$', instr[0]):
                continue
            coded_instr = self.machine_code(instr)
            instr_bytes.append(coded_instr)
        text = b''.join(instr_bytes)
        return text

    def instructions(self, tokenized_program):
        ''' Take a tokenized program and generate lists of token by instruction. '''
        instr = []
        for token in self.segment(tokenized_program, '.text'):
            if token!=self.END_OF_LINE and re.match(f'^{asm_id}:$', token):
                yield [token]
            elif token is self.END_OF_LINE and instr:
                if self.is_pseudo(instr):
                    for pseudo_instr in self.expand_pseudo(instr):
                        yield pseudo_instr.split()
                else:
                    yield instr
                instr = []
            elif token!=self.END_OF_LINE:
                instr.append(token)

    def is_pseudo(self, instr):
        ''' Return True if instr is a psuedo-instruction. '''
        iname = instr[0]
        pseudofunc = getattr(self.isa, f'pseudo_{iname}', None)
        return pseudofunc is not None

    def expand_pseudo(self, instr):
        ''' Invokes the pseudo-instruction generator for instr. '''
        iname, iops = instr[0], instr[1:]
        pseudofunc = getattr(self.isa, f'pseudo_{iname}')
        asm = self.isa._extract_asm(pseudofunc)
        asmops = asm.split()[1:]
        optable = self.machine_code_make_optable(asmops, iops)
        ifield = types.SimpleNamespace(**optable)
        yield from pseudofunc(ifield)

    def segment(self, tokenized_program, segment_name):
        ''' Generate the tokens corresponding to the specified segement. '''
        current_segment = None
        for lineno, token in tokenized_program:
            self.current_line = lineno
            if token in ['.data','.text']:
                current_segment = token
            elif current_segment == segment_name:
                yield token
        if current_segment == None:
            raise AssemblyError('Program contains no segments.')

    def tokenize(self, program):
        ''' Break program text into tokens by whitespace, including special EOL. '''
        for line_number, line in enumerate(program.splitlines(), start=1):
            lex = shlex.shlex(line)
            lex.whitespace = ' \t\r\n,()' # right now we just use () as whitespace
            lex.whitespace_split = True
            token = lex.get_token()
            if token == '':
                continue
            while token != '':
                yield line_number, token
                token = lex.get_token()
            yield line_number, self.END_OF_LINE

    def machine_code(self, tokens):
        '''Takes a list of assembly tokens and dictionary of labels, returns bytearray of encoded instruction'''
        # example: machine_code(['addi','$t0','$t0','4'], {}) -> b'\x21\x08\x00\x04'
        iname, iops = tokens[0], tokens[1:]
        ifunc = getattr(self.isa, f'instruction_{iname}', None)
        if ifunc is None:
            raise AssemblyError(f'Unknown instruction "{iname} {" ".join(iops)}" at line {self.current_line}.')
        pattern = self.isa._extract_pattern(ifunc)
        asm = self.isa._extract_asm(ifunc)
        asmops = asm.split()[1:]        
        return self.machine_code_pack(pattern, asmops, iops)

    def machine_code_pack(self, pattern, asmops, iops):
        '''Return bytes of instruction given pattern and operands.'''

        def raise_error(msg):
            raise AssemblyError(f'{msg} "{" ".join(iops)}" '
                                f'-> "{" ".join(asmops)}" '
                                f'at line {self.current_line}.')

        if len(asmops) != len(iops):
            raise_error('Cannot match arguments')

        op_table = {}  # map field_name -> bitstring (e.g. 'a'->'010011')
        bitcount_table = collections.Counter(pattern)  # count of letters
        for asmop, iop in zip(asmops, iops):
            field_name, bitstring = self.machine_encode_operand(asmop, iop, bitcount_table)
            if not isinstance(bitstring, str):
                raise_error(f'Invalid encoding operand error in')
            if set(bitstring) != set('01'):
                raise_error(f'Non binary encoding error in')
            if field_name not in bitcount_table:
                raise_error(f'Unknown field "{field_name}" in')
            if len(bitstring) != bitcount_table[field_name]:
                raise_error(f'Incorrectly sized field "{field_name}" in')
            optable[field_name] = bitstring

        for p in bitcount_table:
            if p not in '01-' and p not in optable:
                raise_error(f'Unknown pattern "{p}" in')

        instr = 0
        for p in pattern:
            if p=='0':
                instr = (instr<<1)
            elif p=='1':
                instr = (instr<<1) | 0x1
            elif p=='-':
                instr = (instr<<1) # zero for don't cares
            else:
                value = optable[p][0]
                optable[p] = optable[p][1:]
                if value == '0':
                    instr = (instr<<1)
                else
                    assert value == '1'
                    instr = (instr<<1) | 0x1

        encoded_instr_as_bytes = instr.to_bytes(self.isa.isize, byteorder=self.isa.endian, signed=False)
        return encoded_instr_as_bytes

    def machine_encode_operand(self, asmop, iop, bitcount_table):
        '''covert the specified asssembly operand into a bitstring of the correct length.'''
        field_type = asmop[0]
        field_name = asmop[1]
        field_len = bitcount_table[field_name]

        def error_on_none(val, msg):
            if val is None:
                raise AssemblyError(f'{msg} "{iop}" at line {self.current_line}.')

        # Registers
        if field_type == '$':
            rnum = self.isa.register_number_from_name(iop)
            error_on_none(rnum, 'Unknown register name')
            bitstring = int_to_bitstring(rnum, field_len, signed=False)
            error_on_none(bistring, 'Register specifier overflow')

        # 0-Relative Addressing (Instruction Word Aligned)
        elif field_type == '@':
            addr = self.labels.get(iop, None)
            error_on_none(addr, 'Unknown label')
            shifted_addr = addr >> log2(self.isa.isize)
            bitstring = int_to_bitstring(shifted_addr, field_len, signed=False)
            error_on_none(bitstring, 'Address cannot fit in field')

        # 0-Relative Addressing (Byte Aligned)
        elif field_type == '&':
            addr = self.labels.get(iop, None)
            error_on_none(addr, 'Unknown label')
            bitstring = int_to_bitstring(addr, field_len, signed=False)
            error_on_none(bitstring, 'Address cannot fit in field')

        # PC-Relative Addressing
        #elif asmop.startswith('^'):
        #    raise NotImplementedError  # this is going to require some thinking

        # Decimal Immediates
        elif field_type == '!':
            immed = 
MORE
            elif asmop.startswith('!'):
                try:
                    optable[field_name] = int(iop, 10)
                except ValueError:
                    raise AssemblyError(f'Cannot parse "{iop}" as base-10 integer constant at line {self.current_line}.')
            else:
                raise AssemblyError(f'Unknown asmop "{asmop}" in "{asmops}" at line {self.current_line}.')
        return optable

        
        return field_name, 



    def old_machine_code_pack(self, pattern, asmops, iops):
        '''Pack the instruction operands into the assembly instruction.'''
        instr = 0
        optable = self.machine_code_make_optable(asmops, iops)
        counttable = {p:pattern.count(p) for p in optable}
        for p in pattern:
            if p=='0':
                instr = (instr<<1)
            elif p=='1':
                instr = (instr<<1) | 0x1
            elif p=='-':
                instr = (instr<<1) 
            else:
                value = optable[p]
                bitpos = counttable[p]-1
                pbit = bit_select(value, bitpos, bitpos, shift=True)
                assert pbit==0 or pbit==1
                instr = (instr<<1) | pbit
                counttable[p] -= 1

        encoded_instr_as_bytes = instr.to_bytes(self.isa.isize, byteorder=self.isa.endian, signed=False)
        return encoded_instr_as_bytes

    def old_machine_code_make_optable(self, asmops, iops):
        optable = {}
        if len(asmops) != len(iops):
            raise AssemblyError(f'Cannot match arguments "{" ".join(iops)}" to pattern "{" ".join(asmops)}" at line {self.current_line}.')
        for op_def, op_input in zip(asmops, iops):
            # Registers
            field_name = op_def[1:]
            if op_def.startswith('$'):
                rnum = self.isa.register_number_from_name(op_input)
                if rnum is None:
                    raise AssemblyError(f'Unknown register name "{op_input}" at line {self.current_line}.')
                optable[field_name] = rnum
            # 0-Relative Addressing (Instruction Word Aligned)
            elif op_def.startswith('@'):
                if op_input not in self.labels:
                    raise AssemblyError(f'Unknown label "{op_input}" at line {self.current_line}.')
                optable[field_name] = self.labels[op_input] >> log2(self.isa.isize)
            # 0-Relative Addressing (Byte Aligned)
            elif op_def.startswith('&'):
                if op_input not in self.labels:
                    raise AssemblyError(f'Unknown label "{op_input}" at line {self.current_line}.')
                optable[field_name] = self.labels[op_input]
            # PC-Relative Addressing
            elif op_def.startswith('^'):
                if op_input not in self.labels:
                    raise AssemblyError(f'Unknown label "{op_input}" at line {self.current_line}.')
                optable[field_name] = self.labels[op_input] >> log2(self.isa.isize)
                raise NotImplementedError  # this is going to require some re-thinking
            # Decimal Immediates
            elif op_def.startswith('!'):
                try:
                    optable[field_name] = int(op_input, 10)
                except ValueError:
                    raise AssemblyError(f'Cannot parse "{op_input}" as base-10 integer constant at line {self.current_line}.')
            else:
                raise AssemblyError(f'Unknown op_def "{op_def}" in "{asmops}" at line {self.current_line}.')
        return optable
