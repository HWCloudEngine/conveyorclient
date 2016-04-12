cd "$(dirname $0)"

BIN_DIR=/usr/bin
SOURCE_CODE_DIR=/usr/lib64/python2.6/site-packages/

#delete  running file to /usr/bin
rm -rf  ${BIN_DIR}/conveyor

#delete source code to /usr/lib64/python2.6/site-packages/
rm -rf  ${SOURCE_CODE_DIR}/conveyorclient