cd "$(dirname $0)"

BIN_DIR=/usr/bin
SOURCE_CODE_DIR=/usr/lib64/python2.6/site-packages/

#copy  running file to /usr/bin
chmod +x conveyor
cp conveyor ${BIN_DIR}
 

#copy source code to /usr/lib64/python2.6/site-packages/
cp -r ../conveyorclient ${SOURCE_CODE_DIR}