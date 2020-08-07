#!/bin/bash

color_blue="\e[94m"
color_green="\e[92m"
color_red="\e[91m"
color_default="\e[39m"

benchmark_sets_system=/barrett/scratch/benchmarks
benchmark_sets_user=$(pwd)

runexec_binary="runexec"
runexec_options=""

# Cluster configuration
max_mem_quad=64000
max_mem_octa=128000

# Default options
default_time_limit=1200
default_memory_limit=8000
default_num_cpus=2
default_partition="quad"

# QOS time limits
qos_normal_tlimit=1800                       # 30 min max
qos_max2_tlimit=$((4 * qos_normal_tlimit))   # 2 hours max
qos_max12_tlimit=$((24 * qos_normal_tlimit)) # 12 hours max


# Options
time_limit=""
use_wall_time=""
memory_limit=""
num_cpus=""
qos=""
partition=""
working_dir=""
solver_options=""
benchmark_sets=""
interactive="yes"
multi_argument=
max_jobs_per_node=

re_numeric='^[0-9]+$'


#
# Helper functions
#

function usage ()
{
echo -e "
usage: submit-solver.sh [options] EXECUTABLE

positional arguments:
 EXECUTABLE                            solver binary

optional arguments:
 -h, --help                            show this help message and exit
 -s SCRAMBLER, --scrambler SCRAMBLER   use SCRAMBLER to scramble benchmarks
 -t TRACEEXEC, --traceexec TRACEEXEC   use trace executor TRACEEXEC
 -c DIR, --copy DIR                    copy directory DIR to working directory
 -q QOS, --qos QOS                     use SLURM QOS group
 -p PART, --partition PART             use SLURM partition PART (default: $color_blue$default_partition$color_default)
 --time-limit N                        use time limit of N seconds CPU time
                                       (default: $color_blue$default_time_limit$color_default)
 -m                                    multi-argument jobs
 -w, --wall-time                       use WALL time instead of CPU time
 --memory-limit N                      use memory limit of N MB
                                       (default: $color_blue$default_memory_limit$color_default)
 --cpus N                              allocate N CPUs per job (default: $color_blue$default_num_cpus$color_default)
 --working-dir DIR                     use working directory DIR
 --solver-options \"OPTS\"               run EXECUTABLE with options OPTS
 --benchmark-sets \"SET1 SET2 ...\"      run EXECUTABLE on benchmark sets
 --max-jobs-per-node N                 restrict number of jobs per node to N
"
}

function die ()
{
  [ -n "$interactive" ] && echo -n "  "
  echo -e "[${color_red}error${color_default}] $*" 1>&2
  exit 1
}

function warn ()
{
  [ -n "$interactive" ] && echo -n "  "
  echo -e "[${color_red}warn${color_default}] $*"
  if [ -z "$interactive" ]; then
    exit 1
  fi
}

function info ()
{
  [ -n "$interactive" ] && echo -n "  "
  echo -e "[${color_green}info${color_default}] $*"
}

