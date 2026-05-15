define i32 @main() {
entry:
  %i = alloca i32
  %limit = alloca i32
  %total = alloca i32
  store i32 3, i32* %limit
  store i32 0, i32* %i
  store i32 0, i32* %total
  br label %L9
L9:
  %v1 = load i32, i32* %i
  %v2 = load i32, i32* %limit
  %cmp1 = icmp slt i32 %v1, %v2
  br i1 %cmp1, label %L11, label %L18
L11:
  %v3 = load i32, i32* %total
  %v4 = load i32, i32* %i
  %t2 = add i32 0, 0
  store i32 %t2, i32* %total
  %v5 = load i32, i32* %i
  %t3 = add i32 %v5, 1
  store i32 %t3, i32* %i
  br label %L9
L18:
  %v6 = load i32, i32* %total
  ret i32 %v6
}
