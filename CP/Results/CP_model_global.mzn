include "globals.mzn";
include "lex_lesseq.mzn";

%-----------------------------------------------------------------------------%
% Parameters
%-----------------------------------------------------------------------------%

int: m; % couriers
set of int: COURIERS = 1..m;
array[COURIERS] of int: l; % couriers capacities

int: n; % items
set of int: ITEMS = 1..n;
array[ITEMS] of int: s; % items sizes

set of int: D_SIZE = 1..n+1;
array[D_SIZE, D_SIZE] of int: D; % distances

%-----------------------------------------------------------------------------%
% Variables
%-----------------------------------------------------------------------------%

% assignment of items to each courier
array[COURIERS, ITEMS] of var 0..max(s): A;
% order of items for each courier
array[COURIERS, ITEMS] of var 0..n: O;
% distance travelled by each courier
array[COURIERS] of var 1..sum(D): dist;

%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

constraint sum(l) >= sum(s); % total items size less than total couriers capacity

constraint
    forall(i in COURIERS) (
        let {
            array[ITEMS] of var int: assignment = [A[i, j] | j in ITEMS]
        } in
        cumulative([1 | j in ITEMS], assignment, s, l[i]) /\ sum(assignment) > 0
    ); % each courier transports at least one item and respects its own load capacity
constraint 
    forall(j in ITEMS) (
        let {
            array[COURIERS] of var int: assignment = [A[i, j] | i in COURIERS]
        } in
        distribute([1, m-1], [s[j], 0], assignment) 
    ); % each item is carried by exactly one courier
    
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%
constraint
    forall(i,j in COURIERS where i < j /\ 
    l[i]-sum(k in ITEMS)(A[i,k]) > 0 /\ l[j]-sum(k in ITEMS)(A[j,k]) > 0) (
        lex_lesseq([A[i,k] | k in ITEMS], [A[j,k] | k in ITEMS])
    ); % row value symmetry breaking with available capacity condition
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%

% constraints to create O
constraint
    forall(i in COURIERS) (
        forall(j in ITEMS) (
            if A[i, j] == 0 then O[i, j] = 0 else O[i, j] > 0 endif
        ) % each value is in line with those in A
    );
constraint
    forall(i in COURIERS) (
        let {
            array[ITEMS] of var int: order_items = [O[i, j] | j in ITEMS];
            var int: c = count(e in order_items) (e > 0)
        } in
        alldifferent_except_0(order_items) /\ 
        forall(e in 1..c) (count(order_items, e) == 1)
    );

% constraint to create dist
constraint
    forall(i in COURIERS) (
        let {
            array[ITEMS] of var int: order_items = [O[i, j] | j in ITEMS];
            var int: c = count(e in order_items) (e > 0)
        } in 
        dist[i] == sum(j1 in ITEMS, j2 in ITEMS where order_items[j1] != 0 /\ 
                      (order_items[j2] - order_items[j1]) == 1) (D[j1, j2])
                 + sum(j0 in ITEMS where order_items[j0] == 1) (D[n+1, j0])
                 + sum(jn in ITEMS where order_items[jn] == c) (D[jn, n+1])
    );

%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

var int: obj = max(i in COURIERS) (dist[i]);
var int: obj__ = sum(i in COURIERS) (dist[i]);
var float: objective = obj + (0.1*obj__);

%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%

solve :: int_search(O, dom_w_deg, indomain_min, complete) 
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
      :: restart_luby(100)
      :: relax_and_reconstruct(array1d(A), 85)
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
         minimize obj;
%          minimize objective;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

output  [show(obj) ++ "\n"]
     ++ ["[| " ++ join (" | ", [show(dist[i]) | i in COURIERS]) ++ " |]" ++ "\n\n"]
%      ++ ["[| " ++ join (" | ", [show(A[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
%      ++ ["[| " ++ join (" | ", [show(O[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
        ;