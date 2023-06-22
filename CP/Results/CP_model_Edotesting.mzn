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
int: dist_lowerbound = min(i in ITEMS)(D[n+1,i] + D[i,n+1]);
int: dist_upperbound = sum(i in ITEMS)(max(j in ITEMS)(D[j,i]));

%-----------------------------------------------------------------------------%
% Variables
%-----------------------------------------------------------------------------%

% assignment of items to each courier
% array[COURIERS, ITEMS] of var 0..max(s): A;
% TODO: try with A binary
array[COURIERS, ITEMS] of var 0..1: A;
% order of items for each courier
array[COURIERS, ITEMS] of var 0..n: O;
% distance travelled by each courier
% TODO: can restrict dist considerably
array[COURIERS] of var dist_lowerbound..dist_upperbound: dist;

%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

constraint sum(l) >= sum(s); % total items size less than total couriers capacity

% constraints to create A
constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS where A[i, j] == 1)(s[j]) <= l[i] /\ % each courier respects its own load capacity
        count(z in A[i,..])(z==1) > 0 % each courier transports at least one item
    );

constraint
    forall(j in ITEMS) (
        count(z in A[..,j])(z==1) > 0
    );
% TODO: remove
% constraint 
%     forall(j in ITEMS) (
%         max(i in COURIERS)(A[i, j]) == s[j] /\
%         sum(i in COURIERS)(A[i, j]) == s[j] % each item is carried by at most one courier
%     );
    
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%
% TODO: double check
constraint
    forall(i,j in COURIERS where i < j /\ 
    l[i]-sum(k in ITEMS where A[i,k] == 1)(s[k]) > 0 /\ l[j]-sum(k in ITEMS where A[j,k] == 1)(s[k]) > 0) (
        lex_lesseq([A[i,k] | k in ITEMS], [A[j,k] | k in ITEMS])
    ); % row value symmetry breaking with available capacity condition
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%

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
%       :: restart_luby(100)
%       :: relax_and_reconstruct(array1d(A), 85)
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