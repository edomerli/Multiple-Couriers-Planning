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
array[COURIERS, ITEMS] of var 0..1: A;
% order of items for each courier
array[COURIERS, ITEMS] of var 0..n: O;


%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS where A[i,j] == 1)(s[j]) <= l[i] %/\
        /\ count(z in A[i,..])(z==1) > 0 % each courier transports at least one item, implied constraint
    );

constraint
    forall(j in ITEMS) (
        count(z in A[..,j])(z==1) == 1 % each item is transported by exactly one courier
    );
    
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%
% constraint
%     forall(i,j in COURIERS where i < j)(
%         (sum(k in ITEMS where A[i,k] == 1)(s[k]) <= l[j] /\ sum(k in ITEMS where A[j,k] == 1)(s[k]) <= l[i])
%         -> lex_lesseq(A[i,..], A[j,..])
%     );
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%

% constraints to create O
constraint
    forall(i in COURIERS) (
        forall(j in ITEMS) (
            (A[i, j] == 0 <-> O[i, j] == 0) /\
            (A[i, j] == 1 <-> O[i, j] > 0) % each value is in line with those in A
        )
    );

constraint 
    forall(i in COURIERS) ( 
        let {var int: c = count(e in A[i,..]) (e == 1);} in
        forall(e in 1..c) (
            count(O[i,..], e) == 1
        )
    );


%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

int: obj_lowerbound = max(i in ITEMS)(D[n+1,i] + D[i,n+1]);

array[D_SIZE] of int: max_dists = sort([max(j in D_SIZE)(D[i,j]) | i in D_SIZE]);
int: obj_upperbound = sum(i in m..n+1)(max_dists[i]);

var obj_lowerbound..obj_upperbound: obj = max(i in COURIERS)(sum(j1 in ITEMS, j2 in ITEMS where 
        (A[i, j1] = 1 /\ A[i, j2] = 1 /\ O[i, j2] - O[i, j1] == 1)) (D[j1,j2])
        + sum(j0 in ITEMS where O[i, j0] == 1) (D[n+1, j0])
        + sum(j0 in ITEMS where O[i, j0] == count(e in A[i,..])(e==1)) (D[j0, n+1]));


%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%
solve :: int_search(O, dom_w_deg, indomain_min) 
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
      :: restart_luby(100)
      :: relax_and_reconstruct(array1d(A), 85)
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
         minimize obj;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

output  [show(obj) ++ "\n"] %++
%         [show(O[i,j]) ++ if j == n then "\n" else " " endif | i in COURIERS, j in ITEMS]