#!/bin/bash

typeset -i NUM_DIRS=0
typeset -i NUM_TESTS=0
typeset -i NUM_TESTS_OK=0
typeset -i NUM_TESTS_KO=0
KO_TESTS=" "

STOP_IMMEDIATELY=false
RECURSIVE=true
PRINT_COMMAND=false

function test_dir {
  typeset    _dir="$1"
  typeset    _indentation="${2:-}"
  typeset    _subindentation="$_indentation "
  shift 2
  typeset    _subpath
  typeset    _subdir 
  typeset    _subdirs=" "
  typeset    _test
  typeset    _test_library
  typeset    _test_opts_file
  typeset    _test_opts
  typeset    _test_input_file
  typeset    _test_output_file
  typeset    _test_output_file_tmp
  typeset    _test_output
  typeset    _test_diff
  typeset -i _test_exit_code
  typeset    _mu_command
  typeset    _mu_options
  typeset    _mu_base_options
  typeset    _test_status
  typeset    _test_ko_reason
  if [[ ! -d "$_dir" ]] ; then
    echo "ERR: dir '$_dir' does not exists" 1>&2
    return 1
  fi
  #if [[ ! -f "$_dir/EXPECTED_OUTPUT" ]] ; then
  #  echo "ERR: dir '$_dir' does not have file EXPECTED_OUTPUT" 1>&2
  #  return 1
  #fi
  if [[ -f "$_dir/OPTS" ]] ; then
    _mu_base_options=$(cat "$_dir/OPTS")
  fi
  printf "%sDir[%s]\n" "$_indentation" "$_dir"
  NUM_DIRS=$(( $NUM_DIRS + 1 ))
  for _subpath in $(cd "$_dir" && ls -1) ; do
    _path="$_dir/$_subpath"
    if [[ -d "$_path" ]] ; then
      _subdirs="${_subdirs}$_path "
    elif [[ "$_subpath" == test_*.mu ]] ; then
      NUM_TESTS=$(( $NUM_TESTS + 1 ))
      _test=$(echo "$_subpath" | sed -e 's|^test_||g' -e 's|.mu$||g')
      printf "%sTest[%s]..." "$_subindentation" "$_test"
      _test_library="$_dir/$_test.m"
      _test_opts_file="$_dir/$_test.opts"
      _test_input_file="$_dir/$_test.in"
      _test_output_file="$_dir/$_test.out"
      _test_output_file_tmp="$_dir/$_test.tmp"
      _mu_options="$_mu_base_options"
      if [[ -f "$_test_opts_file" ]] ; then
        _test_opts=$(cat "$_test_opts_file")
        _mu_options="${_mu_options} $_test_opts "
      fi
      if [[ -f "$_test_library" ]] ; then
        _mu_options="${_mu_options} -l$_test -L$_dir "
      fi
      if [[ ! -f "$_test_output_file" ]] ; then
        _test_output_file="$_dir/EXPECTED_OUTPUT"
      fi
      _mu_options="${_mu_options} 1> $_test_output_file_tmp 2>&1"
      _mu_command="mu $_path $_mu_options"
      if [[ -f "$_test_input_file" ]] ; then
        _mu_command="cat '$_test_input_file' | $_mu_command"
      fi
      $PRINT_COMMAND && printf "($_mu_command)"
      _test_output=$(eval "$_mu_command") ; _test_exit_code=$?
      if [[ _test_exit_code -ne 0 ]] ; then
        #printf " KO[%s]\n" "$_test_exit_code"
        _test_status=false
        _test_ko_reason="exit_code:${_test_exit_code}"
      else
        if ! diff "$_test_output_file_tmp" "$_test_output_file" 1>/dev/null 2>&1 ; then
          _test_status=false
          _test_ko_reason="diff"
        else
          rm "$_test_output_file_tmp"
          _test_status=true
          _test_ko_reason=""
        fi
      fi
      if $_test_status ; then
        printf "ok\n"
        NUM_TESTS_OK=$(( $NUM_TESTS_OK + 1 ))
      else
        printf "KO[${_test_ko_reason}]\n"
        NUM_TESTS_KO=$(( $NUM_TESTS_KO + 1 ))
        KO_TESTS="$KO_TESTS$_path "
        if $STOP_IMMEDIATELY ; then
          return 1
        fi
      fi
    fi
  done
  if $RECURSIVE ; then
    for _subdir in $_subdirs ; do
      test_dir "$_subdir" "$_indentation " || {
        echo "ERR: cannot test dir $_subdir" 1>&2
        return 1
      }
    done
  fi
}

### M a i n

EMPTY_LIST=" "
dirs="$EMPTY_LIST"
while [[ ${#@} -ne 0 ]] ; do
  arg="$1"
  shift 1
  case "$arg" in
    --help|-h)
      print_help
      exit 0
      ;;
    --dir|-d)
      dirs="${dirs}$1 "
      shift 1
      ;;
    --stop-immediately|--stop|-s)
      STOP_IMMEDIATELY=true
      ;;
    --recursive|-r)
      RECURSIVE=true
      ;;
    --no-recorsive|-n)
      RECURSIVE=false
      ;;
    --print-command|-c)
      PRINT_COMMAND=true
      ;;
    *)
      dirs="${dirs}$arg "
  esac
done

if [[ "$dirs" == "$EMPTY_LIST" ]] ; then
  dirs='.'
fi

for dir in $dirs ; do
  test_dir "$dir"
done

echo "================================================================================"
echo " #DIRS ........... $NUM_DIRS"
echo " #TESTS .......... $NUM_TESTS"
echo " #TESTS[ok] ...... $NUM_TESTS_OK"
echo " #TESTS[ko] ...... $NUM_TESTS_KO"
for d in $KO_TESTS ; do
  echo " KO TEST.......... $d"
done
echo "================================================================================"
