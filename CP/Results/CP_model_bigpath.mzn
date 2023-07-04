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

% distances bounds
int: dist_lowerbound = min(i in ITEMS)(D[n+1,i] + D[i,n+1]);

array[D_SIZE] of int: max_dists = sort([max(j in D_SIZE)(D[i,j]) | i in D_SIZE]);
int: dist_upperbound = sum(i in m..n+1)(max_dists[i]);

%-----------------------------------------------------------------------------%
% Variables
%-----------------------------------------------------------------------------%

array[ITEMS] of var ITEMS: T;  % time/order of each object in the big path
array[1..m+1] of var 1..n+1: B;  % "beginning of route" object for each courier + last value as a placeholder == n+1

% % actually carried loads
array[COURIERS] of var 0..max(l): loads;
% % distance travelled by each courier
array[COURIERS] of var dist_lowerbound..dist_upperbound: dist;


%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

constraint sum(l) >= sum(s); % total items size less than total couriers capacity

% constraints to create T
constraint all_different(T);

% placeholder constraint on B
constraint B[m+1] = n+1;
% initial constraint on B
constraint B[1] = 1;
% order constraint on B
constraint strictly_increasing(B);  % strictly -> each courier delivers at least one item (implied constraint)

% constraints on loads
constraint 
    forall(i in COURIERS) (
        loads[i] == sum(j in ITEMS where B[i] <= j /\ j < B[i+1])(s[T[j]]) /\
        loads[i] <= l[i] % each courier respects its own load capacity
    );

    
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%
constraint
    forall(i,j in COURIERS where i < j)(
        (loads[i] <= l[j] /\ loads[j] <= l[i]) -> T[B[i]] < T[B[j]]
    );
%----------COMMENT TO REMOVE SYMMETRY BREAKING----------%


% % constraint to create dist
constraint
    forall(i in COURIERS) (
        dist[i] == sum(j in ITEMS where B[i] < j /\ j < B[i+1])(D[T[j-1], T[j]])
                 + D[n+1, T[B[i]]] + D[T[B[i+1]-1], n+1]
    );

%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

int: obj_lowerbound = max(i in ITEMS)(D[n+1,i] + D[i,n+1]);

int: obj_upperbound = dist_upperbound;

var obj_lowerbound..obj_upperbound: obj = max(i in COURIERS) (dist[i]);


%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%
% solve :: seq_search([
%               int_search(T, dom_w_deg, indomain_min),
%               int_search(B, dom_w_deg, indomain_min)])
solve :: int_search(B, dom_w_deg, indomain_min) 
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
      :: restart_luby(100)
      :: relax_and_reconstruct(T, 85)
%-----------COMMENT TO REMOVE LNS and RESTART-----------%
         minimize obj;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

% output [show(dist_lowerbound) ++ "|" ++ show(obj_lowerbound) ++ "|" ++ show(dist_upperbound) ++ "\n"];

output  [show(obj) ++ "\n"]
     ++ ["[| " ++ join (" | ", [show(dist[i]) | i in COURIERS]) ++ " |]" ++ "\n\n"]
%      ++ ["[| " ++ join (" | ", [show(A[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
%      ++ ["[| " ++ join (" | ", [show(O[i,j]) | j in ITEMS]) ++ " |]" ++ "\n" | i in COURIERS] ++ ["\n"]
%      ++ ["[| " ++ join (" | ", [show(B[i]) | i in 1..m+1]) ++ " |]" ++ "\n\n"]
%      ++ ["[| " ++ join (" | ", [show(l_capacities[i]) | i in COURIERS]) ++ " |]" ++ "\n\n"]

        ;
        