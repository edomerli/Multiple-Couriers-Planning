model_complete = r"""
    reset;

    ## VARIABLES
    param m;
    param n;
    set COURIERS := {1..m}; # couriers with load capacities
    set ITEMS := {1..n}; # items with sizes
    set D_SIZE := {1..n+1};

    param capacity {COURIERS} > 0 integer;
    param size {ITEMS} > 0 integer;
    param D {D_SIZE, D_SIZE} >= 0 integer; # matrix of distances
    param obj_upper_bound;
    param obj_lower_bound := max {i in ITEMS} (D[n+1,i]+D[i,n+1]);


    var X {COURIERS, D_SIZE, D_SIZE} binary; # tensor defining the route of each courier
    var T {ITEMS} >= 1, <= n integer; # array that encode the visit sequence
    var Obj >= obj_lower_bound, <= obj_upper_bound integer;

    ## OBJECTIVE FUNCTION
    minimize Obj_function: Obj;

    ## CONSTRAINTS
    ## constraints on Obj
    s.t. def_Obj {i in COURIERS}:
        sum {j in D_SIZE, k in D_SIZE} X[i,j,k] * D[j,k] <= Obj;
     
    ## constraints to create X 
    s.t. one_arrival_per_node {k in ITEMS}:
        sum {i in COURIERS, j in D_SIZE} X[i,j,k] = 1; # each X[:,:,k] matrix has exaclty 1 item, just one i courier arrive at k-th point
    s.t. one_departure_per_node {j in ITEMS}:
        sum {i in COURIERS, k in D_SIZE} X[i,j,k] = 1; # each X[:,j,:] matrix has exaclty 1 item, just one i courier depart from j-th point
    s.t. origin_arrival {i in COURIERS}:
        sum {j in D_SIZE} X[i,j,n+1] = 1; # each X[i,:,n+1] column has exactly 1 item, the courier i return at the origin (or origin self loop if no implied constraint)
    s.t. origin_departure {i in COURIERS}:
        sum {k in D_SIZE} X[i,n+1,k] = 1; # each X[i,n+1,:] row has exactly 1 item, the courier i start from the origin (or origin self loop if no implied constraint)
    s.t. no_self_loop {i in COURIERS, j in ITEMS}:
        X[i,j,j] = 0; # the diagonal of each X[i,:,:] is zero, the i courier must move from a point to another
    s.t. balanced_flow {i in COURIERS, j in ITEMS}:
        sum {k in D_SIZE} X[i,k,j] = sum {k in D_SIZE} X[i,j,k]; # for each i courier the sum of each column A[i,:,j] is equal to the sum of each row A[i,j,:]
                                                                 # if the i courier enter arrive at the j-th point it has to depart from it
    s.t. load_capacity {i in COURIERS}:
        sum {j in D_SIZE, k in ITEMS} X[i,j,k]*size[k] <= capacity[i]; # each courier respects its own load capacity 

    ## constraints to create T
    s.t. first_visit {i in COURIERS, k in ITEMS}:
        T[k] <= 1 + 2*n * (1-X[i,n+1,k]); # for every courier the first element delivered, call it k, gets T[k]=1
    s.t. successive_visit_1 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] >= 1 - 2*n * (1-X[i,k,j]); # if the X[i,j,k] is 1 (vehicle i leaves node k and enter the node j) then T[j]-T[i]=1, the point j-th is visited exactly after the k-th point
                                             # value of big-M = 2*n
    s.t. successive_visit_2 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] <= 1 + 2*n * (1-X[i,k,j]);
         
    ## implied constraint 
    # each courier transports at least one item, so don't enable self loops with origin
    s.t. implied_constraint {i in COURIERS}:
        X[i,n+1,n+1] = 0; 
    
    ## symmetry breaking with ordered capacity 
    s.t. symmetry_breaking {i in {1..m-1}}:
        sum {j in ITEMS, k in ITEMS} X[i,j,k]*size[k] >= sum {j in ITEMS, k in ITEMS} X[i+1,j,k]*size[k]; # the load of each courier is ordered as the capacity       
"""

