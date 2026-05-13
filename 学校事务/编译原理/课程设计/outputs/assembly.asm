; MASM 16-bit DOS assembly
; Assemble with MASM/LINK:
; masm program.asm;
; link program.obj;
.MODEL SMALL
.STACK 100h
.DATA
.CODE

main PROC
    push bp
    mov bp, sp
    mov ax, @data
    mov ds, ax
    sub sp, 2
    mov ax, 3
    mov WORD PTR [bp-2], ax
    mov ax, 0
    mov ah, 4Ch
    int 21h
main ENDP

fn_add PROC
    push bp
    mov bp, sp
    sub sp, 8
    mov WORD PTR [bp-2], ax
    mov WORD PTR [bp-4], bx
    mov ax, WORD PTR [bp-2]
    add ax, WORD PTR [bp-4]
    mov WORD PTR [bp-6], ax
    mov ax, WORD PTR [bp-6]
    mov WORD PTR [bp-8], ax
    mov ax, WORD PTR [bp-8]
    mov sp, bp
    pop bp
    ret
fn_add ENDP

main PROC
    push bp
    mov bp, sp
    mov ax, @data
    mov ds, ax
    sub sp, 10
    mov ax, 0
    mov WORD PTR [bp-2], ax
    mov ax, 0
    mov WORD PTR [bp-4], ax
L9:
    mov ax, WORD PTR [bp-2]
    cmp ax, WORD PTR [bp-6]
    jl L11
    jmp L18
L11:
    mov ax, WORD PTR [bp-4]
    mov bx, WORD PTR [bp-2]
    call fn_add
    mov WORD PTR [bp-8], ax
    mov ax, WORD PTR [bp-8]
    mov WORD PTR [bp-4], ax
    mov ax, WORD PTR [bp-2]
    add ax, 1
    mov WORD PTR [bp-10], ax
    mov ax, WORD PTR [bp-10]
    mov WORD PTR [bp-2], ax
    jmp L9
L18:
    mov ax, WORD PTR [bp-4]
    mov ah, 4Ch
    int 21h
main ENDP

END main
