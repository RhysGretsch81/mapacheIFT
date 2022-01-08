''' MIPS machine definition. '''

import string

from helpers import sign_extend, bit_select
from helpers import ExecutionError, ExecutionComplete
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
        self.jumps = set([self.instruction_j, self.instruction_jr, self.instruction_jalr, self.instruction_beq])
        self.endian = 'big'
        self.assembler = Assembler(self)

    def finalize_execution(self, decoded_instruction):
        ifunction, ifields = decoded_instruction
        self.R[0] = 0  # keep regisiter 0 value as zero
        if ifunction not in self.jumps:
            self.PC = self.PC + 4

    def reset_registers(self):
        super().reset_registers()
        self.R[28] = 0x10008000 # same value as SPIM at reset
        self.R[29] = 0x7fffeffc # same value as SPIM at reset

    # Pseudo Instructions

    def pseudo_li(self, ifield):
        'load immediate : pseudo : li $d !i'
        const = ifield.i
        if const.bit_length() <= 16:
            yield f'addiu ${ifield.d} $0 {const}'
        else:
            upper = const & 0xffff0000
            lower = const & 0x0000ffff
            yield f'lui ${ifield.d} {str(upper)}'
            yield f'ori ${ifield.d} ${ifield.d} {str(lower)}'

    def pseudo_la(self, ifield):
        'load address : pseudo : la $d &a'
        upper = (ifield.a >> 16) & 0xffff
        lower = ifield.a & 0xffff
        yield f'lui ${ifield.d} {str(upper)}'
        yield f'ori ${ifield.d} ${ifield.d} {str(lower)}'

    def pseudo_move(self, ifield):
        'move : pseudo : move $d $s'
        yield f'add ${ifield.d} ${ifield.s} $0'

    def pseudo_nop(self, ifield):
        'nop : pseudo : nop'
        yield f'sll $0 $0 0'

    # R-format Instructions

    def instruction_sll(self, ifield):
        'shift left logical : 000000 ----- ttttt ddddd hhhhh 000000: sll $d $t !h'
        self.R[ifield.d] = self.R[ifield.t] << ifield.h

    def instruction_srl(self, ifield):
        'shift right logical : 000000 ----- ttttt ddddd hhhhh 000010: srl $d $t !h'
        self.R[ifield.d] = self.R[ifield.t] >> ifield.h

    def instruction_sra(self, ifield):
        'shift right arithmetic : 000000 ----- ttttt ddddd hhhhh 000011: sra $d $t !h'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> ifield.h

    def instruction_sllv(self, ifield):
        'shift left logical variable : 000000 sssss ttttt ddddd ----- 000100: sllv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] << self.R[ifield.s]

    def instruction_srlv(self, ifield):
        'shift right logical variable : 000000 sssss ttttt ddddd ----- 000110: srlv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] >> self.R[ifield.s]

    def instruction_srav(self, ifield):
        'shift right arithmetic variable : 000000 sssss ttttt ddddd ----- 000111: srav $d $t $s'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> self.R[ifield.s]

    def instruction_jr(self, ifield):
        'jump register : 000000 sssss ----- ----- ----- 001000: jr $s'
        self.invalid_when(self.R[ifield.s] % 4 != 0, 'jr: R[$rs] must be a multiple of 4')
        self.PC = self.R[ifield.s]

    def instruction_jalr(self, ifield):
        'jump-and-link register: 000000 sssss ----- ddddd ----- 001001: jalr $d $s'
        self.invalid_when(self.R[ifield.s] % 4 != 0, 'jalr: R[$rs] must be a multiple of 4')
        self.invalid_when(ifield.s == ifield.d, 'jalr: $rs and $rd must be different registers')
        tmp = self.R[ifield.s]
        self.R[ifield.d] = self.PC + 4
        self.PC = tmp

    def instruction_syscall(self, ifield):
        'system call : 000000 ----- ----- ----- ----- 001100: syscall'
        v0, a0, a1 = 2, 4, 5

        if self.R[v0] == 1:  # print integer
            print(sign_extend(self.R[a0],32))

        elif self.R[v0] == 4:  # print string
            maxstring = 1024
            address = self.R[a0]
            printable_chars = bytes(string.printable, 'ascii')
            for i in range(maxstring):
                next_byte = self.mem_read(address, 1)
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
            input_string = input()
            try:
                self.R[v0] = int(input_string)
            except ValueError:
                raise ExecutionError('invalid integer read during system call')

        elif self.R[v0] == 8:  # read string
            raise NotImplementedError('read string')

        elif self.R[v0] == 10:  # exit
            return ExecutionComplete

        else:
            self.invalid_when(True, 'syscall: invalid system call service')

    def instruction_mflo(self, ifield):
        'move from lo : 000000 ----- ----- ddddd ----- 010010: mflo $d'
        self.R[ifield.d] = self.LO

    def instruction_mult(self, ifield):
        'multiply : 000000 sssss ttttt ----- ----- 011000: mult $s $t'
        result = self.R[ifield.s] * self.R[ifield.t]
        self.LO = result
        self.HI = result>>32

    def instruction_add(self, ifield):
        'add : 000000 sssss ttttt ddddd ----- 100000: add $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] + self.R[ifield.t] 

    # J-format Instructions

    def instruction_j(self, ifield):
        'jump : 000010 aaaaaaaaaaaaaaaaaaaaaaaaaa : j @a'
        upper_bits = bit_select(self.PC + 4, 31, 28)
        self.PC = upper_bits + (ifield.a << 2)

    def instruction_jal(self, ifield):
        'jump and link : 000011 aaaaaaaaaaaaaaaaaaaaaaaaaa : jal @a'
        self.R[31] = self.PC + 4
        upper_bits = bit_select(self.PC + 4, 31, 28)
        self.PC = upper_bits + (ifield.a << 2)

    # I-format Instructions

    #def instruction_beq(self, ifield):
    #    'branch if equal : 000100 sssss ttttt aaaaaaaaaaaaaaaa : beq $s $t ^a'
    #    newpc = self.PC + 4
    #    if self.R[ifield.s] == self.R[ifield.t]:
    #        newpc += sign_extend(ifield.a, 16) << 2
    #    self.PC = newpc

    def instruction_beq(self, ifield):
        'branch if equal : 000100 sssss ttttt aaaaaaaaaaaaaaaa : beq $s $t @a'
        # TODO: this should be PC-relative addressing! started above, but using absolute for now
        newpc = self.PC + 4
        if self.R[ifield.s] == self.R[ifield.t]:
            upper_bits = bit_select(self.PC + 4, 31, 18)
            newpc = upper_bits + (ifield.a << 2)
        self.PC = newpc

    def instruction_addi(self, ifield):
        'add immediate : 001000 sssss ttttt iiiiiiiiiiiiiiii : addi $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] + sign_extend(ifield.i, 16)

    def instruction_addiu(self, ifield):
        'add immediate unsigned : 001001 sssss ttttt iiiiiiiiiiiiiiii : addiu $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] + sign_extend(ifield.i, 16)

    def instruction_ori(self, ifield):
        'or immediate : 001101 sssss ttttt iiiiiiiiiiiiiiii : ori $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] | ifield.i

    def instruction_lui(self, ifield):
        'load upper immediate : 001111 ----- ttttt iiiiiiiiiiiiiiii : lui $t !i'
        self.R[ifield.t] = ifield.i << 16

    def instruction_lw(self, ifield):
        # TODO: add "imm(addr)" format 
        'load word : 100010 sssss ttttt iiiiiiiiiiiiiiii : lw $t !i $s'
        addr = self.R[ifield.s] + sign_extend(ifield.i, 16)
        self.invalid_when(addr % 4 != 0, 'lw: R[$rs]+immed must be a multiple of 4')
        self.R[ifield.t] = self.mem_read_32bit(addr)

    def instruction_sw(self, ifield):
        # TODO: add "imm(addr)" format 
        'store word : 101011 sssss ttttt iiiiiiiiiiiiiiii : sw $t !i $s'
        addr = self.R[ifield.s] + sign_extend(ifield.i, 16)
        self.invalid_when(addr % 4 != 0, 'sw: R[$rs]+immed must be a multiple of 4')
        self.mem_write_32bit(addr, value=self.R[ifield.t])