model_no_sym_break = r"""
    reset;

    ## VARIABLES
    param m;
    param n;
    set COURIERS := {1..m}; # couriers with load capacities
    set ITEMS := {1..n}; # items with sizes
    set D_SIZE := {1..n+1};

    param capacity {COURIERS} > 0 integer;
    param size {ITEMS} > 0 integer;
    param D {D_SIZE, D_SIZE} >= 0 integer; # matrix of distances
    param obj_upper_bound;
    param obj_lower_bound := max {i in ITEMS} (D[n+1,i]+D[i,n+1]);


    var X {COURIERS, D_SIZE, D_SIZE} binary; # tensor defining the route of each courier
    var T {ITEMS} >= 1, <= n integer; # array that encode the visit sequence
    var Obj >= obj_lower_bound, <= obj_upper_bound integer;

    ## OBJECTIVE FUNCTION
    minimize Obj_function: Obj;

    ## CONSTRAINTS
    ## constraints on Obj
    s.t. def_Obj {i in COURIERS}:
        sum {j in D_SIZE, k in D_SIZE} X[i,j,k] * D[j,k] <= Obj;
     
    ## constraints to create X 
    s.t. one_arrival_per_node {k in ITEMS}:
        sum {i in COURIERS, j in D_SIZE} X[i,j,k] = 1; # each X[:,:,k] matrix has exaclty 1 item, just one i courier arrive at k-th point
    s.t. one_departure_per_node {j in ITEMS}:
        sum {i in COURIERS, k in D_SIZE} X[i,j,k] = 1; # each X[:,j,:] matrix has exaclty 1 item, just one i courier depart from j-th point
    s.t. origin_arrival {i in COURIERS}:
        sum {j in D_SIZE} X[i,j,n+1] = 1; # each X[i,:,n+1] column has exactly 1 item, the courier i return at the origin (or origin self loop if no implied constraint)
    s.t. origin_departure {i in COURIERS}:
        sum {k in D_SIZE} X[i,n+1,k] = 1; # each X[i,n+1,:] row has exactly 1 item, the courier i start from the origin (or origin self loop if no implied constraint)
    s.t. no_self_loop {i in COURIERS, j in ITEMS}:
        X[i,j,j] = 0; # the diagonal of each X[i,:,:] is zero, the i courier must move from a point to another
    s.t. balanced_flow {i in COURIERS, j in ITEMS}:
        sum {k in D_SIZE} X[i,k,j] = sum {k in D_SIZE} X[i,j,k]; # for each i courier the sum of each column A[i,:,j] is equal to the sum of each row A[i,j,:]
                                                                 # if the i courier enter arrive at the j-th point it has to depart from it
    s.t. load_capacity {i in COURIERS}:
        sum {j in D_SIZE, k in ITEMS} X[i,j,k]*size[k] <= capacity[i]; # each courier respects its own load capacity 

    ## constraints to create T
    s.t. first_visit {i in COURIERS, k in ITEMS}:
        T[k] <= 1 + 2*n * (1-X[i,n+1,k]); # for every courier the first element delivered, call it k, gets T[k]=1
    s.t. successive_visit_1 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] >= 1 - 2*n * (1-X[i,k,j]); # if the X[i,j,k] is 1 (vehicle i leaves node k and enter the node j) then T[j]-T[i]=1, the point j-th is visited exactly after the k-th point
                                             # value of big-M = 2*n
    s.t. successive_visit_2 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] <= 1 + 2*n * (1-X[i,k,j]);
         
    ## implied constraint 
    # each courier transports at least one item, so don't enable self loops with origin
    s.t. implied_constraint {i in COURIERS}:
        X[i,n+1,n+1] = 0; 
    
    ## symmetry breaking with ordered capacity 
    s.t. symmetry_breaking {i in {1..m-1}}:
        sum {j in ITEMS, k in ITEMS} X[i,j,k]*size[k] >= sum {j in ITEMS, k in ITEMS} X[i+1,j,k]*size[k]; # the load of each courier is ordered as the capacity       
"""

