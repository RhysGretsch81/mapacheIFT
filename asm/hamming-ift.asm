.data

trusted: .word 0b010
untrusted: .word 15
out: .word 0


.text
main:
    #Current wonky work around for bug in lw
    la $t0, trusted
    lw $t0, 0($t0)
    #Using trust -1 indicates all bits are untrusted
    trust $t0, -1

    #Print first value
    move $a0, $t0
    li $v0, 1
    syscall

    la $t1, untrusted
    lw $t1, 0($t1)

    #Print 2nd value
    move $a0, $t1
    li $v0, 1
    syscall

    jal calc_hamming

    move $a0, $t2
    li $v0, 1
    syscall

    #Store value
    la $t0, out
    sw $t2, 0($t0)

    # Exit
    li $v0, 10
    syscall


calc_hamming:
    #assume 32 bit vectors
    li $t2, 0
    xor $t0, $t0, $t1
    li $t3, 32

loop:
    andi $t1, $t0, 1
    add $t2, $t1, $t2

    addi $t3, $t3, -1
    beq $t3, $0, return
    srl $t0, $t0, 1
    j loop


return:
    jr $ra
