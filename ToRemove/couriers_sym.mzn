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

% constraints to create A
constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS) (A[i, j]) <= l[i] /\ % each courier respects its own load capacity
        sum(j in ITEMS) (A[i, j]) > 0 % each courier transports at least one item
    );
constraint 
    forall(j in ITEMS) (
        max(i in COURIERS) (A[i, j]) == s[j] /\
        sum(i in COURIERS) (A[i, j]) == s[j] % each item is carried by at most one courier
    );
constraint
    forall(i,j in COURIERS where 
    i < j /\ l[i]-sum(k in ITEMS)(A[i,k]) > 0 /\ l[j]-sum(k in ITEMS)(A[j,k]) > 0) (
        lex_lesseq([A[i,k] | k in ITEMS], [A[j,k] | k in ITEMS])
    ); % row value symmetry breaking with available capacity condition

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
        let {
            array[ITEMS] of var int: order = [O[i, j] | j in ITEMS];
            var int: c = count(e in order) (e > 0);
        } in 
        alldifferent_except_0(order) /\ 
        forall(e in 1..c) (count(order, e) == 1)
    );

% constraint to create dist
constraint
    forall(i in COURIERS) (
        let {
            array[ITEMS] of var int: order = [O[i, j] | j in ITEMS];
            var int: c = count(e in order) (e > 0);
        } in 
        dist[i] == sum(j1 in ITEMS, j2 in ITEMS where 
                   order[j1] != 0 /\ (order[j2] - order[j1]) == 1) (D[j1, j2])
                 + sum(j0 in ITEMS where order[j0] == 1) (D[n+1, j0])
                 + sum(jn in ITEMS where order[jn] == c) (D[jn, n+1])
    );

%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

var int: obj = max(i in COURIERS) (dist[i]);
var int: obj_2 = sum(i in COURIERS) (dist[i]);
% var int: obj_2 = max(array1d(O));
var float: objective = obj + (0.1*obj_2);

%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%

% LNS on top of RESTART on top of DOMWDEG + MIN SEARCH
solve :: int_search(O, dom_w_deg, indomain_min, complete) 
      :: restart_luby(100)
      :: relax_and_reconstruct(array1d(A), 85)
         minimize objective;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

output  [show(obj) ++ "\n"]
     ++ ["[| " ++ join (" | ", [show(dist[i]) | i in COURIERS]) ++ " |]" ++ "\n\n"]
%      ++ ["[| " ++ join (" | ", [show(A[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
%      ++ ["[| " ++ join (" | ", [show(O[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
        ;