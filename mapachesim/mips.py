''' MIPS machine definition. '''

import keystone  # <- pip3 install keystone-engine
from isa import IsaDefinition, sign_extend, bit_select

class Mips(IsaDefinition):
    ''' MIPS Instruction Set Definition. '''
    def __init__(self):
        super().__init__()
        mips_rnames = {
            0:'$0',    1:'$at',   2:'$v0',   3:'$v1',
            4:'$a0',   5:'$a1',   6:'$a2',   7:'$a3',
            8:'$t0',   9:'$t1',   10:'$t2',  11:'$t3',
            12:'$t4',  13:'$t5',  14:'$t6',  15:'$t7',
            16:'$s0',  17:'$s1',  18:'$s2',  19:'$s3',
            20:'$s4',  21:'$s5',  22:'$s6',  23:'$s7',
            24:'$t8',  25:'$t9',  26:'$k0',  27:'$k1',
            28:'$gp',  29:'$sp',  30:'$fp',  31:'$ra'}
        self.make_register_file('R', 32, 32, rnames=mips_rnames)
        self.make_register('PC', 32)
        self.make_register('HI', 32)
        self.make_register('LO', 32)
        self.jumps = set([self.instruction_j])
        self.endian = 'big'

    def assemble(self, file, text_start_address, data_start_address):
        '''Covert a file to code and data bytes.'''
        ks_arch = keystone.KS_ARCH_MIPS
        ks_mode = keystone.KS_MODE_MIPS32 + keystone.KS_MODE_BIG_ENDIAN
        with open(file,'r') as f:
            source = f.read()
            try:
                self.ks = keystone.Ks(ks_arch, ks_mode)
                encoding, count = self.ks.asm(source, addr=text_start_address)
            except keystone.KsError as e:
                print(f'\nError: Cannot parse assembly. [{e}]\n')
        code = bytes(bytearray(encoding))
        return code, b''  # STUB for data

    def instruction_j(self, ifield):
        'jump: 000010 aaaaaaaaaaaaaaaaaaaaaaaaaa : j @a'
        upper_bits = bit_select(self.PC + 4, 31, 28)
        self.PC = upper_bits + (ifield.a << 2)

    def instruction_add(self, ifield):
        'add : 000000 sssss ttttt ddddd xxxxx 100000: addi $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] + self.R[ifield.t] 

    def instruction_addi(self, ifield):
        'add immediate : 001000 sssss ttttt iiiiiiiiiiiiiiii : addi $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] + sign_extend(ifield.i, 16)

    def instruction_nop(self, ifield):
        'nop : 000000 00000 00000 00000 00000 000000 : nop'
        pass

    def finalize_execution(self, decoded_instr):
        ifunction, ifields = decoded_instr
        self.R[0] = 0  # keep regisiter 0 value as zero
        if ifunction not in self.jumps:
            self.PC = self.PC + 4

