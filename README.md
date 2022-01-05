MapacheSim
==========

MapacheSim is a maluable-architecture processor, assembler, and consoled hardware-emulation system.
It provides a SPIM-like simulator for a variety of architectures useful for both research and teaching.

### Install

The easiest way to get going with MapacheSim is to pull it from github at 
https://github.com/UCSBarchlab/MapacheSim.  In there you will find `mapachesim/mapache` which will 
start the console.

### Running MapacheSim

Run with no arguments (e.g. as simply `./mapache`) it will load the architecture simulator and 
console system to accept commands to load, run, step-through, a examine program behavior at the 
level of machine state.  The command "help" in the console will provide more information about 
actions that can be taken. 

In addition, if MapacheSim is run with an optional "asm" argument (e.g. `./mapache myprogram.asm`) 
it will instead load and then run specified assembly file non-interactively exiting on completion.  
When coupled with the "--quiet" option, it allows the assembly in a manner simmilar to compiled 
program.

### A Quick Example

Here is an example loading a MIPS assembly function, stepping through the first couple of 
instructions, and then continuing on until the end of execution.

```
[Laptop:git MapacheSim/mapachesim] [main*] sherwood% ./mapache 
Loading "Mips" processor model.
Welcome to MapacheSIM. Type help or ? to list commands.

(mapache) load ../asm/factorial-mips.asm
(mapache) step
0000010000: addiu $2 $0 4 
(mapache) 
0000010004: lui $4 4 
(mapache) 
0000010008: ori $4 $4 0 
(mapache) continue

Enter a number: 
Factorial is: 120 
0000010040: syscall (execution complete) (mapache)
```

At any point when execution is stopped you inspect the registers and look through memory (either 
at specific regions of memory or the default start of the "text" and "data" segments.  The full 
32-bit value of each register is shown in hex, and memory is shown in bytes (further segmented 
into 4-byte words for easier reading).

```
(mapache) regs

$0 = 0x00000000  $at= 0x00000000  $v0= 0x0000000a  $v1= 0x00000000
$a0= 0x00000078  $a1= 0x00000078  $a2= 0x00000000  $a3= 0x00000000
$t0= 0x00000000  $t1= 0x00000000  $t2= 0x00000000  $t3= 0x00000000
$t4= 0x00000000  $t5= 0x00000000  $t6= 0x00000000  $t7= 0x00000000
$s0= 0x00000000  $s1= 0x00000000  $s2= 0x00000000  $s3= 0x00000000
$s4= 0x00000000  $s5= 0x00000000  $s6= 0x00000000  $s7= 0x00000000
$t8= 0x00000000  $t9= 0x00000000  $k0= 0x00000000  $k1= 0x00000000
$gp= 0x10008000  $sp= 0x7ffff000  $fp= 0x00000000  $ra= 0x0001001c
PC = 0x00010044  HI = 0x00000000  LO = 0x00000078

(mapache) mem text

0x00010000:  24 02 00 04  3c 04 00 04  34 84 00 00  00 00 00 0c
0x00010010:  24 02 00 05  00 40 20 20  0c 00 40 11  00 40 28 20
0x00010020:  24 02 00 04  3c 04 00 04  34 84 00 12  00 00 00 0c
0x00010030:  00 a0 20 20  24 02 00 01  00 00 00 0c  24 02 00 0a
0x00010040:  00 00 00 0c  23 bd ff fc  af bf 00 00  24 02 00 01
0x00010050:  10 80 40 19  00 44 00 18  00 00 10 12  20 84 ff ff
0x00010060:  08 00 40 14  8b bf 00 00  23 bd 00 04  03 e0 00 08
0x00010070:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00010080:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00010090:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100a0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100b0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100c0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100d0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100e0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000100f0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00

(mapache) mem data

0x00040000:  0a 45 6e 74  65 72 20 61  20 6e 75 6d  62 65 72 3a
0x00040010:  20 00 0a 46  61 63 74 6f  72 69 61 6c  20 69 73 3a
0x00040020:  20 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040030:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040040:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040050:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040060:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040070:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040080:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x00040090:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400a0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400b0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400c0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400d0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400e0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
0x000400f0:  00 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00

(mapache) 
```

For example, in the above data memory dump, the byte at address `0x40000` has the value `0x0a`, 
the byte at address `0x40001` has the value `0x45`, the byte at address `0x4000F` has the value 
`0x3a`, `0x40014` has the value `0x61` etc.  

Looking further up we can see that the PC is 0x00010044, which means that it is pointing to the 
instruction with value `0x23bdfffc`.
