from isa import IsaDefinition

class MemoryConverter:
    def __init__(self, isa):
        self.isa = isa

    def __getitem__(self, address):
        # This is very probably wrong.
        return self.isa.mem_read(address, self.isa.isize)

    def __setitem__(self, address, data):
        # See above.
        self.isa.mem_write(address, int.to_bytes(data, 1, 'big', signed=True))

class M248(IsaDefinition):
    ''' The tiny riscy 2-operand M248 ISA
    - 2 operands
    - 4 instructions
    - 8 bits
    '''
    def __init__(self):
        super().__init__()
        self.make_register_file('R', 4, 8)
        self.make_register('PC', 8)
        self.isize = 1
        self.M = MemoryConverter(self)

    def assemble(self, file, text_start_address, data_start_address):
        ''' Covert a file to code and data bytes. '''
        program = [
            0b00000101, # NAND $zero $r1
            0b00100011, # STORE $r1 $zero => mem[rf[$zero]] = rf[$r1]
            0b00101001, # NAND $r1 $r2
        ]
        return bytes(program), b''

    def instruction_beqz(self, ifield):
        'beqz : iiiddd00 : beqz $d !i'
        self.PC = self.PC + 1 if self.R[ifield.d] == 0 else self.PC + ifield.i

    def instruction_nand(self, ifield):
        'nand : rrrddd01 : nand $r $d'
        if ifield.d != 0:
            self.R[ifield.d] = ~(self.R[ifield.r] & self.R[ifield.d])
        self.PC = self.PC + 1

    def instruction_load(self, ifield):
        'load : rrrddd10 : load $r $d'
        self.R[ifield.d] = self.M[self.R[ifield.r]]
        pass

    def instruction_store(self, ifield):
        'store : rrrddd11 : store $r $d'
        self.M[self.R[ifield.d]] = self.R[ifield.r]