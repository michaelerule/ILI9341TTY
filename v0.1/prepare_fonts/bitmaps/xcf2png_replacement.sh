#!/bin/bash
# the utility xcf2png no longer works, this attempts to replace it using Gimp's built-in scripting language


{
cat <<EOF
(define (converttopng filename savename)
  (let* (
    (image (car (gimp-file-load RUN-NONINTERACTIVE filename filename)))
    (drawable (car (gimp-image-get-active-layer image))) 
  )
  (file-png-save RUN-NONINTERACTIVE image drawable savename savename 0 6 0 0 0 1 1)
  (gimp-image-delete image)
))
(gimp-message-set-handler 1)
EOF

for i in "$@"; do
  echo "(gimp-message \"$i\")"
  echo "(converttopng \"$i\" \"${i%%.xcf}.png\")"
done
echo "(gimp-quit 0)"
} | gimp -i -b -
