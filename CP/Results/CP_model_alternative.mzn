include "globals.mzn";
include "lex_lesseq.mzn";

%-----------------------------------------------------------------------------%
% Parameters
%-----------------------------------------------------------------------------%

int: m; % couriers
set of int: COURIERS = 1..m;
array[COURIERS] of int: l;

int: n; % items
set of int: ITEMS = 1..n;
array[ITEMS] of int: s; % items sizes

set of int: D_SIZE = 1..n+1;
array[D_SIZE, D_SIZE] of int: D; % distances

%-----------------------------------------------------------------------------%
% Variables
%-----------------------------------------------------------------------------%

% assignment of items to each courier
array[ITEMS] of var COURIERS: A;
% order of items for each courier
array[COURIERS, ITEMS] of var 0..n: O;


%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

% constraint sum(l) >= sum(s); % total items size less than total couriers capacity

constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS where A[j] == i)(s[j]) <= l[i] %/\
        /\ count(z in A)(z==i) > 0 % each courier transports at least one item, implied constraint
    );

% constraint
%     forall(j in ITEMS) (
%         count(z in A)(z==1) == 1 % each item is transported by exactly one courier
%     );
    
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%
constraint
    forall(i,j in COURIERS where i < j)(
        (sum(k in ITEMS where A[k] == i)(s[k]) <= l[j] /\ sum(k in ITEMS where A[k] == j)(s[k]) <= l[i])
        -> lex_lesseq([(A[k] == i) | k in ITEMS], [(A[k] == j) | k in ITEMS])
    );
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%

% constraints to create O
constraint
    forall(i in COURIERS) (
        forall(j in ITEMS) (
            (A[j] != i <-> O[i, j] == 0) /\
            (A[j] == i <-> O[i, j] > 0) % each value is in line with those in A
        )
    );

constraint 
    forall(i in COURIERS) (
        let {var int: c = count(e in A) (e == i);} in
        forall(e in 1..c) (
            count([O[i,j] | j in ITEMS], e) == 1
        )
    );
    
%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

int: obj_lowerbound = max(i in ITEMS)(D[n+1,i] + D[i,n+1]);

array[D_SIZE] of int: max_dists = sort([max(j in D_SIZE)(D[i,j]) | i in D_SIZE]);
int: obj_upperbound = sum(i in m..n+1)(max_dists[i]);

var obj_lowerbound..obj_upperbound: obj = max(i in COURIERS)(sum(j1 in ITEMS, j2 in ITEMS where 
        (A[j1] = i /\ A[j2] = i /\ O[i, j2] - O[i, j1] == 1)) (D[j1,j2])
        + sum(j0 in ITEMS where O[i, j0] == 1) (D[n+1, j0])
        + sum(j0 in ITEMS where O[i, j0] == count(e in A)(e==i)) (D[j0, n+1]));


%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%
solve :: int_search(O, dom_w_deg, indomain_min) 
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
      :: restart_luby(100)
      :: relax_and_reconstruct(A, 85)
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
         minimize obj;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

output  [show(obj) ++ "\n"];
        