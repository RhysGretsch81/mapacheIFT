.data

matrix1: .word 10, 15, 11, 17
matrix2: .word 15, 6, 17, 7
outMatrix: .word 0, 0, 0, 0

dim1: .word 2
dim2: .word 2

.text
main:
    la $t0, matrix1
    la $t1, matrix2
    la $t2, dim1
    lw $t2, 0, $t2
    la $t3, dim2
    lw $t3, 0, $t3
    la $a0, outMatrix

    jal rowLoop
    li $v0, 10
    syscall

rowLoop:
    addi $sp, $sp, -4    
    sw $ra, 0($sp)
    li $t4, 0
rowBody:
    jal columnLoop
    addi $t4, $t4, 1
    beq $t4, $t2, return
    j rowBody

columnLoop:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    li $t5, 0
columnBody:
    jal innerLoop
    addi $t5, $t5, 1
    beq $t5, $t3, return
    j columnBody

innerLoop:
    addi $sp, $sp, -4
    sw $ra, 0($sp)
    li $t6, 0
    #Find row index (offset from t4)
    #4*columnsize*index
    li $s0, 4
    mult $s0, $t3
    mflo $s0
    mult $s0, $t4
    mflo $s0
    #Find column index
    #4*index
    li $s1, 4
    mult $s1, $t5
    mflo $s1
    #Now, s0->start for m1, s1->start for m2
    #Init acc to be 0
    li $s7, 0
innerBody:
    add $s2, $t0, $s0
    lw $s3, 0($s2)
    trust $s3, -1
    sw $s3, 0($s2)
    add $s2, $t1, $s1
    lw $s4, 0($s2)
    mult $s3, $s4
    mflo $s5
    add $s7, $s7, $s5

    addi $t6, $t6, 1
    beq $t6, $t3, store
    #s0 will increase by 4, s1 by 4*dim2
    addi $s0, $s0, 4
    li $s6, 4
    mult $s6, $t3
    mflo $s6
    add $s1, $s1, $s6
    j innerBody


store:
    li $a1, 4
    mult $t4, $t3
    mflo $a2
    add $a2, $a2, $t5
    mult $a2, $a1
    mflo $a1
    add $a1, $a1, $a0
    sw $s7, 0($a1)

return:
    lw $ra, 0($sp)
    addi $sp, $sp, 4
    jr $ra
