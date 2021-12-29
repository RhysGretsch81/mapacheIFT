# Simple loop in MIPS assembly

   .text
main:
        addi $t0, $t0, 4

loop:   addi $t1, $t1, 4
        j loop  # simply increment $t1 in a loop
