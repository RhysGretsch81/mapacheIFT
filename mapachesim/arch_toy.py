'''A toy microprocessor definition. '''

from isa import IsaDefinition
from helpers import sign_extend, bit_select

class Toy(IsaDefinition):
    ''' Toy Instruction Set Definition. '''
    def __init__(self):
        super().__init__()
        self.make_register_file('R', 4, 8)
        self.make_register('PC', 8)
        self.isize = 1

    def assemble(self, file, text_start_address, data_start_address):
        '''Covert a file to code and data bytes.'''
        program = [0b00010101, 0b11000000]
        return bytes(program), b''

    def instruction_add(self, ifield):
        'add :      00aabbdd : add $d $a $b'
        self.R[ifield.d] = self.R[ifield.a] + self.R[ifield.b] 
        self.PC = self.PC + 1

    def instruction_sub(self, ifield):
        'subtract : 01aabbdd : sub $d $a $b'
        self.R[ifield.d] = self.R[ifield.a] - self.R[ifield.b] 
        self.PC = self.PC + 1

    def instruction_ld(self, ifield):
        'load :     10aaxxdd : ld $d $a'
        self.R[ifield.d] = 1 # STUB
        self.PC = self.PC + 1

    def instruction_j(self, ifield):
        'jump :     11aaaaaa : j @a'
        self.PC = ifield.a
