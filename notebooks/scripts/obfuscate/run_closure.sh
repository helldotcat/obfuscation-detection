java -jar closure/closure-compiler-v20211006.jar  \
  --compilation_level SIMPLE_OPTIMIZATIONS \
  --js $1 \
  --js_output_file $2
