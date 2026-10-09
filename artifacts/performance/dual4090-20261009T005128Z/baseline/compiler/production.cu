#define WP_NO_BFLOAT16

#define WP_TILE_BLOCK_DIM 32
#define WP_NO_CRT
#include "builtin.h"
#include "deterministic.h"

// Map wp.breakpoint() to a device brkpt at the call site so cuda-gdb attributes the stop to the generated .cu line
#if defined(__CUDACC__) && !defined(_MSC_VER)
#define __debugbreak() __brkpt()
#endif

#define builtin_tid1d() wp::tid(_idx, dim)
#define builtin_tid2d(x, y) wp::tid(x, y, _idx, dim)
#define builtin_tid3d(x, y, z) wp::tid(x, y, z, _idx, dim)
#define builtin_tid4d(x, y, z, w) wp::tid(x, y, z, w, _idx, dim)

#define builtin_block_dim() wp::block_dim()

// CUDA Thread Block Cluster shape declaration. Expands to __cluster_dims__
// only on devices that support clusters (compute capability 9.0+); otherwise
// expands to nothing so the same source compiles cleanly for any target arch.
#if defined(__CUDA_ARCH__) && (__CUDA_ARCH__ >= 900)
#define WP_CLUSTER_DIMS(x, y, z) __cluster_dims__(x, y, z)
#else
#define WP_CLUSTER_DIMS(x, y, z)
#endif

// Maximum registers per thread. __maxnreg__ was added in CUDA Toolkit 12.4;
// older toolkits ignore the opt-in so the same source remains compilable.
#if defined(__CUDACC_VER_MAJOR__) && (__CUDACC_VER_MAJOR__ > 12 || (__CUDACC_VER_MAJOR__ == 12 && __CUDACC_VER_MINOR__ >= 4))
#define WP_MAXNREG(n) __maxnreg__(n)
#else
#define WP_MAXNREG(n)
#endif

// Allow PTXAS to spill registers into shared memory. CUDA Toolkit 13.0
// introduced the pragma, which is unavailable in device-debug compilation.
#if defined(__CUDACC_VER_MAJOR__) && (__CUDACC_VER_MAJOR__ >= 13) && !defined(_DEBUG)
#define WP_ENABLE_SMEM_SPILLING() asm volatile(".pragma \"enable_smem_spilling\";");
#else
#define WP_ENABLE_SMEM_SPILLING()
#endif


// avoid namespacing of float type for casting to float type, this is to avoid wp::float(x), which is not valid in C++
#define float(x) cast_float(x)
#define adj_float(x, adj_x, adj_ret) adj_cast_float(x, adj_x, adj_ret)

#define int(x) cast_int(x)
#define adj_int(x, adj_x, adj_ret) adj_cast_int(x, adj_x, adj_ret)


struct Result_58cdc340
{
    wp::float32 side;
    wp::float32 min_gap;
    wp::float32 min_wall;
    wp::float32 max_penetration;
    wp::int32 termination;
    wp::int32 feasible;
    wp::int32 attempts;
    wp::int32 sweeps;
    wp::int32 accepted;
    wp::int32 rejected;
    wp::int32 proposals;
    wp::float32 final_step;


    Result_58cdc340() = default;
    CUDA_CALLABLE Result_58cdc340(wp::float32 const& side,
    wp::float32 const& min_gap = {},
    wp::float32 const& min_wall = {},
    wp::float32 const& max_penetration = {},
    wp::int32 const& termination = {},
    wp::int32 const& feasible = {},
    wp::int32 const& attempts = {},
    wp::int32 const& sweeps = {},
    wp::int32 const& accepted = {},
    wp::int32 const& rejected = {},
    wp::int32 const& proposals = {},
    wp::float32 const& final_step = {})
        : side{side}
        , min_gap{min_gap}
        , min_wall{min_wall}
        , max_penetration{max_penetration}
        , termination{termination}
        , feasible{feasible}
        , attempts{attempts}
        , sweeps{sweeps}
        , accepted{accepted}
        , rejected{rejected}
        , proposals{proposals}
        , final_step{final_step}

    {
    }

    CUDA_CALLABLE Result_58cdc340& operator += (const Result_58cdc340& rhs)
    {    side += rhs.side;
    min_gap += rhs.min_gap;
    min_wall += rhs.min_wall;
    max_penetration += rhs.max_penetration;
    termination += rhs.termination;
    feasible += rhs.feasible;
    attempts += rhs.attempts;
    sweeps += rhs.sweeps;
    accepted += rhs.accepted;
    rejected += rhs.rejected;
    proposals += rhs.proposals;
    final_step += rhs.final_step;

        return *this;}

};

static CUDA_CALLABLE void adj_Result_58cdc340(wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::float32 const&,
    wp::float32 & adj_side,
    wp::float32 & adj_min_gap,
    wp::float32 & adj_min_wall,
    wp::float32 & adj_max_penetration,
    wp::int32 & adj_termination,
    wp::int32 & adj_feasible,
    wp::int32 & adj_attempts,
    wp::int32 & adj_sweeps,
    wp::int32 & adj_accepted,
    wp::int32 & adj_rejected,
    wp::int32 & adj_proposals,
    wp::float32 & adj_final_step,
    Result_58cdc340 & adj_ret)
{
    adj_side += adj_ret.side;
    adj_min_gap += adj_ret.min_gap;
    adj_min_wall += adj_ret.min_wall;
    adj_max_penetration += adj_ret.max_penetration;
    adj_termination += adj_ret.termination;
    adj_feasible += adj_ret.feasible;
    adj_attempts += adj_ret.attempts;
    adj_sweeps += adj_ret.sweeps;
    adj_accepted += adj_ret.accepted;
    adj_rejected += adj_ret.rejected;
    adj_proposals += adj_ret.proposals;
    adj_final_step += adj_ret.final_step;
}

// Required when compiling adjoints.
CUDA_CALLABLE Result_58cdc340 add(const Result_58cdc340& a, const Result_58cdc340& b)
{
    return Result_58cdc340();
}

CUDA_CALLABLE void adj_atomic_add(Result_58cdc340* p, Result_58cdc340 t)
{
    wp::adj_atomic_add(&p->side, t.side);
    wp::adj_atomic_add(&p->min_gap, t.min_gap);
    wp::adj_atomic_add(&p->min_wall, t.min_wall);
    wp::adj_atomic_add(&p->max_penetration, t.max_penetration);
    wp::adj_atomic_add(&p->termination, t.termination);
    wp::adj_atomic_add(&p->feasible, t.feasible);
    wp::adj_atomic_add(&p->attempts, t.attempts);
    wp::adj_atomic_add(&p->sweeps, t.sweeps);
    wp::adj_atomic_add(&p->accepted, t.accepted);
    wp::adj_atomic_add(&p->rejected, t.rejected);
    wp::adj_atomic_add(&p->proposals, t.proposals);
    wp::adj_atomic_add(&p->final_step, t.final_step);
}




struct Parameters_71195d0b
{
    wp::int32 n;
    wp::float32 initial_side;
    wp::uint64 seed;
    wp::float32 step;
    wp::float32 step_floor;
    wp::float32 step_reduction;
    wp::float32 guard;
    wp::float32 acceptance_tolerance;
    wp::float32 motion_tolerance;
    wp::float32 rotation_mobility;
    wp::float32 relaxation;
    wp::float32 max_translation;
    wp::float32 max_rotation;
    wp::int32 max_attempts;
    wp::int32 max_sweeps;
    wp::int32 stagnation_sweeps;
    wp::int32 proposals_per_square;


    Parameters_71195d0b() = default;
    CUDA_CALLABLE Parameters_71195d0b(wp::int32 const& n,
    wp::float32 const& initial_side = {},
    wp::uint64 const& seed = {},
    wp::float32 const& step = {},
    wp::float32 const& step_floor = {},
    wp::float32 const& step_reduction = {},
    wp::float32 const& guard = {},
    wp::float32 const& acceptance_tolerance = {},
    wp::float32 const& motion_tolerance = {},
    wp::float32 const& rotation_mobility = {},
    wp::float32 const& relaxation = {},
    wp::float32 const& max_translation = {},
    wp::float32 const& max_rotation = {},
    wp::int32 const& max_attempts = {},
    wp::int32 const& max_sweeps = {},
    wp::int32 const& stagnation_sweeps = {},
    wp::int32 const& proposals_per_square = {})
        : n{n}
        , initial_side{initial_side}
        , seed{seed}
        , step{step}
        , step_floor{step_floor}
        , step_reduction{step_reduction}
        , guard{guard}
        , acceptance_tolerance{acceptance_tolerance}
        , motion_tolerance{motion_tolerance}
        , rotation_mobility{rotation_mobility}
        , relaxation{relaxation}
        , max_translation{max_translation}
        , max_rotation{max_rotation}
        , max_attempts{max_attempts}
        , max_sweeps{max_sweeps}
        , stagnation_sweeps{stagnation_sweeps}
        , proposals_per_square{proposals_per_square}

    {
    }

    CUDA_CALLABLE Parameters_71195d0b& operator += (const Parameters_71195d0b& rhs)
    {    n += rhs.n;
    initial_side += rhs.initial_side;
    seed += rhs.seed;
    step += rhs.step;
    step_floor += rhs.step_floor;
    step_reduction += rhs.step_reduction;
    guard += rhs.guard;
    acceptance_tolerance += rhs.acceptance_tolerance;
    motion_tolerance += rhs.motion_tolerance;
    rotation_mobility += rhs.rotation_mobility;
    relaxation += rhs.relaxation;
    max_translation += rhs.max_translation;
    max_rotation += rhs.max_rotation;
    max_attempts += rhs.max_attempts;
    max_sweeps += rhs.max_sweeps;
    stagnation_sweeps += rhs.stagnation_sweeps;
    proposals_per_square += rhs.proposals_per_square;

        return *this;}

};

static CUDA_CALLABLE void adj_Parameters_71195d0b(wp::int32 const&,
    wp::float32 const&,
    wp::uint64 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::float32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 const&,
    wp::int32 & adj_n,
    wp::float32 & adj_initial_side,
    wp::uint64 & adj_seed,
    wp::float32 & adj_step,
    wp::float32 & adj_step_floor,
    wp::float32 & adj_step_reduction,
    wp::float32 & adj_guard,
    wp::float32 & adj_acceptance_tolerance,
    wp::float32 & adj_motion_tolerance,
    wp::float32 & adj_rotation_mobility,
    wp::float32 & adj_relaxation,
    wp::float32 & adj_max_translation,
    wp::float32 & adj_max_rotation,
    wp::int32 & adj_max_attempts,
    wp::int32 & adj_max_sweeps,
    wp::int32 & adj_stagnation_sweeps,
    wp::int32 & adj_proposals_per_square,
    Parameters_71195d0b & adj_ret)
{
    adj_n += adj_ret.n;
    adj_initial_side += adj_ret.initial_side;
    adj_seed += adj_ret.seed;
    adj_step += adj_ret.step;
    adj_step_floor += adj_ret.step_floor;
    adj_step_reduction += adj_ret.step_reduction;
    adj_guard += adj_ret.guard;
    adj_acceptance_tolerance += adj_ret.acceptance_tolerance;
    adj_motion_tolerance += adj_ret.motion_tolerance;
    adj_rotation_mobility += adj_ret.rotation_mobility;
    adj_relaxation += adj_ret.relaxation;
    adj_max_translation += adj_ret.max_translation;
    adj_max_rotation += adj_ret.max_rotation;
    adj_max_attempts += adj_ret.max_attempts;
    adj_max_sweeps += adj_ret.max_sweeps;
    adj_stagnation_sweeps += adj_ret.stagnation_sweeps;
    adj_proposals_per_square += adj_ret.proposals_per_square;
}

// Required when compiling adjoints.
CUDA_CALLABLE Parameters_71195d0b add(const Parameters_71195d0b& a, const Parameters_71195d0b& b)
{
    return Parameters_71195d0b();
}

CUDA_CALLABLE void adj_atomic_add(Parameters_71195d0b* p, Parameters_71195d0b t)
{
    wp::adj_atomic_add(&p->n, t.n);
    wp::adj_atomic_add(&p->initial_side, t.initial_side);
    wp::adj_atomic_add(&p->seed, t.seed);
    wp::adj_atomic_add(&p->step, t.step);
    wp::adj_atomic_add(&p->step_floor, t.step_floor);
    wp::adj_atomic_add(&p->step_reduction, t.step_reduction);
    wp::adj_atomic_add(&p->guard, t.guard);
    wp::adj_atomic_add(&p->acceptance_tolerance, t.acceptance_tolerance);
    wp::adj_atomic_add(&p->motion_tolerance, t.motion_tolerance);
    wp::adj_atomic_add(&p->rotation_mobility, t.rotation_mobility);
    wp::adj_atomic_add(&p->relaxation, t.relaxation);
    wp::adj_atomic_add(&p->max_translation, t.max_translation);
    wp::adj_atomic_add(&p->max_rotation, t.max_rotation);
    wp::adj_atomic_add(&p->max_attempts, t.max_attempts);
    wp::adj_atomic_add(&p->max_sweeps, t.max_sweeps);
    wp::adj_atomic_add(&p->stagnation_sweeps, t.stagnation_sweeps);
    wp::adj_atomic_add(&p->proposals_per_square, t.proposals_per_square);
}




// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:115
static CUDA_CALLABLE wp::uint64 mix64_1(
    wp::uint64 var_value)
{
    //---------
    // primal vars
    wp::uint64 var_0;
    wp::uint64 var_1;
    wp::uint64 var_2;
    wp::uint64 var_3;
    wp::uint64 var_4;
    wp::uint64 var_5;
    wp::uint64 var_6;
    wp::uint64 var_7;
    wp::uint64 var_8;
    wp::uint64 var_9;
    wp::uint64 var_10;
    wp::uint64 var_11;
    wp::uint64 var_12;
    wp::uint64 var_13;
    //---------
    // forward
    // def mix64(value: wp.uint64):                                                           <L 116>
    // z = value                                                                              <L 117>
    var_0 = wp::copy(var_value);
    // z = (z ^ (z >> wp.uint64(30))) * wp.uint64(13787848793156543929)                       <L 118>
    var_1 = 30ull;
    var_2 = wp::rshift(var_0, var_1);
    var_3 = wp::bit_xor(var_0, var_2);
    var_4 = 13787848793156543929ull;
    var_5 = wp::mul(var_3, var_4);
    // z = (z ^ (z >> wp.uint64(27))) * wp.uint64(10723151780598845931)                       <L 119>
    var_6 = 27ull;
    var_7 = wp::rshift(var_5, var_6);
    var_8 = wp::bit_xor(var_5, var_7);
    var_9 = 10723151780598845931ull;
    var_10 = wp::mul(var_8, var_9);
    // return z ^ (z >> wp.uint64(31))                                                        <L 120>
    var_11 = 31ull;
    var_12 = wp::rshift(var_10, var_11);
    var_13 = wp::bit_xor(var_10, var_12);
    return var_13;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:123
static CUDA_CALLABLE void random_value_1(
    wp::uint64 var_state,
    wp::uint64 & ret_0,
    wp::float32 & ret_1)
{
    //---------
    // primal vars
    wp::uint64 var_0;
    wp::uint64 var_1;
    wp::uint64 var_2;
    wp::uint64 var_3;
    wp::uint64 var_4;
    wp::float32 var_5;
    const wp::float32 var_6 = 1.0;
    const wp::float32 var_7 = 16777216.0;
    wp::float32 var_8;
    wp::float32 var_9;
    //---------
    // forward
    // def random_value(state: wp.uint64):                                                    <L 124>
    // nxt = state + wp.uint64(11400714819323198485)                                          <L 125>
    var_0 = 11400714819323198485ull;
    var_1 = wp::add(var_state, var_0);
    // return nxt, float(mix64(nxt) >> wp.uint64(40)) * (1.0 / 16777216.0)                    <L 126>
    var_2 = mix64_1(var_1);
    var_3 = 40ull;
    var_4 = wp::rshift(var_2, var_3);
    var_5 = wp::float(var_4);
    var_8 = wp::div(var_6, var_7);
    var_9 = wp::mul(var_5, var_8);
    ret_0 = var_1;
    ret_1 = var_9;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:139
static CUDA_CALLABLE wp::float32 separate_axis_value_1(
    wp::float32 value)
{

#if defined(__CUDA_ARCH__)
    float result;
    asm volatile("mov.b32 %0, %1;" : "=f"(result) : "f"(value));
    return result;
#else
    return value;
#endif
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:154
static CUDA_CALLABLE void axes_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> & ret_0,
    wp::vec_t<2, wp::float32> & ret_1)
{
    //---------
    // primal vars
    wp::float32 var_0;
    wp::float32 var_1;
    wp::vec_t<2, wp::float32> var_2;
    wp::float32 var_3;
    wp::float32 var_4;
    wp::float32 var_5;
    wp::vec_t<2, wp::float32> var_6;
    //---------
    // forward
    // def axes(theta: float):                                                                <L 155>
    // cosine = wp.cos(theta)                                                                 <L 156>
    var_0 = wp::cos(var_theta);
    // sine = wp.sin(theta)                                                                   <L 157>
    var_1 = wp::sin(var_theta);
    // return wp.vec2(cosine, sine), wp.vec2(-separate_axis_value(sine), separate_axis_value(cosine))       <L 158>
    var_2 = wp::vec_t<2, wp::float32>(var_0, var_1);
    var_3 = separate_axis_value_1(var_1);
    var_4 = wp::neg(var_3);
    var_5 = separate_axis_value_1(var_0);
    var_6 = wp::vec_t<2, wp::float32>(var_4, var_5);
    ret_0 = var_2;
    ret_1 = var_6;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:161
static CUDA_CALLABLE wp::float32 support_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> var_normal)
{
    //---------
    // primal vars
    wp::vec_t<2, wp::float32> var_0;
    wp::vec_t<2, wp::float32> var_1;
    const wp::float32 var_2 = 0.5;
    wp::float32 var_3;
    wp::float32 var_4;
    wp::float32 var_5;
    wp::float32 var_6;
    wp::float32 var_7;
    wp::float32 var_8;
    //---------
    // forward
    // def support(theta: float, normal: wp.vec2):                                            <L 162>
    // u, v = axes(theta)                                                                     <L 163>
    axes_1(var_theta, var_0, var_1);
    // return 0.5 * (wp.abs(wp.dot(u, normal)) + wp.abs(wp.dot(v, normal)))                   <L 164>
    var_3 = wp::dot(var_0, var_normal);
    var_4 = wp::abs(var_3);
    var_5 = wp::dot(var_1, var_normal);
    var_6 = wp::abs(var_5);
    var_7 = wp::add(var_4, var_6);
    var_8 = wp::mul(var_2, var_7);
    return var_8;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:229
static CUDA_CALLABLE wp::float32 pair_gap_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q)
{
    //---------
    // primal vars
    const wp::int32 var_0 = 2;
    wp::float32 var_1;
    wp::vec_t<2, wp::float32> var_2;
    wp::vec_t<2, wp::float32> var_3;
    const wp::int32 var_4 = 2;
    wp::float32 var_5;
    wp::vec_t<2, wp::float32> var_6;
    wp::vec_t<2, wp::float32> var_7;
    const wp::int32 var_8 = 0;
    wp::float32 var_9;
    const wp::int32 var_10 = 0;
    wp::float32 var_11;
    wp::float32 var_12;
    const wp::int32 var_13 = 1;
    wp::float32 var_14;
    const wp::int32 var_15 = 1;
    wp::float32 var_16;
    wp::float32 var_17;
    wp::vec_t<2, wp::float32> var_18;
    const wp::float32 var_19 = -1e+20;
    wp::float32 var_20;
    const wp::int32 var_21 = 0;
    wp::vec_t<2, wp::float32> var_22;
    const wp::int32 var_23 = 1;
    bool var_24;
    wp::vec_t<2, wp::float32> var_25;
    const wp::int32 var_26 = 2;
    bool var_27;
    wp::vec_t<2, wp::float32> var_28;
    const wp::int32 var_29 = 3;
    bool var_30;
    wp::vec_t<2, wp::float32> var_31;
    wp::vec_t<2, wp::float32> var_32;
    wp::vec_t<2, wp::float32> var_33;
    wp::vec_t<2, wp::float32> var_34;
    const wp::float32 var_35 = 0.5;
    wp::float32 var_36;
    wp::float32 var_37;
    wp::float32 var_38;
    wp::float32 var_39;
    wp::float32 var_40;
    wp::float32 var_41;
    const wp::float32 var_42 = 0.5;
    wp::float32 var_43;
    wp::float32 var_44;
    wp::float32 var_45;
    wp::float32 var_46;
    wp::float32 var_47;
    wp::float32 var_48;
    wp::float32 var_49;
    wp::float32 var_50;
    wp::float32 var_51;
    wp::float32 var_52;
    wp::float32 var_53;
    const wp::int32 var_54 = 1;
    wp::vec_t<2, wp::float32> var_55;
    const wp::int32 var_56 = 1;
    bool var_57;
    wp::vec_t<2, wp::float32> var_58;
    const wp::int32 var_59 = 2;
    bool var_60;
    wp::vec_t<2, wp::float32> var_61;
    const wp::int32 var_62 = 3;
    bool var_63;
    wp::vec_t<2, wp::float32> var_64;
    wp::vec_t<2, wp::float32> var_65;
    wp::vec_t<2, wp::float32> var_66;
    wp::vec_t<2, wp::float32> var_67;
    const wp::float32 var_68 = 0.5;
    wp::float32 var_69;
    wp::float32 var_70;
    wp::float32 var_71;
    wp::float32 var_72;
    wp::float32 var_73;
    wp::float32 var_74;
    const wp::float32 var_75 = 0.5;
    wp::float32 var_76;
    wp::float32 var_77;
    wp::float32 var_78;
    wp::float32 var_79;
    wp::float32 var_80;
    wp::float32 var_81;
    wp::float32 var_82;
    wp::float32 var_83;
    wp::float32 var_84;
    wp::float32 var_85;
    wp::float32 var_86;
    const wp::int32 var_87 = 2;
    wp::vec_t<2, wp::float32> var_88;
    const wp::int32 var_89 = 1;
    bool var_90;
    wp::vec_t<2, wp::float32> var_91;
    const wp::int32 var_92 = 2;
    bool var_93;
    wp::vec_t<2, wp::float32> var_94;
    const wp::int32 var_95 = 3;
    bool var_96;
    wp::vec_t<2, wp::float32> var_97;
    wp::vec_t<2, wp::float32> var_98;
    wp::vec_t<2, wp::float32> var_99;
    wp::vec_t<2, wp::float32> var_100;
    const wp::float32 var_101 = 0.5;
    wp::float32 var_102;
    wp::float32 var_103;
    wp::float32 var_104;
    wp::float32 var_105;
    wp::float32 var_106;
    wp::float32 var_107;
    const wp::float32 var_108 = 0.5;
    wp::float32 var_109;
    wp::float32 var_110;
    wp::float32 var_111;
    wp::float32 var_112;
    wp::float32 var_113;
    wp::float32 var_114;
    wp::float32 var_115;
    wp::float32 var_116;
    wp::float32 var_117;
    wp::float32 var_118;
    wp::float32 var_119;
    const wp::int32 var_120 = 3;
    wp::vec_t<2, wp::float32> var_121;
    const wp::int32 var_122 = 1;
    bool var_123;
    wp::vec_t<2, wp::float32> var_124;
    const wp::int32 var_125 = 2;
    bool var_126;
    wp::vec_t<2, wp::float32> var_127;
    const wp::int32 var_128 = 3;
    bool var_129;
    wp::vec_t<2, wp::float32> var_130;
    wp::vec_t<2, wp::float32> var_131;
    wp::vec_t<2, wp::float32> var_132;
    wp::vec_t<2, wp::float32> var_133;
    const wp::float32 var_134 = 0.5;
    wp::float32 var_135;
    wp::float32 var_136;
    wp::float32 var_137;
    wp::float32 var_138;
    wp::float32 var_139;
    wp::float32 var_140;
    const wp::float32 var_141 = 0.5;
    wp::float32 var_142;
    wp::float32 var_143;
    wp::float32 var_144;
    wp::float32 var_145;
    wp::float32 var_146;
    wp::float32 var_147;
    wp::float32 var_148;
    wp::float32 var_149;
    wp::float32 var_150;
    wp::float32 var_151;
    wp::float32 var_152;
    //---------
    // forward
    // def pair_gap(p: wp.vec3, q: wp.vec3):                                                  <L 230>
    // up, vp = axes(p[2])                                                                    <L 231>
    var_1 = wp::extract(var_p, var_0);
    axes_1(var_1, var_2, var_3);
    // uq, vq = axes(q[2])                                                                    <L 232>
    var_5 = wp::extract(var_q, var_4);
    axes_1(var_5, var_6, var_7);
    // d = wp.vec2(q[0] - p[0], q[1] - p[1])                                                  <L 233>
    var_9 = wp::extract(var_q, var_8);
    var_11 = wp::extract(var_p, var_10);
    var_12 = wp::sub(var_9, var_11);
    var_14 = wp::extract(var_q, var_13);
    var_16 = wp::extract(var_p, var_15);
    var_17 = wp::sub(var_14, var_16);
    var_18 = wp::vec_t<2, wp::float32>(var_12, var_17);
    // best = float(-1.0e20)                                                                  <L 234>
    var_20 = wp::float(var_19);
    // for k in range(4):                                                                     <L 235>
    // a = up                                                                                 <L 236>
    var_22 = wp::copy(var_2);
    // if k == 1:                                                                             <L 237>
    var_24 = (var_21 == var_23);
    if (var_24) {
        // a = vp                                                                             <L 238>
        var_25 = wp::copy(var_3);
    }
    if (!var_24) {
        // elif k == 2:                                                                       <L 239>
        var_27 = (var_21 == var_26);
        if (var_27) {
            // a = uq                                                                         <L 240>
            var_28 = wp::copy(var_6);
        }
        if (!var_27) {
            // elif k == 3:                                                                   <L 241>
            var_30 = (var_21 == var_29);
            if (var_30) {
                // a = vq                                                                     <L 242>
                var_31 = wp::copy(var_7);
            }
            var_32 = wp::where(var_30, var_31, var_22);
        }
        var_33 = wp::where(var_27, var_28, var_32);
    }
    var_34 = wp::where(var_24, var_25, var_33);
    // hp = 0.5 * (wp.abs(wp.dot(up, a)) + wp.abs(wp.dot(vp, a)))                             <L 243>
    var_36 = wp::dot(var_2, var_34);
    var_37 = wp::abs(var_36);
    var_38 = wp::dot(var_3, var_34);
    var_39 = wp::abs(var_38);
    var_40 = wp::add(var_37, var_39);
    var_41 = wp::mul(var_35, var_40);
    // hq = 0.5 * (wp.abs(wp.dot(uq, a)) + wp.abs(wp.dot(vq, a)))                             <L 244>
    var_43 = wp::dot(var_6, var_34);
    var_44 = wp::abs(var_43);
    var_45 = wp::dot(var_7, var_34);
    var_46 = wp::abs(var_45);
    var_47 = wp::add(var_44, var_46);
    var_48 = wp::mul(var_42, var_47);
    // best = wp.max(best, wp.abs(wp.dot(d, a)) - hp - hq)                                    <L 245>
    var_49 = wp::dot(var_18, var_34);
    var_50 = wp::abs(var_49);
    var_51 = wp::sub(var_50, var_41);
    var_52 = wp::sub(var_51, var_48);
    var_53 = wp::max(var_20, var_52);
    // a = up                                                                                 <L 236>
    var_55 = wp::copy(var_2);
    // if k == 1:                                                                             <L 237>
    var_57 = (var_54 == var_56);
    if (var_57) {
        // a = vp                                                                             <L 238>
        var_58 = wp::copy(var_3);
    }
    if (!var_57) {
        // elif k == 2:                                                                       <L 239>
        var_60 = (var_54 == var_59);
        if (var_60) {
            // a = uq                                                                         <L 240>
            var_61 = wp::copy(var_6);
        }
        if (!var_60) {
            // elif k == 3:                                                                   <L 241>
            var_63 = (var_54 == var_62);
            if (var_63) {
                // a = vq                                                                     <L 242>
                var_64 = wp::copy(var_7);
            }
            var_65 = wp::where(var_63, var_64, var_55);
        }
        var_66 = wp::where(var_60, var_61, var_65);
    }
    var_67 = wp::where(var_57, var_58, var_66);
    // hp = 0.5 * (wp.abs(wp.dot(up, a)) + wp.abs(wp.dot(vp, a)))                             <L 243>
    var_69 = wp::dot(var_2, var_67);
    var_70 = wp::abs(var_69);
    var_71 = wp::dot(var_3, var_67);
    var_72 = wp::abs(var_71);
    var_73 = wp::add(var_70, var_72);
    var_74 = wp::mul(var_68, var_73);
    // hq = 0.5 * (wp.abs(wp.dot(uq, a)) + wp.abs(wp.dot(vq, a)))                             <L 244>
    var_76 = wp::dot(var_6, var_67);
    var_77 = wp::abs(var_76);
    var_78 = wp::dot(var_7, var_67);
    var_79 = wp::abs(var_78);
    var_80 = wp::add(var_77, var_79);
    var_81 = wp::mul(var_75, var_80);
    // best = wp.max(best, wp.abs(wp.dot(d, a)) - hp - hq)                                    <L 245>
    var_82 = wp::dot(var_18, var_67);
    var_83 = wp::abs(var_82);
    var_84 = wp::sub(var_83, var_74);
    var_85 = wp::sub(var_84, var_81);
    var_86 = wp::max(var_53, var_85);
    // a = up                                                                                 <L 236>
    var_88 = wp::copy(var_2);
    // if k == 1:                                                                             <L 237>
    var_90 = (var_87 == var_89);
    if (var_90) {
        // a = vp                                                                             <L 238>
        var_91 = wp::copy(var_3);
    }
    if (!var_90) {
        // elif k == 2:                                                                       <L 239>
        var_93 = (var_87 == var_92);
        if (var_93) {
            // a = uq                                                                         <L 240>
            var_94 = wp::copy(var_6);
        }
        if (!var_93) {
            // elif k == 3:                                                                   <L 241>
            var_96 = (var_87 == var_95);
            if (var_96) {
                // a = vq                                                                     <L 242>
                var_97 = wp::copy(var_7);
            }
            var_98 = wp::where(var_96, var_97, var_88);
        }
        var_99 = wp::where(var_93, var_94, var_98);
    }
    var_100 = wp::where(var_90, var_91, var_99);
    // hp = 0.5 * (wp.abs(wp.dot(up, a)) + wp.abs(wp.dot(vp, a)))                             <L 243>
    var_102 = wp::dot(var_2, var_100);
    var_103 = wp::abs(var_102);
    var_104 = wp::dot(var_3, var_100);
    var_105 = wp::abs(var_104);
    var_106 = wp::add(var_103, var_105);
    var_107 = wp::mul(var_101, var_106);
    // hq = 0.5 * (wp.abs(wp.dot(uq, a)) + wp.abs(wp.dot(vq, a)))                             <L 244>
    var_109 = wp::dot(var_6, var_100);
    var_110 = wp::abs(var_109);
    var_111 = wp::dot(var_7, var_100);
    var_112 = wp::abs(var_111);
    var_113 = wp::add(var_110, var_112);
    var_114 = wp::mul(var_108, var_113);
    // best = wp.max(best, wp.abs(wp.dot(d, a)) - hp - hq)                                    <L 245>
    var_115 = wp::dot(var_18, var_100);
    var_116 = wp::abs(var_115);
    var_117 = wp::sub(var_116, var_107);
    var_118 = wp::sub(var_117, var_114);
    var_119 = wp::max(var_86, var_118);
    // a = up                                                                                 <L 236>
    var_121 = wp::copy(var_2);
    // if k == 1:                                                                             <L 237>
    var_123 = (var_120 == var_122);
    if (var_123) {
        // a = vp                                                                             <L 238>
        var_124 = wp::copy(var_3);
    }
    if (!var_123) {
        // elif k == 2:                                                                       <L 239>
        var_126 = (var_120 == var_125);
        if (var_126) {
            // a = uq                                                                         <L 240>
            var_127 = wp::copy(var_6);
        }
        if (!var_126) {
            // elif k == 3:                                                                   <L 241>
            var_129 = (var_120 == var_128);
            if (var_129) {
                // a = vq                                                                     <L 242>
                var_130 = wp::copy(var_7);
            }
            var_131 = wp::where(var_129, var_130, var_121);
        }
        var_132 = wp::where(var_126, var_127, var_131);
    }
    var_133 = wp::where(var_123, var_124, var_132);
    // hp = 0.5 * (wp.abs(wp.dot(up, a)) + wp.abs(wp.dot(vp, a)))                             <L 243>
    var_135 = wp::dot(var_2, var_133);
    var_136 = wp::abs(var_135);
    var_137 = wp::dot(var_3, var_133);
    var_138 = wp::abs(var_137);
    var_139 = wp::add(var_136, var_138);
    var_140 = wp::mul(var_134, var_139);
    // hq = 0.5 * (wp.abs(wp.dot(uq, a)) + wp.abs(wp.dot(vq, a)))                             <L 244>
    var_142 = wp::dot(var_6, var_133);
    var_143 = wp::abs(var_142);
    var_144 = wp::dot(var_7, var_133);
    var_145 = wp::abs(var_144);
    var_146 = wp::add(var_143, var_145);
    var_147 = wp::mul(var_141, var_146);
    // best = wp.max(best, wp.abs(wp.dot(d, a)) - hp - hq)                                    <L 245>
    var_148 = wp::dot(var_18, var_133);
    var_149 = wp::abs(var_148);
    var_150 = wp::sub(var_149, var_140);
    var_151 = wp::sub(var_150, var_147);
    var_152 = wp::max(var_119, var_151);
    // return best                                                                            <L 246>
    return var_152;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:292
static CUDA_CALLABLE void residuals_1(
    wp::array_t<wp::vec_t<3, wp::float32>> var_poses,
    wp::int32 var_world,
    wp::int32 var_n,
    wp::float32 var_side,
    wp::float32 & ret_0,
    wp::float32 & ret_1,
    wp::int32 & ret_2)
{
    //---------
    // primal vars
    const wp::float32 var_0 = 1e+20;
    wp::float32 var_1;
    const wp::float32 var_2 = 1e+20;
    wp::float32 var_3;
    const wp::int32 var_4 = 1;
    wp::int32 var_5;
    wp::range_t var_6;
    wp::int32 var_7;
    wp::vec_t<3, wp::float32>* var_8;
    wp::vec_t<3, wp::float32> var_9;
    wp::vec_t<3, wp::float32> var_10;
    bool var_11;
    const wp::int32 var_12 = 0;
    wp::float32 var_13;
    bool var_14;
    bool var_15;
    const wp::int32 var_16 = 1;
    wp::float32 var_17;
    bool var_18;
    bool var_19;
    const wp::int32 var_20 = 2;
    wp::float32 var_21;
    bool var_22;
    bool var_23;
    const wp::int32 var_24 = 0;
    wp::int32 var_25;
    const wp::float32 var_26 = 0.5;
    wp::float32 var_27;
    const wp::int32 var_28 = 0;
    wp::float32 var_29;
    wp::float32 var_30;
    wp::float32 var_31;
    const wp::int32 var_32 = 2;
    wp::float32 var_33;
    const wp::float32 var_34 = 1.0;
    const wp::float32 var_35 = 0.0;
    wp::vec_t<2, wp::float32> var_36;
    wp::float32 var_37;
    wp::float32 var_38;
    wp::float32 var_39;
    const wp::float32 var_40 = 0.5;
    wp::float32 var_41;
    const wp::int32 var_42 = 1;
    wp::float32 var_43;
    wp::float32 var_44;
    wp::float32 var_45;
    const wp::int32 var_46 = 2;
    wp::float32 var_47;
    const wp::float32 var_48 = 0.0;
    const wp::float32 var_49 = 1.0;
    wp::vec_t<2, wp::float32> var_50;
    wp::float32 var_51;
    wp::float32 var_52;
    wp::float32 var_53;
    const wp::int32 var_54 = 1;
    wp::int32 var_55;
    wp::range_t var_56;
    wp::int32 var_57;
    wp::vec_t<3, wp::float32>* var_58;
    wp::float32 var_59;
    wp::vec_t<3, wp::float32> var_60;
    wp::float32 var_61;
    //---------
    // forward
    // def residuals(poses: wp.array2d(dtype=wp.vec3), world: int, n: int, side: float):       <L 293>
    // gap = float(1.0e20)                                                                    <L 294>
    var_1 = wp::float(var_0);
    // wall = float(1.0e20)                                                                   <L 295>
    var_3 = wp::float(var_2);
    // finite = int(1)                                                                        <L 296>
    var_5 = wp::int(var_4);
    // for i in range(n):                                                                     <L 297>
    var_6 = wp::range(var_n);
    start_for_0:;
        if (iter_cmp(var_6) == 0) goto end_for_0;
        var_7 = wp::iter_next(var_6);
        // p = poses[i, world]                                                                <L 298>
        var_8 = wp::address(var_poses, var_7, var_world);
        var_10 = wp::load(var_8);
        var_9 = wp::copy(var_10);
        // if not wp.isfinite(p[0]) or not wp.isfinite(p[1]) or not wp.isfinite(p[2]):        <L 299>
        var_13 = wp::extract(var_9, var_12);
        var_14 = wp::isfinite(var_13);
        var_15 = wp::unot(var_14);
        var_11 = var_15;
        if (!var_11) {
            var_17 = wp::extract(var_9, var_16);
            var_18 = wp::isfinite(var_17);
            var_19 = wp::unot(var_18);
            var_11 = var_11 || var_19;
        }
        if (!var_11) {
            var_21 = wp::extract(var_9, var_20);
            var_22 = wp::isfinite(var_21);
            var_23 = wp::unot(var_22);
            var_11 = var_11 || var_23;
        }
        if (var_11) {
            // finite = 0                                                                     <L 300>
        }
        var_25 = wp::where(var_11, var_24, var_5);
        // wall = wp.min(wall, 0.5 * side - wp.abs(p[0]) - support(p[2], wp.vec2(1.0, 0.0)))       <L 301>
        var_27 = wp::mul(var_26, var_side);
        var_29 = wp::extract(var_9, var_28);
        var_30 = wp::abs(var_29);
        var_31 = wp::sub(var_27, var_30);
        var_33 = wp::extract(var_9, var_32);
        var_36 = wp::vec_t<2, wp::float32>(var_34, var_35);
        var_37 = support_1(var_33, var_36);
        var_38 = wp::sub(var_31, var_37);
        var_39 = wp::min(var_3, var_38);
        // wall = wp.min(wall, 0.5 * side - wp.abs(p[1]) - support(p[2], wp.vec2(0.0, 1.0)))       <L 302>
        var_41 = wp::mul(var_40, var_side);
        var_43 = wp::extract(var_9, var_42);
        var_44 = wp::abs(var_43);
        var_45 = wp::sub(var_41, var_44);
        var_47 = wp::extract(var_9, var_46);
        var_50 = wp::vec_t<2, wp::float32>(var_48, var_49);
        var_51 = support_1(var_47, var_50);
        var_52 = wp::sub(var_45, var_51);
        var_53 = wp::min(var_39, var_52);
        // for j in range(i + 1, n):                                                          <L 303>
        var_55 = wp::add(var_7, var_54);
        var_56 = wp::range(var_55, var_n);
        start_for_2:;
            if (iter_cmp(var_56) == 0) goto end_for_2;
            var_57 = wp::iter_next(var_56);
            // gap = wp.min(gap, pair_gap(p, poses[j, world]))                                <L 304>
            var_58 = wp::address(var_poses, var_57, var_world);
            var_60 = wp::load(var_58);
            var_59 = pair_gap_1(var_9, var_60);
            var_61 = wp::min(var_1, var_59);
            wp::assign(var_1, var_61);
            goto start_for_2;
        end_for_2:;
        wp::assign(var_3, var_53);
        wp::assign(var_5, var_25);
        goto start_for_0;
    end_for_0:;
    // return gap, wall, finite                                                               <L 305>
    ret_0 = var_1;
    ret_1 = var_3;
    ret_2 = var_5;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:129
static CUDA_CALLABLE wp::float32 sign_symmetric_1(
    wp::float32 var_x)
{
    //---------
    // primal vars
    const wp::float32 var_0 = 0.0;
    wp::float32 var_1;
    const wp::float32 var_2 = 1e-06;
    bool var_3;
    const wp::float32 var_4 = 1.0;
    const wp::float32 var_5 = -1e-06;
    bool var_6;
    const wp::float32 var_7 = -1.0;
    wp::float32 var_8;
    wp::float32 var_9;
    //---------
    // forward
    // def sign_symmetric(x: float):                                                          <L 130>
    // s = float(0.0)                                                                         <L 131>
    var_1 = wp::float(var_0);
    // if x > 0.000001:                                                                       <L 132>
    var_3 = (var_x > var_2);
    if (var_3) {
        // s = 1.0                                                                            <L 133>
    }
    if (!var_3) {
        // elif x < -0.000001:                                                                <L 134>
        var_6 = (var_x < var_5);
        if (var_6) {
            // s = -1.0                                                                       <L 135>
        }
        var_8 = wp::where(var_6, var_7, var_1);
    }
    var_9 = wp::where(var_3, var_4, var_8);
    // return s                                                                               <L 136>
    return var_9;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:167
static CUDA_CALLABLE wp::float32 support_derivative_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> var_normal)
{
    //---------
    // primal vars
    wp::vec_t<2, wp::float32> var_0;
    wp::vec_t<2, wp::float32> var_1;
    const wp::float32 var_2 = 0.5;
    wp::float32 var_3;
    wp::float32 var_4;
    wp::float32 var_5;
    wp::float32 var_6;
    wp::float32 var_7;
    wp::float32 var_8;
    wp::float32 var_9;
    wp::float32 var_10;
    wp::float32 var_11;
    wp::float32 var_12;
    //---------
    // forward
    // def support_derivative(theta: float, normal: wp.vec2):                                 <L 168>
    // u, v = axes(theta)                                                                     <L 169>
    axes_1(var_theta, var_0, var_1);
    // return 0.5 * (sign_symmetric(wp.dot(u, normal)) * wp.dot(v, normal)                    <L 170>
    var_3 = wp::dot(var_0, var_normal);
    var_4 = sign_symmetric_1(var_3);
    var_5 = wp::dot(var_1, var_normal);
    var_6 = wp::mul(var_4, var_5);
    // - sign_symmetric(wp.dot(v, normal)) * wp.dot(u, normal))                               <L 171>
    var_7 = wp::dot(var_1, var_normal);
    var_8 = sign_symmetric_1(var_7);
    var_9 = wp::dot(var_0, var_normal);
    var_10 = wp::mul(var_8, var_9);
    var_11 = wp::sub(var_6, var_10);
    var_12 = wp::mul(var_2, var_11);
    return var_12;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:249
static CUDA_CALLABLE wp::float32 bounded_scale_1(
    wp::float32 var_lam,
    wp::float32 var_linear_norm,
    wp::float32 var_angular,
    Parameters_71195d0b var_cfg)
{
    //---------
    // primal vars
    wp::float32* var_0;
    wp::float32 var_1;
    wp::float32 var_2;
    const wp::float32 var_3 = 0.0;
    bool var_4;
    wp::float32* var_5;
    wp::float32 var_6;
    wp::float32 var_7;
    wp::float32 var_8;
    wp::float32 var_9;
    const wp::float32 var_10 = 0.0;
    bool var_11;
    wp::float32* var_12;
    wp::float32 var_13;
    wp::float32 var_14;
    wp::float32 var_15;
    wp::float32 var_16;
    //---------
    // forward
    // def bounded_scale(lam: float, linear_norm: float, angular: float, cfg: Parameters):       <L 250>
    // scale = lam * cfg.relaxation                                                           <L 251>
    var_0 = &((var_cfg).relaxation);
    var_2 = wp::load(var_0);
    var_1 = wp::mul(var_lam, var_2);
    // if linear_norm > 0.0:                                                                  <L 252>
    var_4 = (var_linear_norm > var_3);
    if (var_4) {
        // scale = wp.min(scale, cfg.max_translation / linear_norm)                           <L 253>
        var_5 = &((var_cfg).max_translation);
        var_7 = wp::load(var_5);
        var_6 = wp::div(var_7, var_linear_norm);
        var_8 = wp::min(var_1, var_6);
    }
    var_9 = wp::where(var_4, var_8, var_1);
    // if angular > 0.0:                                                                      <L 254>
    var_11 = (var_angular > var_10);
    if (var_11) {
        // scale = wp.min(scale, cfg.max_rotation / angular)                                  <L 255>
        var_12 = &((var_cfg).max_rotation);
        var_14 = wp::load(var_12);
        var_13 = wp::div(var_14, var_angular);
        var_15 = wp::min(var_9, var_13);
    }
    var_16 = wp::where(var_11, var_15, var_9);
    // return scale                                                                           <L 256>
    return var_16;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:277
static CUDA_CALLABLE void correct_wall_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::float32 var_side,
    wp::vec_t<2, wp::float32> var_normal,
    Parameters_71195d0b var_cfg,
    wp::vec_t<3, wp::float32> & ret_0,
    wp::float32 & ret_1)
{
    //---------
    // primal vars
    const wp::float32 var_0 = 0.5;
    wp::float32 var_1;
    const wp::int32 var_2 = 0;
    wp::float32 var_3;
    const wp::int32 var_4 = 1;
    wp::float32 var_5;
    wp::vec_t<2, wp::float32> var_6;
    wp::float32 var_7;
    wp::float32 var_8;
    const wp::int32 var_9 = 2;
    wp::float32 var_10;
    wp::float32 var_11;
    wp::float32 var_12;
    const wp::float32 var_13 = 0.0;
    wp::float32 var_14;
    wp::float32* var_15;
    bool var_16;
    wp::float32 var_17;
    const wp::int32 var_18 = 2;
    wp::float32 var_19;
    wp::float32 var_20;
    wp::float32 var_21;
    const wp::float32 var_22 = 1.0;
    wp::float32* var_23;
    wp::float32 var_24;
    wp::float32 var_25;
    wp::float32 var_26;
    wp::float32 var_27;
    wp::float32* var_28;
    wp::float32 var_29;
    wp::float32 var_30;
    wp::float32 var_31;
    const wp::float32 var_32 = 1.0;
    wp::float32* var_33;
    wp::float32 var_34;
    wp::float32 var_35;
    wp::float32 var_36;
    wp::float32 var_37;
    wp::float32* var_38;
    wp::float32 var_39;
    wp::float32 var_40;
    wp::float32 var_41;
    wp::float32 var_42;
    const wp::int32 var_43 = 0;
    wp::float32 var_44;
    wp::float32 var_45;
    wp::float32 var_46;
    const wp::int32 var_47 = 1;
    wp::float32 var_48;
    wp::float32 var_49;
    wp::vec_t<3, wp::float32> var_50;
    wp::vec_t<3, wp::float32> var_51;
    wp::float32 var_52;
    wp::float32 var_53;
    wp::vec_t<3, wp::float32> var_54;
    wp::float32 var_55;
    //---------
    // forward
    // def correct_wall(p: wp.vec3, side: float, normal: wp.vec2, cfg: Parameters):           <L 278>
    // gap = 0.5 * side - wp.dot(wp.vec2(p[0], p[1]), normal) - support(p[2], normal)         <L 279>
    var_1 = wp::mul(var_0, var_side);
    var_3 = wp::extract(var_p, var_2);
    var_5 = wp::extract(var_p, var_4);
    var_6 = wp::vec_t<2, wp::float32>(var_3, var_5);
    var_7 = wp::dot(var_6, var_normal);
    var_8 = wp::sub(var_1, var_7);
    var_10 = wp::extract(var_p, var_9);
    var_11 = support_1(var_10, var_normal);
    var_12 = wp::sub(var_8, var_11);
    // motion = float(0.0)                                                                    <L 280>
    var_14 = wp::float(var_13);
    // if gap < cfg.guard:                                                                    <L 281>
    var_15 = &((var_cfg).guard);
    var_17 = wp::load(var_15);
    var_16 = (var_12 < var_17);
    if (var_16) {
        // angular_gradient = -support_derivative(p[2], normal)                               <L 282>
        var_19 = wp::extract(var_p, var_18);
        var_20 = support_derivative_1(var_19, var_normal);
        var_21 = wp::neg(var_20);
        // denominator = 1.0 + cfg.rotation_mobility * angular_gradient * angular_gradient       <L 283>
        var_23 = &((var_cfg).rotation_mobility);
        var_25 = wp::load(var_23);
        var_24 = wp::mul(var_25, var_21);
        var_26 = wp::mul(var_24, var_21);
        var_27 = wp::add(var_22, var_26);
        // scale = bounded_scale((cfg.guard - gap) / denominator, 1.0,                        <L 284>
        var_28 = &((var_cfg).guard);
        var_30 = wp::load(var_28);
        var_29 = wp::sub(var_30, var_12);
        var_31 = wp::div(var_29, var_27);
        // cfg.rotation_mobility * wp.abs(angular_gradient), cfg)                             <L 285>
        var_33 = &((var_cfg).rotation_mobility);
        var_34 = wp::abs(var_21);
        var_36 = wp::load(var_33);
        var_35 = wp::mul(var_36, var_34);
        var_37 = bounded_scale_1(var_31, var_32, var_35, var_cfg);
        // dp = scale * cfg.rotation_mobility * angular_gradient                              <L 286>
        var_38 = &((var_cfg).rotation_mobility);
        var_40 = wp::load(var_38);
        var_39 = wp::mul(var_37, var_40);
        var_41 = wp::mul(var_39, var_21);
        // p = p + wp.vec3(-scale * normal[0], -scale * normal[1], dp)                        <L 287>
        var_42 = wp::neg(var_37);
        var_44 = wp::extract(var_normal, var_43);
        var_45 = wp::mul(var_42, var_44);
        var_46 = wp::neg(var_37);
        var_48 = wp::extract(var_normal, var_47);
        var_49 = wp::mul(var_46, var_48);
        var_50 = wp::vec_t<3, wp::float32>(var_45, var_49, var_41);
        var_51 = wp::add(var_p, var_50);
        // motion = wp.max(scale, wp.abs(dp))                                                 <L 288>
        var_52 = wp::abs(var_41);
        var_53 = wp::max(var_37, var_52);
    }
    var_54 = wp::where(var_16, var_51, var_p);
    var_55 = wp::where(var_16, var_53, var_14);
    // return p, motion                                                                       <L 289>
    ret_0 = var_54;
    ret_1 = var_55;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:174
static CUDA_CALLABLE void pair_constraint_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q,
    wp::float32 & ret_0,
    wp::vec_t<2, wp::float32> & ret_1,
    wp::float32 & ret_2,
    wp::float32 & ret_3)
{
    //---------
    // primal vars
    const wp::int32 var_0 = 0;
    wp::float32 var_1;
    const wp::int32 var_2 = 0;
    wp::float32 var_3;
    wp::float32 var_4;
    const wp::int32 var_5 = 1;
    wp::float32 var_6;
    const wp::int32 var_7 = 1;
    wp::float32 var_8;
    wp::float32 var_9;
    wp::vec_t<2, wp::float32> var_10;
    const wp::int32 var_11 = 2;
    wp::float32 var_12;
    wp::vec_t<2, wp::float32> var_13;
    wp::vec_t<2, wp::float32> var_14;
    const wp::int32 var_15 = 2;
    wp::float32 var_16;
    wp::vec_t<2, wp::float32> var_17;
    wp::vec_t<2, wp::float32> var_18;
    const wp::float32 var_19 = -1e+20;
    wp::float32 var_20;
    const wp::float32 var_21 = 0.0;
    const wp::float32 var_22 = 0.0;
    wp::vec_t<2, wp::float32> var_23;
    const wp::float32 var_24 = 0.0;
    wp::float32 var_25;
    const wp::float32 var_26 = 0.0;
    wp::float32 var_27;
    const wp::int32 var_28 = 0;
    wp::int32 var_29;
    const wp::int32 var_30 = 0;
    wp::vec_t<2, wp::float32> var_31;
    const wp::int32 var_32 = 1;
    bool var_33;
    wp::vec_t<2, wp::float32> var_34;
    const wp::int32 var_35 = 2;
    bool var_36;
    wp::vec_t<2, wp::float32> var_37;
    const wp::int32 var_38 = 3;
    bool var_39;
    wp::vec_t<2, wp::float32> var_40;
    wp::vec_t<2, wp::float32> var_41;
    wp::vec_t<2, wp::float32> var_42;
    wp::vec_t<2, wp::float32> var_43;
    wp::float32 var_44;
    const wp::float32 var_45 = 1.0;
    wp::float32 var_46;
    const wp::float32 var_47 = 0.0;
    bool var_48;
    const wp::float32 var_49 = -1.0;
    wp::float32 var_50;
    wp::float32 var_51;
    wp::float32 var_52;
    wp::float32 var_53;
    wp::float32 var_54;
    const wp::float32 var_55 = 0.5;
    wp::float32 var_56;
    wp::float32 var_57;
    wp::float32 var_58;
    wp::float32 var_59;
    const wp::float32 var_60 = 0.5;
    wp::float32 var_61;
    wp::float32 var_62;
    wp::float32 var_63;
    wp::float32 var_64;
    const wp::float32 var_65 = 0.5;
    wp::float32 var_66;
    wp::float32 var_67;
    wp::float32 var_68;
    wp::float32 var_69;
    wp::float32 var_70;
    wp::float32 var_71;
    const wp::float32 var_72 = 0.5;
    wp::float32 var_73;
    wp::float32 var_74;
    wp::float32 var_75;
    wp::float32 var_76;
    wp::float32 var_77;
    wp::float32 var_78;
    wp::float32 var_79;
    wp::float32 var_80;
    wp::float32 var_81;
    wp::float32 var_82;
    wp::float32 var_83;
    const wp::int32 var_84 = 1;
    wp::float32 var_85;
    wp::float32 var_86;
    const wp::int32 var_87 = 0;
    wp::float32 var_88;
    wp::vec_t<2, wp::float32> var_89;
    wp::float32 var_90;
    wp::float32 var_91;
    const wp::int32 var_92 = 2;
    bool var_93;
    wp::float32 var_94;
    wp::float32 var_95;
    wp::float32 var_96;
    wp::float32 var_97;
    const wp::float32 var_98 = 1e-06;
    wp::float32 var_99;
    bool var_100;
    wp::float32 var_101;
    wp::vec_t<2, wp::float32> var_102;
    wp::float32 var_103;
    wp::float32 var_104;
    const wp::int32 var_105 = 1;
    wp::float32 var_106;
    wp::float32 var_107;
    const wp::float32 var_108 = 1e-06;
    bool var_109;
    wp::float32 var_110;
    wp::vec_t<2, wp::float32> var_111;
    wp::vec_t<2, wp::float32> var_112;
    wp::float32 var_113;
    wp::float32 var_114;
    const wp::int32 var_115 = 1;
    wp::int32 var_116;
    wp::float32 var_117;
    wp::vec_t<2, wp::float32> var_118;
    wp::float32 var_119;
    wp::float32 var_120;
    wp::int32 var_121;
    wp::float32 var_122;
    wp::vec_t<2, wp::float32> var_123;
    wp::float32 var_124;
    wp::float32 var_125;
    wp::int32 var_126;
    const wp::int32 var_127 = 1;
    wp::vec_t<2, wp::float32> var_128;
    const wp::int32 var_129 = 1;
    bool var_130;
    wp::vec_t<2, wp::float32> var_131;
    const wp::int32 var_132 = 2;
    bool var_133;
    wp::vec_t<2, wp::float32> var_134;
    const wp::int32 var_135 = 3;
    bool var_136;
    wp::vec_t<2, wp::float32> var_137;
    wp::vec_t<2, wp::float32> var_138;
    wp::vec_t<2, wp::float32> var_139;
    wp::vec_t<2, wp::float32> var_140;
    wp::float32 var_141;
    const wp::float32 var_142 = 1.0;
    wp::float32 var_143;
    const wp::float32 var_144 = 0.0;
    bool var_145;
    const wp::float32 var_146 = -1.0;
    wp::float32 var_147;
    wp::float32 var_148;
    wp::float32 var_149;
    wp::float32 var_150;
    wp::float32 var_151;
    const wp::float32 var_152 = 0.5;
    wp::float32 var_153;
    wp::float32 var_154;
    wp::float32 var_155;
    wp::float32 var_156;
    const wp::float32 var_157 = 0.5;
    wp::float32 var_158;
    wp::float32 var_159;
    wp::float32 var_160;
    wp::float32 var_161;
    const wp::float32 var_162 = 0.5;
    wp::float32 var_163;
    wp::float32 var_164;
    wp::float32 var_165;
    wp::float32 var_166;
    wp::float32 var_167;
    wp::float32 var_168;
    const wp::float32 var_169 = 0.5;
    wp::float32 var_170;
    wp::float32 var_171;
    wp::float32 var_172;
    wp::float32 var_173;
    wp::float32 var_174;
    wp::float32 var_175;
    wp::float32 var_176;
    wp::float32 var_177;
    wp::float32 var_178;
    wp::float32 var_179;
    wp::float32 var_180;
    const wp::int32 var_181 = 1;
    wp::float32 var_182;
    wp::float32 var_183;
    const wp::int32 var_184 = 0;
    wp::float32 var_185;
    wp::vec_t<2, wp::float32> var_186;
    wp::float32 var_187;
    wp::float32 var_188;
    const wp::int32 var_189 = 2;
    bool var_190;
    wp::float32 var_191;
    wp::float32 var_192;
    wp::float32 var_193;
    wp::float32 var_194;
    const wp::float32 var_195 = 1e-06;
    wp::float32 var_196;
    bool var_197;
    wp::float32 var_198;
    wp::vec_t<2, wp::float32> var_199;
    wp::float32 var_200;
    wp::float32 var_201;
    const wp::int32 var_202 = 1;
    wp::float32 var_203;
    wp::float32 var_204;
    const wp::float32 var_205 = 1e-06;
    bool var_206;
    wp::float32 var_207;
    wp::vec_t<2, wp::float32> var_208;
    wp::vec_t<2, wp::float32> var_209;
    wp::float32 var_210;
    wp::float32 var_211;
    const wp::int32 var_212 = 1;
    wp::int32 var_213;
    wp::float32 var_214;
    wp::vec_t<2, wp::float32> var_215;
    wp::float32 var_216;
    wp::float32 var_217;
    wp::int32 var_218;
    wp::float32 var_219;
    wp::vec_t<2, wp::float32> var_220;
    wp::float32 var_221;
    wp::float32 var_222;
    wp::int32 var_223;
    const wp::int32 var_224 = 2;
    wp::vec_t<2, wp::float32> var_225;
    const wp::int32 var_226 = 1;
    bool var_227;
    wp::vec_t<2, wp::float32> var_228;
    const wp::int32 var_229 = 2;
    bool var_230;
    wp::vec_t<2, wp::float32> var_231;
    const wp::int32 var_232 = 3;
    bool var_233;
    wp::vec_t<2, wp::float32> var_234;
    wp::vec_t<2, wp::float32> var_235;
    wp::vec_t<2, wp::float32> var_236;
    wp::vec_t<2, wp::float32> var_237;
    wp::float32 var_238;
    const wp::float32 var_239 = 1.0;
    wp::float32 var_240;
    const wp::float32 var_241 = 0.0;
    bool var_242;
    const wp::float32 var_243 = -1.0;
    wp::float32 var_244;
    wp::float32 var_245;
    wp::float32 var_246;
    wp::float32 var_247;
    wp::float32 var_248;
    const wp::float32 var_249 = 0.5;
    wp::float32 var_250;
    wp::float32 var_251;
    wp::float32 var_252;
    wp::float32 var_253;
    const wp::float32 var_254 = 0.5;
    wp::float32 var_255;
    wp::float32 var_256;
    wp::float32 var_257;
    wp::float32 var_258;
    const wp::float32 var_259 = 0.5;
    wp::float32 var_260;
    wp::float32 var_261;
    wp::float32 var_262;
    wp::float32 var_263;
    wp::float32 var_264;
    wp::float32 var_265;
    const wp::float32 var_266 = 0.5;
    wp::float32 var_267;
    wp::float32 var_268;
    wp::float32 var_269;
    wp::float32 var_270;
    wp::float32 var_271;
    wp::float32 var_272;
    wp::float32 var_273;
    wp::float32 var_274;
    wp::float32 var_275;
    wp::float32 var_276;
    wp::float32 var_277;
    const wp::int32 var_278 = 1;
    wp::float32 var_279;
    wp::float32 var_280;
    const wp::int32 var_281 = 0;
    wp::float32 var_282;
    wp::vec_t<2, wp::float32> var_283;
    wp::float32 var_284;
    wp::float32 var_285;
    const wp::int32 var_286 = 2;
    bool var_287;
    wp::float32 var_288;
    wp::float32 var_289;
    wp::float32 var_290;
    wp::float32 var_291;
    const wp::float32 var_292 = 1e-06;
    wp::float32 var_293;
    bool var_294;
    wp::float32 var_295;
    wp::vec_t<2, wp::float32> var_296;
    wp::float32 var_297;
    wp::float32 var_298;
    const wp::int32 var_299 = 1;
    wp::float32 var_300;
    wp::float32 var_301;
    const wp::float32 var_302 = 1e-06;
    bool var_303;
    wp::float32 var_304;
    wp::vec_t<2, wp::float32> var_305;
    wp::vec_t<2, wp::float32> var_306;
    wp::float32 var_307;
    wp::float32 var_308;
    const wp::int32 var_309 = 1;
    wp::int32 var_310;
    wp::float32 var_311;
    wp::vec_t<2, wp::float32> var_312;
    wp::float32 var_313;
    wp::float32 var_314;
    wp::int32 var_315;
    wp::float32 var_316;
    wp::vec_t<2, wp::float32> var_317;
    wp::float32 var_318;
    wp::float32 var_319;
    wp::int32 var_320;
    const wp::int32 var_321 = 3;
    wp::vec_t<2, wp::float32> var_322;
    const wp::int32 var_323 = 1;
    bool var_324;
    wp::vec_t<2, wp::float32> var_325;
    const wp::int32 var_326 = 2;
    bool var_327;
    wp::vec_t<2, wp::float32> var_328;
    const wp::int32 var_329 = 3;
    bool var_330;
    wp::vec_t<2, wp::float32> var_331;
    wp::vec_t<2, wp::float32> var_332;
    wp::vec_t<2, wp::float32> var_333;
    wp::vec_t<2, wp::float32> var_334;
    wp::float32 var_335;
    const wp::float32 var_336 = 1.0;
    wp::float32 var_337;
    const wp::float32 var_338 = 0.0;
    bool var_339;
    const wp::float32 var_340 = -1.0;
    wp::float32 var_341;
    wp::float32 var_342;
    wp::float32 var_343;
    wp::float32 var_344;
    wp::float32 var_345;
    const wp::float32 var_346 = 0.5;
    wp::float32 var_347;
    wp::float32 var_348;
    wp::float32 var_349;
    wp::float32 var_350;
    const wp::float32 var_351 = 0.5;
    wp::float32 var_352;
    wp::float32 var_353;
    wp::float32 var_354;
    wp::float32 var_355;
    const wp::float32 var_356 = 0.5;
    wp::float32 var_357;
    wp::float32 var_358;
    wp::float32 var_359;
    wp::float32 var_360;
    wp::float32 var_361;
    wp::float32 var_362;
    const wp::float32 var_363 = 0.5;
    wp::float32 var_364;
    wp::float32 var_365;
    wp::float32 var_366;
    wp::float32 var_367;
    wp::float32 var_368;
    wp::float32 var_369;
    wp::float32 var_370;
    wp::float32 var_371;
    wp::float32 var_372;
    wp::float32 var_373;
    wp::float32 var_374;
    const wp::int32 var_375 = 1;
    wp::float32 var_376;
    wp::float32 var_377;
    const wp::int32 var_378 = 0;
    wp::float32 var_379;
    wp::vec_t<2, wp::float32> var_380;
    wp::float32 var_381;
    wp::float32 var_382;
    const wp::int32 var_383 = 2;
    bool var_384;
    wp::float32 var_385;
    wp::float32 var_386;
    wp::float32 var_387;
    wp::float32 var_388;
    const wp::float32 var_389 = 1e-06;
    wp::float32 var_390;
    bool var_391;
    wp::float32 var_392;
    wp::vec_t<2, wp::float32> var_393;
    wp::float32 var_394;
    wp::float32 var_395;
    const wp::int32 var_396 = 1;
    wp::float32 var_397;
    wp::float32 var_398;
    const wp::float32 var_399 = 1e-06;
    bool var_400;
    wp::float32 var_401;
    wp::vec_t<2, wp::float32> var_402;
    wp::vec_t<2, wp::float32> var_403;
    wp::float32 var_404;
    wp::float32 var_405;
    const wp::int32 var_406 = 1;
    wp::int32 var_407;
    wp::float32 var_408;
    wp::vec_t<2, wp::float32> var_409;
    wp::float32 var_410;
    wp::float32 var_411;
    wp::int32 var_412;
    wp::float32 var_413;
    wp::vec_t<2, wp::float32> var_414;
    wp::float32 var_415;
    wp::float32 var_416;
    wp::int32 var_417;
    wp::float32 var_418;
    wp::vec_t<2, wp::float32> var_419;
    wp::float32 var_420;
    wp::float32 var_421;
    wp::float32 var_422;
    wp::float32 var_423;
    //---------
    // forward
    // def pair_constraint(p: wp.vec3, q: wp.vec3):                                           <L 175>
    // d = wp.vec2(q[0] - p[0], q[1] - p[1])                                                  <L 178>
    var_1 = wp::extract(var_q, var_0);
    var_3 = wp::extract(var_p, var_2);
    var_4 = wp::sub(var_1, var_3);
    var_6 = wp::extract(var_q, var_5);
    var_8 = wp::extract(var_p, var_7);
    var_9 = wp::sub(var_6, var_8);
    var_10 = wp::vec_t<2, wp::float32>(var_4, var_9);
    // up, vp = axes(p[2])                                                                    <L 179>
    var_12 = wp::extract(var_p, var_11);
    axes_1(var_12, var_13, var_14);
    // uq, vq = axes(q[2])                                                                    <L 180>
    var_16 = wp::extract(var_q, var_15);
    axes_1(var_16, var_17, var_18);
    // best = float(-1.0e20)                                                                  <L 181>
    var_20 = wp::float(var_19);
    // center_gradient = wp.vec2(0.0, 0.0)                                                    <L 182>
    var_23 = wp::vec_t<2, wp::float32>(var_21, var_22);
    // gp = float(0.0)                                                                        <L 183>
    var_25 = wp::float(var_24);
    // gq = float(0.0)                                                                        <L 184>
    var_27 = wp::float(var_26);
    // count = int(0)                                                                         <L 185>
    var_29 = wp::int(var_28);
    // for k in range(4):                                                                     <L 186>
    // a = up                                                                                 <L 187>
    var_31 = wp::copy(var_13);
    // if k == 1:                                                                             <L 188>
    var_33 = (var_30 == var_32);
    if (var_33) {
        // a = vp                                                                             <L 189>
        var_34 = wp::copy(var_14);
    }
    if (!var_33) {
        // elif k == 2:                                                                       <L 190>
        var_36 = (var_30 == var_35);
        if (var_36) {
            // a = uq                                                                         <L 191>
            var_37 = wp::copy(var_17);
        }
        if (!var_36) {
            // elif k == 3:                                                                   <L 192>
            var_39 = (var_30 == var_38);
            if (var_39) {
                // a = vq                                                                     <L 193>
                var_40 = wp::copy(var_18);
            }
            var_41 = wp::where(var_39, var_40, var_31);
        }
        var_42 = wp::where(var_36, var_37, var_41);
    }
    var_43 = wp::where(var_33, var_34, var_42);
    // dot = wp.dot(d, a)                                                                     <L 194>
    var_44 = wp::dot(var_10, var_43);
    // direction = float(1.0)                                                                 <L 195>
    var_46 = wp::float(var_45);
    // if dot < 0.0:                                                                          <L 196>
    var_48 = (var_44 < var_47);
    if (var_48) {
        // direction = -1.0                                                                   <L 197>
    }
    var_50 = wp::where(var_48, var_49, var_46);
    // pu = wp.dot(up, a)                                                                     <L 198>
    var_51 = wp::dot(var_13, var_43);
    // pv = wp.dot(vp, a)                                                                     <L 199>
    var_52 = wp::dot(var_14, var_43);
    // qu = wp.dot(uq, a)                                                                     <L 200>
    var_53 = wp::dot(var_17, var_43);
    // qv = wp.dot(vq, a)                                                                     <L 201>
    var_54 = wp::dot(var_18, var_43);
    // hp = 0.5 * (wp.abs(pu) + wp.abs(pv))                                                   <L 202>
    var_56 = wp::abs(var_51);
    var_57 = wp::abs(var_52);
    var_58 = wp::add(var_56, var_57);
    var_59 = wp::mul(var_55, var_58);
    // hq = 0.5 * (wp.abs(qu) + wp.abs(qv))                                                   <L 203>
    var_61 = wp::abs(var_53);
    var_62 = wp::abs(var_54);
    var_63 = wp::add(var_61, var_62);
    var_64 = wp::mul(var_60, var_63);
    // dhp = 0.5 * (sign_symmetric(pu) * pv - sign_symmetric(pv) * pu)                        <L 204>
    var_66 = sign_symmetric_1(var_51);
    var_67 = wp::mul(var_66, var_52);
    var_68 = sign_symmetric_1(var_52);
    var_69 = wp::mul(var_68, var_51);
    var_70 = wp::sub(var_67, var_69);
    var_71 = wp::mul(var_65, var_70);
    // dhq = 0.5 * (sign_symmetric(qu) * qv - sign_symmetric(qv) * qu)                        <L 205>
    var_73 = sign_symmetric_1(var_53);
    var_74 = wp::mul(var_73, var_54);
    var_75 = sign_symmetric_1(var_54);
    var_76 = wp::mul(var_75, var_53);
    var_77 = wp::sub(var_74, var_76);
    var_78 = wp::mul(var_72, var_77);
    // gap = wp.abs(dot) - hp - hq                                                            <L 206>
    var_79 = wp::abs(var_44);
    var_80 = wp::sub(var_79, var_59);
    var_81 = wp::sub(var_80, var_64);
    // dp = -dhp                                                                              <L 207>
    var_82 = wp::neg(var_71);
    // dq = -dhq                                                                              <L 208>
    var_83 = wp::neg(var_78);
    // da = direction * wp.dot(d, wp.vec2(-a[1], a[0]))                                       <L 209>
    var_85 = wp::extract(var_43, var_84);
    var_86 = wp::neg(var_85);
    var_88 = wp::extract(var_43, var_87);
    var_89 = wp::vec_t<2, wp::float32>(var_86, var_88);
    var_90 = wp::dot(var_10, var_89);
    var_91 = wp::mul(var_50, var_90);
    // if k < 2:                                                                              <L 210>
    var_93 = (var_30 < var_92);
    if (var_93) {
        // dp = da + dhq                                                                      <L 211>
        var_94 = wp::add(var_91, var_78);
    }
    if (!var_93) {
        // dq = da + dhp                                                                      <L 213>
        var_95 = wp::add(var_91, var_71);
    }
    var_96 = wp::where(var_93, var_94, var_82);
    var_97 = wp::where(var_93, var_83, var_95);
    // if gap > best + 0.000001:                                                              <L 214>
    var_99 = wp::add(var_20, var_98);
    var_100 = (var_81 > var_99);
    if (var_100) {
        // best = gap                                                                         <L 215>
        var_101 = wp::copy(var_81);
        // center_gradient = direction * a                                                    <L 216>
        var_102 = wp::mul(var_50, var_43);
        // gp = dp                                                                            <L 217>
        var_103 = wp::copy(var_96);
        // gq = dq                                                                            <L 218>
        var_104 = wp::copy(var_97);
        // count = 1                                                                          <L 219>
    }
    if (!var_100) {
        // elif wp.abs(gap - best) <= 0.000001:                                               <L 220>
        var_106 = wp::sub(var_81, var_20);
        var_107 = wp::abs(var_106);
        var_109 = (var_107 <= var_108);
        if (var_109) {
            // best = wp.max(best, gap)                                                       <L 221>
            var_110 = wp::max(var_20, var_81);
            // center_gradient += direction * a                                               <L 222>
            var_111 = wp::mul(var_50, var_43);
            var_112 = wp::add(var_23, var_111);
            // gp += dp                                                                       <L 223>
            var_113 = wp::add(var_25, var_96);
            // gq += dq                                                                       <L 224>
            var_114 = wp::add(var_27, var_97);
            // count += 1                                                                     <L 225>
            var_116 = wp::add(var_29, var_115);
        }
        var_117 = wp::where(var_109, var_110, var_20);
        var_118 = wp::where(var_109, var_112, var_23);
        var_119 = wp::where(var_109, var_113, var_25);
        var_120 = wp::where(var_109, var_114, var_27);
        var_121 = wp::where(var_109, var_116, var_29);
    }
    var_122 = wp::where(var_100, var_101, var_117);
    var_123 = wp::where(var_100, var_102, var_118);
    var_124 = wp::where(var_100, var_103, var_119);
    var_125 = wp::where(var_100, var_104, var_120);
    var_126 = wp::where(var_100, var_105, var_121);
    // a = up                                                                                 <L 187>
    var_128 = wp::copy(var_13);
    // if k == 1:                                                                             <L 188>
    var_130 = (var_127 == var_129);
    if (var_130) {
        // a = vp                                                                             <L 189>
        var_131 = wp::copy(var_14);
    }
    if (!var_130) {
        // elif k == 2:                                                                       <L 190>
        var_133 = (var_127 == var_132);
        if (var_133) {
            // a = uq                                                                         <L 191>
            var_134 = wp::copy(var_17);
        }
        if (!var_133) {
            // elif k == 3:                                                                   <L 192>
            var_136 = (var_127 == var_135);
            if (var_136) {
                // a = vq                                                                     <L 193>
                var_137 = wp::copy(var_18);
            }
            var_138 = wp::where(var_136, var_137, var_128);
        }
        var_139 = wp::where(var_133, var_134, var_138);
    }
    var_140 = wp::where(var_130, var_131, var_139);
    // dot = wp.dot(d, a)                                                                     <L 194>
    var_141 = wp::dot(var_10, var_140);
    // direction = float(1.0)                                                                 <L 195>
    var_143 = wp::float(var_142);
    // if dot < 0.0:                                                                          <L 196>
    var_145 = (var_141 < var_144);
    if (var_145) {
        // direction = -1.0                                                                   <L 197>
    }
    var_147 = wp::where(var_145, var_146, var_143);
    // pu = wp.dot(up, a)                                                                     <L 198>
    var_148 = wp::dot(var_13, var_140);
    // pv = wp.dot(vp, a)                                                                     <L 199>
    var_149 = wp::dot(var_14, var_140);
    // qu = wp.dot(uq, a)                                                                     <L 200>
    var_150 = wp::dot(var_17, var_140);
    // qv = wp.dot(vq, a)                                                                     <L 201>
    var_151 = wp::dot(var_18, var_140);
    // hp = 0.5 * (wp.abs(pu) + wp.abs(pv))                                                   <L 202>
    var_153 = wp::abs(var_148);
    var_154 = wp::abs(var_149);
    var_155 = wp::add(var_153, var_154);
    var_156 = wp::mul(var_152, var_155);
    // hq = 0.5 * (wp.abs(qu) + wp.abs(qv))                                                   <L 203>
    var_158 = wp::abs(var_150);
    var_159 = wp::abs(var_151);
    var_160 = wp::add(var_158, var_159);
    var_161 = wp::mul(var_157, var_160);
    // dhp = 0.5 * (sign_symmetric(pu) * pv - sign_symmetric(pv) * pu)                        <L 204>
    var_163 = sign_symmetric_1(var_148);
    var_164 = wp::mul(var_163, var_149);
    var_165 = sign_symmetric_1(var_149);
    var_166 = wp::mul(var_165, var_148);
    var_167 = wp::sub(var_164, var_166);
    var_168 = wp::mul(var_162, var_167);
    // dhq = 0.5 * (sign_symmetric(qu) * qv - sign_symmetric(qv) * qu)                        <L 205>
    var_170 = sign_symmetric_1(var_150);
    var_171 = wp::mul(var_170, var_151);
    var_172 = sign_symmetric_1(var_151);
    var_173 = wp::mul(var_172, var_150);
    var_174 = wp::sub(var_171, var_173);
    var_175 = wp::mul(var_169, var_174);
    // gap = wp.abs(dot) - hp - hq                                                            <L 206>
    var_176 = wp::abs(var_141);
    var_177 = wp::sub(var_176, var_156);
    var_178 = wp::sub(var_177, var_161);
    // dp = -dhp                                                                              <L 207>
    var_179 = wp::neg(var_168);
    // dq = -dhq                                                                              <L 208>
    var_180 = wp::neg(var_175);
    // da = direction * wp.dot(d, wp.vec2(-a[1], a[0]))                                       <L 209>
    var_182 = wp::extract(var_140, var_181);
    var_183 = wp::neg(var_182);
    var_185 = wp::extract(var_140, var_184);
    var_186 = wp::vec_t<2, wp::float32>(var_183, var_185);
    var_187 = wp::dot(var_10, var_186);
    var_188 = wp::mul(var_147, var_187);
    // if k < 2:                                                                              <L 210>
    var_190 = (var_127 < var_189);
    if (var_190) {
        // dp = da + dhq                                                                      <L 211>
        var_191 = wp::add(var_188, var_175);
    }
    if (!var_190) {
        // dq = da + dhp                                                                      <L 213>
        var_192 = wp::add(var_188, var_168);
    }
    var_193 = wp::where(var_190, var_191, var_179);
    var_194 = wp::where(var_190, var_180, var_192);
    // if gap > best + 0.000001:                                                              <L 214>
    var_196 = wp::add(var_122, var_195);
    var_197 = (var_178 > var_196);
    if (var_197) {
        // best = gap                                                                         <L 215>
        var_198 = wp::copy(var_178);
        // center_gradient = direction * a                                                    <L 216>
        var_199 = wp::mul(var_147, var_140);
        // gp = dp                                                                            <L 217>
        var_200 = wp::copy(var_193);
        // gq = dq                                                                            <L 218>
        var_201 = wp::copy(var_194);
        // count = 1                                                                          <L 219>
    }
    if (!var_197) {
        // elif wp.abs(gap - best) <= 0.000001:                                               <L 220>
        var_203 = wp::sub(var_178, var_122);
        var_204 = wp::abs(var_203);
        var_206 = (var_204 <= var_205);
        if (var_206) {
            // best = wp.max(best, gap)                                                       <L 221>
            var_207 = wp::max(var_122, var_178);
            // center_gradient += direction * a                                               <L 222>
            var_208 = wp::mul(var_147, var_140);
            var_209 = wp::add(var_123, var_208);
            // gp += dp                                                                       <L 223>
            var_210 = wp::add(var_124, var_193);
            // gq += dq                                                                       <L 224>
            var_211 = wp::add(var_125, var_194);
            // count += 1                                                                     <L 225>
            var_213 = wp::add(var_126, var_212);
        }
        var_214 = wp::where(var_206, var_207, var_122);
        var_215 = wp::where(var_206, var_209, var_123);
        var_216 = wp::where(var_206, var_210, var_124);
        var_217 = wp::where(var_206, var_211, var_125);
        var_218 = wp::where(var_206, var_213, var_126);
    }
    var_219 = wp::where(var_197, var_198, var_214);
    var_220 = wp::where(var_197, var_199, var_215);
    var_221 = wp::where(var_197, var_200, var_216);
    var_222 = wp::where(var_197, var_201, var_217);
    var_223 = wp::where(var_197, var_202, var_218);
    // a = up                                                                                 <L 187>
    var_225 = wp::copy(var_13);
    // if k == 1:                                                                             <L 188>
    var_227 = (var_224 == var_226);
    if (var_227) {
        // a = vp                                                                             <L 189>
        var_228 = wp::copy(var_14);
    }
    if (!var_227) {
        // elif k == 2:                                                                       <L 190>
        var_230 = (var_224 == var_229);
        if (var_230) {
            // a = uq                                                                         <L 191>
            var_231 = wp::copy(var_17);
        }
        if (!var_230) {
            // elif k == 3:                                                                   <L 192>
            var_233 = (var_224 == var_232);
            if (var_233) {
                // a = vq                                                                     <L 193>
                var_234 = wp::copy(var_18);
            }
            var_235 = wp::where(var_233, var_234, var_225);
        }
        var_236 = wp::where(var_230, var_231, var_235);
    }
    var_237 = wp::where(var_227, var_228, var_236);
    // dot = wp.dot(d, a)                                                                     <L 194>
    var_238 = wp::dot(var_10, var_237);
    // direction = float(1.0)                                                                 <L 195>
    var_240 = wp::float(var_239);
    // if dot < 0.0:                                                                          <L 196>
    var_242 = (var_238 < var_241);
    if (var_242) {
        // direction = -1.0                                                                   <L 197>
    }
    var_244 = wp::where(var_242, var_243, var_240);
    // pu = wp.dot(up, a)                                                                     <L 198>
    var_245 = wp::dot(var_13, var_237);
    // pv = wp.dot(vp, a)                                                                     <L 199>
    var_246 = wp::dot(var_14, var_237);
    // qu = wp.dot(uq, a)                                                                     <L 200>
    var_247 = wp::dot(var_17, var_237);
    // qv = wp.dot(vq, a)                                                                     <L 201>
    var_248 = wp::dot(var_18, var_237);
    // hp = 0.5 * (wp.abs(pu) + wp.abs(pv))                                                   <L 202>
    var_250 = wp::abs(var_245);
    var_251 = wp::abs(var_246);
    var_252 = wp::add(var_250, var_251);
    var_253 = wp::mul(var_249, var_252);
    // hq = 0.5 * (wp.abs(qu) + wp.abs(qv))                                                   <L 203>
    var_255 = wp::abs(var_247);
    var_256 = wp::abs(var_248);
    var_257 = wp::add(var_255, var_256);
    var_258 = wp::mul(var_254, var_257);
    // dhp = 0.5 * (sign_symmetric(pu) * pv - sign_symmetric(pv) * pu)                        <L 204>
    var_260 = sign_symmetric_1(var_245);
    var_261 = wp::mul(var_260, var_246);
    var_262 = sign_symmetric_1(var_246);
    var_263 = wp::mul(var_262, var_245);
    var_264 = wp::sub(var_261, var_263);
    var_265 = wp::mul(var_259, var_264);
    // dhq = 0.5 * (sign_symmetric(qu) * qv - sign_symmetric(qv) * qu)                        <L 205>
    var_267 = sign_symmetric_1(var_247);
    var_268 = wp::mul(var_267, var_248);
    var_269 = sign_symmetric_1(var_248);
    var_270 = wp::mul(var_269, var_247);
    var_271 = wp::sub(var_268, var_270);
    var_272 = wp::mul(var_266, var_271);
    // gap = wp.abs(dot) - hp - hq                                                            <L 206>
    var_273 = wp::abs(var_238);
    var_274 = wp::sub(var_273, var_253);
    var_275 = wp::sub(var_274, var_258);
    // dp = -dhp                                                                              <L 207>
    var_276 = wp::neg(var_265);
    // dq = -dhq                                                                              <L 208>
    var_277 = wp::neg(var_272);
    // da = direction * wp.dot(d, wp.vec2(-a[1], a[0]))                                       <L 209>
    var_279 = wp::extract(var_237, var_278);
    var_280 = wp::neg(var_279);
    var_282 = wp::extract(var_237, var_281);
    var_283 = wp::vec_t<2, wp::float32>(var_280, var_282);
    var_284 = wp::dot(var_10, var_283);
    var_285 = wp::mul(var_244, var_284);
    // if k < 2:                                                                              <L 210>
    var_287 = (var_224 < var_286);
    if (var_287) {
        // dp = da + dhq                                                                      <L 211>
        var_288 = wp::add(var_285, var_272);
    }
    if (!var_287) {
        // dq = da + dhp                                                                      <L 213>
        var_289 = wp::add(var_285, var_265);
    }
    var_290 = wp::where(var_287, var_288, var_276);
    var_291 = wp::where(var_287, var_277, var_289);
    // if gap > best + 0.000001:                                                              <L 214>
    var_293 = wp::add(var_219, var_292);
    var_294 = (var_275 > var_293);
    if (var_294) {
        // best = gap                                                                         <L 215>
        var_295 = wp::copy(var_275);
        // center_gradient = direction * a                                                    <L 216>
        var_296 = wp::mul(var_244, var_237);
        // gp = dp                                                                            <L 217>
        var_297 = wp::copy(var_290);
        // gq = dq                                                                            <L 218>
        var_298 = wp::copy(var_291);
        // count = 1                                                                          <L 219>
    }
    if (!var_294) {
        // elif wp.abs(gap - best) <= 0.000001:                                               <L 220>
        var_300 = wp::sub(var_275, var_219);
        var_301 = wp::abs(var_300);
        var_303 = (var_301 <= var_302);
        if (var_303) {
            // best = wp.max(best, gap)                                                       <L 221>
            var_304 = wp::max(var_219, var_275);
            // center_gradient += direction * a                                               <L 222>
            var_305 = wp::mul(var_244, var_237);
            var_306 = wp::add(var_220, var_305);
            // gp += dp                                                                       <L 223>
            var_307 = wp::add(var_221, var_290);
            // gq += dq                                                                       <L 224>
            var_308 = wp::add(var_222, var_291);
            // count += 1                                                                     <L 225>
            var_310 = wp::add(var_223, var_309);
        }
        var_311 = wp::where(var_303, var_304, var_219);
        var_312 = wp::where(var_303, var_306, var_220);
        var_313 = wp::where(var_303, var_307, var_221);
        var_314 = wp::where(var_303, var_308, var_222);
        var_315 = wp::where(var_303, var_310, var_223);
    }
    var_316 = wp::where(var_294, var_295, var_311);
    var_317 = wp::where(var_294, var_296, var_312);
    var_318 = wp::where(var_294, var_297, var_313);
    var_319 = wp::where(var_294, var_298, var_314);
    var_320 = wp::where(var_294, var_299, var_315);
    // a = up                                                                                 <L 187>
    var_322 = wp::copy(var_13);
    // if k == 1:                                                                             <L 188>
    var_324 = (var_321 == var_323);
    if (var_324) {
        // a = vp                                                                             <L 189>
        var_325 = wp::copy(var_14);
    }
    if (!var_324) {
        // elif k == 2:                                                                       <L 190>
        var_327 = (var_321 == var_326);
        if (var_327) {
            // a = uq                                                                         <L 191>
            var_328 = wp::copy(var_17);
        }
        if (!var_327) {
            // elif k == 3:                                                                   <L 192>
            var_330 = (var_321 == var_329);
            if (var_330) {
                // a = vq                                                                     <L 193>
                var_331 = wp::copy(var_18);
            }
            var_332 = wp::where(var_330, var_331, var_322);
        }
        var_333 = wp::where(var_327, var_328, var_332);
    }
    var_334 = wp::where(var_324, var_325, var_333);
    // dot = wp.dot(d, a)                                                                     <L 194>
    var_335 = wp::dot(var_10, var_334);
    // direction = float(1.0)                                                                 <L 195>
    var_337 = wp::float(var_336);
    // if dot < 0.0:                                                                          <L 196>
    var_339 = (var_335 < var_338);
    if (var_339) {
        // direction = -1.0                                                                   <L 197>
    }
    var_341 = wp::where(var_339, var_340, var_337);
    // pu = wp.dot(up, a)                                                                     <L 198>
    var_342 = wp::dot(var_13, var_334);
    // pv = wp.dot(vp, a)                                                                     <L 199>
    var_343 = wp::dot(var_14, var_334);
    // qu = wp.dot(uq, a)                                                                     <L 200>
    var_344 = wp::dot(var_17, var_334);
    // qv = wp.dot(vq, a)                                                                     <L 201>
    var_345 = wp::dot(var_18, var_334);
    // hp = 0.5 * (wp.abs(pu) + wp.abs(pv))                                                   <L 202>
    var_347 = wp::abs(var_342);
    var_348 = wp::abs(var_343);
    var_349 = wp::add(var_347, var_348);
    var_350 = wp::mul(var_346, var_349);
    // hq = 0.5 * (wp.abs(qu) + wp.abs(qv))                                                   <L 203>
    var_352 = wp::abs(var_344);
    var_353 = wp::abs(var_345);
    var_354 = wp::add(var_352, var_353);
    var_355 = wp::mul(var_351, var_354);
    // dhp = 0.5 * (sign_symmetric(pu) * pv - sign_symmetric(pv) * pu)                        <L 204>
    var_357 = sign_symmetric_1(var_342);
    var_358 = wp::mul(var_357, var_343);
    var_359 = sign_symmetric_1(var_343);
    var_360 = wp::mul(var_359, var_342);
    var_361 = wp::sub(var_358, var_360);
    var_362 = wp::mul(var_356, var_361);
    // dhq = 0.5 * (sign_symmetric(qu) * qv - sign_symmetric(qv) * qu)                        <L 205>
    var_364 = sign_symmetric_1(var_344);
    var_365 = wp::mul(var_364, var_345);
    var_366 = sign_symmetric_1(var_345);
    var_367 = wp::mul(var_366, var_344);
    var_368 = wp::sub(var_365, var_367);
    var_369 = wp::mul(var_363, var_368);
    // gap = wp.abs(dot) - hp - hq                                                            <L 206>
    var_370 = wp::abs(var_335);
    var_371 = wp::sub(var_370, var_350);
    var_372 = wp::sub(var_371, var_355);
    // dp = -dhp                                                                              <L 207>
    var_373 = wp::neg(var_362);
    // dq = -dhq                                                                              <L 208>
    var_374 = wp::neg(var_369);
    // da = direction * wp.dot(d, wp.vec2(-a[1], a[0]))                                       <L 209>
    var_376 = wp::extract(var_334, var_375);
    var_377 = wp::neg(var_376);
    var_379 = wp::extract(var_334, var_378);
    var_380 = wp::vec_t<2, wp::float32>(var_377, var_379);
    var_381 = wp::dot(var_10, var_380);
    var_382 = wp::mul(var_341, var_381);
    // if k < 2:                                                                              <L 210>
    var_384 = (var_321 < var_383);
    if (var_384) {
        // dp = da + dhq                                                                      <L 211>
        var_385 = wp::add(var_382, var_369);
    }
    if (!var_384) {
        // dq = da + dhp                                                                      <L 213>
        var_386 = wp::add(var_382, var_362);
    }
    var_387 = wp::where(var_384, var_385, var_373);
    var_388 = wp::where(var_384, var_374, var_386);
    // if gap > best + 0.000001:                                                              <L 214>
    var_390 = wp::add(var_316, var_389);
    var_391 = (var_372 > var_390);
    if (var_391) {
        // best = gap                                                                         <L 215>
        var_392 = wp::copy(var_372);
        // center_gradient = direction * a                                                    <L 216>
        var_393 = wp::mul(var_341, var_334);
        // gp = dp                                                                            <L 217>
        var_394 = wp::copy(var_387);
        // gq = dq                                                                            <L 218>
        var_395 = wp::copy(var_388);
        // count = 1                                                                          <L 219>
    }
    if (!var_391) {
        // elif wp.abs(gap - best) <= 0.000001:                                               <L 220>
        var_397 = wp::sub(var_372, var_316);
        var_398 = wp::abs(var_397);
        var_400 = (var_398 <= var_399);
        if (var_400) {
            // best = wp.max(best, gap)                                                       <L 221>
            var_401 = wp::max(var_316, var_372);
            // center_gradient += direction * a                                               <L 222>
            var_402 = wp::mul(var_341, var_334);
            var_403 = wp::add(var_317, var_402);
            // gp += dp                                                                       <L 223>
            var_404 = wp::add(var_318, var_387);
            // gq += dq                                                                       <L 224>
            var_405 = wp::add(var_319, var_388);
            // count += 1                                                                     <L 225>
            var_407 = wp::add(var_320, var_406);
        }
        var_408 = wp::where(var_400, var_401, var_316);
        var_409 = wp::where(var_400, var_403, var_317);
        var_410 = wp::where(var_400, var_404, var_318);
        var_411 = wp::where(var_400, var_405, var_319);
        var_412 = wp::where(var_400, var_407, var_320);
    }
    var_413 = wp::where(var_391, var_392, var_408);
    var_414 = wp::where(var_391, var_393, var_409);
    var_415 = wp::where(var_391, var_394, var_410);
    var_416 = wp::where(var_391, var_395, var_411);
    var_417 = wp::where(var_391, var_396, var_412);
    // return best, center_gradient / float(count), gp / float(count), gq / float(count)       <L 226>
    var_418 = wp::float(var_417);
    var_419 = wp::div(var_414, var_418);
    var_420 = wp::float(var_417);
    var_421 = wp::div(var_415, var_420);
    var_422 = wp::float(var_417);
    var_423 = wp::div(var_416, var_422);
    ret_0 = var_413;
    ret_1 = var_419;
    ret_2 = var_421;
    ret_3 = var_423;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:259
static CUDA_CALLABLE void correct_pair_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q,
    Parameters_71195d0b var_cfg,
    wp::vec_t<3, wp::float32> & ret_0,
    wp::vec_t<3, wp::float32> & ret_1,
    wp::float32 & ret_2)
{
    //---------
    // primal vars
    wp::float32 var_0;
    wp::vec_t<2, wp::float32> var_1;
    wp::float32 var_2;
    wp::float32 var_3;
    const wp::float32 var_4 = 0.0;
    wp::float32 var_5;
    wp::float32* var_6;
    bool var_7;
    wp::float32 var_8;
    const wp::float32 var_9 = 2.0;
    wp::float32 var_10;
    wp::float32 var_11;
    wp::float32* var_12;
    wp::float32 var_13;
    wp::float32 var_14;
    wp::float32 var_15;
    wp::float32 var_16;
    wp::float32 var_17;
    wp::float32 var_18;
    const wp::float32 var_19 = 1e-08;
    bool var_20;
    wp::float32* var_21;
    wp::float32 var_22;
    wp::float32 var_23;
    wp::float32 var_24;
    wp::float32 var_25;
    wp::float32 var_26;
    wp::float32* var_27;
    wp::float32 var_28;
    wp::float32 var_29;
    wp::float32 var_30;
    wp::float32 var_31;
    wp::float32 var_32;
    wp::vec_t<2, wp::float32> var_33;
    wp::float32* var_34;
    wp::float32 var_35;
    wp::float32 var_36;
    wp::float32 var_37;
    wp::float32* var_38;
    wp::float32 var_39;
    wp::float32 var_40;
    wp::float32 var_41;
    const wp::int32 var_42 = 0;
    wp::float32 var_43;
    wp::float32 var_44;
    const wp::int32 var_45 = 1;
    wp::float32 var_46;
    wp::float32 var_47;
    wp::vec_t<3, wp::float32> var_48;
    wp::vec_t<3, wp::float32> var_49;
    const wp::int32 var_50 = 0;
    wp::float32 var_51;
    const wp::int32 var_52 = 1;
    wp::float32 var_53;
    wp::vec_t<3, wp::float32> var_54;
    wp::vec_t<3, wp::float32> var_55;
    wp::float32 var_56;
    wp::float32 var_57;
    wp::float32 var_58;
    wp::float32 var_59;
    wp::float32 var_60;
    wp::vec_t<3, wp::float32> var_61;
    wp::vec_t<3, wp::float32> var_62;
    wp::float32 var_63;
    wp::vec_t<3, wp::float32> var_64;
    wp::vec_t<3, wp::float32> var_65;
    wp::float32 var_66;
    //---------
    // forward
    // def correct_pair(p: wp.vec3, q: wp.vec3, cfg: Parameters):                             <L 260>
    // gap, normal, gp, gq = pair_constraint(p, q)                                            <L 261>
    pair_constraint_1(var_p, var_q, var_0, var_1, var_2, var_3);
    // motion = float(0.0)                                                                    <L 262>
    var_5 = wp::float(var_4);
    // if gap < cfg.guard:                                                                    <L 263>
    var_6 = &((var_cfg).guard);
    var_8 = wp::load(var_6);
    var_7 = (var_0 < var_8);
    if (var_7) {
        // denominator = 2.0 * wp.dot(normal, normal) + cfg.rotation_mobility * (gp * gp + gq * gq)       <L 264>
        var_10 = wp::dot(var_1, var_1);
        var_11 = wp::mul(var_9, var_10);
        var_12 = &((var_cfg).rotation_mobility);
        var_13 = wp::mul(var_2, var_2);
        var_14 = wp::mul(var_3, var_3);
        var_15 = wp::add(var_13, var_14);
        var_17 = wp::load(var_12);
        var_16 = wp::mul(var_17, var_15);
        var_18 = wp::add(var_11, var_16);
        // if denominator > 0.00000001:                                                       <L 265>
        var_20 = (var_18 > var_19);
        if (var_20) {
            // angular = cfg.rotation_mobility * wp.max(wp.abs(gp), wp.abs(gq))               <L 266>
            var_21 = &((var_cfg).rotation_mobility);
            var_22 = wp::abs(var_2);
            var_23 = wp::abs(var_3);
            var_24 = wp::max(var_22, var_23);
            var_26 = wp::load(var_21);
            var_25 = wp::mul(var_26, var_24);
            // scale = bounded_scale((cfg.guard - gap) / denominator, wp.length(normal), angular, cfg)       <L 267>
            var_27 = &((var_cfg).guard);
            var_29 = wp::load(var_27);
            var_28 = wp::sub(var_29, var_0);
            var_30 = wp::div(var_28, var_18);
            var_31 = wp::length(var_1);
            var_32 = bounded_scale_1(var_30, var_31, var_25, var_cfg);
            // delta = scale * normal                                                         <L 268>
            var_33 = wp::mul(var_32, var_1);
            // dp = scale * cfg.rotation_mobility * gp                                        <L 269>
            var_34 = &((var_cfg).rotation_mobility);
            var_36 = wp::load(var_34);
            var_35 = wp::mul(var_32, var_36);
            var_37 = wp::mul(var_35, var_2);
            // dq = scale * cfg.rotation_mobility * gq                                        <L 270>
            var_38 = &((var_cfg).rotation_mobility);
            var_40 = wp::load(var_38);
            var_39 = wp::mul(var_32, var_40);
            var_41 = wp::mul(var_39, var_3);
            // p = p + wp.vec3(-delta[0], -delta[1], dp)                                      <L 271>
            var_43 = wp::extract(var_33, var_42);
            var_44 = wp::neg(var_43);
            var_46 = wp::extract(var_33, var_45);
            var_47 = wp::neg(var_46);
            var_48 = wp::vec_t<3, wp::float32>(var_44, var_47, var_37);
            var_49 = wp::add(var_p, var_48);
            // q = q + wp.vec3(delta[0], delta[1], dq)                                        <L 272>
            var_51 = wp::extract(var_33, var_50);
            var_53 = wp::extract(var_33, var_52);
            var_54 = wp::vec_t<3, wp::float32>(var_51, var_53, var_41);
            var_55 = wp::add(var_q, var_54);
            // motion = wp.max(wp.length(delta), wp.max(wp.abs(dp), wp.abs(dq)))              <L 273>
            var_56 = wp::length(var_33);
            var_57 = wp::abs(var_37);
            var_58 = wp::abs(var_41);
            var_59 = wp::max(var_57, var_58);
            var_60 = wp::max(var_56, var_59);
        }
        var_61 = wp::where(var_20, var_49, var_p);
        var_62 = wp::where(var_20, var_55, var_q);
        var_63 = wp::where(var_20, var_60, var_5);
    }
    var_64 = wp::where(var_7, var_61, var_p);
    var_65 = wp::where(var_7, var_62, var_q);
    var_66 = wp::where(var_7, var_63, var_5);
    // return p, q, motion                                                                    <L 274>
    ret_0 = var_64;
    ret_1 = var_65;
    ret_2 = var_66;
    return;
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:115
static CUDA_CALLABLE void adj_mix64_1(
    wp::uint64 var_value,
    wp::uint64 & adj_value,
    wp::uint64 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:123
static CUDA_CALLABLE void adj_random_value_1(
    wp::uint64 var_state,
    wp::uint64 & ret_0,
    wp::float32 & ret_1,
    wp::uint64 & adj_state,
    wp::uint64 & adj_ret_0,
    wp::float32 & adj_ret_1)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:139
static CUDA_CALLABLE void adj_separate_axis_value_1(
    wp::float32 value,
    wp::float32 & adj_value,
    wp::float32 & adj_ret)
{
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:154
static CUDA_CALLABLE void adj_axes_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> & ret_0,
    wp::vec_t<2, wp::float32> & ret_1,
    wp::float32 & adj_theta,
    wp::vec_t<2, wp::float32> & adj_ret_0,
    wp::vec_t<2, wp::float32> & adj_ret_1)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:161
static CUDA_CALLABLE void adj_support_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> var_normal,
    wp::float32 & adj_theta,
    wp::vec_t<2, wp::float32> & adj_normal,
    wp::float32 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:229
static CUDA_CALLABLE void adj_pair_gap_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q,
    wp::vec_t<3, wp::float32> & adj_p,
    wp::vec_t<3, wp::float32> & adj_q,
    wp::float32 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:292
static CUDA_CALLABLE void adj_residuals_1(
    wp::array_t<wp::vec_t<3, wp::float32>> var_poses,
    wp::int32 var_world,
    wp::int32 var_n,
    wp::float32 var_side,
    wp::float32 & ret_0,
    wp::float32 & ret_1,
    wp::int32 & ret_2,
    wp::array_t<wp::vec_t<3, wp::float32>> & adj_poses,
    wp::int32 & adj_world,
    wp::int32 & adj_n,
    wp::float32 & adj_side,
    wp::float32 & adj_ret_0,
    wp::float32 & adj_ret_1,
    wp::int32 & adj_ret_2)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:129
static CUDA_CALLABLE void adj_sign_symmetric_1(
    wp::float32 var_x,
    wp::float32 & adj_x,
    wp::float32 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:167
static CUDA_CALLABLE void adj_support_derivative_1(
    wp::float32 var_theta,
    wp::vec_t<2, wp::float32> var_normal,
    wp::float32 & adj_theta,
    wp::vec_t<2, wp::float32> & adj_normal,
    wp::float32 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:249
static CUDA_CALLABLE void adj_bounded_scale_1(
    wp::float32 var_lam,
    wp::float32 var_linear_norm,
    wp::float32 var_angular,
    Parameters_71195d0b var_cfg,
    wp::float32 & adj_lam,
    wp::float32 & adj_linear_norm,
    wp::float32 & adj_angular,
    Parameters_71195d0b & adj_cfg,
    wp::float32 & adj_ret)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:277
static CUDA_CALLABLE void adj_correct_wall_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::float32 var_side,
    wp::vec_t<2, wp::float32> var_normal,
    Parameters_71195d0b var_cfg,
    wp::vec_t<3, wp::float32> & ret_0,
    wp::float32 & ret_1,
    wp::vec_t<3, wp::float32> & adj_p,
    wp::float32 & adj_side,
    wp::vec_t<2, wp::float32> & adj_normal,
    Parameters_71195d0b & adj_cfg,
    wp::vec_t<3, wp::float32> & adj_ret_0,
    wp::float32 & adj_ret_1)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:174
static CUDA_CALLABLE void adj_pair_constraint_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q,
    wp::float32 & ret_0,
    wp::vec_t<2, wp::float32> & ret_1,
    wp::float32 & ret_2,
    wp::float32 & ret_3,
    wp::vec_t<3, wp::float32> & adj_p,
    wp::vec_t<3, wp::float32> & adj_q,
    wp::float32 & adj_ret_0,
    wp::vec_t<2, wp::float32> & adj_ret_1,
    wp::float32 & adj_ret_2,
    wp::float32 & adj_ret_3)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}


// /home/user/DEV/asquerix/artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py:259
static CUDA_CALLABLE void adj_correct_pair_1(
    wp::vec_t<3, wp::float32> var_p,
    wp::vec_t<3, wp::float32> var_q,
    Parameters_71195d0b var_cfg,
    wp::vec_t<3, wp::float32> & ret_0,
    wp::vec_t<3, wp::float32> & ret_1,
    wp::float32 & ret_2,
    wp::vec_t<3, wp::float32> & adj_p,
    wp::vec_t<3, wp::float32> & adj_q,
    Parameters_71195d0b & adj_cfg,
    wp::vec_t<3, wp::float32> & adj_ret_0,
    wp::vec_t<3, wp::float32> & adj_ret_1,
    wp::float32 & adj_ret_2)
{
	// reverse mode disabled (no backward-enabled kernel depends on this function)
}



extern "C" __global__ void simulate_0a446899_cuda_kernel_forward(
    wp::launch_bounds_t<1> dim,
    Parameters_71195d0b var_cfg,
    wp::uint64 var_offset,
    wp::array_t<wp::vec_t<3, wp::float32>> var_accepted_pose,
    wp::array_t<wp::vec_t<3, wp::float32>> var_work,
    wp::array_t<Result_58cdc340> var_results,
    wp::array_t<wp::float32> var_trace,
    wp::int32 var_debug,
    wp::int32 var_stage,
    wp::int32 var_chunk_attempts)
{
    wp::tile_shared_storage_t tile_mem;

    for (size_t _idx = static_cast<size_t>(blockDim.x) * static_cast<size_t>(blockIdx.x) + static_cast<size_t>(threadIdx.x);
         _idx < dim.size;
         _idx += static_cast<size_t>(blockDim.x) * static_cast<size_t>(gridDim.x))
    {
            // reset shared memory allocator
        wp::tile_shared_storage_t::init();

        //---------
        // primal vars
        wp::int32 var_0;
        const wp::int32 var_1 = 0;
        bool var_2;
        Result_58cdc340 var_3;
        const wp::int32 var_4 = 0;
        wp::float32* var_5;
        wp::float32 var_6;
        wp::float32 var_7;
        wp::float32* var_8;
        wp::float32 var_9;
        wp::float32 var_10;
        wp::uint64* var_11;
        wp::uint64 var_12;
        wp::uint64 var_13;
        wp::uint64 var_14;
        wp::uint64 var_15;
        wp::uint64 var_16;
        const wp::float32 var_17 = 0.5;
        wp::float32* var_18;
        wp::float32 var_19;
        wp::float32 var_20;
        const wp::float32 var_21 = 0.7071067811865476;
        wp::float32 var_22;
        wp::float32* var_23;
        wp::float32 var_24;
        wp::float32 var_25;
        const wp::int32 var_26 = 1;
        wp::int32 var_27;
        wp::int32* var_28;
        wp::range_t var_29;
        wp::int32 var_30;
        wp::int32 var_31;
        const wp::int32 var_32 = 0;
        wp::int32 var_33;
        wp::int32* var_34;
        wp::range_t var_35;
        wp::int32 var_36;
        wp::int32 var_37;
        wp::uint64 var_38;
        wp::float32 var_39;
        wp::uint64 var_40;
        wp::float32 var_41;
        wp::uint64 var_42;
        wp::float32 var_43;
        const wp::float32 var_44 = 2.0;
        wp::float32 var_45;
        const wp::float32 var_46 = 1.0;
        wp::float32 var_47;
        wp::float32 var_48;
        const wp::float32 var_49 = 2.0;
        wp::float32 var_50;
        const wp::float32 var_51 = 1.0;
        wp::float32 var_52;
        wp::float32 var_53;
        const wp::float32 var_54 = 1.5707963267948966;
        wp::float32 var_55;
        wp::vec_t<3, wp::float32> var_56;
        wp::int32* var_57;
        const wp::int32 var_58 = 1;
        wp::int32 var_59;
        wp::int32 var_60;
        const wp::int32 var_61 = 1;
        wp::int32 var_62;
        wp::range_t var_63;
        wp::int32 var_64;
        wp::vec_t<3, wp::float32>* var_65;
        wp::vec_t<3, wp::float32> var_66;
        wp::vec_t<3, wp::float32> var_67;
        const wp::int32 var_68 = 0;
        wp::float32 var_69;
        const wp::int32 var_70 = 0;
        wp::float32 var_71;
        wp::float32 var_72;
        const wp::int32 var_73 = 1;
        wp::float32 var_74;
        const wp::int32 var_75 = 1;
        wp::float32 var_76;
        wp::float32 var_77;
        wp::float32 var_78;
        wp::float32 var_79;
        wp::float32 var_80;
        const wp::float32 var_81 = 2.0;
        const wp::float32 var_82 = 4.0;
        wp::float32* var_83;
        wp::float32 var_84;
        wp::float32 var_85;
        wp::float32 var_86;
        bool var_87;
        const wp::int32 var_88 = 0;
        wp::int32 var_89;
        const wp::int32 var_90 = 1;
        bool var_91;
        const wp::int32 var_92 = 1;
        wp::uint64 var_93;
        const wp::int32 var_94 = 0;
        bool var_95;
        const wp::int32 var_96 = 0;
        const wp::int32 var_97 = 0;
        bool var_98;
        const wp::int32 var_99 = 3;
        const wp::float32 var_100 = 0.0;
        Result_58cdc340* var_101;
        Result_58cdc340 var_102;
        Result_58cdc340 var_103;
        Result_58cdc340 var_104;
        bool var_105;
        wp::int32* var_106;
        const wp::int32 var_107 = 0;
        bool var_108;
        wp::int32 var_109;
        wp::int32* var_110;
        wp::int32* var_111;
        bool var_112;
        wp::int32 var_113;
        wp::int32 var_114;
        wp::int32 var_115;
        bool var_116;
        const wp::int32 var_117 = 0;
        bool var_118;
        wp::int32* var_119;
        const wp::int32 var_120 = 0;
        bool var_121;
        wp::int32 var_122;
        wp::int32* var_123;
        const wp::int32 var_124 = 0;
        bool var_125;
        wp::int32 var_126;
        const wp::int32 var_127 = 1;
        wp::int32 var_128;
        const wp::int32 var_129 = 1;
        bool var_130;
        wp::int32* var_131;
        wp::float32* var_132;
        wp::float32 var_133;
        wp::float32 var_134;
        wp::int32 var_135;
        wp::int32 var_136;
        wp::float32 var_137;
        const wp::int32 var_138 = 1;
        wp::range_t var_139;
        wp::int32 var_140;
        wp::int32* var_141;
        wp::int32* var_142;
        bool var_143;
        wp::int32 var_144;
        wp::int32 var_145;
        wp::int32* var_146;
        wp::int32 var_147;
        wp::int32 var_148;
        wp::int32* var_149;
        const wp::int32 var_150 = 1;
        wp::int32 var_151;
        wp::int32 var_152;
        wp::float32* var_153;
        wp::float32* var_154;
        wp::float32 var_155;
        wp::float32 var_156;
        wp::float32 var_157;
        const wp::int32 var_158 = 0;
        wp::int32 var_159;
        const wp::int32 var_160 = 0;
        wp::int32 var_161;
        const wp::int32 var_162 = 0;
        wp::int32 var_163;
        wp::int32* var_164;
        wp::range_t var_165;
        wp::int32 var_166;
        wp::int32 var_167;
        wp::vec_t<3, wp::float32>* var_168;
        wp::vec_t<3, wp::float32> var_169;
        wp::vec_t<3, wp::float32> var_170;
        wp::int32* var_171;
        wp::range_t var_172;
        wp::int32 var_173;
        wp::int32 var_174;
        const wp::float32 var_175 = 0.0;
        wp::float32 var_176;
        wp::int32* var_177;
        wp::range_t var_178;
        wp::int32 var_179;
        wp::int32 var_180;
        wp::vec_t<3, wp::float32>* var_181;
        wp::vec_t<3, wp::float32> var_182;
        wp::vec_t<3, wp::float32> var_183;
        const wp::int32 var_184 = 0;
        const wp::float32 var_185 = 1.0;
        const wp::float32 var_186 = 0.0;
        wp::vec_t<2, wp::float32> var_187;
        const wp::int32 var_188 = 1;
        bool var_189;
        const wp::float32 var_190 = -1.0;
        const wp::float32 var_191 = 0.0;
        wp::vec_t<2, wp::float32> var_192;
        const wp::int32 var_193 = 2;
        bool var_194;
        const wp::float32 var_195 = 0.0;
        const wp::float32 var_196 = 1.0;
        wp::vec_t<2, wp::float32> var_197;
        const wp::int32 var_198 = 3;
        bool var_199;
        const wp::float32 var_200 = 0.0;
        const wp::float32 var_201 = -1.0;
        wp::vec_t<2, wp::float32> var_202;
        wp::vec_t<2, wp::float32> var_203;
        wp::vec_t<2, wp::float32> var_204;
        wp::vec_t<2, wp::float32> var_205;
        wp::vec_t<3, wp::float32> var_206;
        wp::float32 var_207;
        wp::float32 var_208;
        const wp::int32 var_209 = 1;
        const wp::float32 var_210 = 1.0;
        const wp::float32 var_211 = 0.0;
        wp::vec_t<2, wp::float32> var_212;
        const wp::int32 var_213 = 1;
        bool var_214;
        const wp::float32 var_215 = -1.0;
        const wp::float32 var_216 = 0.0;
        wp::vec_t<2, wp::float32> var_217;
        const wp::int32 var_218 = 2;
        bool var_219;
        const wp::float32 var_220 = 0.0;
        const wp::float32 var_221 = 1.0;
        wp::vec_t<2, wp::float32> var_222;
        const wp::int32 var_223 = 3;
        bool var_224;
        const wp::float32 var_225 = 0.0;
        const wp::float32 var_226 = -1.0;
        wp::vec_t<2, wp::float32> var_227;
        wp::vec_t<2, wp::float32> var_228;
        wp::vec_t<2, wp::float32> var_229;
        wp::vec_t<2, wp::float32> var_230;
        wp::vec_t<3, wp::float32> var_231;
        wp::float32 var_232;
        wp::float32 var_233;
        const wp::int32 var_234 = 2;
        const wp::float32 var_235 = 1.0;
        const wp::float32 var_236 = 0.0;
        wp::vec_t<2, wp::float32> var_237;
        const wp::int32 var_238 = 1;
        bool var_239;
        const wp::float32 var_240 = -1.0;
        const wp::float32 var_241 = 0.0;
        wp::vec_t<2, wp::float32> var_242;
        const wp::int32 var_243 = 2;
        bool var_244;
        const wp::float32 var_245 = 0.0;
        const wp::float32 var_246 = 1.0;
        wp::vec_t<2, wp::float32> var_247;
        const wp::int32 var_248 = 3;
        bool var_249;
        const wp::float32 var_250 = 0.0;
        const wp::float32 var_251 = -1.0;
        wp::vec_t<2, wp::float32> var_252;
        wp::vec_t<2, wp::float32> var_253;
        wp::vec_t<2, wp::float32> var_254;
        wp::vec_t<2, wp::float32> var_255;
        wp::vec_t<3, wp::float32> var_256;
        wp::float32 var_257;
        wp::float32 var_258;
        const wp::int32 var_259 = 3;
        const wp::float32 var_260 = 1.0;
        const wp::float32 var_261 = 0.0;
        wp::vec_t<2, wp::float32> var_262;
        const wp::int32 var_263 = 1;
        bool var_264;
        const wp::float32 var_265 = -1.0;
        const wp::float32 var_266 = 0.0;
        wp::vec_t<2, wp::float32> var_267;
        const wp::int32 var_268 = 2;
        bool var_269;
        const wp::float32 var_270 = 0.0;
        const wp::float32 var_271 = 1.0;
        wp::vec_t<2, wp::float32> var_272;
        const wp::int32 var_273 = 3;
        bool var_274;
        const wp::float32 var_275 = 0.0;
        const wp::float32 var_276 = -1.0;
        wp::vec_t<2, wp::float32> var_277;
        wp::vec_t<2, wp::float32> var_278;
        wp::vec_t<2, wp::float32> var_279;
        wp::vec_t<2, wp::float32> var_280;
        wp::vec_t<3, wp::float32> var_281;
        wp::float32 var_282;
        wp::float32 var_283;
        wp::int32* var_284;
        wp::range_t var_285;
        wp::int32 var_286;
        wp::int32 var_287;
        const wp::int32 var_288 = 1;
        wp::int32 var_289;
        wp::int32* var_290;
        wp::range_t var_291;
        wp::int32 var_292;
        wp::int32 var_293;
        wp::vec_t<3, wp::float32>* var_294;
        wp::vec_t<3, wp::float32>* var_295;
        wp::vec_t<3, wp::float32> var_296;
        wp::vec_t<3, wp::float32> var_297;
        wp::float32 var_298;
        wp::vec_t<3, wp::float32> var_299;
        wp::vec_t<3, wp::float32> var_300;
        wp::float32 var_301;
        wp::int32* var_302;
        const wp::int32 var_303 = 1;
        wp::int32 var_304;
        wp::int32 var_305;
        wp::int32* var_306;
        wp::float32 var_307;
        wp::float32 var_308;
        wp::int32 var_309;
        wp::int32 var_310;
        const wp::int32 var_311 = 0;
        bool var_312;
        const wp::int32 var_313 = 4;
        wp::int32 var_314;
        wp::float32 var_315;
        wp::float32 var_316;
        wp::int32 var_317;
        wp::float32 var_318;
        wp::float32* var_319;
        wp::float32* var_320;
        wp::float32 var_321;
        wp::float32 var_322;
        wp::float32 var_323;
        bool var_324;
        const wp::int32 var_325 = 1;
        wp::int32 var_326;
        wp::float32 var_327;
        wp::float32 var_328;
        wp::int32 var_329;
        wp::float32* var_330;
        bool var_331;
        wp::float32 var_332;
        const wp::int32 var_333 = 1;
        wp::int32 var_334;
        const wp::int32 var_335 = 0;
        wp::int32 var_336;
        wp::int32* var_337;
        bool var_338;
        wp::int32 var_339;
        const wp::int32 var_340 = 1;
        wp::int32 var_341;
        wp::float32 var_342;
        wp::float32 var_343;
        wp::int32 var_344;
        wp::int32 var_345;
        bool var_346;
        const wp::int32 var_347 = 0;
        bool var_348;
        wp::float32* var_349;
        wp::float32* var_350;
        bool var_351;
        wp::float32 var_352;
        wp::float32 var_353;
        wp::int32 var_354;
        const wp::int32 var_355 = 1;
        bool var_356;
        wp::int32* var_357;
        const wp::int32 var_358 = 1;
        wp::int32 var_359;
        wp::int32 var_360;
        wp::int32* var_361;
        wp::range_t var_362;
        wp::int32 var_363;
        wp::int32 var_364;
        wp::vec_t<3, wp::float32>* var_365;
        wp::vec_t<3, wp::float32> var_366;
        wp::vec_t<3, wp::float32> var_367;
        wp::int32* var_368;
        const wp::int32 var_369 = 1;
        wp::int32 var_370;
        wp::int32 var_371;
        wp::int32* var_372;
        wp::range_t var_373;
        wp::int32 var_374;
        wp::int32 var_375;
        wp::vec_t<3, wp::float32>* var_376;
        wp::vec_t<3, wp::float32> var_377;
        wp::vec_t<3, wp::float32> var_378;
        wp::float32* var_379;
        wp::float32* var_380;
        wp::float32* var_381;
        wp::float32 var_382;
        wp::float32 var_383;
        wp::float32 var_384;
        wp::float32 var_385;
        wp::float32 var_386;
        wp::int32 var_387;
        const wp::int32 var_388 = 1;
        bool var_389;
        wp::float32* var_390;
        wp::float32 var_391;
        wp::float32 var_392;
        wp::int32* var_393;
        const wp::int32 var_394 = 4;
        bool var_395;
        wp::int32 var_396;
        wp::int32 var_397;
        const wp::int32 var_398 = 1;
        bool var_399;
        const wp::int32 var_400 = 1;
        const wp::int32 var_401 = 1;
        bool var_402;
        const wp::int32 var_403 = 2;
        wp::int32 var_404;
        wp::int32* var_405;
        wp::float32* var_406;
        wp::float32 var_407;
        wp::float32 var_408;
        wp::int32 var_409;
        wp::int32 var_410;
        wp::float32 var_411;
        const wp::float32 var_412 = 0.0;
        wp::float32 var_413;
        wp::float32 var_414;
        wp::float32 var_415;
        bool var_416;
        const wp::int32 var_417 = 1;
        bool var_418;
        wp::float32 var_419;
        wp::float32* var_420;
        wp::float32* var_421;
        wp::float32 var_422;
        wp::float32 var_423;
        wp::float32 var_424;
        bool var_425;
        wp::int32 var_426;
        //---------
        // forward
        // def simulate(cfg: Parameters, offset: wp.uint64,                                       <L 309>
        // world = wp.tid()                                                                       <L 312>
        var_0 = builtin_tid1d();
        // if stage == 0:                                                                         <L 313>
        var_2 = (var_stage == var_1);
        if (var_2) {
            // result = Result()                                                                  <L 314>
            var_3 = Result_58cdc340();
            // result.termination = 0                                                             <L 315>
            var_3.termination = var_4;
            // result.side = cfg.initial_side                                                     <L 316>
            var_5 = &((var_cfg).initial_side);
            var_7 = wp::load(var_5);
            var_6 = wp::copy(var_7);
            var_3.side = var_6;
            // result.final_step = cfg.step                                                       <L 317>
            var_8 = &((var_cfg).step);
            var_10 = wp::load(var_8);
            var_9 = wp::copy(var_10);
            var_3.final_step = var_9;
            // state = cfg.seed ^ mix64(offset + wp.uint64(world))                                <L 318>
            var_11 = &((var_cfg).seed);
            var_12 = wp::uint64(var_0);
            var_13 = wp::add(var_offset, var_12);
            var_14 = mix64_1(var_13);
            var_16 = wp::load(var_11);
            var_15 = wp::bit_xor(var_16, var_14);
            // room = 0.5 * cfg.initial_side - 0.7071067811865476 - cfg.guard                     <L 319>
            var_18 = &((var_cfg).initial_side);
            var_20 = wp::load(var_18);
            var_19 = wp::mul(var_17, var_20);
            var_22 = wp::sub(var_19, var_21);
            var_23 = &((var_cfg).guard);
            var_25 = wp::load(var_23);
            var_24 = wp::sub(var_22, var_25);
            // initialized = int(1)                                                               <L 320>
            var_27 = wp::int(var_26);
            // for i in range(cfg.n):                                                             <L 321>
            var_28 = &((var_cfg).n);
            var_30 = wp::load(var_28);
            var_29 = wp::range(var_30);
            start_for_0:;
                if (iter_cmp(var_29) == 0) goto end_for_0;
                var_31 = wp::iter_next(var_29);
                // placed = int(0)                                                                <L 322>
                var_33 = wp::int(var_32);
                // for proposal in range(cfg.proposals_per_square):                               <L 323>
                var_34 = &((var_cfg).proposals_per_square);
                var_36 = wp::load(var_34);
                var_35 = wp::range(var_36);
                start_for_2:;
                    if (iter_cmp(var_35) == 0) goto end_for_2;
                    var_37 = wp::iter_next(var_35);
                    // state, rx = random_value(state)                                            <L 324>
                    random_value_1(var_15, var_38, var_39);
                    // state, ry = random_value(state)                                            <L 325>
                    random_value_1(var_38, var_40, var_41);
                    // state, rt = random_value(state)                                            <L 326>
                    random_value_1(var_40, var_42, var_43);
                    // candidate = wp.vec3((2.0 * rx - 1.0) * room, (2.0 * ry - 1.0) * room, rt * 1.5707963267948966)       <L 327>
                    var_45 = wp::mul(var_44, var_39);
                    var_47 = wp::sub(var_45, var_46);
                    var_48 = wp::mul(var_47, var_24);
                    var_50 = wp::mul(var_49, var_41);
                    var_52 = wp::sub(var_50, var_51);
                    var_53 = wp::mul(var_52, var_24);
                    var_55 = wp::mul(var_43, var_54);
                    var_56 = wp::vec_t<3, wp::float32>(var_48, var_53, var_55);
                    // result.proposals += 1                                                      <L 328>
                    var_57 = &((var_3).proposals);
                    var_60 = wp::load(var_57);
                    var_59 = wp::add(var_60, var_58);
                    var_3.proposals = var_59;
                    // clear = int(1)                                                             <L 329>
                    var_62 = wp::int(var_61);
                    // for j in range(i):                                                         <L 330>
                    var_63 = wp::range(var_31);
                    start_for_4:;
                        if (iter_cmp(var_63) == 0) goto end_for_4;
                        var_64 = wp::iter_next(var_63);
                        // p = accepted_pose[j, world]                                            <L 331>
                        var_65 = wp::address(var_accepted_pose, var_64, var_0);
                        var_67 = wp::load(var_65);
                        var_66 = wp::copy(var_67);
                        // dx = p[0] - candidate[0]                                               <L 332>
                        var_69 = wp::extract(var_66, var_68);
                        var_71 = wp::extract(var_56, var_70);
                        var_72 = wp::sub(var_69, var_71);
                        // dy = p[1] - candidate[1]                                               <L 333>
                        var_74 = wp::extract(var_66, var_73);
                        var_76 = wp::extract(var_56, var_75);
                        var_77 = wp::sub(var_74, var_76);
                        // if dx * dx + dy * dy < 2.0 + 4.0 * cfg.guard:                          <L 334>
                        var_78 = wp::mul(var_72, var_72);
                        var_79 = wp::mul(var_77, var_77);
                        var_80 = wp::add(var_78, var_79);
                        var_83 = &((var_cfg).guard);
                        var_85 = wp::load(var_83);
                        var_84 = wp::mul(var_82, var_85);
                        var_86 = wp::add(var_81, var_84);
                        var_87 = (var_80 < var_86);
                        if (var_87) {
                            // clear = 0                                                          <L 335>
                        }
                        var_89 = wp::where(var_87, var_88, var_62);
                        wp::assign(var_62, var_89);
                        goto start_for_4;
                    end_for_4:;
                    // if clear == 1:                                                             <L 336>
                    var_91 = (var_62 == var_90);
                    if (var_91) {
                        // accepted_pose[i, world] = candidate                                    <L 337>
                        wp::array_store(var_accepted_pose, var_31, var_0, var_56);
                        // placed = 1                                                             <L 338>
                        // break                                                                  <L 339>
                        wp::assign(var_15, var_42);
                        wp::assign(var_33, var_92);
                        goto end_for_2;
                    }
                    var_93 = wp::where(var_91, var_15, var_42);
                    wp::assign(var_15, var_93);
                    goto start_for_2;
                end_for_2:;
                // if placed == 0:                                                                <L 340>
                var_95 = (var_33 == var_94);
                if (var_95) {
                    // initialized = 0                                                            <L 341>
                    // break                                                                      <L 342>
                    wp::assign(var_27, var_96);
                    goto end_for_0;
                }
                goto start_for_0;
            end_for_0:;
            // if initialized == 0:                                                               <L 343>
            var_98 = (var_27 == var_97);
            if (var_98) {
                // result.termination = 3                                                         <L 344>
                var_3.termination = var_99;
                // result.side = 0.0                                                              <L 345>
                var_3.side = var_100;
            }
        }
        if (!var_2) {
            // result = results[world]                                                            <L 347>
            var_101 = wp::address(var_results, var_0);
            var_103 = wp::load(var_101);
            var_102 = wp::copy(var_103);
        }
        var_104 = wp::where(var_2, var_3, var_102);
        // initialized = int(result.termination == 0 and result.attempts < cfg.max_attempts)       <L 348>
        var_106 = &((var_104).termination);
        var_109 = wp::load(var_106);
        var_108 = (var_109 == var_107);
        var_105 = var_108;
        if (var_105) {
            var_110 = &((var_104).attempts);
            var_111 = &((var_cfg).max_attempts);
            var_113 = wp::load(var_110);
            var_114 = wp::load(var_111);
            var_112 = (var_113 < var_114);
            var_105 = var_105 && var_112;
        }
        var_115 = wp::int(var_105);
        // if stage == 0 and cfg.max_attempts == 0 and result.termination == 0:                   <L 349>
        var_118 = (var_stage == var_117);
        var_116 = var_118;
        if (var_116) {
            var_119 = &((var_cfg).max_attempts);
            var_122 = wp::load(var_119);
            var_121 = (var_122 == var_120);
            var_116 = var_116 && var_121;
        }
        if (var_116) {
            var_123 = &((var_104).termination);
            var_126 = wp::load(var_123);
            var_125 = (var_126 == var_124);
            var_116 = var_116 && var_125;
        }
        if (var_116) {
            // initialized = 1                                                                    <L 350>
        }
        var_128 = wp::where(var_116, var_127, var_115);
        // if initialized == 1:                                                                   <L 351>
        var_130 = (var_128 == var_129);
        if (var_130) {
            // gap, wall, finite = residuals(accepted_pose, world, cfg.n, result.side)            <L 352>
            var_131 = &((var_cfg).n);
            var_132 = &((var_104).side);
            var_136 = wp::load(var_131);
            var_137 = wp::load(var_132);
            residuals_1(var_accepted_pose, var_0, var_136, var_137, var_133, var_134, var_135);
            // result.feasible = 1                                                                <L 353>
            var_104.feasible = var_138;
            // for local_attempt in range(chunk_attempts):                                        <L 354>
            var_139 = wp::range(var_chunk_attempts);
            start_for_6:;
                if (iter_cmp(var_139) == 0) goto end_for_6;
                var_140 = wp::iter_next(var_139);
                // if result.attempts >= cfg.max_attempts:                                        <L 355>
                var_141 = &((var_104).attempts);
                var_142 = &((var_cfg).max_attempts);
                var_144 = wp::load(var_141);
                var_145 = wp::load(var_142);
                var_143 = (var_144 >= var_145);
                if (var_143) {
                    // break                                                                      <L 356>
                    goto end_for_6;
                }
                // attempt = result.attempts                                                      <L 357>
                var_146 = &((var_104).attempts);
                var_148 = wp::load(var_146);
                var_147 = wp::copy(var_148);
                // result.attempts += 1                                                           <L 358>
                var_149 = &((var_104).attempts);
                var_152 = wp::load(var_149);
                var_151 = wp::add(var_152, var_150);
                var_104.attempts = var_151;
                // proposed_side = result.side - result.final_step                                <L 359>
                var_153 = &((var_104).side);
                var_154 = &((var_104).final_step);
                var_156 = wp::load(var_153);
                var_157 = wp::load(var_154);
                var_155 = wp::sub(var_156, var_157);
                // success = int(0)                                                               <L 360>
                var_159 = wp::int(var_158);
                // stagnant = int(0)                                                              <L 361>
                var_161 = wp::int(var_160);
                // stalled = int(0)                                                               <L 362>
                var_163 = wp::int(var_162);
                // for i in range(cfg.n):                                                         <L 363>
                var_164 = &((var_cfg).n);
                var_166 = wp::load(var_164);
                var_165 = wp::range(var_166);
                start_for_8:;
                    if (iter_cmp(var_165) == 0) goto end_for_8;
                    var_167 = wp::iter_next(var_165);
                    // work[i, world] = accepted_pose[i, world]                                   <L 364>
                    var_168 = wp::address(var_accepted_pose, var_167, var_0);
                    var_170 = wp::load(var_168);
                    var_169 = wp::copy(var_170);
                    wp::array_store(var_work, var_167, var_0, var_169);
                    goto start_for_8;
                end_for_8:;
                // for sweep in range(cfg.max_sweeps):                                            <L 365>
                var_171 = &((var_cfg).max_sweeps);
                var_173 = wp::load(var_171);
                var_172 = wp::range(var_173);
                start_for_10:;
                    if (iter_cmp(var_172) == 0) goto end_for_10;
                    var_174 = wp::iter_next(var_172);
                    // motion = float(0.0)                                                        <L 366>
                    var_176 = wp::float(var_175);
                    // for i in range(cfg.n):                                                     <L 367>
                    var_177 = &((var_cfg).n);
                    var_179 = wp::load(var_177);
                    var_178 = wp::range(var_179);
                    start_for_12:;
                        if (iter_cmp(var_178) == 0) goto end_for_12;
                        var_180 = wp::iter_next(var_178);
                        // p = work[i, world]                                                     <L 368>
                        var_181 = wp::address(var_work, var_180, var_0);
                        var_183 = wp::load(var_181);
                        var_182 = wp::copy(var_183);
                        // for k in range(4):                                                     <L 369>
                        // normal = wp.vec2(1.0, 0.0)                                             <L 370>
                        var_187 = wp::vec_t<2, wp::float32>(var_185, var_186);
                        // if k == 1:                                                             <L 371>
                        var_189 = (var_184 == var_188);
                        if (var_189) {
                            // normal = wp.vec2(-1.0, 0.0)                                        <L 372>
                            var_192 = wp::vec_t<2, wp::float32>(var_190, var_191);
                        }
                        if (!var_189) {
                            // elif k == 2:                                                       <L 373>
                            var_194 = (var_184 == var_193);
                            if (var_194) {
                                // normal = wp.vec2(0.0, 1.0)                                     <L 374>
                                var_197 = wp::vec_t<2, wp::float32>(var_195, var_196);
                            }
                            if (!var_194) {
                                // elif k == 3:                                                   <L 375>
                                var_199 = (var_184 == var_198);
                                if (var_199) {
                                    // normal = wp.vec2(0.0, -1.0)                                <L 376>
                                    var_202 = wp::vec_t<2, wp::float32>(var_200, var_201);
                                }
                                var_203 = wp::where(var_199, var_202, var_187);
                            }
                            var_204 = wp::where(var_194, var_197, var_203);
                        }
                        var_205 = wp::where(var_189, var_192, var_204);
                        // p, m = correct_wall(p, proposed_side, normal, cfg)                     <L 377>
                        correct_wall_1(var_182, var_155, var_205, var_cfg, var_206, var_207);
                        // motion = wp.max(motion, m)                                             <L 378>
                        var_208 = wp::max(var_176, var_207);
                        // normal = wp.vec2(1.0, 0.0)                                             <L 370>
                        var_212 = wp::vec_t<2, wp::float32>(var_210, var_211);
                        // if k == 1:                                                             <L 371>
                        var_214 = (var_209 == var_213);
                        if (var_214) {
                            // normal = wp.vec2(-1.0, 0.0)                                        <L 372>
                            var_217 = wp::vec_t<2, wp::float32>(var_215, var_216);
                        }
                        if (!var_214) {
                            // elif k == 2:                                                       <L 373>
                            var_219 = (var_209 == var_218);
                            if (var_219) {
                                // normal = wp.vec2(0.0, 1.0)                                     <L 374>
                                var_222 = wp::vec_t<2, wp::float32>(var_220, var_221);
                            }
                            if (!var_219) {
                                // elif k == 3:                                                   <L 375>
                                var_224 = (var_209 == var_223);
                                if (var_224) {
                                    // normal = wp.vec2(0.0, -1.0)                                <L 376>
                                    var_227 = wp::vec_t<2, wp::float32>(var_225, var_226);
                                }
                                var_228 = wp::where(var_224, var_227, var_212);
                            }
                            var_229 = wp::where(var_219, var_222, var_228);
                        }
                        var_230 = wp::where(var_214, var_217, var_229);
                        // p, m = correct_wall(p, proposed_side, normal, cfg)                     <L 377>
                        correct_wall_1(var_206, var_155, var_230, var_cfg, var_231, var_232);
                        // motion = wp.max(motion, m)                                             <L 378>
                        var_233 = wp::max(var_208, var_232);
                        // normal = wp.vec2(1.0, 0.0)                                             <L 370>
                        var_237 = wp::vec_t<2, wp::float32>(var_235, var_236);
                        // if k == 1:                                                             <L 371>
                        var_239 = (var_234 == var_238);
                        if (var_239) {
                            // normal = wp.vec2(-1.0, 0.0)                                        <L 372>
                            var_242 = wp::vec_t<2, wp::float32>(var_240, var_241);
                        }
                        if (!var_239) {
                            // elif k == 2:                                                       <L 373>
                            var_244 = (var_234 == var_243);
                            if (var_244) {
                                // normal = wp.vec2(0.0, 1.0)                                     <L 374>
                                var_247 = wp::vec_t<2, wp::float32>(var_245, var_246);
                            }
                            if (!var_244) {
                                // elif k == 3:                                                   <L 375>
                                var_249 = (var_234 == var_248);
                                if (var_249) {
                                    // normal = wp.vec2(0.0, -1.0)                                <L 376>
                                    var_252 = wp::vec_t<2, wp::float32>(var_250, var_251);
                                }
                                var_253 = wp::where(var_249, var_252, var_237);
                            }
                            var_254 = wp::where(var_244, var_247, var_253);
                        }
                        var_255 = wp::where(var_239, var_242, var_254);
                        // p, m = correct_wall(p, proposed_side, normal, cfg)                     <L 377>
                        correct_wall_1(var_231, var_155, var_255, var_cfg, var_256, var_257);
                        // motion = wp.max(motion, m)                                             <L 378>
                        var_258 = wp::max(var_233, var_257);
                        // normal = wp.vec2(1.0, 0.0)                                             <L 370>
                        var_262 = wp::vec_t<2, wp::float32>(var_260, var_261);
                        // if k == 1:                                                             <L 371>
                        var_264 = (var_259 == var_263);
                        if (var_264) {
                            // normal = wp.vec2(-1.0, 0.0)                                        <L 372>
                            var_267 = wp::vec_t<2, wp::float32>(var_265, var_266);
                        }
                        if (!var_264) {
                            // elif k == 2:                                                       <L 373>
                            var_269 = (var_259 == var_268);
                            if (var_269) {
                                // normal = wp.vec2(0.0, 1.0)                                     <L 374>
                                var_272 = wp::vec_t<2, wp::float32>(var_270, var_271);
                            }
                            if (!var_269) {
                                // elif k == 3:                                                   <L 375>
                                var_274 = (var_259 == var_273);
                                if (var_274) {
                                    // normal = wp.vec2(0.0, -1.0)                                <L 376>
                                    var_277 = wp::vec_t<2, wp::float32>(var_275, var_276);
                                }
                                var_278 = wp::where(var_274, var_277, var_262);
                            }
                            var_279 = wp::where(var_269, var_272, var_278);
                        }
                        var_280 = wp::where(var_264, var_267, var_279);
                        // p, m = correct_wall(p, proposed_side, normal, cfg)                     <L 377>
                        correct_wall_1(var_256, var_155, var_280, var_cfg, var_281, var_282);
                        // motion = wp.max(motion, m)                                             <L 378>
                        var_283 = wp::max(var_258, var_282);
                        // work[i, world] = p                                                     <L 379>
                        wp::array_store(var_work, var_180, var_0, var_281);
                        wp::assign(var_66, var_281);
                        wp::assign(var_176, var_283);
                        goto start_for_12;
                    end_for_12:;
                    // for i in range(cfg.n):                                                     <L 380>
                    var_284 = &((var_cfg).n);
                    var_286 = wp::load(var_284);
                    var_285 = wp::range(var_286);
                    start_for_14:;
                        if (iter_cmp(var_285) == 0) goto end_for_14;
                        var_287 = wp::iter_next(var_285);
                        // for j in range(i + 1, cfg.n):                                          <L 381>
                        var_289 = wp::add(var_287, var_288);
                        var_290 = &((var_cfg).n);
                        var_292 = wp::load(var_290);
                        var_291 = wp::range(var_289, var_292);
                        start_for_16:;
                            if (iter_cmp(var_291) == 0) goto end_for_16;
                            var_293 = wp::iter_next(var_291);
                            // p, q, m = correct_pair(work[i, world], work[j, world], cfg)        <L 382>
                            var_294 = wp::address(var_work, var_287, var_0);
                            var_295 = wp::address(var_work, var_293, var_0);
                            var_299 = wp::load(var_294);
                            var_300 = wp::load(var_295);
                            correct_pair_1(var_299, var_300, var_cfg, var_296, var_297, var_298);
                            // work[i, world] = p                                                 <L 383>
                            wp::array_store(var_work, var_287, var_0, var_296);
                            // work[j, world] = q                                                 <L 384>
                            wp::array_store(var_work, var_293, var_0, var_297);
                            // motion = wp.max(motion, m)                                         <L 385>
                            var_301 = wp::max(var_176, var_298);
                            wp::assign(var_66, var_296);
                            wp::assign(var_176, var_301);
                            wp::assign(var_282, var_298);
                            goto start_for_16;
                        end_for_16:;
                        wp::assign(var_64, var_293);
                        goto start_for_14;
                    end_for_14:;
                    // result.sweeps += 1                                                         <L 386>
                    var_302 = &((var_104).sweeps);
                    var_305 = wp::load(var_302);
                    var_304 = wp::add(var_305, var_303);
                    var_104.sweeps = var_304;
                    // gap, wall, finite = residuals(work, world, cfg.n, proposed_side)           <L 387>
                    var_306 = &((var_cfg).n);
                    var_310 = wp::load(var_306);
                    residuals_1(var_work, var_0, var_310, var_155, var_307, var_308, var_309);
                    // if finite == 0:                                                            <L 388>
                    var_312 = (var_309 == var_311);
                    if (var_312) {
                        // result.termination = 4                                                 <L 389>
                        var_104.termination = var_313;
                        // break                                                                  <L 390>
                        wp::assign(var_167, var_287);
                        wp::assign(var_133, var_307);
                        wp::assign(var_134, var_308);
                        wp::assign(var_135, var_309);
                        goto end_for_10;
                    }
                    var_314 = wp::where(var_312, var_167, var_287);
                    var_315 = wp::where(var_312, var_133, var_307);
                    var_316 = wp::where(var_312, var_134, var_308);
                    var_317 = wp::where(var_312, var_135, var_309);
                    // if wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance:              <L 391>
                    var_318 = wp::min(var_315, var_316);
                    var_319 = &((var_cfg).guard);
                    var_320 = &((var_cfg).acceptance_tolerance);
                    var_322 = wp::load(var_319);
                    var_323 = wp::load(var_320);
                    var_321 = wp::sub(var_322, var_323);
                    var_324 = (var_318 >= var_321);
                    if (var_324) {
                        // success = 1                                                            <L 392>
                        // break                                                                  <L 393>
                        wp::assign(var_167, var_314);
                        wp::assign(var_133, var_315);
                        wp::assign(var_134, var_316);
                        wp::assign(var_135, var_317);
                        wp::assign(var_159, var_325);
                        goto end_for_10;
                    }
                    var_326 = wp::where(var_324, var_167, var_314);
                    var_327 = wp::where(var_324, var_133, var_315);
                    var_328 = wp::where(var_324, var_134, var_316);
                    var_329 = wp::where(var_324, var_135, var_317);
                    // if motion <= cfg.motion_tolerance:                                         <L 394>
                    var_330 = &((var_cfg).motion_tolerance);
                    var_332 = wp::load(var_330);
                    var_331 = (var_176 <= var_332);
                    if (var_331) {
                        // stagnant += 1                                                          <L 395>
                        var_334 = wp::add(var_161, var_333);
                    }
                    if (!var_331) {
                        // stagnant = 0                                                           <L 397>
                    }
                    var_336 = wp::where(var_331, var_334, var_335);
                    // if stagnant >= cfg.stagnation_sweeps:                                      <L 398>
                    var_337 = &((var_cfg).stagnation_sweeps);
                    var_339 = wp::load(var_337);
                    var_338 = (var_336 >= var_339);
                    if (var_338) {
                        // stalled = 1                                                            <L 399>
                        // break                                                                  <L 400>
                        wp::assign(var_167, var_326);
                        wp::assign(var_133, var_327);
                        wp::assign(var_134, var_328);
                        wp::assign(var_135, var_329);
                        wp::assign(var_161, var_336);
                        wp::assign(var_163, var_340);
                        goto end_for_10;
                    }
                    var_341 = wp::where(var_338, var_167, var_326);
                    var_342 = wp::where(var_338, var_133, var_327);
                    var_343 = wp::where(var_338, var_134, var_328);
                    var_344 = wp::where(var_338, var_135, var_329);
                    var_345 = wp::where(var_338, var_161, var_336);
                    wp::assign(var_167, var_341);
                    wp::assign(var_133, var_342);
                    wp::assign(var_134, var_343);
                    wp::assign(var_135, var_344);
                    wp::assign(var_161, var_345);
                    goto start_for_10;
                end_for_10:;
                // floor_failed = int(success == 0 and result.final_step <= cfg.step_floor)       <L 403>
                var_348 = (var_159 == var_347);
                var_346 = var_348;
                if (var_346) {
                    var_349 = &((var_104).final_step);
                    var_350 = &((var_cfg).step_floor);
                    var_352 = wp::load(var_349);
                    var_353 = wp::load(var_350);
                    var_351 = (var_352 <= var_353);
                    var_346 = var_346 && var_351;
                }
                var_354 = wp::int(var_346);
                // if success == 1:                                                               <L 404>
                var_356 = (var_159 == var_355);
                if (var_356) {
                    // result.side = proposed_side                                                <L 405>
                    var_104.side = var_155;
                    // result.accepted += 1                                                       <L 406>
                    var_357 = &((var_104).accepted);
                    var_360 = wp::load(var_357);
                    var_359 = wp::add(var_360, var_358);
                    var_104.accepted = var_359;
                    // for i in range(cfg.n):                                                     <L 407>
                    var_361 = &((var_cfg).n);
                    var_363 = wp::load(var_361);
                    var_362 = wp::range(var_363);
                    start_for_18:;
                        if (iter_cmp(var_362) == 0) goto end_for_18;
                        var_364 = wp::iter_next(var_362);
                        // accepted_pose[i, world] = work[i, world]                               <L 408>
                        var_365 = wp::address(var_work, var_364, var_0);
                        var_367 = wp::load(var_365);
                        var_366 = wp::copy(var_367);
                        wp::array_store(var_accepted_pose, var_364, var_0, var_366);
                        goto start_for_18;
                    end_for_18:;
                }
                if (!var_356) {
                    // result.rejected += 1                                                       <L 410>
                    var_368 = &((var_104).rejected);
                    var_371 = wp::load(var_368);
                    var_370 = wp::add(var_371, var_369);
                    var_104.rejected = var_370;
                    // for i in range(cfg.n):                                                     <L 411>
                    var_372 = &((var_cfg).n);
                    var_374 = wp::load(var_372);
                    var_373 = wp::range(var_374);
                    start_for_20:;
                        if (iter_cmp(var_373) == 0) goto end_for_20;
                        var_375 = wp::iter_next(var_373);
                        // work[i, world] = accepted_pose[i, world]                               <L 412>
                        var_376 = wp::address(var_accepted_pose, var_375, var_0);
                        var_378 = wp::load(var_376);
                        var_377 = wp::copy(var_378);
                        wp::array_store(var_work, var_375, var_0, var_377);
                        goto start_for_20;
                    end_for_20:;
                    // result.final_step = wp.max(cfg.step_floor, result.final_step * cfg.step_reduction)       <L 413>
                    var_379 = &((var_cfg).step_floor);
                    var_380 = &((var_104).final_step);
                    var_381 = &((var_cfg).step_reduction);
                    var_383 = wp::load(var_380);
                    var_384 = wp::load(var_381);
                    var_382 = wp::mul(var_383, var_384);
                    var_386 = wp::load(var_379);
                    var_385 = wp::max(var_386, var_382);
                    var_104.final_step = var_385;
                }
                var_387 = wp::where(var_356, var_364, var_375);
                // if debug == 1:                                                                 <L 414>
                var_389 = (var_debug == var_388);
                if (var_389) {
                    // trace[attempt, world] = result.side                                        <L 415>
                    var_390 = &((var_104).side);
                    var_392 = wp::load(var_390);
                    var_391 = wp::copy(var_392);
                    wp::array_store(var_trace, var_147, var_0, var_391);
                }
                // if result.termination == 4:                                                    <L 416>
                var_393 = &((var_104).termination);
                var_396 = wp::load(var_393);
                var_395 = (var_396 == var_394);
                if (var_395) {
                    // break                                                                      <L 417>
                    wp::assign(var_31, var_387);
                    goto end_for_6;
                }
                var_397 = wp::where(var_395, var_31, var_387);
                // if floor_failed == 1:                                                          <L 418>
                var_399 = (var_354 == var_398);
                if (var_399) {
                    // result.termination = 1                                                     <L 419>
                    var_104.termination = var_400;
                    // if stalled == 1:                                                           <L 420>
                    var_402 = (var_163 == var_401);
                    if (var_402) {
                        // result.termination = 2                                                 <L 421>
                        var_104.termination = var_403;
                    }
                    // break                                                                      <L 422>
                    wp::assign(var_31, var_397);
                    goto end_for_6;
                }
                var_404 = wp::where(var_399, var_31, var_397);
                wp::assign(var_31, var_404);
                goto start_for_6;
            end_for_6:;
            // gap, wall, finite = residuals(accepted_pose, world, cfg.n, result.side)            <L 423>
            var_405 = &((var_cfg).n);
            var_406 = &((var_104).side);
            var_410 = wp::load(var_405);
            var_411 = wp::load(var_406);
            residuals_1(var_accepted_pose, var_0, var_410, var_411, var_407, var_408, var_409);
            // result.min_gap = gap                                                               <L 424>
            var_104.min_gap = var_407;
            // result.min_wall = wall                                                             <L 425>
            var_104.min_wall = var_408;
            // result.max_penetration = wp.max(0.0, -wp.min(gap, wall))                           <L 426>
            var_413 = wp::min(var_407, var_408);
            var_414 = wp::neg(var_413);
            var_415 = wp::max(var_412, var_414);
            var_104.max_penetration = var_415;
            // result.feasible = int(finite == 1 and wp.min(gap, wall) >= cfg.guard - cfg.acceptance_tolerance)       <L 427>
            var_418 = (var_409 == var_417);
            var_416 = var_418;
            if (var_416) {
                var_419 = wp::min(var_407, var_408);
                var_420 = &((var_cfg).guard);
                var_421 = &((var_cfg).acceptance_tolerance);
                var_423 = wp::load(var_420);
                var_424 = wp::load(var_421);
                var_422 = wp::sub(var_423, var_424);
                var_425 = (var_419 >= var_422);
                var_416 = var_416 && var_425;
            }
            var_426 = wp::int(var_416);
            var_104.feasible = var_426;
        }
        // results[world] = result                                                                <L 428>
        wp::array_store(var_results, var_0, var_104);
    }
}



extern "C" __global__ void contact_diagnostic_36c8e1d0_cuda_kernel_forward(
    wp::launch_bounds_t<1> dim,
    wp::array_t<wp::vec_t<3, wp::float32>> var_p,
    wp::array_t<wp::vec_t<3, wp::float32>> var_q,
    Parameters_71195d0b var_cfg,
    wp::float32 var_side,
    wp::int32 var_wall_mode,
    wp::array_t<wp::float32> var_values)
{
    wp::tile_shared_storage_t tile_mem;

    for (size_t _idx = static_cast<size_t>(blockDim.x) * static_cast<size_t>(blockIdx.x) + static_cast<size_t>(threadIdx.x);
         _idx < dim.size;
         _idx += static_cast<size_t>(blockDim.x) * static_cast<size_t>(gridDim.x))
    {
            // reset shared memory allocator
        wp::tile_shared_storage_t::init();

        //---------
        // primal vars
        wp::int32 var_0;
        const wp::int32 var_1 = 1;
        bool var_2;
        wp::vec_t<3, wp::float32>* var_3;
        const wp::float32 var_4 = 1.0;
        const wp::float32 var_5 = 0.0;
        wp::vec_t<2, wp::float32> var_6;
        wp::vec_t<3, wp::float32> var_7;
        wp::float32 var_8;
        wp::vec_t<3, wp::float32> var_9;
        wp::vec_t<3, wp::float32>* var_10;
        wp::vec_t<3, wp::float32>* var_11;
        wp::float32 var_12;
        wp::vec_t<2, wp::float32> var_13;
        wp::float32 var_14;
        wp::float32 var_15;
        wp::vec_t<3, wp::float32> var_16;
        wp::vec_t<3, wp::float32> var_17;
        const wp::int32 var_18 = 0;
        const wp::int32 var_19 = 0;
        wp::float32 var_20;
        wp::float32 var_21;
        const wp::int32 var_22 = 1;
        const wp::int32 var_23 = 1;
        wp::float32 var_24;
        wp::float32 var_25;
        const wp::int32 var_26 = 2;
        const wp::int32 var_27 = 3;
        const wp::int32 var_28 = 0;
        wp::float32 var_29;
        const wp::int32 var_30 = 4;
        const wp::int32 var_31 = 1;
        wp::float32 var_32;
        const wp::int32 var_33 = 5;
        const wp::int32 var_34 = 6;
        wp::vec_t<3, wp::float32>* var_35;
        wp::vec_t<3, wp::float32>* var_36;
        wp::vec_t<3, wp::float32> var_37;
        wp::vec_t<3, wp::float32> var_38;
        wp::float32 var_39;
        wp::vec_t<3, wp::float32> var_40;
        wp::vec_t<3, wp::float32> var_41;
        wp::float32 var_42;
        //---------
        // forward
        // def contact_diagnostic(p: wp.array(dtype=wp.vec3), q: wp.array(dtype=wp.vec3),         <L 439>
        // i = wp.tid()                                                                           <L 441>
        var_0 = builtin_tid1d();
        // if wall_mode == 1:                                                                     <L 442>
        var_2 = (var_wall_mode == var_1);
        if (var_2) {
            // updated, motion = correct_wall(p[i], side, wp.vec2(1.0, 0.0), cfg)                 <L 443>
            var_3 = wp::address(var_p, var_0);
            var_6 = wp::vec_t<2, wp::float32>(var_4, var_5);
            var_9 = wp::load(var_3);
            correct_wall_1(var_9, var_side, var_6, var_cfg, var_7, var_8);
            // p[i] = updated                                                                     <L 444>
            wp::array_store(var_p, var_0, var_7);
        }
        if (!var_2) {
            // gap, normal, gp, gq = pair_constraint(p[i], q[i])                                  <L 446>
            var_10 = wp::address(var_p, var_0);
            var_11 = wp::address(var_q, var_0);
            var_16 = wp::load(var_10);
            var_17 = wp::load(var_11);
            pair_constraint_1(var_16, var_17, var_12, var_13, var_14, var_15);
            // values[i, 0] = gap                                                                 <L 447>
            wp::array_store(var_values, var_0, var_18, var_12);
            // values[i, 1] = -normal[0]                                                          <L 448>
            var_20 = wp::extract(var_13, var_19);
            var_21 = wp::neg(var_20);
            wp::array_store(var_values, var_0, var_22, var_21);
            // values[i, 2] = -normal[1]                                                          <L 449>
            var_24 = wp::extract(var_13, var_23);
            var_25 = wp::neg(var_24);
            wp::array_store(var_values, var_0, var_26, var_25);
            // values[i, 3] = gp                                                                  <L 450>
            wp::array_store(var_values, var_0, var_27, var_14);
            // values[i, 4] = normal[0]                                                           <L 451>
            var_29 = wp::extract(var_13, var_28);
            wp::array_store(var_values, var_0, var_30, var_29);
            // values[i, 5] = normal[1]                                                           <L 452>
            var_32 = wp::extract(var_13, var_31);
            wp::array_store(var_values, var_0, var_33, var_32);
            // values[i, 6] = gq                                                                  <L 453>
            wp::array_store(var_values, var_0, var_34, var_15);
            // updated_p, updated_q, motion = correct_pair(p[i], q[i], cfg)                       <L 454>
            var_35 = wp::address(var_p, var_0);
            var_36 = wp::address(var_q, var_0);
            var_40 = wp::load(var_35);
            var_41 = wp::load(var_36);
            correct_pair_1(var_40, var_41, var_cfg, var_37, var_38, var_39);
            // p[i] = updated_p                                                                   <L 455>
            wp::array_store(var_p, var_0, var_37);
            // q[i] = updated_q                                                                   <L 456>
            wp::array_store(var_q, var_0, var_38);
        }
        var_42 = wp::where(var_2, var_8, var_39);
    }
}



extern "C" __global__ void gather_7e00af20_cuda_kernel_forward(
    wp::launch_bounds_t<2> dim,
    wp::array_t<wp::vec_t<3, wp::float32>> var_poses,
    wp::array_t<wp::int32> var_indices,
    wp::array_t<wp::vec_t<3, wp::float32>> var_output,
    wp::int32 var_n)
{
    wp::tile_shared_storage_t tile_mem;

    for (size_t _idx = static_cast<size_t>(blockDim.x) * static_cast<size_t>(blockIdx.x) + static_cast<size_t>(threadIdx.x);
         _idx < dim.size;
         _idx += static_cast<size_t>(blockDim.x) * static_cast<size_t>(gridDim.x))
    {
            // reset shared memory allocator
        wp::tile_shared_storage_t::init();

        //---------
        // primal vars
        wp::int32 var_0;
        wp::int32 var_1;
        bool var_2;
        wp::int32* var_3;
        wp::int32 var_4;
        wp::vec_t<3, wp::float32>* var_5;
        wp::vec_t<3, wp::float32> var_6;
        wp::vec_t<3, wp::float32> var_7;
        //---------
        // forward
        // def gather(poses: wp.array2d(dtype=wp.vec3), indices: wp.array(dtype=int), output: wp.array2d(dtype=wp.vec3), n: int):       <L 432>
        // square, selected = wp.tid()                                                            <L 433>
        builtin_tid2d(var_0, var_1);
        // if square < n:                                                                         <L 434>
        var_2 = (var_0 < var_n);
        if (var_2) {
            // output[selected, square] = poses[square, indices[selected]]                        <L 435>
            var_3 = wp::address(var_indices, var_1);
            var_4 = wp::load(var_3);
            var_5 = wp::address(var_poses, var_0, var_4);
            var_7 = wp::load(var_5);
            var_6 = wp::copy(var_7);
            wp::array_store(var_output, var_1, var_0, var_6);
        }
    }
}

