# buggy code example 1

.text
main:
        addi $t0, $t0, 1000000000

loop:   addi $t1, $t1, 4
        j loop  # simply increment $t1 in a loop
