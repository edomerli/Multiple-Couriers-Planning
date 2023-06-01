include "globals.mzn";

%% VARIABLES AND DOMAINS

int: m; % couriers
set of int: COURIERS = 1..m;
array[COURIERS] of int: l; % couriers capacities

int: n; % items
set of int: ITEMS = 1..n;
array[ITEMS] of int: s; % items sizes

set of int: D_SIZE = 1..n+1;
array[D_SIZE, D_SIZE] of int: D; % distances

% assignment of items to each courier
array[COURIERS, ITEMS] of var 0..max(s): A;
% order of items for each courier
array[COURIERS, ITEMS] of var 0..n: O;
% distance travelled by each courier
array[COURIERS] of var 1..sum(D): dist;


%% CONSTRAINTS

constraint sum(l) >= sum(s); % total items size less than total couriers capacity

% constraints to create A
constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS)(A[i, j]) <= l[i] /\ % each courier respects its own load capacity
        sum(j in ITEMS)(A[i, j]) > 0 % each courier transports at least one item
    );
constraint 
    forall(j in ITEMS) (
        max(i in COURIERS)(A[i, j]) == s[j] /\
        sum(i in COURIERS)(A[i, j]) == s[j] % each item is carried by at most one courier
    );

% constraints to create O
constraint
    forall(i in COURIERS) (
        forall(j in ITEMS) (
            (A[i, j] == 0 -> O[i, j] == 0) /\
            (A[i, j] > 0 -> O[i, j] > 0) % each value is in line with those in A
        )
    );
constraint 
    forall(i in COURIERS) ( 
        let {array[ITEMS] of var int: row = [O[i, j] | j in ITEMS];} in
        let {var int: c = count(e in row) (e > 0);} in
        forall(e in 1..c) (
            count([row[j] | j in ITEMS], e) == 1
        )
    );

% constraint to create dist
constraint
    forall(i in COURIERS) (
        let {array[ITEMS] of var int: row = [O[i, j] | j in ITEMS];} in
        let {var int: c = count(e in row) (e > 0);} in
        dist[i] == sum(j1 in ITEMS, j2 in ITEMS where (A[i, j1] != 0 /\ A[i, j2] != 0))
                   (D[j1, j2] * ((O[i, j2] - O[i, j1]) == 1))
        + sum(j0 in ITEMS where A[i, j0] != 0) (D[n+1, j0] * (O[i, j0] == 1))
        + sum(j0 in ITEMS where A[i, j0] != 0) (D[j0, n+1] * (O[i, j0] == c))
    );


%% OBJECTIVE

var int: obj = max(i in COURIERS)(dist[i]); 
solve minimize obj;

% var int: obj_m = max(i in COURIERS)(dist[i]);
% var int: obj_s = sum(i in COURIERS)(dist[i]); 
% solve minimize (2*m * obj_m) + obj_s;


%% OUTPUT

output  ["[| " ++ join (" | ", [show(dist[i]) | i in COURIERS]) ++ " |]" ++ "\n\n"] ++
        ["[| " ++ join (" | ", [show(A[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"] ++
        ["[| " ++ join (" | ", [show(O[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS]
        ;