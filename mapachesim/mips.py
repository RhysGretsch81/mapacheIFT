''' MIPS machine definition. '''

from helpers import sign_extend, bit_select
from isa import IsaDefinition
from assembler import Assembler

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
        self.jumps = set([self.instruction_j, self.instruction_jr, self.instruction_jalr])
        self.endian = 'big'
        self.assembler = Assembler(self)

    def finalize_execution(self, decoded_instr):
        ifunction, ifields = decoded_instr
        self.R[0] = 0  # keep regisiter 0 value as zero
        if ifunction not in self.jumps:
            self.PC = self.PC + 4

    def invalid_when(self, condition, message):
        if condition:
            raise ValueError(message)

    # R-format Instructions

    def instruction_sll(self, ifield):
        'shift left logical : 000000 xxxxx ttttt ddddd hhhhh 000000: sll $d $t !h'
        self.R[ifield.d] = self.R[ifield.t] << ifield.h

    def instruction_srl(self, ifield):
        'shift right logical : 000000 xxxxx ttttt ddddd hhhhh 000010: srl $d $t !h'
        self.R[ifield.d] = self.R[ifield.t] >> ifield.h

    def instruction_sra(self, ifield):
        'shift right arithmetic : 000000 xxxxx ttttt ddddd hhhhh 000011: sra $d $t !h'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> ifield.h

    def instruction_sllv(self, ifield):
        'shift left logical variable : 000000 sssss ttttt ddddd xxxxx 000100: sllv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] << self.R[ifield.s]

    def instruction_srlv(self, ifield):
        'shift right logical variable : 000000 sssss ttttt ddddd xxxxx 000110: srlv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] >> self.R[ifield.s]

    def instruction_srav(self, ifield):
        'shift right arithmetic variable : 000000 sssss ttttt ddddd xxxxx 000111: srav $d $t $s'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> self.R[ifield.s]

    def instruction_jr(self, ifield):
        'jump register : 000000 sssss xxxxx xxxxx xxxxx 001000: jr $s'
        self.invalid_when(self.R[ifield.s] % 4 != 0, 'jr: R[$rs] must be a multiple of 4')
        self.PC = self.R[ifield.s]

    def instruction_jalr(self, ifield):
        'jump-and-link register: 000000 sssss xxxxx ddddd xxxxx 001001: jalr $d $s'
        self.invalid_when(self.R[ifield.s] % 4 != 0, 'jalr: R[$rs] must be a multiple of 4')
        self.invalid_when(ifield.s == ifield.d, 'jalr: $rs and $rd must be different registers')
        tmp = self.R[ifield.s]
        self.R[ifield.d] = self.PC + 4
        self.PC = tmp

    def instruction_syscall(self, ifield):
        'system call : 000000 xxxxx xxxxx xxxxx xxxxx 001100: syscall'
        v0, a0, a1 = 2, 4, 5
        if self.R[v0] == 1:  # print integer
            print(sign_extend(self.R[a0],32))
        elif self.R[v0] == 4:  # print string
            maxstring = 1024
            address = self.R[a0]
            printable_chars = set(bytes(string.printable, 'ascii'))
            for i in range(maxstring):
                next_byte = self.mem_read(start_addr, 1)
                if next_byte == b'\x00':
                    break
                elif next_byte in printable_chars:
                    print(next_byte.decode('ascii'), end='')
                else:
                    print('<?>', end='')
                address += 1
            else: # hit the maxstring limit
                    print(f'... (string continues beyond limit of {maxstring})', end='')
        elif self.R[v0] == 5:  # read integer
            raise NotImplementedError('read integer')
        elif self.R[v0] == 8:  # read string
            raise NotImplementedError('read string')
        elif self.R[v0] == 10:  # exit
            raise NotImplementedError('exit')
        else:
            self.invalid_when(True, 'syscall: invalid system call service')

    def instruction_add(self, ifield):
        'add : 000000 sssss ttttt ddddd xxxxx 100000: addi $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] + self.R[ifield.t] 

    # J-format Instructions

    def instruction_j(self, ifield):
        'jump : 000010 aaaaaaaaaaaaaaaaaaaaaaaaaa : j @a'
        upper_bits = bit_select(self.PC + 4, 31, 28)
        self.PC = upper_bits + (ifield.a << 2)

    # I-format Instructions

    def instruction_addi(self, ifield):
        'add immediate : 001000 sssss ttttt iiiiiiiiiiiiiiii : addi $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] + sign_extend(ifield.i, 16)

    def instruction_nop(self, ifield):
        'nop : 000000 00000 00000 00000 00000 000000 : nop'
        pass

