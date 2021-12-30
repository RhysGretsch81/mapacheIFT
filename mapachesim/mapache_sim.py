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
        self.initialize()

    def initialize(self):
        #self.machine = m248.M248()
        self.machine = mips.Mips()
        #self.machine = toy.Toy()
        print(f'Loading "{type(self.machine).__name__}" processor model.')
        self.text_start_address = self.machine.text_start_address
        self.data_start_address = self.machine.data_start_address
        self.breakpoints = {}
        # map 2MB memory for emulation
        self.machine.mem_map(self.text_start_address, 2 * 1024 * 1024)

    def parse_arg_as_address(self, arg, default=None):
        '''Take an argument and attempt convert it address (as a number or label).'''
        # TODO: add label conversion here
        try:
            if arg:
                addr = int(arg,16)
            else:
                addr = default
        except ValueError as e:
            self.error_msg(f'Error: Unable to parse hex address "{arg}"')
        return addr

    def parse_arg_as_integer(self, arg, default=None):
        '''Take an argument and attempt convert it to an integer (base 10).'''
        try:
            if arg:
                intval = int(arg,10)
            else:
                intval = default
        except ValueError as e:
            self.error_msg(f'Error: Unable to parse as base 10 number "{arg}"')
        return intval

    def print_current_instruction(self, pc, istring, note=None):
        '''Print the current instruction.'''
        note_string = f'({note})' if note else ''
        print(f'{pc:010x}: {istring} {note_string}')

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

    def load_text(self, code):
        '''Load a bytearray of code into instruction memory, and start up simulator.'''
        self.machine.mem_write(self.text_start_address, code) # write code to emulated memory
        self.machine.PC = self.text_start_address # set pc using the setter

    def load_data(self, data):
        '''Load a bytearray in to the data segment and set up the rest of memory.'''
        self.machine.mem_write(self.data_start_address, data) # write data segment to emulated memory 

    def error_msg(self, msg):
        '''Print a non-fatal error message to the user.'''
        print(f'\n{msg}\n')

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
        
        self.load_text(testcode)
        print()
        self.print_registers()
        print()
        self.print_memory(self.text_start_address)
        print()

    def do_settext(self, arg):
        'Set the text segment start address: e.g. "settext 0x10000"'
        self.text_start_address = int(arg,16)

    def do_setdata(self, arg):
        'Set the data segment start address: e.g. "setdata 0x40000"'
        self.data_start_address = int(arg,16)

    def do_load(self, arg):
        'Load an assembly file into the simulator: e.g. "load filename.asm"'
        filename = arg
        try:
            tstart, dstart = self.text_start_address, self.data_start_address
            with open(filename,'r') as file:
                program = file.read()
            code, data = self.machine.assembler.assemble(program, tstart, dstart)
            self.load_data(data)
            self.load_text(code)
        except FileNotFoundError as e:
            self.error_msg(f'Error: Cannot find file "{filename}" to load. [{e}]')


    def do_step(self, arg):
        'Step the program execution forwar N instructions: e.g. "step 3", "step"'
        n_steps = self.parse_arg_as_integer(arg, default=1)
        for i in range(n_steps):
            pc, instruction_string = self.machine.step()
            self.print_current_instruction(pc, instruction_string)

    def do_regs(self, arg):
        'Print the relavent registers of the processor: e.g. "regs"'
        print()
        self.print_registers()
        print()

    def do_mem(self, arg):
        'Print the specified regions of memory: e.g. "mem 0x40000", "mem text"'
        if arg == 'text':
            addr = self.text_start_address
        elif arg == 'data':
            addr = self.data_start_address
        else:
            addr = self.parse_arg_as_address(arg, default=self.data_start_address)
        if addr:
            print()
            self.print_memory(addr)
            print()

    def do_run(self, arg):
        'Run the loaded program. e.g. "run"'
        self.machine.PC = self.text_start_address
        pc, instruction_string = self.machine.step()
        while self.machine.PC not in self.breakpoints:
            pc, instruction_string = self.machine.step()
        self.print_current_instruction(pc, instruction_string, 'breakpoint')

    def do_continue(self, arg):
        'Continue running program after break. e.g. "continue"'
        pc, instruction_string = self.machine.step()
        while self.machine.PC not in self.breakpoints:
            pc, instruction_string = self.machine.step()
        self.print_current_instruction(pc, instruction_string, 'breakpoint')

    def do_reinitialize(self, arg):
        'Clear the memory and registers and reload machine model. e.g. "reinitialize"'
        self.initialize()

    def do_breakpoint(self, arg):
        'Set a breakpoint at address or label. e.g. "breakpoint 0x1000C", "breakpoint foobar"'
        addr = self.parse_arg_as_address(arg)
        if addr:
            if addr % self.machine.isize != 0:
                self.error_msg(f'Cannot add unaligned breakpoint to address "{addr}".')
            else:
                self.breakpoints[addr] = arg
                print(f'Added breakpoint at {addr} (named "{arg}").')

    def do_delete(self, arg):
        'Delete breakpoint at specificed address or label.'
        addr = self.parse_arg_as_address(arg)
        if addr:
            if addr in self.breakpoints:
                del self.breakpoint[addr]
                print(f'Removed breakpoint from address "{addr}".')
            else:
                self.error_msg(f'No breakpoint set at "{addr}".')

    def do_list(self, arg):
        'List all breakpoints. e.g. "list"'
        print('Currently tracking {len(self.breakpoints)} breakpoints.')
        for addr in self.breakpoints:
            print('  {addr:010x}: {self.breakpoints[addr]}')

    def do_exit(self, arg):
        'Exit MapacheSIM: exit'
        print('\nThank you for using MapacheSIM :)\n') 
        exit()

    do_EOF = do_exit
    do_quit = do_exit

# ==========================================================================

if __name__ == '__main__':
    MapacheShell().cmdloop()

