include "globals.mzn";

int: m; %couriers
set of int: COURIERS = 1..m;
array[COURIERS] of int: l; %courier capacities

int: n; %items
set of int: ITEMS = 1..n;
array[ITEMS] of int: s; %item sizes

set of int: D_SIZE = 1..n+1;
array[D_SIZE, D_SIZE] of int: D;

array[COURIERS, ITEMS] of var 0..max(s): A;
int: tot = 0;

%inutile
constraint 
    forall(i in D_SIZE) (
        D[i,i] == 0
    );
    
constraint sum(l) >= sum(s);

constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS)(A[i, j]) <= l[i] /\
        sum(j in ITEMS)(A[i, j]) > 0
    );

%!!! at most one    
constraint 
    forall(j in ITEMS) (
        sum(i in COURIERS)(A[i, j]) == s[j]
    );

solve satisfy;

output [
    "okkkk", show(A)
];