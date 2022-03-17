''' MIPS machine definition. '''

import string

from helpers import sign_extend, bit_select, decimalstr_to_int
from helpers import ExecutionError, ExecutionComplete
from isa import IsaDefinition
from assembler import Assembler



def _chunk_list(lst, n):
    '''Chunk a list into a list of lists of length n.'''
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


class Mips_IFT(IsaDefinition):
    ''' MIPS Instruction Set Definition. '''
    #Architecture for ISA information flow tracking in MIPS assembly
    #The programmer must declare what is untrusted
    def __init__(self):
        super().__init__()
        self.ift_ratio = 32
        self.split_mem() #Indicates every bit maps to an ift bit
        self.mem_last_addr = self.text_start_address + 2*1024*1024
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
        #Shadow registers for IFT
        self.make_register_file('T', 32, int(32/self.ift_ratio), rnames=mips_rnames)
        self.make_register('PC', 32)
        self.make_register('HI', 32)
        self.make_register('LO', 32)

        jumps = 'j jal jr jalr beq'.split()
        self.jumps = set(getattr(self, f'instruction_{jump}') for jump in jumps)
        self.endian = 'big'
        self.assembler = Assembler(self)
        self.mem_locations = []

    #Manage memory for IFT bits
    def split_mem(self):
        mem_size = 2*1024*1024 #Size allocated in console.py
        data_space = self.text_start_address+mem_size-self.data_start_address
        partitions = self.ift_ratio+1
        self.ift_data_address = int(self.ift_ratio*data_space/partitions)
        self.ift_data_address += self.text_start_address
        #Normalize to data alignment
        self.ift_data_address -= self.ift_data_address % 4

        ift_offset = int(self.ift_ratio*mem_size/partitions)
        self.ift_stack_address = self.stack_start_address + ift_offset
        self.ift_stack_address -= self.ift_stack_address % 4
    
    def get_ift_addr(self, addr):
        #Ensure address is the location for data
        if addr < self.stack_start_address:
            assert(addr >= self.data_start_address)
            offset = addr - self.data_start_address
            #Divide by 4 necessary to normalize address values
            offset = offset // 4
            return self.ift_data_address + 4*(offset//self.ift_ratio)
        else:
            stack_size = 2*1024*1024
            assert(addr < self.stack_start_address + stack_size)
            offset = self.stack_start_address + stack_size - addr
            return self.ift_stack_address + int(offset/self.ift_ratio)
    
    def get_ift_bit(self, addr):
        if addr < self.stack_start_address:
            offset = (addr - self.data_start_address) // 4
            return offset % self.ift_ratio
        else:
            stack_size = 2*1024*1024
            offset = self.stack_start_address + stack_size - addr
            return offset % self.ift_ratio 
    
    def ift_mask(self, addr):
        ift_length = int(32/self.ift_ratio)
        ift_bit = self.get_ift_bit(addr)
        mask = 0
        for i in range(ift_bit, ift_bit + ift_length):
            mask |= 1<<i
        return mask
    
    def ift_load(self, addr):
        ift_addr = self.get_ift_addr(addr)
        ift_bit = self.get_ift_bit(addr)
        ift_word = self.mem_read_32bit(ift_addr)
        mask = self.ift_mask(addr)
        return (ift_word & mask) >> ift_bit
    
    def ift_store(self, addr, data):
        assert(len(bin(data))-2 <= 32/self.ift_ratio)
        ift_addr = self.get_ift_addr(addr)
        ift_bit = self.get_ift_bit(addr)
        ift_word = self.mem_read_32bit(ift_addr)
        data = data << ift_bit
        mask = ~self.ift_mask(addr)
        ift_word &= mask
        ift_word |= data
        if ift_word == 2**32 - 1:
            #necessary to store properly if all 1's (Completely untrusted)
            ift_word = -1
        self.mem_write_32bit(ift_addr, ift_word)

    def print_mem(self, verbose=True):

        def mformat(rval):
            return f'{rval:02x}'
        
        def getColor(trustVal, bits):
            num1s = bin(trustVal).count('1')
            if trustVal and num1s == bits:
                return '\033[91m'
            elif trustVal:
                return '\033[93m'
            return '\033[92m'

        sep = '  '
        buf = '          '
        untrustedClr = '\033[91m'
        clearClr = '\033[0m'
        print()
        for addr in sorted(self.mem_locations):
            data = [mformat(b) for b in self.mem_read(addr, 4)]
            ift_addr = self.get_ift_addr(addr)
            ift_data = self.mem_read_32bit(ift_addr)
            ift_data = (ift_data & self.ift_mask(addr)) >> self.get_ift_bit(addr)
            data_str = [' '.join(chunk) for chunk in _chunk_list(data, 1)]
            bits_per_byte = 8 // self.ift_ratio if self.ift_ratio < 8 else 1
            for index, byte in enumerate(data_str):
                ift_bit1 = (3-index) * 8 // self.ift_ratio
                mask = (2**bits_per_byte - 1) << ift_bit1
                color = getColor(ift_data & mask, bits_per_byte)
                byte = f'{color}' + byte + f'{clearClr}'
                data_str[index] = byte
            data_str = sep.join(data_str)
            data_str = f'{addr:#010x}:{sep}{data_str}'
            ift_str = ''
            if verbose:
                ift_str = f' | IFT: {bin(ift_data)}'
            print(data_str  + ift_str)
        print()

    def finalize_execution(self, decoded_instruction):
        ifunction, ifields = decoded_instruction
        self.R[0] = 0  # keep regisiter 0 value as zero
        if ifunction not in self.jumps:
            self.PC = self.PC + 4

    def reset_registers(self):
        super().reset_registers()
        self.R[28] = 0x10008000 # same value as SPIM at reset
        self.R[29] = 0x7fffeffc # same value as SPIM at reset

    # -- Pseudo Instructions ---
    # (note: all pseudo operands will be coverted to 32-bit unsigned)

    def pseudo_li(self, ifield):
        'load immediate : pseudo : li $d !i'
        const = ifield.i
        if const.bit_length() <= 16:  # FIX: check negative numbers
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
        self.T[ifield.d] = self.T[ifield.t]

    def instruction_srl(self, ifield):
        'shift right logical : 000000 ----- ttttt ddddd hhhhh 000010: srl $d $t !h'
        self.R[ifield.d] = self.R[ifield.t] >> ifield.h
        self.T[ifield.d] = self.T[ifield.t]

    def instruction_sra(self, ifield):
        'shift right arithmetic : 000000 ----- ttttt ddddd hhhhh 000011: sra $d $t !h'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> ifield.h
        self.T[ifield.d] = self.T[ifield.t]

    def instruction_sllv(self, ifield):
        'shift left logical variable : 000000 sssss ttttt ddddd ----- 000100: sllv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] << self.R[ifield.s]
        self.T[ifield.d] = self.T[ifield.t] | self.T[ifield.s]

    def instruction_srlv(self, ifield):
        'shift right logical variable : 000000 sssss ttttt ddddd ----- 000110: srlv $d $t $s'
        self.R[ifield.d] = self.R[ifield.t] >> self.R[ifield.s]
        self.T[ifield.d] = self.T[ifield.t] | self.T[ifield.s]

    def instruction_srav(self, ifield):
        'shift right arithmetic variable : 000000 sssss ttttt ddddd ----- 000111: srav $d $t $s'
        self.R[ifield.d] = sign_extend(self.R[ifield.t],32) >> self.R[ifield.s]
        self.T[ifield.d] = self.T[ifield.t] | self.T[ifield.s]

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
            try:
                input_str = input()
            except EOFError:
                raise ExecutionError('syscall read end-of-file')
            input_int = decimalstr_to_int(input_str)
            if input_int:
                self.R[v0] = input_int
            else:
                raise ExecutionError('invalid integer read during system call')

        elif self.R[v0] == 8:  # read string
            raise NotImplementedError('read string')

        elif self.R[v0] == 10:  # exit
            self.print_mem()
            return ExecutionComplete

        else:
            self.invalid_when(True, f'syscall: invalid system call service (v0={self.R[v0]})')

    def instruction_mflo(self, ifield):
        'move from lo : 000000 ----- ----- ddddd ----- 010010: mflo $d'
        self.R[ifield.d] = self.LO
        self.T[ifield.d] = self.LO_trust

    def instruction_mult(self, ifield):
        'multiply : 000000 sssss ttttt ----- ----- 011000: mult $s $t'
        result = self.R[ifield.s] * self.R[ifield.t]
        self.LO = result
        self.HI = result>>32
        self.LO_trust = self.T[ifield.s] | self.T[ifield.t]
        self.HI_trust = self.T[ifield.s] | self.T[ifield.t]

    def instruction_add(self, ifield):
        'add : 000000 sssss ttttt ddddd ----- 100000: add $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] + self.R[ifield.t]
        self.T[ifield.d] = self.T[ifield.s] | self.T[ifield.t]

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
        self.T[ifield.t] = self.T[ifield.s]

    def instruction_addiu(self, ifield):
        'add immediate unsigned : 001001 sssss ttttt iiiiiiiiiiiiiiii : addiu $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] + sign_extend(ifield.i, 16)
        self.T[ifield.t] = self.T[ifield.s]

    def instruction_ori(self, ifield):
        'or immediate : 001101 sssss ttttt iiiiiiiiiiiiiiii : ori $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] | ifield.i
        self.T[ifield.t] = self.T[ifield.s] | self.T[ifield.s]

    def instruction_lui(self, ifield):
        'load upper immediate : 001111 ----- ttttt iiiiiiiiiiiiiiii : lui $t !i'
        self.R[ifield.t] = ifield.i << 16

    def instruction_lw(self, ifield):
        # TODO: add "imm(addr)" format 
        'load word : 100010 sssss ttttt iiiiiiiiiiiiiiii : lw $t !i $s'
        addr = self.R[ifield.s] + sign_extend(ifield.i, 16)
        self.invalid_when(addr % 4 != 0, 'lw: R[$rs]+immed must be a multiple of 4')
        self.invalid_when(addr >= self.ift_data_address and addr <= self.ift_stack_address, \
            'Address (%s) encroaching on memory reserved for IFT'%hex(addr))
        self.R[ifield.t] = self.mem_read_32bit(addr)
        self.T[ifield.t] = self.ift_load(addr)
        #Track accessed memory locations
        self.mem_locations += [addr] if addr not in self.mem_locations else []

    def instruction_sw(self, ifield):
        # TODO: add "imm(addr)" format 
        'store word : 101011 sssss ttttt iiiiiiiiiiiiiiii : sw $t !i $s'
        addr = self.R[ifield.s] + sign_extend(ifield.i, 16)
        self.invalid_when(addr % 4 != 0, 'sw: R[$rs]+immed must be a multiple of 4')
        self.invalid_when(addr >= self.ift_data_address and addr <= self.ift_stack_address, \
            'Address (%s) encroaching on memory reserved for IFT'%hex(addr))
        val = self.R[ifield.t] - (1<<31) if self.R[ifield.t] & (1<<31) and \
              self.R[ifield.t] > 0 else \
              self.R[ifield.t]
        self.mem_write_32bit(addr, value=val)
        self.ift_store(addr, self.T[ifield.t])
        #Track accessed memory locations
        self.mem_locations += [addr] if addr not in self.mem_locations else []
    
    def instruction_xor(self, ifield):
        'Bitwise exclusive or : 000000 sssss ttttt ddddd ----- 100110 : xor $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] ^ self.R[ifield.t]
        self.T[ifield.d] = self.T[ifield.s] | self.T[ifield.t]

    def instruction_and(self, ifield):
        'Bitwise and : 000000 sssss ttttt ddddd ----- 100100 : and $d $s $t'
        self.R[ifield.d] = self.R[ifield.s] & self.R[ifield.t]
        self.T[ifield.d] = self.T[ifield.s] | self.T[ifield.t]
    
    def instruction_andi(self, ifield):
        'Bitwise and immediate : 001100 sssss ttttt iiiiiiiiiiiiiiii : andi $t $s !i'
        self.R[ifield.t] = self.R[ifield.s] & sign_extend(ifield.i, 16)
        self.T[ifield.t] = self.T[ifield.s]
    
    def instruction_trust(self, ifield):
        'Trust value in register: 101010 ttttt iiiiiiiiiiiiiiii ----- : trust $t !i'
        #This instruction sets the trust value for a register
        self.T[ifield.t] = sign_extend(ifield.i, 16)