# Print available benchmark sets
function print_benchmark_sets ()
{
  benchmark_files="$*"
  echo -e "available benchmark sets:"
  cnt=1
  for f in $benchmark_files; do
    n=$(basename "$f")
    s=${n#benchmark_set_}
    num=$(wc -l "$f" | awk '{print $1}')

    d=$(dirname "$f")
    if [[ "$d" == "$benchmark_sets_system" ]]; then
      printf "  %5s $s ($num) [system]\n" "[$cnt]"
    else
      printf "  ${color_blue}%5s $s ($num) [user]${color_default}\n" "[$cnt]"
    fi
    ((cnt+=1))
  done
}

#
# Option parsing
#

while [ $# -gt 0 ]
do
  case $1 in
    -h|--help)
      usage
      exit 1
      ;;
    -s|--scrambler)
      shift
      scrambler="$1"
      ;;
    -t|--traceexec)
      shift
      traceexec="$1"
      ;;
    -c|--copy)
      shift
      copy_dir="$1"
      ;;
    -q|--qos)
      shift
      qos="$1"
      interactive=""
      ;;
    -p|--partition)
      shift
      partition="$1"
      interactive=""
      ;;
    --time-limit)
      shift
      time_limit="$1"
      interactive=""
      ;;
    -w|--wall-time)
      use_wall_time="yes"
      ;;
    --memory-limit)
      shift
      memory_limit="$1"
      interactive=""
      ;;
    --cpus)
      shift
      num_cpus="$1"
      interactive=""
      ;;
    --working-dir)
      shift
      working_dir="$1"
      interactive=""
      ;;
    --solver-options)
      shift
      solver_options="$1"
      interactive=""
      ;;
    --benchmark-sets|--arguments)
      shift
      benchmark_sets="$1"
      interactive=""
      ;;
    --max-jobs-per-node)
      shift
      max_jobs_per_node="$1"
      ;;
    -m)
      multi_argument="yes"
      ;;
    -*)
      die "invalid option '$1'"
      ;;
    *)
      [[ "$solver" != "" ]] && die "executable already set to '$solver'"
      solver="$1"
      ;;
  esac
  shift
done

# Check if current user is in the benchexec group
(getent group benchexec | grep -q "$(whoami)") || \
  die "Your user is not in the 'benchexec' group." \
      "Ask an admin on #cluster to add your user to the 'benchexec' group."

[ -z "$solver" ] && die "no executable specified"
[ ! -e "$solver" ] && die "executable '$solver' does not exist"
[ -d "$solver" ] && die "executable '$solver' is a directory"
[ ! -x "$solver" ] && die "executable '$solver' is not executable"

solver=$(readlink -f "$solver")
solver_name=$(basename "$solver")
info "using solver '$solver'"

if [ -n "$scrambler" ]; then
  scrambler=$(readlink -f "$scrambler")
  scrambler_seed=$RANDOM
  info "using scrambler '$scrambler' with seed '$scrambler_seed'"
fi

[ -n "$traceexec" ] && info "using trace executor '$traceexec'"
[[ -n "$traceexec" && -z "$scrambler" ]] && \
  die "trace executor needs scrambler"

[[ -n "$copy_dir" && ! -e "$copy_dir" ]] && \
  die "copy directory '$copy_dir' does not exist"

#
# Find available system and user benchmark sets
#
find_paths="$benchmark_sets_user"
if [ -e "$benchmark_sets_system" ]; then
  find_paths="$find_paths $benchmark_sets_system"
fi
sets=$(find $find_paths -maxdepth 1 -type f -name 'benchmark_set_*' | sort)

[[ -z "$sets" ]] && \
  die "no benchmark sets found in " \
      "'$benchmark_sets_system' and '$benchmark_sets_user'"

if [ -n "$interactive" ]; then
  print_benchmark_sets "$sets"
fi

