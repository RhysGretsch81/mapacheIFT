'''The UCSB Mapache Interactive Architecture Simulator'''

import cmd
import mips
import toy
import m248

def chunk_list(lst, n):
    '''Chunk a list into a list of lists of length n.'''
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


class MapacheShell(cmd.Cmd):
    '''The Mapache Interactive Shell. 

       The shell handles all manner of error catching and presentation
       for the machine simulator and assembler in as an ISA independent
       manner as possible.'''

    intro = 'Welcome to MapacheSIM. Type help or ? to list commands.\n'
    prompt = '(mapache) '

    def __init__(self):
        super().__init__()
        #self.machine = m248.M248()
        self.machine = mips.Mips()
        #self.machine = toy.Toy()
        self.text_start_address = 0x10000
        self.data_start_address = 0x40000
        # map 2MB memory for emulation
        self.machine.mem_map(self.text_start_address, 2 * 1024 * 1024)

    def print_registers(self):
        '''Helper function for printing register state.'''

        def rformat(rval):
            return f'{rval:#010x}'
            #return '0' if rval==0 else f'{rval:#010x}'

        def pprint_regs(reg_values):
            # TODO: check bits is not 32 and handle that case as well
            reg_formatted = [f'{name:<3}= {rformat(rval):>10}' for name,bits,rval in reg_values]
            for reg_line in chunk_list(reg_formatted, 4):
                print('  '.join(reg_line))

        pprint_regs(self.machine.registers())

    def print_memory(self, start_addr=None, size=256, width=16, sep='  '):
        '''Helper function for printing memory state.'''

        def mformat(rval):
            return f'{rval:02x}'

        start_addr = start_addr if start_addr else self.data_start_address
        memory = self.machine.mem_read(start_addr, size)
        mem_formated = [mformat(b) for b in memory]
        for offset in range(0, size, width):
            addr = start_addr + offset
            row = mem_formated[offset:offset+width]
            mem_words = [' '.join(chunk) for chunk in chunk_list(row, 4)]
            mem_row = sep.join(mem_words)
            print(f'{addr:#010x}:{sep}{mem_row}')

    def load_instr(self, code):
        '''Load a bytearray of code into instruction memory, and start up simulator.'''
        self.machine.mem_write(self.text_start_address, code) # write code to emulated memory
        self.machine.PC = self.text_start_address # set pc using the setter

    def do_mtest(self, arg):
        # non-public command to run a working test
        testcode = b''.join([b'\x21\x08\x00\x04',  # addi $t0, $t0, 4
                             b'\x21\x29\x00\x04',  # addi $t1, $t1, 4 <- loop
                             b'\x08\x00\x40\x01',  # j loop
                             b'\x00\x00\x00\x00',  # nop
                             b'\x21\x4a\x00\x04']) # addi $t2, $t2, 4
                        
        print()
        print('        addi $t0, $t0, 4  # 21 08 00 04')
        print('  loop: addi $t1, $t1, 4  # 21 29 00 04')
        print('        j loop            # 08 00 40 01')
        print('        nop               # 00 00 00 00')
        print('        addi $t2, $t2, 4  # 21 4a 00 04')
        print()
        
        self.load_instr(testcode)
        print()
        self.print_registers()
        print()
        self.print_memory(self.text_start_address)
        print()

    def do_settext(self, arg):
        'Set the text segment start address: settext 0x10000'
        self.text_start_address = int(arg,16)

    def do_setdata(self, arg):
        'Set the data segment start address: settext 0x40000'
        self.data_start_address = int(arg,16)

    def do_load(self, arg):
        'Load an assembly file into the simulator: load filename.asm'
        filename = arg
        try:
            code, data = self.machine.assemble(filename, self.text_start_address, self.data_start_address)
            self.machine.mem_write(self.data_start_address, data) # write data segment to emulated memory 
            self.load_instr(code)
        except FileNotFoundError as e:
            print(f'\nError: Cannot find file "{filename}" to load. [{e}]\n')


    def do_step(self, arg):
        instruction_string = self.machine.step()
        print(instruction_string)

    def do_regs(self, arg):
        'Print the relavent registers of the processor: regs'
        print()
        self.print_registers()
        print()

    def do_mem(self, arg):
        'Print the specified regions of memory: mem [addr_in_hex]'
        print()
        try:
            if arg:
                addr = int(arg,16)
            else:
                addr = None
            self.print_memory(addr)
            print()
        except ValueError as e:
            print(f'Error: Unable to convert hex address. [{e}]\n')

    def do_exit(self, arg):
        'Exit MapacheSIM: exit'
        print('\nThank you for using MapacheSIM :)\n') 
        exit()

    do_EOF = do_exit
    do_quit = do_exit

# ==========================================================================

if __name__ == '__main__':
    MapacheShell().cmdloop()