model_no_implied = r"""
    reset;

    ## VARIABLES
    param m;
    param n;
    set COURIERS := {1..m}; # couriers with load capacities
    set ITEMS := {1..n}; # items with sizes
    set D_SIZE := {1..n+1};

    param capacity {COURIERS} > 0 integer;
    param size {ITEMS} > 0 integer;
    param D {D_SIZE, D_SIZE} >= 0 integer; # matrix of distances
    param obj_upper_bound := sum {i in D_SIZE} (max {j in D_SIZE} D[i,j]);
    param obj_lower_bound := max {i in ITEMS} (D[n+1,i]+D[i,n+1]);


    var X {COURIERS, D_SIZE, D_SIZE} binary; # tensor defining the route of each courier
    var T {ITEMS} >= 1, <= n integer; # array that encode the visit sequence
    var Obj >= obj_lower_bound, <= obj_upper_bound integer;

    ## OBJECTIVE FUNCTION
    minimize Obj_function: Obj;

    ## CONSTRAINTS
    ## constraints on Obj
    s.t. def_Obj {i in COURIERS}:
        sum {j in D_SIZE, k in D_SIZE} X[i,j,k] * D[j,k] <= Obj;
     
    ## constraints to create X 
    s.t. one_arrival_per_node {k in ITEMS}:
        sum {i in COURIERS, j in D_SIZE} X[i,j,k] = 1; # each X[:,:,k] matrix has exaclty 1 item, just one i courier arrive at k-th point
    s.t. one_departure_per_node {j in ITEMS}:
        sum {i in COURIERS, k in D_SIZE} X[i,j,k] = 1; # each X[:,j,:] matrix has exaclty 1 item, just one i courier depart from j-th point
    s.t. origin_arrival {i in COURIERS}:
        sum {j in D_SIZE} X[i,j,n+1] = 1; # each X[i,:,n+1] column has exactly 1 item, the courier i return at the origin (or origin self loop if no implied constraint)
    s.t. origin_departure {i in COURIERS}:
        sum {k in D_SIZE} X[i,n+1,k] = 1; # each X[i,n+1,:] row has exactly 1 item, the courier i start from the origin (or origin self loop if no implied constraint)
    s.t. no_self_loop {i in COURIERS, j in ITEMS}:
        X[i,j,j] = 0; # the diagonal of each X[i,:,:] is zero, the i courier must move from a point to another
    s.t. balanced_flow {i in COURIERS, j in ITEMS}:
        sum {k in D_SIZE} X[i,k,j] = sum {k in D_SIZE} X[i,j,k]; # for each i courier the sum of each column A[i,:,j] is equal to the sum of each row A[i,j,:]
                                                                 # if the i courier enter arrive at the j-th point it has to depart from it
    s.t. load_capacity {i in COURIERS}:
        sum {j in D_SIZE, k in ITEMS} X[i,j,k]*size[k] <= capacity[i]; # each courier respects its own load capacity 

    ## constraints to create T
    s.t. first_visit {i in COURIERS, k in ITEMS}:
        T[k] <= 1 + 2*n * (1-X[i,n+1,k]); # for every courier the first element delivered, call it k, gets T[k]=1
    s.t. successive_visit_1 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] >= 1 - 2*n * (1-X[i,k,j]); # if the X[i,j,k] is 1 (vehicle i leaves node k and enter the node j) then T[j]-T[i]=1, the point j-th is visited exactly after the k-th point
                                             # value of big-M = 2*n
    s.t. successive_visit_2 {i in COURIERS, j in ITEMS, k in ITEMS}:
        T[j]-T[k] <= 1 + 2*n * (1-X[i,k,j]);

    ## symmetry breaking with ordered capacity 
    s.t. symmetry_breaking {i in {1..m-1}}:
        sum {j in ITEMS, k in ITEMS} X[i,j,k]*size[k] >= sum {j in ITEMS, k in ITEMS} X[i+1,j,k]*size[k]; # the load of each courier is ordered as the capacity       
"""

