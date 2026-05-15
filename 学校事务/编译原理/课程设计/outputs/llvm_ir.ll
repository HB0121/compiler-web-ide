@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
declare i32 @printf(i8*, ...)

define i32 @main() {
entry:
  %a = alloca i32
  %b = alloca i32
  store i32 4, i32* %a
  %v1 = load i32, i32* %a
  %t2 = add i32 0, 0
  store i32 %t2, i32* %b
  %v2 = load i32, i32* %b
  %cmp1 = icmp sgt i32 %v2, 10
  br i1 %cmp1, label %L11, label %L14
L11:
  %v3 = load i32, i32* %b
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), i32 %v3)
  %t3 = add i32 0, 0
  br label %L16
L14:
  call i32 (i8*, ...) @printf(i8* getelementptr inbounds ([4 x i8], [4 x i8]* @.fmt_int, i32 0, i32 0), i32 0)
  %t4 = add i32 0, 0
  br label %L16
L16:
  ret i32 0
}
