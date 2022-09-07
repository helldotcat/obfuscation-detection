
cd $(dirname "$1")

defendjs --input $(basename "$1") --output $2 --features=control_flow,literals,mangle,compress
