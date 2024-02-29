: mod3? dup 3 mod 0 = if + else drop then ;
: mod5? dup 5 mod 0 = if + else drop then ;
: mod3or5?  dup dup 3 mod 0 = swap 5 mod 0 = + if + else drop then ;
: problem1  1000 0 do i mod3or5? loop ;