declare -A benchmark_list
declare -A benchmark_list_rev
declare -A benchmark_files
cnt=1
for f in $sets; do
  file_name=$(basename "$f")
  set_name=${file_name#benchmark_set_}
  benchmark_list[$cnt]=$set_name
  benchmark_list_rev[${set_name,,}]=$cnt
  benchmark_files[$cnt]=$f
  ((cnt+=1))
done

# Select benchmark sets
benchmark_indices=""
while true;
do
  if [ -n "$interactive" ]; then
    read -e -p \
      "select benchmark set (default: ${benchmark_list[1]}): " benchmark_sets
  fi

  msg="no benchmarks selected"

  # Allow bash range syntax {n..m} for selecting multiple benchmark sets
  if [[ "$benchmark_sets" == *".."* ]]; then
    benchmark_sets="$(eval echo "$benchmark_sets")"
  fi
  IFS=" " read -r -a sets <<< "$benchmark_sets"
  for bset in "${sets[@]}"; do
    if [[ "$bset" =~ $re_numeric ]]; then
      if (( bset >= 1 && bset < cnt)); then
        benchmark_indices="$benchmark_indices $bset"
        continue
      fi
    else
      regex="$bset"
      if [[ "$bset" == *"*"* ]]; then
        regex="${bset//\*/.*}" # Replace * with .* to have proper wildcard
        msg="no matching benchmark sets found with '$bset'"
      fi
      for s in "${benchmark_list[@]}"; do
        if [[ "$s" =~ ^$regex$ ]]; then
          s=${s,,}
          if [ -n "${benchmark_list_rev[$s]}" ]; then
            benchmark_indices="$benchmark_indices ${benchmark_list_rev[$s]}"
          fi
        fi
      done
      continue
    fi
  done
  if [ -z "$benchmark_indices" ]; then
    warn "$msg"
  else
    break
  fi
done
benchmark_sets=""
num_benchmark_sets=0
info "using benchmark set(s):"
for idx in $benchmark_indices; do
  file="${benchmark_files[$idx]}"
  info "  $file"
  benchmark_sets="$benchmark_sets $file"
  (( num_benchmark_sets++ ))
  [[ $(tail -c1 "$file" | wc -l) == 0 ]] && \
    die "Benchmark set file '$file' does not end with a newline"
done

#
# Choose working directory
#
while true
do
  if [ -n "$interactive" ]; then
    read -e -p "choose working directory: " working_dir
  fi
  if [ -z "$working_dir" ]; then
    warn "no working directory specified"
    continue
  fi
  if [ ! -d "$working_dir" ]; then
    break
  fi
  warn "directory '$working_dir' already exists"
done
info "using directory '${working_dir}'"

#
# Configure solver options
#
if [ -n "$interactive" ]; then
  read -e -p "choose '$solver_name' options: " solver_options
fi
[ -n "$solver_options" ] && info "using options '$solver_options'"

#
# Choose partition
#
while true
do
  if [ -n "$interactive" ]; then
    echo "cluster partition:"
    echo "  [1] quad: 2x4 CPUs 3.5GHz/64GB (default)"
    echo "  [2] octa: 2x8 CPUs 2.1GHz/128GB"
    read -e -p "choose partition (default: $default_partition): " partition
  fi
  case "$partition" in
    ""|1)
      partition="$default_partition"
      break
      ;;
    2)
      partition="octa"
      break
      ;;
    quad|octa|all)
      break
      ;;
    *)
      warn "invalid partition '$partition' choose 'quad octa all'"
      ;;
  esac
done
info "using partition '$partition'"

#
# Choose time limit
#
while true
do
  if [ -n "$interactive" ]; then
    read -p "choose time limit (default: $default_time_limit): " time_limit
  fi

  if [ -z "$time_limit" ]; then
    time_limit=$default_time_limit
    break
  elif [[ "$time_limit" == "0" ]]; then
    warn "unlimited time limit not allowed"
    continue
  elif [[ "$qos" == "normal" && "$time_limit" -gt "$qos_normal_tlimit" ]]; then
    warn "QOS '$qos' has a maximum time limit of $qos_normal_tlimit seconds"
    continue
  elif [[ "$qos" == "max2" && "$time_limit" -gt "$qos_max2_tlimit" ]]; then
    warn "QOS '$qos' has a maximum time limit of $qos_max2_tlimit seconds"
    continue
  elif [[ "$qos" == "max12" && "$time_limit" -gt "$qos_max12_tlimit" ]]; then
    warn "QOS '$qos' has a maximum time limit of $qos_max12_tlimit seconds"
    continue
  fi
  if [[ ! $time_limit =~ $re_numeric ]]; then
    warn "time limit '$time_limit' is not a number"
    continue
  else
    break
  fi
done
info "using time limit '$time_limit'"

#
# Choose memory limit
#
while true
do
  if [ -n "$interactive" ]; then
    read -p \
      "choose space limit (default: ${default_memory_limit}MB): " memory_limit
  fi

  if [ -z "$memory_limit" ]; then
    memory_limit=$default_memory_limit
    break
  fi
  if [[ ! $memory_limit =~ $re_numeric ]]; then
    warn "space limit '$memory_limit' is not a number"
    continue
  else
    break
  fi
