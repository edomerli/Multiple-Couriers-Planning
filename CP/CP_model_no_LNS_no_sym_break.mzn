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

% order of items for each courier
array[COURIERS, D_SIZE] of var D_SIZE: T;


%-----------------------------------------------------------------------------%
% Constraints
%-----------------------------------------------------------------------------%

constraint 
    forall(i in COURIERS) (
        sum(j in ITEMS where T[i,j] != j)(s[j]) <= l[i]    % load capacities are respected
%         /\ ((count(j in ITEMS)(T[i,j] != j) > 0) -> (T[i,n+1] != n+1))  % if courier delivers items then the node origin must be
                                                                        % present in the subcircuit (complementary of implied c.)
        /\ T[i,n+1] != n+1    % implied constraint
    );

constraint
    forall(j in ITEMS) (
        count(z in T[..,j])(z != j) == 1 % each item is transported by exactly one courier
    );

% constraints to create T as a set of Hamiltonian sub-cycles (or sub-circuits)
constraint 
    forall(i in COURIERS) (
        subcircuit(T[i,..])
    );


%-----------------------------------------------------------------------------%
% Objective
%-----------------------------------------------------------------------------%

int: obj_lowerbound = max(i in ITEMS)(D[n+1,i] + D[i,n+1]);

array[D_SIZE] of int: max_dists = sort([max(j in D_SIZE)(D[i,j]) | i in D_SIZE]);
int: obj_upperbound = sum(i in m..n+1)(max_dists[i]);
        
var obj_lowerbound..obj_upperbound: obj = max(i in COURIERS)(sum(j in D_SIZE where T[i,j] != j) (D[j,T[i,j]]));


%-----------------------------------------------------------------------------%
% Search Strategy
%-----------------------------------------------------------------------------%
solve :: int_search(T, dom_w_deg, indomain_min) 
         minimize obj;

%-----------------------------------------------------------------------------%
% Output
%-----------------------------------------------------------------------------%

output  [show(obj) ++ "\n"] ++
        [show(T[i,j]) ++ if j == n+1 then "\n" else " " endif | i in COURIERS, j in D_SIZE]