''' Generic Assembler. '''

import re
from helpers import bit_select, log2

# Right now Assember reaches way too far into the isa class.  The isa
# class might be refactors to be a thinner interface, with the simulation
# stripped out to seperate class as well?

class Assembler:
    def __init__(self, isa):
        self.isa = isa

    def assemble(self, program, start_addr=None):
        ''' Return a list of byte-encoded assembly from source. '''
        rawtext, data = [], []
        labels = {}
        if start_addr is None:
            start_addr = self.isa.text_start_address
        for tokens in self.assemble_segment_tokens(program,'.data'):
            data.append(self.assemble_data(tokens, labels))
        for tokens in self.assemble_segment_tokens(program,'.text'):
            label = self.assemble_label(tokens)
            if label:
                instr_num = len(rawtext)
                labels[label] = instr_num * self.isa.isize + start_addr
                print(hex(instr_num * self.isa.isize + start_addr))
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
            else:
                value = optable[p]
                bitpos = counttable[p]-1
                pbit = bit_select(value, bitpos, bitpos, shift=True)
                assert pbit==0 or pbit==1
                instr = (instr<<1) | pbit
                counttable[p] -= 1

        encoded_instr_as_bytes = instr.to_bytes(self.isa.isize, byteorder=self.isa.endian, signed=False)
        print(hex(instr))
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