done
info "using memory limit of ${memory_limit}M"


# maximum number of CPUs depends on selected partition
if [[ "$partition" == "octa" ]]; then
  num_virtual_cores=32
else
  num_virtual_cores=16
fi

num_physical_cores=$((num_virtual_cores / 2))
max_num_cpus=$num_virtual_cores

#
# Choose number of CPUs per job
#
while true
do
  if [ -n "$interactive" ]; then
    read -p \
      "choose CPUs/job (default: $default_num_cpus, max = $max_num_cpus): " \
      num_cpus
  fi

  if [ -z "$num_cpus" ]; then
    num_cpus=$default_num_cpus
    break
  fi
  if [[ ! $num_cpus =~ $re_numeric ]]; then
    warn "'$num_cpus' is not a number"
    continue
  fi
  if [[ $num_cpus -lt 1 || $num_cpus -gt $max_num_cpus ]]; then
    warn "number of CPUs must be between 1 and $max_num_cpus"
    continue
  else
    break
  fi
done
info "using $num_cpus CPUs"


#
# Select QOS based on time limit
#
if [ -z "$qos" ]; then
  if [[ "$time_limit" -le "$qos_normal_tlimit" ]]; then
    qos="normal"
  elif [[ "$time_limit" -le "$qos_max2_tlimit" ]]; then
    qos="max2"
  else
    qos="max12"
  fi
fi
info "using QOS '$qos'"


#
# Configure runexec options
#
if [[ $time_limit != 0 ]]; then
  if [ -z "$use_wall_time" ]; then
    runexec_options="--timelimit $time_limit"
  else
    runexec_options="--walltimelimit $time_limit"
  fi
fi
runexec_options="$runexec_options --memlimit ${memory_limit}MB"
info "using runexec options: $runexec_options"

#
# Compute maximum number of jobs per node
# This is done via memory allocation since this allows more fine grained
# allocation.
#
memory_limit_slurm=0
if [ -n "$max_jobs_per_node" ]; then
  if [ "$partition" == "quad" ]; then
    ((memory_limit_slurm=max_mem_quad/max_jobs_per_node))
    info "restricting number of jobs per node to: $max_jobs_per_node"
  elif [ "$partition" == "octa" ]; then
    ((memory_limit_slurm=max_mem_octa/max_jobs_per_node))
    info "restricting number of jobs per node to: $max_jobs_per_node"
  fi
fi
if ((memory_limit_slurm < memory_limit)); then
  memory_limit_slurm=$memory_limit
fi

#
# Setup working directory
#
mkdir -p "$working_dir"
working_dir="$(realpath "$working_dir")"

# Create options file
{
  if [ -z "$use_wall_time" ]; then
    echo "cpu time limit:  $time_limit"
  else
    echo "wall time limit: $time_limit"
  fi
  echo "memory limit:    $memory_limit"
  echo "command:         $solver_name $solver_options"
  echo "runexec:         $runexec_options"
  echo "qos:             $qos"
  echo "partition:       $partition"
  if [ -n "$scrambler" ]; then
    echo "scrambler:       $scrambler"
    echo "scrambler seed:  $scrambler_seed"
  fi
  if [ -n "$traceexec" ]; then
    echo "traceexec:       $traceexec"
  fi
  if [ -n "$max_jobs_per_node" ]; then
    echo "jobs per node:  $max_jobs_per_node"
  fi
} > "$working_dir/options"

#
# Setup binaries/scripts
#

# Copy solver binary
cp "$solver" "$working_dir"

# Copy contents of directory
[ -n "$copy_dir" ] && cp -a "$copy_dir/." "$working_dir/"

# Copy scrambler
if [ -n "$scrambler" ]; then
  cp "$scrambler" "$working_dir/"
  scrambler_name="$(basename "$scrambler")"
fi

# Wrap solver for trace executor
if [ -n "$traceexec" ]; then
  cp "$traceexec" "$working_dir/"
  cat > "$working_dir/solver-wrapped.sh" << EOF
