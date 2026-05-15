assume cs:code,ds:data,ss:stack,es:extended
extended segment
  db 1024 dup (0)
extended ends
stack segment
  db 1024 dup (0)
stack ends
dispmsg macro message
  lea dx, message
  mov ah, 9
  int 21h
endm
data segment
  _buff_p db 256 dup (24h)
  _buff_s db 256 dup (0)
  _msg_p db 0ah,'Output:',0
  _msg_s db 0ah,'Input:',0
  next_row db 0dh,0ah,'$'
  error db 'input error, please re-enter: ','$'
data ends
code segment
start:
    mov ax,extended
    mov es,ax
    mov ax,stack
    mov ss,ax
    mov sp,1024
    mov bp,sp
    mov ax,data
    mov ds,ax

square:
    PUSH BP
    MOV BP,SP
    SUB SP,2
    MOV AX,ss:[bp+4]
    MOV BX,ss:[bp+4]
    MUL BX
    MOV ss:[bp-2],AX
    MOV AX,ss:[bp-2]
    MOV SP,BP
    POP BP
    RET

main:
    PUSH BP
    MOV BP,SP
    SUB SP,10
    MOV AX,4
    MOV ss:[bp-2],AX
    MOV AX,ss:[bp-2]
    PUSH AX
    CALL square
    MOV ss:[bp-4],AX
    MOV AX,ss:[bp-4]
    MOV ss:[bp-6],AX
    MOV AX,ss:[bp-6]
    CMP AX,10
    JG _11
    JMP far ptr _14
_11:
    MOV AX,ss:[bp-6]
    PUSH AX
    CALL write
    MOV ss:[bp-8],AX
    JMP far ptr _16
_14:
    MOV AX,0
    PUSH AX
    CALL write
    MOV ss:[bp-10],AX
_16:
    MOV AX,0
    mov ah,4ch
    int 21h


read proc near
    push bp
    mov bp, sp
    mov bx,offset _msg_s
    call _print
    push bx
    push cx
    push dx
proc_pre_start:
    xor ax, ax
    xor bx, bx
    xor cx, cx
    xor dx, dx
proc_judge_sign:
    mov ah, 1
    int 21h
    cmp al, '-'
    jne proc_next
    mov dx, 0ffffh
    jmp proc_digit_in
proc_next:
    cmp al, 30h
    jb proc_unexpected
    cmp al, 39h
    ja proc_unexpected
    sub al, 30h
    shl bx, 1
    mov cx, bx
    shl bx, 1
    shl bx, 1
    add bx, cx
    add bl, al
    adc bh, 0
proc_digit_in:
    mov ah, 1
    int 21h
    jmp proc_next
proc_save:
    cmp dx, 0ffffh
    jne proc_result_save
    neg bx
proc_result_save:
    mov ax, bx
    jmp proc_input_done
proc_unexpected:
    cmp al, 0dh
    je proc_save
    dispmsg next_row
    dispmsg error
    jmp proc_pre_start
proc_input_done:
    pop dx
    pop cx
    pop bx
    pop bp
    ret
read endp

write proc near
    push bp
    mov bp, sp
    push ax
    push bx
    push cx
    push dx
    mov bx,offset _msg_p
    call _print
    xor cx, cx
    mov bx, [bp+4]
    test bx, 8000h
    jz proc_nonneg
    neg bx
    mov dl,'-'
    mov ah, 2
    int 21h
proc_nonneg:
    mov ax, bx
    cwd
    mov bx, 10
proc_div_again:
    xor dx, dx
    div bx
    add dl, 30h
    push dx
    inc cx
    cmp ax, 0
    jne proc_div_again
proc_digit_out:
    pop dx
    mov ah, 2
    int 21h
    loop proc_digit_out
proc_output_done:
    pop dx
    pop cx
    pop bx
    pop ax
    pop bp
    ret 2
write endp

_print:
    mov si,0
    mov di,offset _buff_p
_p_lp_1:
    mov al,ds:[bx+si]
    cmp al,0
    je _p_brk_1
    mov ds:[di],al
    inc si
    inc di
    jmp short _p_lp_1
_p_brk_1:
    mov dx,offset _buff_p
    mov ah,09h
    int 21h
    mov cx,si
    mov di,offset _buff_p
_p_lp_2:
    mov al,24h
    mov ds:[di],al
    inc di
    loop _p_lp_2
    ret
code ends
end start
