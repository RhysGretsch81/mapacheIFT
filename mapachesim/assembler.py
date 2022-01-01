''' Generic Assembler. '''

import re
from helpers import bit_select, log2, align
from helpers import ISADefinitionError, AssemblyError

asm_id = '[a-zA-Z_][a-zA-Z0-9_]*'

class Assembler:
    def __init__(self, isa):
        self.isa = isa
        self.END_OF_LINE = object()

    def assemble(self, program, text_start_address, data_start_address):
        ''' Return a list of byte-encoded assembly from source. '''
        labels = {}
        tokenized_program = list(self.tokenize(program))
        data = self.assemble_data(labels, tokenized_program, data_start_address)
        self.set_text_labels(labels, tokenized_program, text_start_address)
        text = self.assemble_text(labels, tokenized_program)
        return text, data

    def assemble_data(self, labels, tokenized_program, data_start_address):
        ''' Return the data segment bytes and update the label table. '''
        data_bytes = []
        address = data_start_address
        for lineno, label, type, coded_data in self.program_data(tokenized_program):
            # add padding as appropriate
            padding = self.pad_to_align(address, type)
            address += len(padding)
            data_bytes.append(padding)
            # set the label to point to the padded location and append bytes
            labels[label] = address
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
        for lineno, token in self.segment(tokenized_program, '.data'):
            if token == self.END_OF_LINE:
                if dline == []:
                    continue
                print(dline)
                label = self.parse_label(dline[0], lineno)
                type, value = self.code_data(dline[1], dline[2], lineno)
                yield lineno, label, type, value 
                dline = []
            else:
                dline.append(token)
        if dline != []:
            raise AssemblyError(f'Incomplete data "{dline}" at line {lineno}.')

    def parse_label(self, label, lineno):
        if re.match(f'^{asm_id}:$', label):
            return label[:-1]
        else:
            raise AssemblyError(f'Bad data label at line {lineno}.')

    def code_data(self, type, value, lineno):
        ''' Encode the provided assembly data as bytestring. '''
        # TODO should the word size be an ISA specific thing?
        # TODO More error checking here 
        if type == '.asciiz':
            if value[0]!='"' or value[-1]!='"':
                raise AssemblyError(f'Bad string constant at line {lineno}.')
            naked_string = value[1:-1]
            return 'asciiz', naked_string.encode('ascii') + b'\x00'
        elif type == '.word':
            return 'word', int(value).to_bytes(4, self.isa.endian)
        elif type == '.half':
            return 'half', int(value).to_bytes(2, self.isa.endian)
        else:
            raise AssemblyError(f'Unknown data type "{type}" at line {lineno}.')

    def set_text_labels(self, labels, tokenized_program, text_start_address):
        ''' Walk the instructions and set the text label addresses. '''
        instr_number = 0
        for lineno, instr in self.instructions(tokenized_program):
            if re.match(f'^{asm_id}:$', instr[0]):
                label_name = instr[0][:-1]
                labels[label_name] = instr_number * self.isa.isize + text_start_address
            else:
                instr_number += 1

    def assemble_text(self, labels, tokenized_program):
        ''' Given the labels and tokenized program, return a list of bytes for the text segment. '''
        instr_bytes = []
        for lineno, instr in self.instructions(tokenized_program):
            if re.match(f'^{asm_id}:$', instr[0]):
                continue
            coded_instr = self.machine_code(instr, labels)
            instr_bytes.append(coded_instr)
        text = b''.join(instr_bytes)
        return text

    def instructions(self, tokenized_program):
        ''' Take a tokenized program and generate lists of token by instruction. '''
        instr = []
        for lineno, token in self.segment(tokenized_program, '.text'):
            if token!=self.END_OF_LINE and re.match(f'^{asm_id}:$', token):
                yield lineno, [token]
            elif token is self.END_OF_LINE and instr:
                yield lineno, instr
                instr = []
            elif token!=self.END_OF_LINE:
                instr.append(token)

    def segment(self, tokenized_program, segment_name):
        ''' Generate the tokens corresponding to the specified segement. '''
        for lineno, token in tokenized_program:
            if token in ['.data','.text']:
                current_segment = token
            elif current_segment == segment_name:
                yield lineno, token

    def tokenize(self, program):
        ''' Break program text into tokens by whitespace, including special EOL. '''
        for line_number, line in enumerate(program.splitlines()):
            # this is a hack and will mess up string constants for certain
            line = line.split('#')[0] # remove everything after "#"
            line = re.sub(',',' ',line) # remove all commas
            tokens = line.split()
            if len(tokens)==0:
                continue
            for token in tokens:
                yield line_number, token
            yield line_number, self.END_OF_LINE

    def machine_code(self, tokens, labels):
        '''Takes a list of assembly tokens and dictionary of labels, returns bytearray of encoded instruction'''
        # example: machine_code(['addi','$t0','$t0','4'], {}) -> b'\x21\x08\x00\x04'
        iname = tokens[0]
        iops = tokens[1:]
        for ifunc in self.isa._ifuncs:
            if ifunc.__name__ == f'instruction_{iname}':
                pattern = self.isa._extract_pattern(ifunc)
                asm = self.isa._extract_asm(ifunc)
                asmops = asm.split()[1:]
                return self.machine_code_pack(pattern, asmops, iops, labels)
        raise ISADefinitionError(f'Cannot find instruction "{iname}".')

    def machine_code_pack(self, pattern, asmops, iops, labels):
        '''Pack the instruction operands into the assembly instruction.'''
        instr = 0
        optable = self.machine_code_make_optable(asmops, iops, labels)
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

    def machine_code_make_optable(self, asmops, iops, labels):
        optable = {}
        if len(asmops) != len(iops):
            raise AssemblyError(f'Cannot match "{asmops}" to "{iops}.')
        for op_def, op_input in zip(asmops, iops):
            if op_def.startswith('$'):
                rnum = self.isa.register_number_from_name(op_input)
                optable[op_def[1:]] = rnum
            elif op_def.startswith('@'):
                optable[op_def[1:]] = labels[op_input] >> log2(self.isa.isize)
            elif op_def.startswith('!'):
                optable[op_def[1:]] = int(op_input, 16)
            else:
                raise AssemblyError(f'Unknown op_def "{op_def}" in "{asmops}".')
        return optable