#!/bin/sh
$solver_name $solver_options \$1
EOF
  chmod +x "$working_dir/solver-wrapped.sh"
  solver_name=$(basename "$traceexec")
  solver_options="./solver-wrapped.sh"
fi

#
# Create array job for each benchmark set
#
for benchmark_set in $benchmark_sets; do
  set_name="$(basename "$benchmark_set")"
  set_name="${set_name#benchmark_set_}"
  working_dir_set="$working_dir/$set_name"
  mkdir -p "$working_dir_set"

  # Save benchmarks file, solver
  cp "$benchmark_set" "$working_dir_set/benchmarks"

  # Number of benchmark files = number of jobs in the array job
  ntasks=$(wc -l "$benchmark_set" | cut -d ' ' -f 1)

  # Single-argument script: benchmark set files contain an input file per line
  COMMAND=""
  if [ -z "$multi_argument" ]; then

    # Get most common prefix of all benchmark files
    prefix=$(
  python - <<EOF
from os.path import dirname, commonprefix
path = dirname(commonprefix(open('$benchmark_set').readlines()))
if path: print('{}/'.format(path))
EOF
    )

    # Create wrapper for scrambler and solver
    # Scrambler is run within runexec environment
    if [ -n "$scrambler_name" ]; then
      cat > "scrambler-wrapper.sh" << EOF
#!/bin/sh
INPUT_FILE="/tmp/\$(basename \"\$1\")"
./$scrambler_name \"\$BENCHMARK\" $scrambler_seed > "\$INPUT_FILE"
./$solver_name $solver_options "\$INPUT_FILE\"
EOF
      chmod +x "scrambler-wrapper.sh"
      COMMAND="$working_dir/scrambler-wrapper.sh \"\$ARGS\""
    fi

    WSUBDIR="\${ARGS#$prefix}"
  else
    WSUBDIR="slurm-\${SLURM_ARRAY_TASK_ID}"
  fi

  if [ -z "$COMMAND" ]; then
    COMMAND="$working_dir/$solver_name $solver_options"
    if [ -z "$multi_argument" ]; then
      COMMAND="$COMMAND \$ARGS"
    else
      COMMAND="$COMMAND \$ARGS"
    fi
  fi

  # Create sbatch script
  SBATCH_SCRIPT="$working_dir_set/script.sh"

  cat > "$SBATCH_SCRIPT" << EOF
#!/bin/bash
#SBATCH -e /dev/null
#SBATCH -o /dev/null
#SBATCH -c $num_cpus
#SBATCH -a 1-$ntasks
#SBATCH --qos=$qos
#SBATCH --partition=$partition
#SBATCH -t 00:00:$time_limit
#SBATCH --mem=${memory_limit_slurm}M
#SBATCH -D $working_dir

set -e -o pipefail

ARGS="\$(sed \${SLURM_ARRAY_TASK_ID}'q;d' $working_dir_set/benchmarks)"
LOGDIR="$working_dir_set/$WSUBDIR"
mkdir -p "\$LOGDIR"
out="\$LOGDIR/run.out"
OUTPUT="\$LOGDIR/output.log"

export ARGS
export OUTPUT
export LOGDIR
(
  echo "c host:       \$(hostname)"
  echo "c start:      \$(date)"
  echo "c arrayjobid: \${SLURM_ARRAY_JOB_ID}"
  echo "c jobid:      \${SLURM_JOB_ID}"
  echo "c command:    $COMMAND"
  echo "c args:       \$ARGS"

  $runexec_binary $runexec_options --dir "\$LOGDIR" --full-access-dir "\$LOGDIR" --full-access-dir "/barrett/scratch/haozewu/" --output "\${OUTPUT}" -- $COMMAND

  echo "c done"
) > "\$out" 2>&1
EOF

  # Create sub shell, change working directory and execute script
  (cd "$working_dir_set" && exec sbatch --job-name="$set_name" ./script.sh)
done
